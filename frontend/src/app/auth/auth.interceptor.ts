import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';

import { AuthTokenStore } from './auth-token.store';

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const token = inject(AuthTokenStore).getToken();

  if (!token || !request.url.startsWith('/api/v1/')) {
    return next(request);
  }

  const path = request.url.split(/[?#]/, 1)[0];

  if (path === '/api/v1/login' || path === '/api/v1/register') {
    return next(request);
  }

  return next(
    request.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    })
  );
};
