import { HttpErrorResponse, provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { ResumeAtsApiService } from './resume-ats-api.service';
import {
  AtsFindingCode,
  ResumeAtsApiResponse
} from './resume-ats.models';

describe('ResumeAtsApiService', () => {
  let service: ResumeAtsApiService;
  let httpMock: HttpTestingController;

  const codes: AtsFindingCode[] = [
    'contact_email',
    'section_skills',
    'section_education',
    'section_experience',
    'section_skills_content',
    'section_education_content',
    'section_experience_content',
    'quantified_outcome_evidence'
  ];

  const sampleResponse: ResumeAtsApiResponse = {
    message: 'Resume ATS report generated successfully',
    data: {
      report_version: 'ats-v1',
      score: null,
      findings: codes.map((code) => ({
        code,
        status: 'not_assessed',
        explanation: 'Synthetic ATS explanation.',
        supporting_text: [],
        recommendation: null
      })),
      limitations: ['Synthetic assessment only.']
    }
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });

    service = TestBed.inject(ResumeAtsApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('sends an opt-in POST to the authenticated Laravel ATS route', () => {
    let received: ResumeAtsApiResponse | undefined;

    service.requestReport(42).subscribe((response) => {
      received = response;
    });

    const request = httpMock.expectOne(
      '/api/v1/resumes/42/analysis/ats'
    );

    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({});

    request.flush(sampleResponse);

    expect(received).toEqual(sampleResponse);
    expect(received?.data.score).toBeNull();
    expect(received?.data.findings.length).toBe(8);
  });

  it('does not send a request before subscription', () => {
    const report$ = service.requestReport(9);

    httpMock.expectNone('/api/v1/resumes/9/analysis/ats');

    report$.subscribe();

    const request = httpMock.expectOne(
      '/api/v1/resumes/9/analysis/ats'
    );

    request.flush(sampleResponse);
  });

  it('rejects invalid resume IDs without an HTTP request', () => {
    const invalidIds = [
      0,
      -1,
      1.5,
      Number.NaN,
      Number.POSITIVE_INFINITY,
      Number.MAX_SAFE_INTEGER + 1
    ];

    for (const resumeId of invalidIds) {
      expect(() => service.requestReport(resumeId)).toThrow(
        RangeError
      );
    }
  });

  it('propagates upstream errors without fabricating a report', () => {
    const failures: HttpErrorResponse[] = [];

    service.requestReport(7).subscribe({
      error: (error: HttpErrorResponse) => {
        failures.push(error);
      }
    });

    const request = httpMock.expectOne(
      '/api/v1/resumes/7/analysis/ats'
    );

    request.flush(
      { message: 'Resume ATS service unavailable' },
      {
        status: 502,
        statusText: 'Bad Gateway'
      }
    );

    expect(failures.length).toBe(1);
    expect(failures[0]?.status).toBe(502);
  });
});
