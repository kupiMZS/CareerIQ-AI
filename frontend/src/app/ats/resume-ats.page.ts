import { HttpErrorResponse } from '@angular/common/http';
import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { finalize, Subscription } from 'rxjs';

import { AuthTokenStore } from '../auth/auth-token.store';
import { ResumeAtsApiService } from './resume-ats-api.service';
import { ResumeAtsApiResponse } from './resume-ats.models';

@Component({
  selector: 'app-resume-ats-page',
  imports: [RouterLink],
  template: `
    <main class="page">
      <a routerLink="/resumes">Back to my résumés</a>
      <header class="heading">
        <p class="eyebrow">CAREERIQ AI · RÉSUMÉ REVIEW</p>
        <h1>ATS assessment</h1>
        <p class="intro">
          Review résumé structure, supporting evidence, and practical
          improvements. This assessment does not calculate an ATS score.
        </p>
      </header>

      @if (resumeId(); as id) {
        <section class="panel" aria-labelledby="report-heading">
          <h2 id="report-heading">Résumé #{{ id }}</h2>
          <p class="subtle">
            Your report is generated only when you request it.
          </p>
          <button
            type="button"
            class="primary"
            [disabled]="busy() || !isAuthenticated()"
            (click)="requestReport()"
          >
            {{ busy() ? 'Generating report…' : 'Generate ATS report' }}
          </button>
          @if (busy()) {
            <p role="status" class="subtle">Analyzing résumé…</p>
          }
        </section>
      } @else {
        <p class="error" role="alert">Invalid résumé identifier.</p>
      }

      @if (!isAuthenticated()) {
        <p class="notice">
          Your session is no longer available.
          <a routerLink="/login">Sign in again</a>.
        </p>
      }

      @if (errorMessage(); as message) {
        <p class="error" role="alert">{{ message }}</p>
      }

      @if (report(); as data) {
        <section class="panel" aria-labelledby="results-heading">
          <p class="eyebrow">ASSESSMENT RESULTS</p>
          <h2 id="results-heading">Findings</h2>
          <p class="subtle">
            No numerical ATS score is provided for this assessment.
          </p>

          <ol class="findings">
            @for (finding of data.findings; track finding.code) {
              <li class="finding">
                <div class="finding-heading">
                  <h3>{{ findingLabel(finding.code) }}</h3>
                  <span class="status">
                    {{ statusLabel(finding.status) }}
                  </span>
                </div>

                <p>{{ finding.explanation }}</p>

                @if (finding.supporting_text.length > 0) {
                  <h4>Supporting text</h4>
                  <ul>
                    @for (
                      excerpt of finding.supporting_text;
                      track $index
                    ) {
                      <li>{{ excerpt }}</li>
                    }
                  </ul>
                }

                @if (finding.recommendation; as recommendation) {
                  <h4>Recommendation</h4>
                  <p>{{ recommendation }}</p>
                }
              </li>
            }
          </ol>
        </section>

        @if (data.limitations.length > 0) {
          <section class="panel" aria-labelledby="limits-heading">
            <h2 id="limits-heading">Assessment limitations</h2>
            <ul>
              @for (limitation of data.limitations; track $index) {
                <li>{{ limitation }}</li>
              }
            </ul>
          </section>
        }
      }
    </main>
  `,
  styles: [`
    :host {
      display: block;
      min-height: 100%;
      color: #152338;
      font-family: system-ui, -apple-system, sans-serif;
    }

    .page {
      box-sizing: border-box;
      max-width: 920px;
      margin: 0 auto;
      padding: 2rem 1rem 4rem;
    }

    .heading {
      margin-bottom: 1.75rem;
    }

    .eyebrow {
      color: #3769a9;
      font-size: .75rem;
      font-weight: 750;
      letter-spacing: .1em;
    }

    h1 {
      font-size: clamp(1.8rem, 4vw, 2.5rem);
      letter-spacing: -.04em;
      margin: .3rem 0 .65rem;
    }

    h2 {
      font-size: 1.3rem;
      margin: 0 0 .65rem;
    }

    h3 {
      font-size: 1rem;
      margin: 0;
    }

    h4 {
      font-size: .88rem;
      margin: 1rem 0 .35rem;
    }

    p, li {
      line-height: 1.65;
      overflow-wrap: anywhere;
    }

    .intro, .subtle {
      color: #5b687a;
    }

    .panel {
      background: #fff;
      border: 1px solid #e3e9f1;
      border-radius: 16px;
      padding: 1.5rem;
      margin-bottom: 1.25rem;
    }

    .primary {
      padding: .8rem 1.2rem;
      border: 0;
      border-radius: 9px;
      color: white;
      background: #1858a4;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }

    .primary:disabled {
      opacity: .6;
      cursor: not-allowed;
    }

    button:focus-visible, a:focus-visible {
      outline: 3px solid #9bc6ff;
      outline-offset: 3px;
    }

    .findings {
      padding-left: 1.35rem;
    }

    .finding {
      padding: 1.1rem 0;
      border-bottom: 1px solid #e3e9f1;
    }

    .finding:last-child {
      border-bottom: 0;
    }

    .finding-heading {
      display: flex;
      gap: .75rem;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
    }

    .status {
      padding: .2rem .55rem;
      border-radius: 999px;
      background: #edf2f9;
      font-size: .78rem;
      font-weight: 700;
    }

    .error, .notice {
      border-radius: 9px;
      padding: 1rem;
      margin-bottom: 1rem;
    }

    .error {
      background: #fff1f2;
      border: 1px solid #fecdd3;
      color: #9f1239;
    }

    .notice {
      background: #eff6ff;
      border: 1px solid #bfdbfe;
    }

    @media (max-width: 520px) {
      .panel {
        padding: 1rem;
      }
    }
  `]
})
export class ResumeAtsPage {
  private readonly api = inject(ResumeAtsApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly tokens = inject(AuthTokenStore);
  private readonly destroyRef = inject(DestroyRef);

  private activeRequest?: Subscription;

  readonly isAuthenticated = this.tokens.isAuthenticated;
  readonly resumeId = signal<number | null>(null);
  readonly busy = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly report = signal<ResumeAtsApiResponse['data'] | null>(null);

  constructor() {
    this.route.paramMap
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((params) => {
        this.activeRequest?.unsubscribe();

        const raw = params.get('resumeId') ?? '';
        const numericId = /^[1-9]\d*$/.test(raw)
          ? Number(raw)
          : NaN;

        this.resumeId.set(
          Number.isSafeInteger(numericId) ? numericId : null
        );
        this.report.set(null);
        this.errorMessage.set(null);
        this.busy.set(false);
      });
  }

  requestReport(): void {
    const id = this.resumeId();

    if (this.busy() || id === null) {
      return;
    }

    this.report.set(null);
    this.errorMessage.set(null);

    if (!this.isAuthenticated()) {
      this.errorMessage.set(
        'Sign in to request an ATS report.'
      );
      return;
    }

    this.busy.set(true);

    this.activeRequest = this.api.requestReport(id)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.busy.set(false))
      )
      .subscribe({
        next: (response) => {
          this.report.set(response.data);
        },
        error: (error: unknown) => {
          this.errorMessage.set(this.describeError(error));
        }
      });
  }

  findingLabel(code: string): string {
    const labels: Record<string, string> = {
      contact_email: 'Contact email',
      section_skills: 'Skills section',
      section_education: 'Education section',
      section_experience: 'Experience section',
      section_skills_content: 'Skills content',
      section_education_content: 'Education content',
      section_experience_content: 'Experience content',
      quantified_outcome_evidence: 'Quantified achievement evidence'
    };

    return labels[code] ?? code.replaceAll('_', ' ');
  }

  statusLabel(status: string): string {
    const labels: Record<string, string> = {
      satisfied: 'Satisfied',
      needs_attention: 'Needs attention',
      not_assessed: 'Not assessed'
    };

    return labels[status] ?? 'Not assessed';
  }

  private describeError(error: unknown): string {
    if (!(error instanceof HttpErrorResponse)) {
      return 'The ATS request could not be completed.';
    }

    if (error.status === 401) {
      this.tokens.clear();
      return 'Your session has expired. Sign in again.';
    }

    if (error.status === 403) {
      return 'You do not have permission to access this résumé.';
    }

    if (error.status === 404) {
      return 'This résumé could not be found.';
    }

    if (error.status === 502 || error.status === 503) {
      return 'The ATS service is currently unavailable.';
    }

    return 'The ATS request could not be completed.';
  }
}
