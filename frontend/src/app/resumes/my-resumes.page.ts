import { HttpErrorResponse } from '@angular/common/http';
import {
  Component,
  DestroyRef,
  inject,
  OnInit,
  signal
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { AuthTokenStore } from '../auth/auth-token.store';
import { ResumeListApiService } from './resume-list-api.service';
import {
  ResumeListItem,
  ResumeListResponse
} from './resume-list.models';

@Component({
  selector: 'app-my-resumes-page',
  imports: [RouterLink],
  template: `
    <main class="page">
      <header>
        <p class="eyebrow">CAREERIQ AI · RÉSUMÉ LIBRARY</p>
        <h1>My résumés</h1>
        <p class="intro">
          Choose one of your uploaded résumés to review its
          ATS assessment. No assessment runs automatically.
        </p>
      </header>

      @if (loading()) {
        <p class="panel" role="status">Loading your résumés…</p>
      } @else if (errorMessage(); as message) {
        <section class="panel" aria-labelledby="error-heading">
          <h2 id="error-heading">Unable to load résumés</h2>
          <p role="alert">{{ message }}</p>

          @if (isAuthenticated()) {
            <button type="button" (click)="loadResumes()">
              Try again
            </button>
          } @else {
            <a routerLink="/login">Sign in again</a>
          }
        </section>
      } @else if (resumes(); as items) {
        @if (items.length === 0) {
          <section class="panel" aria-labelledby="empty-heading">
            <h2 id="empty-heading">No résumés yet</h2>
            <p>
              You have not uploaded a résumé to this account.
            </p>
          </section>
        } @else {
          <ul class="resume-list" aria-label="Your résumés">
            @for (resume of items; track resume.id) {
              <li class="panel">
                <h2>
                  {{ resume.title || resume.file_name ||
                     'Untitled résumé' }}
                </h2>
                <p class="meta">Résumé #{{ resume.id }}</p>

                @if (resume.status) {
                  <p class="meta">Status: {{ resume.status }}</p>
                }

                <a
                  [routerLink]="[
                    '/resumes', resume.id, 'ats'
                  ]"
                  class="action"
                >
                  View ATS assessment
                </a>
              </li>
            }
          </ul>
        }
      }
    </main>
  `,
  styles: [`
    :host {
      display: block;
      color: #152338;
      font-family: system-ui, -apple-system, sans-serif;
    }

    .page {
      box-sizing: border-box;
      max-width: 920px;
      margin: 0 auto;
      padding: 2rem 1rem 4rem;
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
    }

    h2 {
      font-size: 1.2rem;
      margin-top: 0;
    }

    p {
      line-height: 1.65;
      overflow-wrap: anywhere;
    }

    .intro, .meta {
      color: #5b687a;
    }

    .resume-list {
      list-style: none;
      padding: 0;
    }

    .panel {
      padding: 1.5rem;
      margin: 1rem 0;
      background: #fff;
      border: 1px solid #e3e9f1;
      border-radius: 16px;
    }

    .action {
      display: inline-block;
      padding: .8rem 1.1rem;
      margin-top: .5rem;
      border-radius: 9px;
      background: #1858a4;
      color: white;
      font-weight: 700;
      text-decoration: none;
    }

    button {
      padding: .7rem 1.1rem;
      border: 0;
      border-radius: 9px;
      background: #1858a4;
      color: #fff;
      font: inherit;
      cursor: pointer;
    }

    a:focus-visible, button:focus-visible {
      outline: 3px solid #9bc6ff;
      outline-offset: 3px;
    }
  `]
})
export class MyResumesPage implements OnInit {
  private readonly api = inject(ResumeListApiService);
  private readonly tokens = inject(AuthTokenStore);
  private readonly destroyRef = inject(DestroyRef);

  readonly isAuthenticated = this.tokens.isAuthenticated;
  readonly loading = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly resumes = signal<ResumeListItem[] | null>(null);

  ngOnInit(): void {
    this.loadResumes();
  }

  loadResumes(): void {
    if (this.loading()) {
      return;
    }

    if (!this.isAuthenticated()) {
      this.resumes.set(null);
      this.errorMessage.set('Please sign in to view your résumés.');
      return;
    }

    this.loading.set(true);
    this.errorMessage.set(null);
    this.resumes.set(null);

    this.api.getResumes().pipe(
      takeUntilDestroyed(this.destroyRef),
      finalize(() => this.loading.set(false))
    ).subscribe({
      next: (response: ResumeListResponse) => {
        if (
          !response ||
          !Array.isArray(response.data) ||
          !response.data.every((item) =>
            item !== null &&
            Number.isSafeInteger(item.id) &&
            item.id > 0
          )
        ) {
          this.errorMessage.set(
            'The résumé list could not be read.'
          );
          return;
        }

        this.resumes.set(response.data);
      },
      error: (error: unknown) => {
        if (
          error instanceof HttpErrorResponse &&
          error.status === 401
        ) {
          this.tokens.clear();
          this.errorMessage.set(
            'Your session has expired. Please sign in again.'
          );
          return;
        }

        if (
          error instanceof HttpErrorResponse &&
          error.status === 403
        ) {
          this.errorMessage.set(
            'You do not have permission to view these résumés.'
          );
          return;
        }

        this.errorMessage.set(
          'The résumé service is currently unavailable.'
        );
      }
    });
  }
}
