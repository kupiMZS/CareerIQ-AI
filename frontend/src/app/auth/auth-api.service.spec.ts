import {
  HttpClient,
  HttpErrorResponse,
  provideHttpClient,
  withInterceptors
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { AuthApiService } from './auth-api.service';
import { authInterceptor } from './auth.interceptor';
import { AuthTokenStore } from './auth-token.store';
import { AuthUser, LoginCredentials } from './auth.models';

describe('AuthApiService', () => {
  let service: AuthApiService;
  let requests: HttpTestingController;
  let tokens: AuthTokenStore;
  let http: HttpClient;

  const credentials: LoginCredentials = {
    email: 'synthetic@example.test',
    password: 'synthetic-test-password'
  };

  const user: AuthUser = {
    id: 42,
    name: 'Synthetic User',
    email: 'synthetic@example.test',
    created_at: '2026-10-29T00:00:00.000000Z'
  };

  const validLoginResponse = {
    success: true,
    message: 'Login successful',
    data: {
      user,
      token: '42|synthetic-sanctum-token'
    }
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting()
      ]
    });

    service = TestBed.inject(AuthApiService);
    requests = TestBed.inject(HttpTestingController);
    tokens = TestBed.inject(AuthTokenStore);
    http = TestBed.inject(HttpClient);
  });

  afterEach(() => {
    requests.verify();
  });

  it('does not send login or change state before subscription', () => {
    tokens.setToken('previous-synthetic-token');

    service.login(credentials);

    requests.expectNone('/api/v1/login');
    expect(tokens.getToken()).toBe('previous-synthetic-token');
  });

  it('logs in and stores the valid bearer token in memory', () => {
    let received: AuthUser | undefined;

    service.login(credentials).subscribe((result) => {
      received = result;
    });

    const request = requests.expectOne('/api/v1/login');

    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual(credentials);
    expect(request.request.headers.has('Authorization')).toBe(false);

    request.flush(validLoginResponse);

    expect(received).toEqual(user);
    expect(tokens.getToken()).toBe('42|synthetic-sanctum-token');
    expect(tokens.isAuthenticated()).toBe(true);

    http.get('/api/v1/user').subscribe();

    const authenticated = requests.expectOne('/api/v1/user');

    expect(authenticated.request.headers.get('Authorization')).toBe(
      'Bearer 42|synthetic-sanctum-token'
    );

    authenticated.flush({});
  });

  it('rejects malformed login users without storing a token', () => {
    const failures: unknown[] = [];

    service.login(credentials).subscribe({
      error: (error: unknown) => failures.push(error)
    });

    const request = requests.expectOne('/api/v1/login');

    request.flush({
      ...validLoginResponse,
      data: {
        user: { ...user, id: 'invalid' },
        token: 'synthetic-token'
      }
    });

    expect(failures.length).toBe(1);
    expect(tokens.getToken()).toBeNull();
  });

  it('rejects malformed bearer tokens', () => {
    const failures: unknown[] = [];

    service.login(credentials).subscribe({
      error: (error: unknown) => failures.push(error)
    });

    const request = requests.expectOne('/api/v1/login');

    request.flush({
      ...validLoginResponse,
      data: {
        user,
        token: 'invalid token with spaces'
      }
    });

    expect(failures.length).toBe(1);
    expect(tokens.getToken()).toBeNull();
  });

  it('does not retain a previous token after failed login', () => {
    tokens.setToken('old-synthetic-token');

    const failures: HttpErrorResponse[] = [];

    service.login(credentials).subscribe({
      error: (error: HttpErrorResponse) => failures.push(error)
    });

    expect(tokens.getToken()).toBeNull();

    const request = requests.expectOne('/api/v1/login');

    expect(request.request.headers.has('Authorization')).toBe(false);

    request.flush(
      { success: false, message: 'Invalid credentials' },
      { status: 401, statusText: 'Unauthorized' }
    );

    expect(failures.length).toBe(1);
    expect(failures[0]?.status).toBe(401);
    expect(tokens.getToken()).toBeNull();
  });

  it('retrieves the authenticated user with a bearer token', () => {
    tokens.setToken('synthetic-token');

    let received: AuthUser | undefined;

    service.getCurrentUser().subscribe((result) => {
      received = result;
    });

    const request = requests.expectOne('/api/v1/user');

    expect(request.request.method).toBe('GET');
    expect(request.request.headers.get('Authorization')).toBe(
      'Bearer synthetic-token'
    );

    request.flush({
      success: true,
      message: 'User retrieved successfully',
      data: user
    });

    expect(received).toEqual(user);
  });

  it('clears the token when the current-user API returns 401', () => {
    tokens.setToken('expired-synthetic-token');

    const failures: HttpErrorResponse[] = [];

    service.getCurrentUser().subscribe({
      error: (error: HttpErrorResponse) => failures.push(error)
    });

    const request = requests.expectOne('/api/v1/user');

    request.flush(
      { success: false, message: 'Unauthenticated' },
      { status: 401, statusText: 'Unauthorized' }
    );

    expect(failures.length).toBe(1);
    expect(failures[0]?.status).toBe(401);
    expect(tokens.getToken()).toBeNull();
  });

  it('revokes the active token and clears local authentication', () => {
    tokens.setToken('synthetic-token');

    let completed = false;

    service.logout().subscribe({
      complete: () => {
        completed = true;
      }
    });

    const request = requests.expectOne('/api/v1/logout');

    expect(request.request.method).toBe('POST');
    expect(request.request.headers.get('Authorization')).toBe(
      'Bearer synthetic-token'
    );

    request.flush({
      success: true,
      message: 'Logged out successfully',
      data: null
    });

    expect(completed).toBe(true);
    expect(tokens.getToken()).toBeNull();
  });

  it('clears local authentication even if logout fails', () => {
    tokens.setToken('synthetic-token');

    const failures: HttpErrorResponse[] = [];

    service.logout().subscribe({
      error: (error: HttpErrorResponse) => failures.push(error)
    });

    const request = requests.expectOne('/api/v1/logout');

    request.flush(
      { message: 'Service unavailable' },
      { status: 503, statusText: 'Service Unavailable' }
    );

    expect(failures.length).toBe(1);
    expect(failures[0]?.status).toBe(503);
    expect(tokens.getToken()).toBeNull();
  });

  it('does not call logout when there is no active token', () => {
    let completed = false;

    service.logout().subscribe({
      complete: () => {
        completed = true;
      }
    });

    requests.expectNone('/api/v1/logout');
    expect(completed).toBe(true);
    expect(tokens.getToken()).toBeNull();
  });
});
