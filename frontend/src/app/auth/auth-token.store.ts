import { computed, Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class AuthTokenStore {
  private readonly tokenState = signal<string | null>(null);

  readonly isAuthenticated = computed(
    () => this.tokenState() !== null
  );

  getToken(): string | null {
    return this.tokenState();
  }

  setToken(token: string): void {
    if (
      typeof token !== 'string' ||
      token.length === 0 ||
      token.length > 4096 ||
      !/^\S+$/.test(token)
    ) {
      throw new RangeError('Invalid authentication token.');
    }

    this.tokenState.set(token);
  }

  clear(): void {
    this.tokenState.set(null);
  }
}
