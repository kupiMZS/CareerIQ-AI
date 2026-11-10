import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import {
  catchError,
  defer,
  finalize,
  map,
  Observable,
  of,
  tap,
  throwError
} from 'rxjs';

import { AuthTokenStore } from './auth-token.store';
import { AuthUser, LoginCredentials } from './auth.models';

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' &&
    value !== null &&
    !Array.isArray(value);
}

function parseEnvelope(value: unknown): Record<string, unknown> {
  if (
    !isRecord(value) ||
    value['success'] !== true ||
    typeof value['message'] !== 'string'
  ) {
    throw new Error('Invalid authentication response.');
  }

  return value;
}

function parseUser(value: unknown): AuthUser {
  if (!isRecord(value)) {
    throw new Error('Invalid authentication user.');
  }

  const id = value['id'];
  const name = value['name'];
  const email = value['email'];
  const createdAt = value['created_at'];

  if (
    typeof id !== 'number' ||
    !Number.isSafeInteger(id) ||
    id <= 0 ||
    typeof name !== 'string' ||
    name.trim().length === 0 ||
    typeof email !== 'string' ||
    email.trim().length === 0 ||
    (createdAt !== null && typeof createdAt !== 'string')
  ) {
    throw new Error('Invalid authentication user.');
  }

  return {
    id,
    name,
    email,
    created_at: createdAt
  };
}

@Injectable({ providedIn: 'root' })
export class AuthApiService {
  private readonly http = inject(HttpClient);
  private readonly tokens = inject(AuthTokenStore);

  login(credentials: LoginCredentials): Observable<AuthUser> {
    return defer(() => {
      // Do not retain a previous identity during a new login attempt.
      this.tokens.clear();

      return this.http.post<unknown>('/api/v1/login', credentials).pipe(
        map((response) => {
          const envelope = parseEnvelope(response);
          const data = envelope['data'];

          if (
            !isRecord(data) ||
            typeof data['token'] !== 'string'
          ) {
            throw new Error('Invalid login response.');
          }

          return {
            user: parseUser(data['user']),
            token: data['token']
          };
        }),
        tap(({ token }) => this.tokens.setToken(token)),
        map(({ user }) => user)
      );
    });
  }

  getCurrentUser(): Observable<AuthUser> {
    return defer(() => {
      const requestedToken = this.tokens.getToken();

      return this.http.get<unknown>('/api/v1/user').pipe(
        map((response) => {
          const envelope = parseEnvelope(response);
          return parseUser(envelope['data']);
        }),
        catchError((error: unknown) => {
          if (
            error instanceof HttpErrorResponse &&
            error.status === 401 &&
            this.tokens.getToken() === requestedToken
          ) {
            this.tokens.clear();
          }

          return throwError(() => error);
        })
      );
    });
  }

  logout(): Observable<void> {
    return defer(() => {
      const activeToken = this.tokens.getToken();

      if (activeToken === null) {
        return of(void 0);
      }

      return this.http.post<unknown>('/api/v1/logout', {}).pipe(
        map((response) => {
          parseEnvelope(response);
        }),
        finalize(() => {
          // A later login must not be cleared by an older logout.
          if (this.tokens.getToken() === activeToken) {
            this.tokens.clear();
          }
        })
      );
    });
  }
}
