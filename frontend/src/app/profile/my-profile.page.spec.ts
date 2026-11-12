import {
  provideHttpClient
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting
} from '@angular/common/http/testing';
import {
  ComponentFixture,
  TestBed
} from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it
} from 'vitest';

import { routes } from '../app.routes';
import { authGuard } from '../auth/auth.guard';
import { MyProfilePage } from './my-profile.page';
import { UserProfile } from './profile.models';

describe('MyProfilePage', () => {
  let fixture: ComponentFixture<MyProfilePage>;
  let page: MyProfilePage;
  let http: HttpTestingController;

  const profile: UserProfile = {
    id: 7,
    first_name: 'Ada',
    last_name: 'Example',
    phone: null,
    location: null,
    country: null,
    headline: 'Engineer',
    summary: null,
    linkedin_url: null,
    github_url: null,
    portfolio_url: null,
    years_experience: 3
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MyProfilePage],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    }).compileComponents();

    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(MyProfilePage);
    page = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    http.verify();
  });

  function finishLoad(value: UserProfile | null): void {
    const request = http.expectOne('/api/v1/profile');

    expect(request.request.method).toBe('GET');

    request.flush({
      success: true,
      message: 'Profile retrieved successfully',
      data: value
    });

    fixture.detectChanges();
  }

  it('shows the create form when no profile exists', () => {
    finishLoad(null);

    expect(page.profile()).toBeNull();
    expect(page.loading()).toBe(false);
    expect(fixture.nativeElement.textContent)
      .toContain('Create your profile');
  });

  it('creates a profile using POST', () => {
    finishLoad(null);

    page.form.controls.first_name.setValue('Ada');
    page.form.controls.years_experience.setValue(3);
    page.form.markAsDirty();

    page.saveProfile();

    const request = http.expectOne('/api/v1/profile');

    expect(request.request.method).toBe('POST');
    expect(request.request.body.first_name).toBe('Ada');
    expect(request.request.body.years_experience).toBe(3);

    request.flush({
      success: true,
      message: 'Profile created successfully',
      data: profile
    }, {
      status: 201,
      statusText: 'Created'
    });

    fixture.detectChanges();

    expect(page.profile()?.id).toBe(7);
    expect(page.saving()).toBe(false);
    expect(page.form.pristine).toBe(true);
  });

  it('updates an existing profile using PUT', () => {
    finishLoad(profile);

    page.form.controls.headline.setValue('Lead Engineer');
    page.form.markAsDirty();

    page.saveProfile();

    const request = http.expectOne('/api/v1/profile');

    expect(request.request.method).toBe('PUT');
    expect(request.request.body.headline)
      .toBe('Lead Engineer');

    request.flush({
      success: true,
      message: 'Profile updated successfully',
      data: {
        ...profile,
        headline: 'Lead Engineer'
      }
    });

    fixture.detectChanges();

    expect(page.profile()?.headline).toBe('Lead Engineer');
    expect(page.form.pristine).toBe(true);
  });

  it('does not submit invalid experience values', () => {
    finishLoad(null);

    page.form.controls.years_experience.setValue(81);
    page.saveProfile();

    http.expectNone('/api/v1/profile');

    expect(page.form.invalid).toBe(true);
    expect(page.saveError()).toContain('correct');
  });

  it('enforces Laravel field length limits', () => {
    finishLoad(null);

    const controls = page.form.controls;

    controls.first_name.setValue('A'.repeat(101));
    controls.last_name.setValue('B'.repeat(101));
    controls.phone.setValue('1'.repeat(31));
    controls.location.setValue('C'.repeat(101));
    controls.summary.setValue('D'.repeat(2001));

    const longUrl = 'https://example.com/' + 'x'.repeat(236);
    controls.linkedin_url.setValue(longUrl);
    controls.github_url.setValue(longUrl);
    controls.portfolio_url.setValue(longUrl);

    expect(controls.first_name.hasError('maxlength')).toBe(true);
    expect(controls.last_name.hasError('maxlength')).toBe(true);
    expect(controls.phone.hasError('maxlength')).toBe(true);
    expect(controls.location.hasError('maxlength')).toBe(true);
    expect(controls.summary.hasError('maxlength')).toBe(true);
    expect(controls.linkedin_url.hasError('maxlength')).toBe(true);
    expect(controls.github_url.hasError('maxlength')).toBe(true);
    expect(controls.portfolio_url.hasError('maxlength')).toBe(true);

    page.saveProfile();
    http.expectNone('/api/v1/profile');

    expect(page.form.invalid).toBe(true);
  });

  it('requires confirmation before deleting a profile', () => {
    finishLoad(profile);

    page.deleteProfile();
    http.expectNone('/api/v1/profile');

    page.requestDelete();

    expect(page.confirmingDelete()).toBe(true);

    page.cancelDelete();

    expect(page.confirmingDelete()).toBe(false);

    page.requestDelete();
    page.deleteProfile();

    const request = http.expectOne('/api/v1/profile');

    expect(request.request.method).toBe('DELETE');

    request.flush({
      success: true,
      message: 'Profile deleted successfully',
      data: null
    });

    fixture.detectChanges();

    expect(page.profile()).toBeNull();
    expect(page.confirmingDelete()).toBe(false);
    expect(page.deleting()).toBe(false);
  });

  it('registers the profile route behind authGuard', () => {
    finishLoad(null);

    const route = routes.find(
      (candidate) => candidate.path === 'profile'
    );

    expect(route).toBeDefined();
    expect(route?.component).toBe(MyProfilePage);
    expect(route?.canActivate).toContain(authGuard);
  });
});
