import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { map, Observable } from 'rxjs';

import { ProfilePayload, UserProfile } from './profile.models';

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' &&
    value !== null &&
    !Array.isArray(value);
}

function parseEnvelope(value: unknown): unknown {
  if (
    !isRecord(value) ||
    value['success'] !== true ||
    typeof value['message'] !== 'string' ||
    !Object.prototype.hasOwnProperty.call(value, 'data')
  ) {
    throw new Error('Invalid profile API response.');
  }

  return value['data'];
}

function nullableText(
  value: Record<string, unknown>,
  field: string
): string | null {
  const item = value[field];

  if (item !== null && typeof item !== 'string') {
    throw new Error('Invalid profile field: ' + field);
  }

  return item;
}

function parseProfile(value: unknown): UserProfile {
  if (!isRecord(value)) {
    throw new Error('Invalid profile data.');
  }

  const id = value['id'];
  const experience = value['years_experience'];

  if (
    typeof id !== 'number' ||
    !Number.isSafeInteger(id) ||
    id <= 0 ||
    typeof experience !== 'number' ||
    !Number.isInteger(experience) ||
    experience < 0 ||
    experience > 80
  ) {
    throw new Error('Invalid profile data.');
  }

  return {
    id,
    first_name: nullableText(value, 'first_name'),
    last_name: nullableText(value, 'last_name'),
    phone: nullableText(value, 'phone'),
    location: nullableText(value, 'location'),
    country: nullableText(value, 'country'),
    headline: nullableText(value, 'headline'),
    summary: nullableText(value, 'summary'),
    linkedin_url: nullableText(value, 'linkedin_url'),
    github_url: nullableText(value, 'github_url'),
    portfolio_url: nullableText(value, 'portfolio_url'),
    years_experience: experience
  };
}

function parseRequiredProfile(response: unknown): UserProfile {
  return parseProfile(parseEnvelope(response));
}

@Injectable({ providedIn: 'root' })
export class ProfileApiService {
  private readonly http = inject(HttpClient);
  private readonly endpoint = '/api/v1/profile';

  getProfile(): Observable<UserProfile | null> {
    return this.http.get<unknown>(this.endpoint).pipe(
      map((response) => {
        const data = parseEnvelope(response);

        return data === null ? null : parseProfile(data);
      })
    );
  }

  createProfile(payload: ProfilePayload): Observable<UserProfile> {
    return this.http.post<unknown>(this.endpoint, payload).pipe(
      map(parseRequiredProfile)
    );
  }

  updateProfile(payload: ProfilePayload): Observable<UserProfile> {
    return this.http.put<unknown>(this.endpoint, payload).pipe(
      map(parseRequiredProfile)
    );
  }

  deleteProfile(): Observable<void> {
    return this.http.delete<unknown>(this.endpoint).pipe(
      map((response) => {
        parseEnvelope(response);
      })
    );
  }
}
