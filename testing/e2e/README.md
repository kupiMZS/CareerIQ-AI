# CareerIQ-AI ATS Browser E2E

## Purpose

Runs the authenticated Angular -> Laravel -> FastAPI ATS journey
using headless Firefox and a synthetic PDF resume.

Verifies login, upload, explicit ATS generation, eight findings,
no numerical score, exactly one successful FastAPI ATS request,
and no persisted ATS analysis.

## Run

From the repository root:

    bash testing/e2e/run_ats_browser.sh

The runner resolves the repository root automatically.

## Requirements

- Linux, Bash, Python 3, curl, Docker Compose, and Node dependencies.
- Firefox Snap and its bundled GeckoDriver.
- Writable $HOME/snap/firefox/common directory.
- Existing development containers running.
- Expected Git branch; HEAD must remain unchanged during each run.

The runner is specific to this Linux development environment.
It is not yet a portable CI workflow.

## CI checkout mode

Local development mode is the default. It preserves the existing
branch and protected Angular configuration safeguards.

For a clean CI checkout, run:

    CAREERIQ_E2E_CI=1 bash testing/e2e/run_ats_browser.sh

CI mode accepts detached HEAD and requires a clean working tree.
It verifies that Git HEAD and the working tree remain unchanged.

CI mode also selects a standalone GeckoDriver executable
from PATH and creates a temporary Firefox profile under $HOME.
The local default continues to use Snap Firefox and its bundled
GeckoDriver, with profiles under $HOME/snap/firefox/common.

CI requires a compatible Firefox and standalone GeckoDriver
installation, Docker image preparation, and service configuration
before the complete browser test can run in GitHub Actions.

## Isolation

The runner uses separate temporary Laravel and FastAPI containers,
SQLite, private storage, a synthetic PDF, dynamic localhost ports,
and a temporary Firefox profile.

It does not use the normal development MySQL database for test data.

## Cleanup

The runner closes Firefox, terminates the verified GeckoDriver PID,
stops the temporary Angular server, verifies port release, removes
temporary containers, and cleans temporary files on success.

On failure, diagnostics are retained. Inspect exact paths and
process ownership before attempting manual cleanup.

## Repository safety

The runner protects the existing frontend/angular.json modification.
It permits only the runner and this README as untracked files.
It does not stage, commit, or push code.

## Additional regression commands

Angular:

    cd frontend
    npm test -- --watch=false
    npm run build

AI engine:

    cd ai-engine
    ruff format --check .
    ruff check .
    python -m pytest -q

Laravel PHPUnit must be run separately with verified in-memory
SQLite and isolated storage. Never target the development database.
