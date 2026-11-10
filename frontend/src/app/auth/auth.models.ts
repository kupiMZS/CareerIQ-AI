export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthUser {
  id: number;
  name: string;
  email: string;
  created_at: string | null;
}
