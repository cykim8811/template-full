export interface User {
  id: string;
  email: string;
  username: string;
  avatar_url: string | null;
  created_at: string;
}

export async function fetchCurrentUser(): Promise<User | null> {
  const res = await fetch("/api/auth/me");
  if (!res.ok) return null;
  return res.json();
}
