import { Routes } from '@angular/router';

import { ResumeAtsPage } from './ats/resume-ats.page';
import { authGuard } from './auth/auth.guard';
import { LoginPage } from './auth/login.page';
import { MyProfilePage } from './profile/my-profile.page';
import { MyResumesPage } from './resumes/my-resumes.page';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'login' },
  { path: 'login', component: LoginPage },
  {
    path: 'profile',
    component: MyProfilePage,
    canActivate: [authGuard]
  },
  {
    path: 'resumes',
    component: MyResumesPage,
    canActivate: [authGuard]
  },
  {
    path: 'resumes/:resumeId/ats',
    component: ResumeAtsPage,
    canActivate: [authGuard]
  },
  { path: '**', redirectTo: 'login' }
];
