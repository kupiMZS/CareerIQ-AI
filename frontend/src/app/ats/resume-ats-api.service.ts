import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { ResumeAtsApiResponse } from './resume-ats.models';

@Injectable({ providedIn: 'root' })
export class ResumeAtsApiService {
  private readonly http = inject(HttpClient);

  requestReport(resumeId: number): Observable<ResumeAtsApiResponse> {
    if (!Number.isSafeInteger(resumeId) || resumeId <= 0) {
      throw new RangeError('Resume ID must be a positive safe integer.');
    }

    return this.http.post<ResumeAtsApiResponse>(
      `/api/v1/resumes/${resumeId}/analysis/ats`,
      {}
    );
  }
}
