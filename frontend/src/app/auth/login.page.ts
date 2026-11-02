import { HttpErrorResponse } from '@angular/common/http';
import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators
} from '@angular/forms';
import { finalize } from 'rxjs';
import { RouterLink } from '@angular/router';

import { AuthApiService } from './auth-api.service';
import { AuthTokenStore } from './auth-token.store';
import { AuthUser } from './auth.models';

@Component({
  selector: 'app-login-page',
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <section class="auth-card" aria-labelledby="login-heading">
      @if (currentUser(); as user) {
        <p class="eyebrow">ACCOUNT</p>
        <h2 id="login-heading">Signed in</h2>
        <p class="description">
          You are signed in as <strong>{{ user.name }}</strong>.
        </p>
        <p class="account-email">{{ user.email }}</p>
        <p class="privacy-note">
          Your session is held in memory and ends when the page reloads.
        </p>
        <a class="resume-link" routerLink="/resumes">
          My résumés
        </a>
        <button
          class="primary logout"
          type="button"
          [disabled]="busy()"
          (click)="signOut()"
        >
          {{ busy() ? 'Signing out…' : 'Sign out' }}
        </button>
      } @else {
        <p class="eyebrow">SECURE ACCOUNT ACCESS</p>
        <h2 id="login-heading">Welcome back</h2>
        <p class="description">
          Sign in to access your CareerIQ AI account and résumé tools.
        </p>

        <form [formGroup]="form" (ngSubmit)="submit()">
          <label for="login-email">Email address</label>
          <input
            id="login-email"
            type="email"
            formControlName="email"
            autocomplete="email"
            placeholder="you@example.com"
          />

          <label for="login-password">Password</label>
          <input
            id="login-password"
            type="password"
            formControlName="password"
            autocomplete="current-password"
            placeholder="Enter your password"
          />

          <button
            class="primary login"
            type="submit"
            [disabled]="busy() || form.invalid"
          >
            {{ busy() ? 'Signing in…' : 'Sign in' }}
          </button>
        </form>

        <p class="privacy-note">
          This page does not save your authentication token
          in browser storage.
        </p>
      }

      @if (errorMessage()) {
        <p class="error" role="alert">{{ errorMessage() }}</p>
      }
    </section>
  `,
  styles: [`
    :host {
      display: block;
      padding: 1.5rem 1rem;
      color: #152338;
      font-family: system-ui, -apple-system, sans-serif;
    }

    .auth-card {
      box-sizing: border-box;
      max-width: 440px;
      margin: 1.5rem auto;
      padding: 2.5rem;
      background: #ffffff;
      border: 1px solid #e3e9f1;
      border-radius: 18px;
      box-shadow: 0 12px 40px rgba(16, 35, 65, .07);
    }

    .eyebrow {
      margin: 0 0 1rem;
      color: #3769a9;
      font-size: .72rem;
      font-weight: 750;
      letter-spacing: .12em;
    }

    h2 {
      font-size: 1.85rem;
      letter-spacing: -.04em;
      margin: 0 0 .7rem;
    }

    .description {
      color: #5b687a;
      font-size: .95rem;
      line-height: 1.65;
      margin-bottom: 1.75rem;
    }

    form {
      display: flex;
      flex-direction: column;
    }

    label {
      font-weight: 650;
      font-size: .9rem;
      margin-bottom: .5rem;
    }

    input {
      box-sizing: border-box;
      width: 100%;
      padding: .85rem;
      margin-bottom: 1.2rem;
      border: 1px solid #cbd5e1;
      border-radius: 9px;
      background: white;
      color: #152338;
      font: inherit;
    }

    input:focus-visible,
    button:focus-visible {
      outline: 3px solid #9bc6ff;
      outline-offset: 2px;
    }

    .resume-link {
      display: block;
      margin: 1rem 0;
      padding: .8rem 1.2rem;
      border-radius: 9px;
      background: #edf4ff;
      color: #1858a4;
      font-weight: 700;
      text-align: center;
      text-decoration: none;
    }

    .resume-link:focus-visible {
      outline: 3px solid #9bc6ff;
      outline-offset: 3px;
    }

    .primary {
      width: 100%;
      padding: .9rem 1.2rem;
      border: 0;
      border-radius: 9px;
      background: #1858a4;
      color: white;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }

    .primary:disabled {
      opacity: .55;
      cursor: not-allowed;
    }

    .privacy-note,
    .account-email {
      color: #64748b;
      font-size: .85rem;
      line-height: 1.6;
    }

    .privacy-note {
      margin-top: 1.25rem;
    }

    .error {
      margin-top: 1.2rem;
      padding: .85rem;
      background: #fff1f2;
      border: 1px solid #fecdd3;
      border-radius: 8px;
      color: #9f1239;
      font-size: .9rem;
      line-height: 1.5;
    }
  `]
})
export class LoginPage {
  private readonly auth = inject(AuthApiService);
  private readonly tokens = inject(AuthTokenStore);
  private readonly destroyRef = inject(DestroyRef);

  readonly form = new FormGroup({
    email: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.email]
    }),
    password: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required]
    })
  });

  readonly busy = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly currentUser = signal<AuthUser | null>(null);

  submit(): void {
    if (this.busy() || this.form.invalid || this.currentUser()) {
      return;
    }

    this.busy.set(true);
    this.errorMessage.set(null);

    this.auth.login(this.form.getRawValue()).pipe(
      takeUntilDestroyed(this.destroyRef),
      finalize(() => this.busy.set(false))
    ).subscribe({
      next: (user) => {
        this.currentUser.set(user);
        this.form.controls.password.reset();
      },
      error: (error: unknown) => {
        this.form.controls.password.reset();

        this.errorMessage.set(
          error instanceof HttpErrorResponse && error.status === 401
            ? 'Invalid email or password.'
            : 'Sign-in failed. Please try again.'
        );
      }
    });
  }

  signOut(): void {
    if (this.busy() || !this.tokens.isAuthenticated()) {
      return;
    }

    this.busy.set(true);
    this.errorMessage.set(null);

    this.auth.logout().pipe(
      takeUntilDestroyed(this.destroyRef),
      finalize(() => this.busy.set(false))
    ).subscribe({
      complete: () => {
        this.currentUser.set(null);
      },
      error: () => {
        this.currentUser.set(null);
        this.errorMessage.set(
          'Signed out locally. Server token revocation could not be confirmed.'
        );
      }
    });
  }
}
