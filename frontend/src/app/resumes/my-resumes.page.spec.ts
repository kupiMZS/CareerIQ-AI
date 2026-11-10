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

    const retryButton = element.querySelector(
      'section[aria-labelledby="error-heading"] button'
    ) as HTMLButtonElement;

    expect(retryButton).toBeTruthy();
    retryButton.click();

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
  function chooseFile(
    element: HTMLElement,
    file: File
  ): void {
    const input = element.querySelector(
      '#resume-upload-file'
    ) as HTMLInputElement;

    Object.defineProperty(input, 'files', {
      configurable: true,
      value: {
        item: (index: number) =>
          index === 0 ? file : null
      }
    });

    input.dispatchEvent(new Event('change'));
  }

  function enterUploadTitle(
    element: HTMLElement,
    value: string
  ): void {
    const input = element.querySelector(
      '#resume-upload-title'
    ) as HTMLInputElement;

    input.value = value;
    input.dispatchEvent(new Event('input'));
  }

  it('uploads a fictional PDF and adds an ATS link', () => {
    const fixture = TestBed.createComponent(MyResumesPage);

    fixture.detectChanges();

    httpMock.expectOne('/api/v1/resumes')
      .flush({ data: [] });

    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;

    enterUploadTitle(element, 'Synthetic résumé');

    const file = new File(
      ['%PDF-1.7\\nFictional résumé content.'],
      'synthetic.pdf',
      { type: 'application/pdf' }
    );

    chooseFile(element, file);

    (element.querySelector(
      'button.upload-button'
    ) as HTMLButtonElement).click();

    const request = httpMock.expectOne('/api/v1/resumes');

    expect(request.request.method).toBe('POST');
    expect(request.request.body).toBeInstanceOf(FormData);

    const payload = request.request.body as FormData;

    expect(payload.get('title')).toBe('Synthetic résumé');
    const sentFile = payload.get('file') as File;

    expect(sentFile.name).toBe(file.name);
    expect(sentFile.size).toBe(file.size);

    request.flush({
      message: 'Resume uploaded successfully',
      data: {
        id: 73,
        title: 'Synthetic résumé',
        file_name: 'synthetic.pdf',
        file_type: 'application/pdf',
        status: 'uploaded',
        created_at: null
      }
    }, {
      status: 201,
      statusText: 'Created'
    });

    fixture.detectChanges();

    expect(element.textContent)
      .toContain('Résumé uploaded successfully.');

    expect(
      element.querySelector(
        'a[href="/resumes/73/ats"]'
      )
    ).toBeTruthy();

    httpMock.expectNone(
      '/api/v1/resumes/73/analysis/ats'
    );

    fixture.destroy();
  });

  it('rejects an unsupported file without HTTP', () => {
    const fixture = TestBed.createComponent(MyResumesPage);

    fixture.detectChanges();

    httpMock.expectOne('/api/v1/resumes')
      .flush({ data: [] });

    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;

    enterUploadTitle(element, 'Synthetic résumé');

    chooseFile(
      element,
      new File(['invalid'], 'resume.txt', {
        type: 'text/plain'
      })
    );

    (element.querySelector(
      'button.upload-button'
    ) as HTMLButtonElement).click();

    fixture.detectChanges();

    expect(element.textContent)
      .toContain('Choose a PDF, DOC, or DOCX file.');

    httpMock.expectNone('/api/v1/resumes');

    fixture.destroy();
  });

  it('rejects a file larger than 5 MiB', () => {
    const fixture = TestBed.createComponent(MyResumesPage);

    fixture.detectChanges();

    httpMock.expectOne('/api/v1/resumes')
      .flush({ data: [] });

    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;

    enterUploadTitle(element, 'Large synthetic résumé');

    const largeFile = new File(
      [new Uint8Array(5 * 1024 * 1024 + 1)],
      'large.pdf',
      { type: 'application/pdf' }
    );

    chooseFile(element, largeFile);

    (element.querySelector(
      'button.upload-button'
    ) as HTMLButtonElement).click();

    fixture.detectChanges();

    expect(element.textContent)
      .toContain('no larger than 5 MiB');

    httpMock.expectNone('/api/v1/resumes');

    fixture.destroy();
  });

  it('shows a safe validation error for HTTP 422', () => {
    const fixture = TestBed.createComponent(MyResumesPage);

    fixture.detectChanges();

    httpMock.expectOne('/api/v1/resumes')
      .flush({ data: [] });

    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;

    enterUploadTitle(element, 'Synthetic résumé');

    chooseFile(
      element,
      new File(['fictional'], 'synthetic.pdf', {
        type: 'application/pdf'
      })
    );

    (element.querySelector(
      'button.upload-button'
    ) as HTMLButtonElement).click();

    httpMock.expectOne('/api/v1/resumes').flush(
      { message: 'Private validation details' },
      { status: 422, statusText: 'Unprocessable Content' }
    );

    fixture.detectChanges();

    expect(element.textContent)
      .toContain('The server rejected this résumé.');

    expect(element.textContent)
      .not.toContain('Private validation details');

    fixture.destroy();
  });

  it('clears the session when upload returns HTTP 401', () => {
    const fixture = TestBed.createComponent(MyResumesPage);

    fixture.detectChanges();

    httpMock.expectOne('/api/v1/resumes')
      .flush({ data: [] });

    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;

    enterUploadTitle(element, 'Synthetic résumé');

    chooseFile(
      element,
      new File(['fictional'], 'synthetic.pdf', {
        type: 'application/pdf'
      })
    );

    (element.querySelector(
      'button.upload-button'
    ) as HTMLButtonElement).click();

    httpMock.expectOne('/api/v1/resumes').flush(
      { message: 'Unauthenticated.' },
      { status: 401, statusText: 'Unauthorized' }
    );

    fixture.detectChanges();

    expect(tokens.getToken()).toBeNull();

    expect(element.textContent)
      .toContain('Your session has expired.');

    fixture.destroy();
  });

  it('accepts a fictional PDF above 2 MiB but within 5 MiB', () => {
    const fixture = TestBed.createComponent(MyResumesPage);

    fixture.detectChanges();

    httpMock.expectOne('/api/v1/resumes')
      .flush({ data: [] });

    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;

    enterUploadTitle(
      element,
      'Synthetic large résumé'
    );

    const file = new File(
      [new Uint8Array(2 * 1024 * 1024 + 1)],
      'large-synthetic.pdf',
      { type: 'application/pdf' }
    );

    chooseFile(element, file);

    (element.querySelector(
      'button.upload-button'
    ) as HTMLButtonElement).click();

    const request = httpMock.expectOne('/api/v1/resumes');

    expect(request.request.method).toBe('POST');
    expect(request.request.body).toBeInstanceOf(FormData);

    const payload = request.request.body as FormData;

    expect(payload.get('title'))
      .toBe('Synthetic large résumé');

    const submittedFile = payload.get('file') as File;

    expect(submittedFile.size)
      .toBe(2 * 1024 * 1024 + 1);

    request.flush({
      message: 'Resume uploaded successfully',
      data: {
        id: 74,
        title: 'Synthetic large résumé',
        file_name: 'large-synthetic.pdf',
        file_type: 'application/pdf',
        status: 'uploaded',
        created_at: null
      }
    }, {
      status: 201,
      statusText: 'Created'
    });

    fixture.detectChanges();

    expect(
      element.querySelector(
        'a[href="/resumes/74/ats"]'
      )
    ).toBeTruthy();

    httpMock.expectNone(
      '/api/v1/resumes/74/analysis/ats'
    );

    fixture.destroy();
  });
});
