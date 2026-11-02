import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { AuthTokenStore } from '../auth/auth-token.store';
import { MyResumesPage } from './my-resumes.page';
import { ResumeListResponse } from './resume-list.models';

describe('MyResumesPage', () => {
  let httpMock: HttpTestingController;
  let tokens: AuthTokenStore;

  const sample: ResumeListResponse = {
    data: [
      {
        id: 42,
        title: 'Synthetic developer résumé',
        file_name: 'synthetic.pdf',
        file_type: 'application/pdf',
        status: 'uploaded',
        created_at: null
      },
      {
        id: 43,
        title: null,
        file_name: 'second.pdf',
        file_type: 'application/pdf',
        status: 'uploaded',
        created_at: null
      }
    ]
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });

    tokens = TestBed.inject(AuthTokenStore);
    tokens.setToken('synthetic-test-token');
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('lists owned résumés and links to ATS without generating it', () => {
    const fixture = TestBed.createComponent(MyResumesPage);

    fixture.detectChanges();

    const request = httpMock.expectOne('/api/v1/resumes');

    expect(request.request.method).toBe('GET');

    request.flush(sample);
    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;

    expect(element.textContent)
      .toContain('Synthetic developer résumé');
    expect(element.textContent).toContain('second.pdf');

    expect(
      element.querySelector('a[href="/resumes/42/ats"]')
    ).toBeTruthy();

    expect(
      element.querySelector('a[href="/resumes/43/ats"]')
    ).toBeTruthy();

    httpMock.expectNone(
      '/api/v1/resumes/42/analysis/ats'
    );

    fixture.destroy();
  });

  it('shows an empty state for a new account', () => {
    const fixture = TestBed.createComponent(MyResumesPage);

    fixture.detectChanges();

    httpMock.expectOne('/api/v1/resumes')
      .flush({ data: [] });

    fixture.detectChanges();

    expect(fixture.nativeElement.textContent)
      .toContain('No résumés yet');

    fixture.destroy();
  });

  it('clears the token on HTTP 401', () => {
    const fixture = TestBed.createComponent(MyResumesPage);

    fixture.detectChanges();

    httpMock.expectOne('/api/v1/resumes').flush(
      { message: 'Unauthenticated.' },
      { status: 401, statusText: 'Unauthorized' }
    );

    fixture.detectChanges();

    expect(tokens.getToken()).toBeNull();
    expect(fixture.nativeElement.textContent)
      .toContain('Your session has expired.');
    expect(
      fixture.nativeElement.querySelector('a[href="/login"]')
    ).toBeTruthy();

    fixture.destroy();
  });

  it('offers retry after a safe server error', () => {
    const fixture = TestBed.createComponent(MyResumesPage);

    fixture.detectChanges();

    httpMock.expectOne('/api/v1/resumes').flush(
      { message: 'Private internal error' },
      { status: 503, statusText: 'Service Unavailable' }
    );

    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;

    expect(element.textContent).toContain('Try again');
    expect(element.textContent).not.toContain('Private internal error');

    (element.querySelector('button') as HTMLButtonElement).click();

    const retry = httpMock.expectOne('/api/v1/resumes');

    retry.flush(sample);
    fixture.detectChanges();

    expect(element.textContent)
      .toContain('Synthetic developer résumé');

    fixture.destroy();
  });

  it('rejects a malformed list without creating ATS links', () => {
    const fixture = TestBed.createComponent(MyResumesPage);

    fixture.detectChanges();

    httpMock.expectOne('/api/v1/resumes').flush({
      data: [{ id: 0, title: 'Invalid record' }]
    });

    fixture.detectChanges();

    expect(fixture.nativeElement.textContent)
      .toContain('The résumé list could not be read.');

    expect(
      fixture.nativeElement.querySelector(
        'a[href="/resumes/0/ats"]'
      )
    ).toBeNull();

    fixture.destroy();
  });

  it('cancels a pending list request when destroyed', () => {
    const fixture = TestBed.createComponent(MyResumesPage);

    fixture.detectChanges();

    const request = httpMock.expectOne('/api/v1/resumes');

    fixture.destroy();

    expect(request.cancelled).toBe(true);
  });
});
