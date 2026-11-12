import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
  HttpErrorResponse,
  provideHttpClient
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { ProfileApiService } from './profile-api.service';
import { UserProfile } from './profile.models';

describe('ProfileApiService', () => {
  let service: ProfileApiService;
  let http: HttpTestingController;

  const profile: UserProfile = {
    id: 1,
    first_name: 'Example',
    last_name: 'User',
    phone: null,
    location: null,
    country: null,
    headline: 'Software Engineer',
    summary: null,
    linkedin_url: null,
    github_url: null,
    portfolio_url: null,
    years_experience: 3
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });

    service = TestBed.inject(ProfileApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('returns null when no profile exists', () => {
    let result: UserProfile | null | undefined;

    service.getProfile().subscribe((value) => {
      result = value;
    });

    const request = http.expectOne('/api/v1/profile');

    expect(request.request.method).toBe('GET');

    request.flush({
      success: true,
      message: 'Profile retrieved successfully',
      data: null
    });

    expect(result).toBeNull();
  });

  it('loads an existing profile', () => {
    let result: UserProfile | null | undefined;

    service.getProfile().subscribe((value) => {
      result = value;
    });

    const request = http.expectOne('/api/v1/profile');

    request.flush({
      success: true,
      message: 'Profile retrieved successfully',
      data: profile
    });

    expect(result).toEqual(profile);
  });

  it('creates a profile with POST', () => {
    let result: UserProfile | undefined;

    service.createProfile({
      first_name: 'Example',
      years_experience: 3
    }).subscribe((value) => {
      result = value;
    });

    const request = http.expectOne('/api/v1/profile');

    expect(request.request.method).toBe('POST');
    expect(request.request.body.first_name).toBe('Example');

    request.flush({
      success: true,
      message: 'Profile created successfully',
      data: profile
    }, {
      status: 201,
      statusText: 'Created'
    });

    expect(result).toEqual(profile);
  });

  it('updates a profile with PUT', () => {
    let result: UserProfile | undefined;

    service.updateProfile({
      headline: 'Software Engineer'
    }).subscribe((value) => {
      result = value;
    });

    const request = http.expectOne('/api/v1/profile');

    expect(request.request.method).toBe('PUT');

    request.flush({
      success: true,
      message: 'Profile updated successfully',
      data: profile
    });

    expect(result).toEqual(profile);
  });

  it('deletes a profile with DELETE', () => {
    let completed = false;

    service.deleteProfile().subscribe({
      complete: () => {
        completed = true;
      }
    });

    const request = http.expectOne('/api/v1/profile');

    expect(request.request.method).toBe('DELETE');

    request.flush({
      success: true,
      message: 'Profile deleted successfully',
      data: null
    });

    expect(completed).toBe(true);
  });

  it('rejects an invalid response envelope', () => {
    let receivedError: unknown;

    service.getProfile().subscribe({
      error: (error: unknown) => {
        receivedError = error;
      }
    });

    http.expectOne('/api/v1/profile').flush({
      success: false,
      message: 'Unexpected response',
      data: profile
    });

    expect(receivedError).toEqual(
      expect.any(Error)
    );
  });

  it('rejects malformed profile data', () => {
    let receivedError: unknown;

    service.getProfile().subscribe({
      error: (error: unknown) => {
        receivedError = error;
      }
    });

    http.expectOne('/api/v1/profile').flush({
      success: true,
      message: 'Profile retrieved successfully',
      data: {
        ...profile,
        years_experience: 'three'
      }
    });

    expect(receivedError).toEqual(
      expect.any(Error)
    );
  });

  it('preserves HTTP 401 errors for authentication handling', () => {
    let receivedError: unknown;

    service.getProfile().subscribe({
      error: (error: unknown) => {
        receivedError = error;
      }
    });

    http.expectOne('/api/v1/profile').flush(
      { message: 'Unauthenticated' },
      {
        status: 401,
        statusText: 'Unauthorized'
      }
    );

    expect(receivedError).toEqual(
      expect.any(HttpErrorResponse)
    );

    expect(
      (receivedError as HttpErrorResponse).status
    ).toBe(401);
  });
});
