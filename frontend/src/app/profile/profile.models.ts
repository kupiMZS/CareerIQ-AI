export interface UserProfile {
  id: number;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  location: string | null;
  country: string | null;
  headline: string | null;
  summary: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
  years_experience: number;
}

export type ProfilePayload = Partial<Omit<UserProfile, 'id'>>;
