import {
  provideHttpClient
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { ResumeListApiService } from './resume-list-api.service';
import { ResumeListResponse } from './resume-list.models';

describe('ResumeListApiService', () => {
  let service: ResumeListApiService;
  let httpMock: HttpTestingController;

  const response: ResumeListResponse = {
    data: [{
      id: 42,
      title: 'Synthetic résumé',
      file_name: 'synthetic.pdf',
      file_type: 'application/pdf',
      status: 'uploaded',
      created_at: null
    }]
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });

    service = TestBed.inject(ResumeListApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('loads the authenticated résumé collection', () => {
    let received: ResumeListResponse | undefined;

    service.getResumes().subscribe((result) => {
      received = result;
    });

    const request = httpMock.expectOne('/api/v1/resumes');

    expect(request.request.method).toBe('GET');
    expect(request.request.body).toBeNull();

    request.flush(response);

    expect(received).toEqual(response);
  });

  it('does not make a request before subscription', () => {
    const result$ = service.getResumes();

    httpMock.expectNone('/api/v1/resumes');

    result$.subscribe();

    httpMock.expectOne('/api/v1/resumes').flush(response);
  });
  it('uploads a résumé using multipart FormData', () => {
    const file = new File(
      ['%PDF-1.7\\nSynthetic test content.'],
      'synthetic.pdf',
      { type: 'application/pdf' }
    );

    let receivedId: number | undefined;

    service.uploadResume('Synthetic résumé', file)
      .subscribe((result) => {
        receivedId = result.data.id;
      });

    const request = httpMock.expectOne('/api/v1/resumes');

    expect(request.request.method).toBe('POST');
    expect(request.request.body).toBeInstanceOf(FormData);

    const form = request.request.body as FormData;

    expect(form.get('title')).toBe('Synthetic résumé');
    const sentFile = form.get('file') as File;

    expect(sentFile.name).toBe(file.name);
    expect(sentFile.size).toBe(file.size);

    expect(
      request.request.headers.has('Content-Type')
    ).toBe(false);

    request.flush({
      message: 'Resume uploaded successfully',
      data: {
        id: 42,
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

    expect(receivedId).toBe(42);
  });

  it('does not upload before subscription', () => {
    const file = new File(
      ['Synthetic PDF'],
      'synthetic.pdf',
      { type: 'application/pdf' }
    );

    const result$ = service.uploadResume(
      'Synthetic résumé',
      file
    );

    httpMock.expectNone('/api/v1/resumes');

    result$.subscribe();

    httpMock.expectOne('/api/v1/resumes').flush({
      message: 'Resume uploaded successfully',
      data: {
        id: 42,
        title: 'Synthetic résumé',
        file_name: 'synthetic.pdf',
        file_type: 'application/pdf',
        status: 'uploaded',
        created_at: null
      }
    });
  });
});
