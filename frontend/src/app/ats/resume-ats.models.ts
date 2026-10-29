export type AtsFindingCode =
  | 'contact_email'
  | 'section_skills'
  | 'section_education'
  | 'section_experience'
  | 'section_skills_content'
  | 'section_education_content'
  | 'section_experience_content'
  | 'quantified_outcome_evidence';

export type AtsFindingStatus =
  | 'satisfied'
  | 'needs_attention'
  | 'not_assessed';

export interface ResumeAtsFinding {
  code: AtsFindingCode;
  status: AtsFindingStatus;
  explanation: string;
  supporting_text: string[];
  recommendation: string | null;
}

export interface ResumeAtsReport {
  report_version: 'ats-v1';
  score: null;
  findings: ResumeAtsFinding[];
  limitations: string[];
}

export interface ResumeAtsApiResponse {
  message: string;
  data: ResumeAtsReport;
}
