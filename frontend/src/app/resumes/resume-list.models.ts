export interface ResumeListItem {
  id: number;
  title: string | null;
  file_name: string | null;
  file_type: string | null;
  status: string | null;
  created_at: string | null;
}

export interface ResumeListResponse {
  data: ResumeListItem[];
}
