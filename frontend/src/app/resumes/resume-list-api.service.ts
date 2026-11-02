import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { ResumeListResponse } from './resume-list.models';

@Injectable({ providedIn: 'root' })
export class ResumeListApiService {
  private readonly http = inject(HttpClient);

  getResumes(): Observable<ResumeListResponse> {
    return this.http.get<ResumeListResponse>('/api/v1/resumes');
  }
}
