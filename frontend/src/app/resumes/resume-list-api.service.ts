import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ResumeListResponse,
  ResumeUploadResponse
} from './resume-list.models';

@Injectable({ providedIn: 'root' })
export class ResumeListApiService {
  private readonly http = inject(HttpClient);

  getResumes(): Observable<ResumeListResponse> {
    return this.http.get<ResumeListResponse>('/api/v1/resumes');
  }

  uploadResume(
    title: string,
    file: File
  ): Observable<ResumeUploadResponse> {
    const form = new FormData();

    form.append('title', title);
    form.append('file', file, file.name);

    // Leave Content-Type unset. The browser supplies the
    // multipart boundary automatically.
    return this.http.post<ResumeUploadResponse>(
      '/api/v1/resumes',
      form
    );
  }
}
