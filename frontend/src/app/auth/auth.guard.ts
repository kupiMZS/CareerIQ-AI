import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthTokenStore } from './auth-token.store';

export const authGuard: CanActivateFn = () => {
  const tokens = inject(AuthTokenStore);

  return tokens.isAuthenticated()
    ? true
    : inject(Router).createUrlTree(['/login']);
};
