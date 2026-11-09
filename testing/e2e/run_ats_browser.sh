(
  set -euo pipefail
  script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
  cd "$(git -C "$script_dir" rev-parse --show-toplevel)"

  verify_untracked() {
    local file
    while IFS= read -r -d '' file; do
      case "$file" in
        testing/e2e/run_ats_browser.sh|testing/e2e/README.md) ;;
        *)
          echo "FAIL: Unexpected untracked file: $file"
          return 1
          ;;
      esac
    done < <(git ls-files --others --exclude-standard -z)
  }

  verify_local_changes() {
    local file
    local angular_seen=0

    while IFS= read -r -d '' file; do
      case "$file" in
        frontend/angular.json)
          angular_seen=1
          ;;
        testing/e2e/README.md|testing/e2e/run_ats_browser.sh)
          ;;
        *)
          echo "FAIL: Unexpected modified file: $file"
          return 1
          ;;
      esac
    done < <(git diff --name-only -z)

    if [ "$angular_seen" != 1 ]; then
      echo 'FAIL: Expected protected Angular modification missing.'
      return 1
    fi
  }

  echo '=== PHASE 3F: REUSABLE AUTHENTICATED BROWSER E2E ==='

  ci_mode="${CAREERIQ_E2E_CI:-0}"

  case "$ci_mode" in
    0|1) ;;
    *)
      echo 'FAIL: CAREERIQ_E2E_CI must be 0 or 1.'
      exit 1
      ;;
  esac

  initial_head="$(git rev-parse HEAD)"

  if [ "$ci_mode" = 1 ]; then
    test -z "$(git status --porcelain --untracked-files=all)"
    echo 'PASS: Clean CI checkout verified.'
  else
    test "$(git branch --show-current)" = phase3-ats-analysis
    verify_local_changes
    test -z "$(git diff --cached --name-only)"
    verify_untracked
    echo 'PASS: Local development checkpoint verified.'
  fi

  angular_sha="$(sha256sum frontend/angular.json | awk '{print $1}')"
  runner_sha="$(sha256sum testing/e2e/run_ats_browser.sh | awk '{print $1}')"
  readme_sha="$(sha256sum testing/e2e/README.md | awk '{print $1}')"
  test -x frontend/node_modules/.bin/ng
  if [ "$ci_mode" = 1 ]; then
    driver_command="$(command -v geckodriver || true)"
    test -n "$driver_command"
    driver_bin="$(readlink -f "$driver_command")"

    case "$driver_bin" in
      /snap/*|/usr/bin/snap)
        echo 'FAIL: CI requires a standalone GeckoDriver executable.'
        exit 1
        ;;
      /*)
        test -f "$driver_bin"
        test -x "$driver_bin"
        ;;
      *)
        echo 'FAIL: CI GeckoDriver must resolve to an absolute executable.'
        exit 1
        ;;
    esac

    profile_parent="$HOME"
    echo "PASS: Standalone CI GeckoDriver verified: $driver_bin"
  else
    driver_bin="$(readlink -f /snap/firefox/current/usr/lib/firefox/geckodriver 2>/dev/null || true)"

    case "$driver_bin" in
      /snap/firefox/*/usr/lib/firefox/geckodriver)
        test -x "$driver_bin"
        ;;
      *)
        echo 'FAIL: Verified Snap GeckoDriver executable unavailable.'
        exit 1
        ;;
    esac

    profile_parent="$HOME/snap/firefox/common"
    echo "PASS: Direct GeckoDriver verified: $driver_bin"
  fi

  command -v setsid >/dev/null
  command -v ss >/dev/null
  test -d "$profile_parent"
  test -w "$profile_parent"

  umask 077
  scratch="$(mktemp -d "$HOME/careeriq-browser-ats.XXXXXX")"
  profile_root="$(mktemp -d "$profile_parent/careeriq-profile.XXXXXX")"
  ai_name="careeriq-browser-ai-${BASHPID}"
  be_name="careeriq-browser-be-${BASHPID}"
  ui_pid=''
  wd_pid=''

  cleanup() {
    rc=$?
    trap - EXIT
    echo '=== CLEANUP AND FINAL GIT SAFETY ==='
    stop_verified_group() {
      local role="$1" pid="$2" port="$3" marker="$4"
      [ -n "$pid" ] || return 0

      if ! ps -p "$pid" >/dev/null 2>&1; then
        echo "PASS: $role launcher already exited."
        return 0
      fi

      local uid pgid command_line
      uid="$(ps -o uid= -p "$pid" 2>/dev/null | tr -d ' ' || true)"
      pgid="$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' ' || true)"
      command_line="$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)"

      if [ "$uid" != "$(id -u)" ] || [ "$pgid" != "$pid" ] ||
         [[ "$command_line" != *"$marker"* ]] ||
         [[ "$command_line" != *"$port"* ]]; then
        echo "FAIL: Refusing to signal unverified $role PID $pid."
        echo "INFO: $role process: $command_line"
        return 1
      fi

      if ! kill -TERM -- "-$pid" 2>/dev/null; then
        echo "FAIL: SIGTERM denied for verified $role group $pid."
        return 1
      fi

      for attempt in $(seq 1 20); do
        local state
        state="$(ps -o stat= -p "$pid" 2>/dev/null | tr -d ' ' || true)"

        if [ -z "$state" ] || [[ "$state" == Z* ]]; then
          wait "$pid" 2>/dev/null || true
          echo "PASS: $role launcher exited."
          return 0
        fi

        sleep 0.2
      done

      echo "FAIL: $role launcher still running after bounded shutdown."
      return 1
    }

    stop_verified_driver() {
      local pid="$1" port="$2" profile="$3"
      [ -n "$pid" ] || return 0

      if ! ps -p "$pid" >/dev/null 2>&1; then
        echo "PASS: GeckoDriver already exited."
        return 0
      fi

      local uid pgid executable state
      local -a arguments=()

      uid="$(ps -o uid= -p "$pid" 2>/dev/null | tr -d ' ' || true)"
      pgid="$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' ' || true)"
      executable="$(readlink -f "/proc/$pid/exe" 2>/dev/null || true)"

      if ! readarray -d '' -t arguments < "/proc/$pid/cmdline"; then
        echo "FAIL: Cannot inspect GeckoDriver arguments."
        return 1
      fi

      if [ "$uid" != "$(id -u)" ] ||
         [ "$pgid" != "$pid" ] ||
         [ "$executable" != "$driver_bin" ] ||
         [ "${#arguments[@]}" -ne 9 ] ||
         [ "${arguments[1]:-}" != "--host" ] ||
         [ "${arguments[2]:-}" != "127.0.0.1" ] ||
         [ "${arguments[3]:-}" != "--port" ] ||
         [ "${arguments[4]:-}" != "$port" ] ||
         [ "${arguments[5]:-}" != "--profile-root" ] ||
         [ "${arguments[6]:-}" != "$profile" ] ||
         [ "${arguments[7]:-}" != "--log" ] ||
         [ "${arguments[8]:-}" != "error" ]; then
        echo "FAIL: Refusing to signal unverified GeckoDriver PID $pid."
        return 1
      fi

      if ! kill -TERM "$pid" 2>/dev/null; then
        echo "FAIL: SIGTERM denied for GeckoDriver PID $pid."
        return 1
      fi

      for attempt in $(seq 1 30); do
        state="$(ps -o stat= -p "$pid" 2>/dev/null | tr -d ' ' || true)"

        if [ -z "$state" ] || [[ "$state" == Z* ]]; then
          wait "$pid" 2>/dev/null || true
          echo "PASS: Verified GeckoDriver PID exited."
          return 0
        fi

        sleep 0.2
      done

      echo "FAIL: GeckoDriver PID $pid remains running."
      return 1
    }

    verify_port_released() {
      local role="$1" port="$2" listeners
      [ -n "$port" ] || return 0

      if ! listeners="$(ss -H -ltn "( sport = :$port )" 2>/dev/null)"; then
        echo "FAIL: Unable to inspect $role port $port."
        return 1
      fi

      if [ -n "$listeners" ]; then
        echo "FAIL: $role port $port still listening."
        ss -ltnp "( sport = :$port )" || true
        return 1
      fi

      echo "PASS: $role port $port released."
    }

    if ! stop_verified_group Angular "$ui_pid" "${ui_port:-}" 'npm run start'; then
      rc=1
    fi

    if ! stop_verified_driver "$wd_pid" "${wd_port:-}" "$profile_root"; then
      rc=1
    fi

    if ! verify_port_released Angular "${ui_port:-}"; then rc=1; fi
    if ! verify_port_released GeckoDriver "${wd_port:-}"; then rc=1; fi
    if [ "$rc" -ne 0 ]; then
      echo '=== FAILURE DIAGNOSTICS ==='
      tail -20 "$scratch/angular.log" 2>/dev/null || true
      tail -15 "$scratch/geckodriver.log" 2>/dev/null || true
    fi
    for name in "$be_name" "$ai_name"; do
      if [ -n "$(docker ps -aq --filter "name=^/${name}$")" ]; then
        docker rm -f "$name" >/dev/null 2>&1 || rc=1
      fi
      if [ -n "$(docker ps -aq --filter "name=^/${name}$")" ]; then
        echo "FAIL: Temporary container remains: $name"
        rc=1
      else
        echo "PASS: Temporary container absent: $name"
      fi
    done
    case "$profile_root" in
      "$HOME"/snap/firefox/common/careeriq-profile.??????|"$HOME"/careeriq-profile.??????)
        if [ "$rc" -eq 0 ]; then
          rm -rf -- "$profile_root" || rc=1
          echo 'PASS: Temporary Firefox profile root removed.'
        else
          echo "INFO: Keeping Firefox profile diagnostics in $profile_root"
        fi
        ;;
      *) echo 'FAIL: Unsafe Firefox profile cleanup path.'; rc=1 ;;
    esac
    case "$scratch" in
      "$HOME"/careeriq-browser-ats.??????)
        if [ "$rc" -eq 0 ]; then
          rm -rf -- "$scratch" || rc=1
          echo 'PASS: Temporary test files removed.'
        else
          echo "INFO: Keeping failure diagnostics in $scratch"
        fi
        ;;
      *) echo 'FAIL: Unsafe cleanup path.'; rc=1 ;;
    esac
    git_state_ok=0

    if [ "$ci_mode" = 1 ]; then
      if test "$(git rev-parse HEAD)" = "$initial_head" &&
         test -z "$(git status --porcelain --untracked-files=all)" &&
         test "$(sha256sum frontend/angular.json | awk '{print $1}')" = "$angular_sha" &&
         test "$(sha256sum testing/e2e/run_ats_browser.sh | awk '{print $1}')" = "$runner_sha" &&
         test "$(sha256sum testing/e2e/README.md | awk '{print $1}')" = "$readme_sha" &&
         git diff --check; then
        git_state_ok=1
      fi
    else
      if test "$(git branch --show-current)" = phase3-ats-analysis &&
         test "$(git rev-parse HEAD)" = "$initial_head" &&
         verify_local_changes &&
         test -z "$(git diff --cached --name-only)" &&
         verify_untracked &&
         test "$(sha256sum frontend/angular.json | awk '{print $1}')" = "$angular_sha" &&
         test "$(sha256sum testing/e2e/run_ats_browser.sh | awk '{print $1}')" = "$runner_sha" &&
         test "$(sha256sum testing/e2e/README.md | awk '{print $1}')" = "$readme_sha" &&
         git diff --check; then
        git_state_ok=1
      fi
    fi

    if [ "$git_state_ok" = 1 ]; then
      echo 'PASS: Protected repository state unchanged.'
    else
      echo 'FAIL: Git state needs inspection.'
      rc=1
    fi
    git status --short
    if [ "$rc" -eq 0 ]; then
      echo '=== PHASE 3F E2E COMPLETE ==='
    else
      echo '=== PHASE 3F E2E INCOMPLETE ==='
    fi
    exit "$rc"
  }
  trap cleanup EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM

  test -z "$(docker ps -aq --filter "name=^/${ai_name}$")"
  test -z "$(docker ps -aq --filter "name=^/${be_name}$")"

  read -r api_port ui_port wd_port < <(python3 - <<'PY'
import socket
socks = []
for _ in range(3):
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    socks.append(sock)
print(*(s.getsockname()[1] for s in socks))
for sock in socks:
    sock.close()
PY
  )
  export CAREERIQ_UI_PORT="$ui_port" CAREERIQ_WD_PORT="$wd_port"
  export CAREERIQ_TEST_PDF="$scratch/synthetic.pdf"
  echo "Temporary ports: API=$api_port Angular=$ui_port WebDriver=$wd_port"

  python3 - "$api_port" "$scratch/proxy.json" "$CAREERIQ_TEST_PDF" <<'PY'
import json
import sys
from pathlib import Path
port, proxy_file, pdf_file = sys.argv[1:]
original = json.loads(Path('frontend/proxy.conf.json').read_text())
assert original['/api/**']['target'] == 'http://127.0.0.1:8000'
Path(proxy_file).write_text(json.dumps({
    '/api/**': {'target': f'http://127.0.0.1:{port}',
                'changeOrigin': True, 'secure': False}
}))
lines = ['Synthetic ATS Test Resume', 'Email: candidate@example.test',
         'Skills', 'Python Linux Docker', 'Education',
         'Bachelor of Computer Science', 'Experience',
         'Improved deployment efficiency by 20 percent']
stream = ('BT\n/F1 12 Tf\n72 740 Td\n17 TL\n' +
          ''.join(f'({line}) Tj\nT*\n' for line in lines) +
          'ET\n').encode('ascii')
objects = [
    b'<< /Type /Catalog /Pages 2 0 R >>',
    b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    (b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] '
     b'/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>'),
    b'<< /Length ' + str(len(stream)).encode() +
    b' >>\nstream\n' + stream + b'endstream',
    b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
]
pdf = bytearray(b'%PDF-1.4\n')
offsets = []
for i, obj in enumerate(objects, 1):
    offsets.append(len(pdf))
    pdf.extend(f'{i} 0 obj\n'.encode() + obj + b'\nendobj\n')
xref = len(pdf)
pdf.extend(b'xref\n0 6\n0000000000 65535 f \n')
for offset in offsets:
    pdf.extend(f'{offset:010d} 00000 n \n'.encode())
pdf.extend(b'trailer\n<< /Root 1 0 R /Size 6 >>\nstartxref\n' +
           str(xref).encode() + b'\n%%EOF\n')
assert 0 < len(pdf) < 5 * 1024 * 1024
Path(pdf_file).write_bytes(pdf)
print('PASS: Temporary proxy and synthetic PDF prepared.')
PY

  echo '=== START ISOLATED FASTAPI AND LARAVEL CONTAINERS ==='
  docker compose run --rm --no-deps -d \
    --name "$ai_name" --entrypoint python ai-engine \
    -m uvicorn app.main:app --host 0.0.0.0 --port 8000 >/dev/null

  app_key="$(python3 - <<'PY'
import base64
import os
print('base64:' + base64.b64encode(os.urandom(32)).decode())
PY
  )"
  docker compose run --rm --no-deps -d \
    --name "$be_name" -p "127.0.0.1:${api_port}:8000" \
    -e APP_ENV=testing -e APP_DEBUG=false \
    -e DB_CONNECTION=sqlite -e DB_URL= \
    -e DB_DATABASE=/tmp/careeriq-browser-e2e/database.sqlite \
    -e LARAVEL_STORAGE_PATH=/tmp/careeriq-browser-e2e/storage \
    -e FILESYSTEM_DISK=local -e CACHE_STORE=array \
    -e SESSION_DRIVER=array -e QUEUE_CONNECTION=sync \
    -e MAIL_MAILER=array -e "APP_KEY=$app_key" \
    -e "AI_ENGINE_URL=http://${ai_name}:8000" \
    backend sh -c 'sleep 86400' >/dev/null
  unset app_key
  test "$(docker port "$be_name" 8000/tcp)" = "127.0.0.1:$api_port"

  docker exec -i "$be_name" sh -eu -s <<'INNER'
base=/tmp/careeriq-browser-e2e
mkdir -p "$base/storage/app/private" \
  "$base/storage/framework/cache/data" \
  "$base/storage/framework/sessions" \
  "$base/storage/framework/views" "$base/storage/logs"
touch "$DB_DATABASE"
php -r '
require "vendor/autoload.php";
$app = require "bootstrap/app.php";
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
$s = getenv("LARAVEL_STORAGE_PATH");
$ok = config("app.env") === "testing"
    && config("database.default") === "sqlite"
    && config("database.connections.sqlite.database") === getenv("DB_DATABASE")
    && empty(config("database.connections.sqlite.url"))
    && $app->storagePath() === $s
    && config("filesystems.default") === "local"
    && config("filesystems.disks.local.root") === $s."/app/private"
    && config("cache.default") === "array"
    && config("session.driver") === "array"
    && config("queue.default") === "sync"
    && config("services.ai_engine.url") === getenv("AI_ENGINE_URL")
    && str_starts_with(getenv("AI_ENGINE_URL"), "http://careeriq-browser-ai-")
    && !$app->configurationIsCached();
echo $ok ? "PASS: Isolated Laravel configuration.\n" : "FAIL: Isolation.\n";
if (!$ok) exit(1);
'
curl --fail --silent --show-error --noproxy '*' \
  --retry 20 --retry-delay 1 --retry-connrefused --max-time 30 \
  "$AI_ENGINE_URL/health" >/dev/null
php artisan migrate --force --no-interaction --quiet
php -r '
$db = new PDO("sqlite:".getenv("DB_DATABASE"));
foreach (["users", "resumes", "resume_analyses"] as $table) {
    if ((int)$db->query("SELECT COUNT(*) FROM ".$table)->fetchColumn() !== 0) exit(1);
}
echo "PASS: Real FastAPI reachable; test database starts empty.\n";
'
INNER

  docker exec -d "$be_name" php artisan serve \
    --no-reload --host=0.0.0.0 --port=8000
  api_ready=0
  for attempt in $(seq 1 60); do
    code="$(curl --silent --noproxy '*' --max-time 2 \
      -H 'Accept: application/json' --output /dev/null \
      --write-out '%{http_code}' \
      "http://127.0.0.1:$api_port/api/v1/resumes" 2>/dev/null || true)"
    if [ "$code" = 401 ]; then api_ready=1; break; fi
    sleep .5
  done
  test "$api_ready" = 1
  echo 'PASS: Temporary Laravel authenticated endpoint ready.'

  code="$(curl --silent --show-error --noproxy '*' --max-time 30 \
    -H 'Accept: application/json' -H 'Content-Type: application/json' \
    --data '{"name":"Synthetic Browser User","email":"ats-browser@example.test","password":"password123"}' \
    --output "$scratch/registration.json" --write-out '%{http_code}' \
    "http://127.0.0.1:$api_port/api/v1/register")"
  test "$code" = 201
  echo 'PASS: Fictional user registered through temporary Laravel.'

  echo '=== START TEMPORARY ANGULAR AND GECKODRIVER ==='
  setsid bash -c '
    cd frontend
    exec npm run start -- --host 127.0.0.1 --port "$1" --proxy-config "$2"
  ' _ "$ui_port" "$scratch/proxy.json" > "$scratch/angular.log" 2>&1 &
  ui_pid=$!
  ui_ready=0
  for attempt in $(seq 1 120); do
    code="$(curl --silent --noproxy '*' --max-time 2 \
      --output /dev/null --write-out '%{http_code}' \
      "http://127.0.0.1:$ui_port/login" 2>/dev/null || true)"
    if [ "$code" = 200 ]; then ui_ready=1; break; fi
    if ! kill -0 "$ui_pid" 2>/dev/null; then echo 'FAIL: Angular exited.'; exit 1; fi
    sleep .5
  done
  test "$ui_ready" = 1
  code="$(curl --silent --noproxy '*' --max-time 10 \
    -H 'Accept: application/json' --output /dev/null \
    --write-out '%{http_code}' \
    "http://127.0.0.1:$ui_port/api/v1/resumes")"
  test "$code" = 401
  echo 'PASS: Angular and temporary API proxy responding correctly.'
  setsid "$driver_bin" --host 127.0.0.1 --port "$wd_port" \
    --profile-root "$profile_root" \
    --log error > "$scratch/geckodriver.log" 2>&1 &
  wd_pid=$!

  echo '=== TEST REAL FIREFOX USER JOURNEY ==='
  python3 - <<'PY'
import json
import os
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

wd_base = 'http://127.0.0.1:' + os.environ['CAREERIQ_WD_PORT']
app = 'http://127.0.0.1:' + os.environ['CAREERIQ_UI_PORT']
pdf = os.environ['CAREERIQ_TEST_PDF']

def wd(method, path, payload=None, timeout=45):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {} if payload is None else {'Content-Type': 'application/json'}
    req = Request(wd_base + path, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.load(response)['value']
    except HTTPError as exc:
        try:
            err = json.loads(exc.read().decode())['value']
            description = f"{err.get('error')}: {err.get('message')}"
        except (ValueError, KeyError, AttributeError):
            description = 'Unparseable WebDriver error'
        raise AssertionError(
            f'WebDriver {method} {path.rsplit("/", 1)[-1]} HTTP {exc.code}: '
            f'{description}'
        ) from None

def wait(check, label, seconds=40):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        try:
            if check():
                print('PASS:', label, flush=True)
                return
        except Exception:
            pass
        time.sleep(.25)
    raise AssertionError('Timed out: ' + label)

wait(lambda: wd('GET', '/status', timeout=2).get('ready'),
     'GeckoDriver ready', 15)
session = None
try:
    session = wd('POST', '/session', {
        'capabilities': {'alwaysMatch': {
            'browserName': 'firefox',
            'moz:firefoxOptions': {'args': ['-headless']}
        }}
    }, timeout=60)['sessionId']
    print('PASS: Headless Firefox running.', flush=True)
    prefix = '/session/' + session

    def js(code):
        return wd('POST', prefix + '/execute/sync',
                  {'script': code, 'args': []})

    def element(selector):
        result = wd('POST', prefix + '/element',
                    {'using': 'css selector', 'value': selector})
        return result['element-6066-11e4-a52e-4f735466cecf']

    def fill(selector, value):
        wait(lambda: js(f'''
            const e = document.querySelector({json.dumps(selector)});
            return !!e && !e.disabled;
        '''), f'{selector} is enabled')
        try:
            wd('POST', prefix + '/element/' + element(selector) + '/value',
               {'text': value})
        except AssertionError as exc:
            raise AssertionError(f'Input {selector}: {exc}') from None

    def click(selector):
        wait(lambda: js(f'''
            const e = document.querySelector({json.dumps(selector)});
            return !!e && !e.disabled;
        '''), f'{selector} is clickable')
        wd('POST', prefix + '/element/' + element(selector) + '/click', {})

    def ats_count():
        return js('''
            return performance.getEntriesByType('resource')
                .filter(x => x.name.includes('/analysis/ats')).length;
        ''')

    wd('POST', prefix + '/url', {'url': app + '/login'})
    wait(lambda: bool(js('''
        return document.querySelector('#login-email')
          && document.querySelector('button.login');
    ''')), 'Real Angular login page displayed')

    fill('#login-email', 'ats-browser@example.test')
    fill('#login-password', 'password123')
    click('button.login')
    wait(lambda: bool(js("return document.querySelector('a.resume-link');")),
         'Login authenticated against temporary Laravel')
    click('a.resume-link')
    wait(lambda: js('return location.pathname;') == '/resumes'
         and bool(js("return document.querySelector('#resume-upload-file');")),
         'Angular résumé library displayed')

    # Critical correction: wait for Angular loading() to finish.
    wait(lambda: bool(js('''
        const title = document.querySelector('#resume-upload-title');
        const file = document.querySelector('#resume-upload-file');
        return title && file && !title.disabled && !file.disabled;
    ''')), 'Resume input controls enabled after list loading')

    fill('#resume-upload-title', 'Synthetic Browser ATS Resume')
    assert js('return document.querySelector("#resume-upload-title").value;') \
        == 'Synthetic Browser ATS Resume'
    print('PASS: Real résumé title entered.', flush=True)

    fill('#resume-upload-file', pdf)
    assert js('return document.querySelector("#resume-upload-file").files.length;') == 1
    print('PASS: Browser selected synthetic PDF.', flush=True)
    click('button.upload-button')
    wait(lambda: bool(js('''
        return Array.from(document.querySelectorAll('li.panel')).some(
            e => e.textContent.includes('Synthetic Browser ATS Resume')
              && e.querySelector('a.action[href*="/ats"]')
        );
    ''')), 'Synthetic résumé uploaded and listed', 50)

    assert ats_count() == 0, 'ATS request ran during upload'
    print('PASS: No automatic ATS during upload.', flush=True)
    click('a.action[href*="/ats"]')
    wait(lambda: js('return location.pathname;').endswith('/ats')
         and bool(js("return document.querySelector('button.primary');")),
         'ATS page reached through Angular')
    assert ats_count() == 0, 'ATS request ran during navigation'
    assert js("return document.querySelectorAll('li.finding').length;") == 0
    print('PASS: No automatic ATS during navigation.', flush=True)

    click('button.primary')
    wait(lambda: js("return document.querySelectorAll('li.finding').length;") == 8,
         'Eight real ATS findings displayed', 60)
    assert ats_count() == 1, 'Expected exactly one browser ATS request'
    assert js('''
        return !!document.querySelector('#results-heading')
          && document.body.innerText.includes('No numerical ATS score');
    ''')
    print('PASS: Scoreless ATS report displayed.', flush=True)
    print('RESULT: REAL AUTHENTICATED BROWSER JOURNEY VERIFIED', flush=True)
finally:
    if session:
        wd('DELETE', '/session/' + session, timeout=30)
        print('PASS: Firefox session closed.', flush=True)
PY

  echo '=== VERIFY ISOLATED DATA AND FASTAPI REQUEST COUNT ==='
  docker exec "$be_name" php -r '
$db = new PDO("sqlite:".getenv("DB_DATABASE"));
$counts = [];
foreach (["users", "resumes", "resume_analyses"] as $table) {
    $counts[$table] = (int)$db->query("SELECT COUNT(*) FROM ".$table)->fetchColumn();
}
$row = $db->query("SELECT user_id,file_path,file_size FROM resumes LIMIT 1")
    ->fetch(PDO::FETCH_ASSOC);
$path = $row ? getenv("LARAVEL_STORAGE_PATH")."/app/private/".$row["file_path"] : "";
$ok = $counts["users"] === 1 && $counts["resumes"] === 1
    && $counts["resume_analyses"] === 0 && $row
    && str_starts_with($row["file_path"], "resumes/".$row["user_id"]."/")
    && is_file($path) && filesize($path) === (int)$row["file_size"];
echo $ok ? "PASS: One user, one private PDF, zero saved ATS reports.\n"
         : "FAIL: Temporary database/storage counts.\n";
if (!$ok) exit(1);
'
  hits="$(docker logs "$ai_name" 2>&1 \
    | grep -c 'POST /analyze/ats HTTP/1.1.*200' || true)"
  echo "Successful FastAPI ATS requests: $hits"
  test "$hits" = 1
  echo 'PASS: Exactly one ATS call after explicit browser click.'
  echo '=== REAL AUTHENTICATED BROWSER INTEGRATION PASSED ==='
)
