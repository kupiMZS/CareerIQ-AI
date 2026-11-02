import { TestBed } from '@angular/core/testing';
import {
  ActivatedRouteSnapshot,
  provideRouter,
  Router,
  RouterStateSnapshot,
  UrlTree
} from '@angular/router';

import { authGuard } from './auth.guard';
import { AuthTokenStore } from './auth-token.store';

describe('authGuard', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideRouter([])]
    });
  });

  function evaluateGuard() {
    return TestBed.runInInjectionContext(() =>
      authGuard(
        {} as ActivatedRouteSnapshot,
        {} as RouterStateSnapshot
      )
    );
  }

  it('redirects guests to the login page', () => {
    const result = evaluateGuard();

    expect(result).toBeInstanceOf(UrlTree);

    if (!(result instanceof UrlTree)) {
      throw new Error('Expected login redirect.');
    }

    const router = TestBed.inject(Router);

    expect(router.serializeUrl(result)).toBe('/login');
  });

  it('allows a session held in memory', () => {
    const tokens = TestBed.inject(AuthTokenStore);

    tokens.setToken('synthetic-test-token');

    expect(evaluateGuard()).toBe(true);
  });
});
