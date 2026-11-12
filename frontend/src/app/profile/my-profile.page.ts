import { HttpErrorResponse } from '@angular/common/http';
import {
  Component,
  DestroyRef,
  inject,
  OnInit,
  signal
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  FormBuilder,
  ReactiveFormsModule,
  Validators
} from '@angular/forms';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { ProfileApiService } from './profile-api.service';
import { ProfilePayload, UserProfile } from './profile.models';

@Component({
  selector: 'app-my-profile-page',
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <main class="page">
      <header>
        <p class="eyebrow">CAREERIQ AI · YOUR ACCOUNT</p>
        <h1>My profile</h1>
        <p class="intro">
          Keep your professional information up to date.
          Changes are saved only when you select Save.
        </p>
        <a routerLink="/resumes">Back to my résumés</a>
      </header>

      @if (loading()) {
        <section class="panel" role="status">
          Loading your profile…
        </section>
      } @else if (loadError(); as message) {
        <section class="panel">
          <h2>Unable to load your profile</h2>
          <p role="alert">{{ message }}</p>
          <button type="button" (click)="loadProfile()">
            Try again
          </button>
          <a routerLink="/login">Sign in again</a>
        </section>
      } @else {
        <section class="panel">
          @if (profile() === null) {
            <h2>Create your profile</h2>
            <p class="intro">
              No profile exists for this account yet.
              Fill in your details to create one.
            </p>
          } @else {
            <h2>Edit your profile</h2>
            <p class="intro">
              Update the fields below and save your changes.
            </p>
          }

          @if (successMessage(); as message) {
            <p class="success" role="status">{{ message }}</p>
          }

          @if (saveError(); as message) {
            <p class="error" role="alert">{{ message }}</p>
          }

          <form
            [formGroup]="form"
            (ngSubmit)="saveProfile()"
            novalidate
          >
            <fieldset
              class="fields"
              [disabled]="saving() || deleting()"
            >
              <div class="field">
                <label for="profile-first-name">First name</label>
                <input
                  id="profile-first-name"
                  type="text"
                  autocomplete="given-name"
                  maxlength="100"
                  formControlName="first_name"
                />
              </div>

              <div class="field">
                <label for="profile-last-name">Last name</label>
                <input
                  id="profile-last-name"
                  type="text"
                  autocomplete="family-name"
                  maxlength="100"
                  formControlName="last_name"
                />
              </div>

              <div class="field">
                <label for="profile-phone">Phone</label>
                <input
                  id="profile-phone"
                  type="tel"
                  autocomplete="tel"
                  maxlength="30"
                  formControlName="phone"
                />
              </div>

              <div class="field">
                <label for="profile-location">Location</label>
                <input
                  id="profile-location"
                  type="text"
                  maxlength="100"
                  formControlName="location"
                />
              </div>

              <div class="field">
                <label for="profile-country">Country</label>
                <input
                  id="profile-country"
                  type="text"
                  autocomplete="country-name"
                  maxlength="100"
                  formControlName="country"
                />
              </div>

              <div class="field">
                <label for="profile-experience">
                  Years of experience
                </label>
                <input
                  id="profile-experience"
                  type="number"
                  min="0"
                  max="80"
                  step="1"
                  formControlName="years_experience"
                />
              </div>

              <div class="field full">
                <label for="profile-headline">
                  Professional headline
                </label>
                <input
                  id="profile-headline"
                  type="text"
                  maxlength="255"
                  formControlName="headline"
                />
              </div>

              <div class="field full">
                <label for="profile-summary">
                  Professional summary
                </label>
                <textarea
                  id="profile-summary"
                  rows="5"
                  maxlength="2000"
                  formControlName="summary"
                ></textarea>
              </div>

              <div class="field full">
                <label for="profile-linkedin">LinkedIn URL</label>
                <input
                  id="profile-linkedin"
                  type="url"
                  maxlength="255"
                  placeholder="https://www.linkedin.com/in/..."
                  formControlName="linkedin_url"
                />
              </div>

              <div class="field full">
                <label for="profile-github">GitHub URL</label>
                <input
                  id="profile-github"
                  type="url"
                  maxlength="255"
                  placeholder="https://github.com/..."
                  formControlName="github_url"
                />
              </div>

              <div class="field full">
                <label for="profile-portfolio">Portfolio URL</label>
                <input
                  id="profile-portfolio"
                  type="url"
                  maxlength="255"
                  placeholder="https://..."
                  formControlName="portfolio_url"
                />
              </div>
            </fieldset>

            <p class="hint">
              Website links should start with https:// or http://.
              Experience must be a whole number from 0 to 80.
            </p>

            @if (form.invalid && (form.touched || form.dirty)) {
              <p class="error" role="alert">
                Check the experience value, field lengths and
                website URLs before saving.
              </p>
            }

            <div class="actions">
              <button
                type="submit"
                class="primary"
                [disabled]="
                  saving() ||
                  deleting() ||
                  form.invalid ||
                  (profile() !== null && !form.dirty)
                "
              >
                @if (saving()) {
                  Saving…
                } @else if (profile() === null) {
                  Create profile
                } @else {
                  Save changes
                }
              </button>
            </div>
          </form>
        </section>

        @if (profile() !== null) {
          <section class="panel danger-zone">
            <h2>Delete profile</h2>
            <p>
              Deleting your profile removes its saved details.
              This action cannot be undone.
            </p>

            @if (deleteError(); as message) {
              <p class="error" role="alert">{{ message }}</p>
            }

            @if (!confirmingDelete()) {
              <button
                type="button"
                class="danger"
                [disabled]="saving() || deleting()"
                (click)="requestDelete()"
              >
                Delete profile…
              </button>
            } @else {
              <div
                class="confirmation"
                role="group"
                aria-label="Confirm profile deletion"
              >
                <p>
                  Are you sure? Unsaved form changes will also
                  be lost.
                </p>

                <div class="actions">
                  <button
                    type="button"
                    class="danger"
                    [disabled]="deleting() || saving()"
                    (click)="deleteProfile()"
                  >
                    {{ deleting() ? 'Deleting…' : 'Yes, delete profile' }}
                  </button>

                  <button
                    type="button"
                    [disabled]="deleting()"
                    (click)="cancelDelete()"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            }
          </section>
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
      line-height: 1.6;
      overflow-wrap: anywhere;
    }

    .intro, .hint {
      color: #5b687a;
    }

    header {
      margin-bottom: 1.5rem;
    }

    .panel {
      border: 1px solid #d8e0ea;
      border-radius: 14px;
      background: #fff;
      padding: 1.5rem;
      margin-bottom: 1.25rem;
    }

    .fields {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 1rem;
      border: 0;
      margin: 1.5rem 0 0;
      padding: 0;
      min-width: 0;
    }

    .field {
      display: flex;
      flex-direction: column;
      gap: .4rem;
      min-width: 0;
    }

    .field.full {
      grid-column: 1 / -1;
    }

    label {
      font-weight: 650;
    }

    input, textarea {
      box-sizing: border-box;
      width: 100%;
      padding: .7rem;
      border: 1px solid #cbd5e1;
      border-radius: 9px;
      font: inherit;
      color: inherit;
    }

    textarea {
      resize: vertical;
    }

    input:focus-visible,
    textarea:focus-visible,
    button:focus-visible,
    a:focus-visible {
      outline: 3px solid #93c5fd;
      outline-offset: 2px;
    }

    .hint {
      font-size: .88rem;
    }

    .actions {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: .75rem;
      margin-top: 1rem;
    }

    button {
      padding: .7rem 1rem;
      border: 1px solid #94a3b8;
      border-radius: 9px;
      font: inherit;
      cursor: pointer;
      background: #fff;
      color: inherit;
    }

    button.primary {
      background: #1d4ed8;
      border-color: #1d4ed8;
      color: #fff;
      font-weight: 650;
    }

    button.danger {
      border-color: #be123c;
      color: #9f1239;
    }

    button:disabled {
      opacity: .55;
      cursor: not-allowed;
    }

    .success {
      color: #166534;
    }

    .error {
      color: #9f1239;
    }

    .danger-zone {
      border-color: #fecdd3;
    }

    .confirmation {
      padding-top: .5rem;
    }

    @media (max-width: 640px) {
      .fields {
        grid-template-columns: 1fr;
      }

      .panel {
        padding: 1rem;
      }
    }
  `]
})
export class MyProfilePage implements OnInit {
  private readonly api = inject(ProfileApiService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly fb = inject(FormBuilder).nonNullable;

  private readonly urlValidators = [
    Validators.maxLength(255),
    Validators.pattern(/^https?:\/\/\S+$/i)
  ];

  readonly form = this.fb.group({
    first_name: ['', [Validators.maxLength(100)]],
    last_name: ['', [Validators.maxLength(100)]],
    phone: ['', [Validators.maxLength(30)]],
    location: ['', [Validators.maxLength(100)]],
    country: ['', [Validators.maxLength(100)]],
    headline: ['', [Validators.maxLength(255)]],
    summary: ['', [Validators.maxLength(2000)]],
    linkedin_url: ['', this.urlValidators],
    github_url: ['', this.urlValidators],
    portfolio_url: ['', this.urlValidators],
    years_experience: [
      0,
      [
        Validators.required,
        Validators.min(0),
        Validators.max(80),
        Validators.pattern(/^\d+$/)
      ]
    ]
  });

  readonly profile = signal<UserProfile | null>(null);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly deleting = signal(false);

  readonly loadError = signal<string | null>(null);
  readonly saveError = signal<string | null>(null);
  readonly deleteError = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);

  readonly confirmingDelete = signal(false);

  ngOnInit(): void {
    this.loadProfile();
  }

  loadProfile(): void {
    if (this.saving() || this.deleting()) {
      return;
    }

    this.loading.set(true);
    this.loadError.set(null);
    this.saveError.set(null);
    this.deleteError.set(null);
    this.successMessage.set(null);
    this.confirmingDelete.set(false);

    this.api.getProfile()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false))
      )
      .subscribe({
        next: (profile) => {
          this.profile.set(profile);
          this.form.reset(this.formValues(profile));
          this.form.markAsPristine();
        },
        error: (error: unknown) => {
          this.loadError.set(
            this.describeError(error, 'Please try again.')
          );
        }
      });
  }

  saveProfile(): void {
    if (this.loading() || this.saving() || this.deleting()) {
      return;
    }

    this.form.markAllAsTouched();

    const values = this.form.getRawValue();
    const experience = values.years_experience;

    if (
      this.form.invalid ||
      !Number.isInteger(experience) ||
      experience < 0 ||
      experience > 80
    ) {
      this.saveError.set('Please correct the form before saving.');
      return;
    }

    const trimOrNull = (text: string): string | null => {
      const trimmed = text.trim();
      return trimmed.length > 0 ? trimmed : null;
    };

    const payload: ProfilePayload = {
      first_name: trimOrNull(values.first_name),
      last_name: trimOrNull(values.last_name),
      phone: trimOrNull(values.phone),
      location: trimOrNull(values.location),
      country: trimOrNull(values.country),
      headline: trimOrNull(values.headline),
      summary: trimOrNull(values.summary),
      linkedin_url: trimOrNull(values.linkedin_url),
      github_url: trimOrNull(values.github_url),
      portfolio_url: trimOrNull(values.portfolio_url),
      years_experience: experience
    };

    const creating = this.profile() === null;

    this.saving.set(true);
    this.saveError.set(null);
    this.successMessage.set(null);
    this.confirmingDelete.set(false);

    const request = creating
      ? this.api.createProfile(payload)
      : this.api.updateProfile(payload);

    request
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.saving.set(false))
      )
      .subscribe({
        next: (profile) => {
          this.profile.set(profile);
          this.form.reset(this.formValues(profile));
          this.form.markAsPristine();
          this.successMessage.set(
            creating
              ? 'Your profile was created successfully.'
              : 'Your changes were saved successfully.'
          );
        },
        error: (error: unknown) => {
          this.saveError.set(
            this.describeError(
              error,
              'Unable to save your profile. Please try again.'
            )
          );
        }
      });
  }

  requestDelete(): void {
    if (
      this.profile() === null ||
      this.saving() ||
      this.deleting()
    ) {
      return;
    }

    this.deleteError.set(null);
    this.confirmingDelete.set(true);
  }

  cancelDelete(): void {
    if (!this.deleting()) {
      this.confirmingDelete.set(false);
    }
  }

  deleteProfile(): void {
    if (
      this.profile() === null ||
      !this.confirmingDelete() ||
      this.saving() ||
      this.deleting()
    ) {
      return;
    }

    this.deleting.set(true);
    this.deleteError.set(null);
    this.successMessage.set(null);

    this.api.deleteProfile()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.deleting.set(false))
      )
      .subscribe({
        next: () => {
          this.profile.set(null);
          this.form.reset(this.formValues(null));
          this.form.markAsPristine();
          this.confirmingDelete.set(false);
          this.successMessage.set(
            'Your profile was deleted successfully.'
          );
        },
        error: (error: unknown) => {
          this.deleteError.set(
            this.describeError(
              error,
              'Unable to delete your profile. Please try again.'
            )
          );
        }
      });
  }

  private formValues(profile: UserProfile | null) {
    return {
      first_name: profile?.first_name ?? '',
      last_name: profile?.last_name ?? '',
      phone: profile?.phone ?? '',
      location: profile?.location ?? '',
      country: profile?.country ?? '',
      headline: profile?.headline ?? '',
      summary: profile?.summary ?? '',
      linkedin_url: profile?.linkedin_url ?? '',
      github_url: profile?.github_url ?? '',
      portfolio_url: profile?.portfolio_url ?? '',
      years_experience: profile?.years_experience ?? 0
    };
  }

  private describeError(
    error: unknown,
    fallback: string
  ): string {
    if (error instanceof HttpErrorResponse) {
      if (error.status === 401) {
        return 'Your session has expired. Please sign in again.';
      }

      if (error.status === 422) {
        return 'Some profile fields were rejected. Check your entries.';
      }

      if (error.status === 409) {
        return 'A profile already exists. Reload to see the latest data.';
      }

      if (error.status === 404) {
        return 'Your profile was not found. Reload and try again.';
      }
    }

    return fallback;
  }
}
