import {
  HttpClient,
  provideHttpClient,
  withInterceptors
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { authInterceptor } from './auth.interceptor';
import { AuthTokenStore } from './auth-token.store';

describe('Angular bearer authentication', () => {
  let http: HttpClient;
  let requests: HttpTestingController;
  let tokens: AuthTokenStore;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting()
      ]
    });

    http = TestBed.inject(HttpClient);
    requests = TestBed.inject(HttpTestingController);
    tokens = TestBed.inject(AuthTokenStore);
  });

  afterEach(() => {
    requests.verify();
  });

  it('starts unauthenticated without persistent credentials', () => {
    expect(tokens.isAuthenticated()).toBe(false);
    expect(tokens.getToken()).toBeNull();

    http.post('/api/v1/resumes/42/analysis/ats', {}).subscribe();

    const request = requests.expectOne(
      '/api/v1/resumes/42/analysis/ats'
    );

    expect(request.request.headers.has('Authorization')).toBe(false);

    request.flush({});
  });

  it('attaches a Sanctum bearer token to protected API requests', () => {
    tokens.setToken('42|synthetic-test-token');

    expect(tokens.isAuthenticated()).toBe(true);

    http.post('/api/v1/resumes/42/analysis/ats', {}).subscribe();

    const request = requests.expectOne(
      '/api/v1/resumes/42/analysis/ats'
    );

    expect(request.request.headers.get('Authorization')).toBe(
      'Bearer 42|synthetic-test-token'
    );

    request.flush({});
  });

  it('never attaches the token to login or registration', () => {
    tokens.setToken('synthetic-token');

    for (const path of ['/api/v1/login', '/api/v1/register']) {
      http.post(path, {}).subscribe();

      const request = requests.expectOne(path);

      expect(request.request.headers.has('Authorization')).toBe(false);

      request.flush({});
    }
  });

  it('does not send the token to external URLs', () => {
    tokens.setToken('synthetic-token');

    const url =
      'https://example.invalid/api/v1/resumes/5/analysis/ats';

    http.get(url).subscribe();

    const request = requests.expectOne(url);

    expect(request.request.headers.has('Authorization')).toBe(false);

    request.flush({});
  });

  it('removes bearer authorization when the session is cleared', () => {
    tokens.setToken('synthetic-token');
    tokens.clear();

    expect(tokens.isAuthenticated()).toBe(false);
    expect(tokens.getToken()).toBeNull();

    http.get('/api/v1/user').subscribe();

    const request = requests.expectOne('/api/v1/user');

    expect(request.request.headers.has('Authorization')).toBe(false);

    request.flush({});
  });

  it('rejects invalid tokens without replacing the current token', () => {
    tokens.setToken('valid-synthetic-token');

    for (const invalid of ['', '  ', 'bad\ntoken']) {
      expect(() => tokens.setToken(invalid)).toThrow(RangeError);
    }

    expect(tokens.getToken()).toBe('valid-synthetic-token');
  });
});
