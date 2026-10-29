import {
  provideHttpClient,
  withInterceptors
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting
} from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { authInterceptor } from './auth.interceptor';
import { AuthTokenStore } from './auth-token.store';
import { LoginPage } from './login.page';

describe('LoginPage', () => {
  let fixture: ComponentFixture<LoginPage>;
  let requests: HttpTestingController;
  let tokens: AuthTokenStore;

  const validResponse = {
    success: true,
    message: 'Login successful',
    data: {
      user: {
        id: 42,
        name: 'Synthetic User',
        email: 'synthetic@example.test',
        created_at: null
      },
      token: '42|synthetic-login-token'
    }
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LoginPage],
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting()
      ]
    }).compileComponents();

    requests = TestBed.inject(HttpTestingController);
    tokens = TestBed.inject(AuthTokenStore);

    fixture = TestBed.createComponent(LoginPage);
    fixture.detectChanges();
  });

  afterEach(() => {
    requests.verify();
  });

  function fillInput(selector: string, value: string): void {
    const input = fixture.nativeElement.querySelector(
      selector
    ) as HTMLInputElement;

    expect(input).toBeTruthy();

    input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true }));

    fixture.detectChanges();
  }

  function submitForm(): void {
    const form = fixture.nativeElement.querySelector(
      'form'
    ) as HTMLFormElement;

    expect(form).toBeTruthy();

    form.dispatchEvent(new Event('submit', {
      bubbles: true,
      cancelable: true
    }));

    fixture.detectChanges();
  }

  function enterValidCredentials(): void {
    fillInput('#login-email', 'synthetic@example.test');
    fillInput('#login-password', 'synthetic-password');
  }

  function signIn(): void {
    enterValidCredentials();
    submitForm();

    const request = requests.expectOne('/api/v1/login');

    request.flush(validResponse);
    fixture.detectChanges();
  }

  it('renders the login form without sending a request', () => {
    const element = fixture.nativeElement as HTMLElement;

    expect(element.textContent).toContain('Welcome back');
    expect(element.querySelector('#login-email')).toBeTruthy();
    expect(element.querySelector('#login-password')).toBeTruthy();

    requests.expectNone('/api/v1/login');
    expect(tokens.getToken()).toBeNull();
  });

  it('prevents invalid form submission', () => {
    const element = fixture.nativeElement as HTMLElement;

    const button = element.querySelector(
      'button.login'
    ) as HTMLButtonElement;

    expect(button.disabled).toBe(true);

    submitForm();

    requests.expectNone('/api/v1/login');
  });

  it('logs in and displays the authenticated account', () => {
    enterValidCredentials();
    submitForm();

    const request = requests.expectOne('/api/v1/login');

    expect(request.request.method).toBe('POST');
    expect(request.request.headers.has('Authorization')).toBe(false);
    expect(request.request.body).toEqual({
      email: 'synthetic@example.test',
      password: 'synthetic-password'
    });

    request.flush(validResponse);
    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;

    expect(element.textContent).toContain('Synthetic User');
    expect(element.textContent).toContain('Signed in');
    expect(element.querySelector('button.logout')).toBeTruthy();
    expect(tokens.getToken()).toBe('42|synthetic-login-token');
    expect(element.querySelector('input[type=password]')).toBeNull();
  });

  it('shows a safe error after invalid credentials', () => {
    enterValidCredentials();
    submitForm();

    requests.expectOne('/api/v1/login').flush(
      { success: false, message: 'Invalid credentials' },
      { status: 401, statusText: 'Unauthorized' }
    );

    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;

    expect(element.textContent).toContain('Invalid email or password.');
    expect(tokens.getToken()).toBeNull();

    const password = element.querySelector(
      '#login-password'
    ) as HTMLInputElement;

    expect(password.value).toBe('');
  });

  it('rejects malformed login responses without authentication', () => {
    enterValidCredentials();
    submitForm();

    requests.expectOne('/api/v1/login').flush({
      success: true,
      message: 'Login successful',
      data: {
        user: validResponse.data.user,
        token: 'not a valid token'
      }
    });

    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;

    expect(element.textContent).toContain(
      'Sign-in failed. Please try again.'
    );
    expect(tokens.getToken()).toBeNull();
  });

  it('revokes the session through logout and returns to the form', () => {
    signIn();

    const element = fixture.nativeElement as HTMLElement;

    const button = element.querySelector(
      'button.logout'
    ) as HTMLButtonElement;

    button.click();
    fixture.detectChanges();

    const request = requests.expectOne('/api/v1/logout');

    expect(request.request.method).toBe('POST');
    expect(request.request.headers.get('Authorization')).toBe(
      'Bearer 42|synthetic-login-token'
    );

    request.flush({
      success: true,
      message: 'Logged out successfully',
      data: null
    });

    fixture.detectChanges();

    expect(tokens.getToken()).toBeNull();
    expect(element.textContent).toContain('Welcome back');
  });

  it('reports that server revocation is unconfirmed after logout failure', () => {
    signIn();

    const element = fixture.nativeElement as HTMLElement;

    (element.querySelector('button.logout') as HTMLButtonElement).click();

    requests.expectOne('/api/v1/logout').flush(
      { message: 'Service unavailable' },
      { status: 503, statusText: 'Service Unavailable' }
    );

    fixture.detectChanges();

    expect(tokens.getToken()).toBeNull();
    expect(element.textContent).toContain(
      'Server token revocation could not be confirmed.'
    );
  });
});
