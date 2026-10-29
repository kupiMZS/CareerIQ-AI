import { Routes } from '@angular/router';

import { LoginPage } from './auth/login.page';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'login' },
  { path: 'login', component: LoginPage },
  { path: '**', redirectTo: 'login' }
];
