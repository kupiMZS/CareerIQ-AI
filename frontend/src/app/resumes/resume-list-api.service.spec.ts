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
});
