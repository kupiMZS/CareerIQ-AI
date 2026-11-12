import { HttpErrorResponse } from '@angular/common/http';
import {
  Component,
  DestroyRef,
  ElementRef,
  inject,
  OnInit,
  signal,
  ViewChild
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { AuthTokenStore } from '../auth/auth-token.store';
import { ResumeListApiService } from './resume-list-api.service';
import {
  ResumeListItem,
  ResumeListResponse,
  ResumeUploadResponse
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

      <nav aria-label="Account navigation">
        <a routerLink="/profile">My profile</a>
      </nav>

      <section class="panel" aria-labelledby="upload-heading">
        <h2 id="upload-heading">Upload a résumé</h2>
        <p class="meta">
          PDF, DOC or DOCX · Maximum 5 MiB
        </p>

        <div class="upload-fields">
          <label for="resume-upload-title">Résumé title</label>
          <input
            id="resume-upload-title"
            type="text"
            maxlength="255"
            [value]="uploadTitle()"
            [disabled]="uploading() || loading()"
            (input)="onTitleInput($event)"
          />

          <label for="resume-upload-file">Choose a file</label>
          <input
            #uploadFileInput
            id="resume-upload-file"
            type="file"
            accept=".pdf,.doc,.docx"
            [disabled]="uploading() || loading()"
            (change)="onFileSelection($event)"
          />

          <button
            type="button"
            class="upload-button"
            [disabled]="uploading() || loading() || !isAuthenticated()"
            (click)="uploadResume()"
          >
            {{ uploading() ? 'Uploading…' : 'Upload résumé' }}
          </button>
        </div>

        @if (uploading()) {
          <p role="status">Uploading your résumé…</p>
        }

        @if (uploadSuccess(); as message) {
          <p class="upload-success" role="status">{{ message }}</p>
        }

        @if (uploadError(); as message) {
          <p class="upload-error" role="alert">{{ message }}</p>
        }

        @if (!isAuthenticated()) {
          <p>
            <a routerLink="/login">Sign in again</a>
            to upload a résumé.
          </p>
        }
      </section>

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

    .upload-fields {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: .75rem;
    }

    .upload-fields label {
      font-weight: 700;
    }

    .upload-fields input {
      box-sizing: border-box;
      width: 100%;
      max-width: 480px;
      padding: .7rem;
      border: 1px solid #cbd5e1;
      border-radius: 9px;
      font: inherit;
    }

    .upload-success {
      color: #166534;
    }

    .upload-error {
      color: #9f1239;
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
  @ViewChild('uploadFileInput')
  private fileInput?: ElementRef<HTMLInputElement>;

  private readonly api = inject(ResumeListApiService);
  private readonly tokens = inject(AuthTokenStore);
  private readonly destroyRef = inject(DestroyRef);

  readonly isAuthenticated = this.tokens.isAuthenticated;
  readonly loading = signal(false);
  readonly uploading = signal(false);
  readonly uploadTitle = signal('');
  readonly selectedFile = signal<File | null>(null);
  readonly uploadError = signal<string | null>(null);
  readonly uploadSuccess = signal<string | null>(null);

  // Match Laravel's 5120 KiB validation and PHP's 5M limit.
  private readonly maxUploadBytes = 5 * 1024 * 1024;
  readonly errorMessage = signal<string | null>(null);
  readonly resumes = signal<ResumeListItem[] | null>(null);

  ngOnInit(): void {
    this.loadResumes();
  }

  onTitleInput(event: Event): void {
    const input = event.target as HTMLInputElement;

    this.uploadTitle.set(input.value);
    this.uploadError.set(null);
    this.uploadSuccess.set(null);
  }

  onFileSelection(event: Event): void {
    const input = event.target as HTMLInputElement;

    this.selectedFile.set(input.files?.item(0) ?? null);
    this.uploadError.set(null);
    this.uploadSuccess.set(null);
  }

  uploadResume(): void {
    if (this.uploading() || this.loading()) {
      return;
    }

    this.uploadError.set(null);
    this.uploadSuccess.set(null);

    if (!this.isAuthenticated()) {
      this.uploadError.set(
        'Your session has expired. Sign in again.'
      );
      return;
    }

    const title = this.uploadTitle().trim();
    const file = this.selectedFile();

    if (!title || title.length > 255) {
      this.uploadError.set(
        'Enter a résumé title between 1 and 255 characters.'
      );
      return;
    }

    if (!file) {
      this.uploadError.set('Choose a résumé file.');
      return;
    }

    if (!/\.(pdf|doc|docx)$/i.test(file.name)) {
      this.uploadError.set(
        'Choose a PDF, DOC, or DOCX file.'
      );
      return;
    }

    if (
      file.size <= 0 ||
      file.size > this.maxUploadBytes
    ) {
      this.uploadError.set(
        'The file must be non-empty and no larger than 5 MiB.'
      );
      return;
    }

    this.uploading.set(true);

    this.api.uploadResume(title, file).pipe(
      takeUntilDestroyed(this.destroyRef),
      finalize(() => this.uploading.set(false))
    ).subscribe({
      next: (response: ResumeUploadResponse) => {
        if (
          !response ||
          !response.data ||
          !Number.isSafeInteger(response.data.id) ||
          response.data.id <= 0
        ) {
          this.uploadError.set(
            'The upload response could not be read. ' +
            'Check your résumé list before trying again.'
          );
          return;
        }

        const uploaded = response.data;

        this.resumes.update((items) => [
          uploaded,
          ...(items ?? []).filter(
            (item) => item.id !== uploaded.id
          )
        ]);

        this.errorMessage.set(null);
        this.uploadTitle.set('');
        this.selectedFile.set(null);

        if (this.fileInput) {
          this.fileInput.nativeElement.value = '';
        }

        this.uploadSuccess.set(
          'Résumé uploaded successfully. ' +
          'You can now choose its ATS assessment.'
        );
      },
      error: (error: unknown) => {
        if (error instanceof HttpErrorResponse) {
          if (error.status === 401) {
            this.tokens.clear();
            this.uploadError.set(
              'Your session has expired. Sign in again.'
            );
            return;
          }

          if (error.status === 422) {
            this.uploadError.set(
              'The server rejected this résumé. ' +
              'Check its title, format, and size.'
            );
            return;
          }
        }

        this.uploadError.set(
          'The résumé upload could not be completed.'
        );
      }
    });
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
