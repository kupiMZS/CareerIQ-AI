import {
  provideHttpClient
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import {
  ActivatedRoute,
  convertToParamMap,
  ParamMap,
  provideRouter
} from '@angular/router';
import { BehaviorSubject } from 'rxjs';

import { AuthTokenStore } from '../auth/auth-token.store';
import { ResumeAtsPage } from './resume-ats.page';
import {
  AtsFindingCode,
  ResumeAtsApiResponse
} from './resume-ats.models';

describe('ResumeAtsPage', () => {
  let params: BehaviorSubject<ParamMap>;
  let httpMock: HttpTestingController;
  let tokens: AuthTokenStore;

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
        status: 'needs_attention',
        explanation: 'Synthetic assessment explanation.',
        supporting_text: ['Synthetic résumé excerpt.'],
        recommendation: 'Improve this résumé section.'
      })),
      limitations: ['Only supplied text was assessed.']
    }
  };

  beforeEach(() => {
    params = new BehaviorSubject<ParamMap>(
      convertToParamMap({ resumeId: '42' })
    );

    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        {
          provide: ActivatedRoute,
          useValue: { paramMap: params.asObservable() }
        }
      ]
    });

    tokens = TestBed.inject(AuthTokenStore);
    tokens.setToken('synthetic-test-token');

    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    params.complete();
  });

  it('does not request a report before an explicit click', () => {
    const fixture = TestBed.createComponent(ResumeAtsPage);

    fixture.detectChanges();

    httpMock.expectNone('/api/v1/resumes/42/analysis/ats');

    expect(fixture.nativeElement.textContent)
      .toContain('Generate ATS report');

    fixture.destroy();
  });

  it('renders findings, evidence and limitations after success', () => {
    const fixture = TestBed.createComponent(ResumeAtsPage);

    fixture.detectChanges();

    const button: HTMLButtonElement =
      fixture.nativeElement.querySelector('button');

    button.click();
    fixture.detectChanges();

    expect(button.disabled).toBe(true);

    const request = httpMock.expectOne(
      '/api/v1/resumes/42/analysis/ats'
    );

    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({});

    request.flush(sampleResponse);
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent as string;

    expect(text).toContain('Findings');
    expect(text).toContain('Quantified achievement evidence');
    expect(text).toContain('Synthetic résumé excerpt.');
    expect(text).toContain('Improve this résumé section.');
    expect(text).toContain('Only supplied text was assessed.');
    expect(text).toContain('does not calculate an ATS score');

    expect(fixture.componentInstance.report()?.score).toBeNull();

    fixture.destroy();
  });

  it('shows a safe error and does not fabricate results', () => {
    const fixture = TestBed.createComponent(ResumeAtsPage);

    fixture.componentInstance.requestReport();

    httpMock.expectOne(
      '/api/v1/resumes/42/analysis/ats'
    ).flush(
      { message: 'Internal error details must not be shown.' },
      { status: 502, statusText: 'Bad Gateway' }
    );

    fixture.detectChanges();

    expect(fixture.nativeElement.textContent)
      .toContain('The ATS service is currently unavailable.');

    expect(fixture.nativeElement.textContent)
      .not.toContain('Internal error details');

    expect(fixture.componentInstance.report()).toBeNull();

    fixture.destroy();
  });

  it('clears the memory token when the session expires', () => {
    const fixture = TestBed.createComponent(ResumeAtsPage);

    fixture.componentInstance.requestReport();

    httpMock.expectOne(
      '/api/v1/resumes/42/analysis/ats'
    ).flush(
      { message: 'Unauthenticated.' },
      { status: 401, statusText: 'Unauthorized' }
    );

    fixture.detectChanges();

    expect(tokens.getToken()).toBeNull();
    expect(fixture.nativeElement.textContent)
      .toContain('Your session has expired.');

    fixture.destroy();
  });

  it('rejects invalid résumé identifiers without HTTP', () => {
    params.next(convertToParamMap({ resumeId: '0' }));

    const fixture = TestBed.createComponent(ResumeAtsPage);

    fixture.detectChanges();
    fixture.componentInstance.requestReport();

    expect(fixture.componentInstance.resumeId()).toBeNull();
    expect(fixture.nativeElement.textContent)
      .toContain('Invalid résumé identifier.');

    httpMock.expectNone('/api/v1/resumes/0/analysis/ats');

    fixture.destroy();
  });

  it('cancels a pending request when the résumé changes', () => {
    const fixture = TestBed.createComponent(ResumeAtsPage);

    fixture.componentInstance.requestReport();

    const pending = httpMock.expectOne(
      '/api/v1/resumes/42/analysis/ats'
    );

    params.next(convertToParamMap({ resumeId: '43' }));

    expect(pending.cancelled).toBe(true);
    expect(fixture.componentInstance.resumeId()).toBe(43);
    expect(fixture.componentInstance.report()).toBeNull();

    fixture.destroy();
  });
});
