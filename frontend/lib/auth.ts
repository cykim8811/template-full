export interface User {
  id: string;
  email: string;
  username: string;
  avatar_url: string | null;
  created_at: string;
}

export interface UserUpdate {
  username?: string;
  avatar_url?: string | null;
}

export async function fetchCurrentUser(): Promise<User | null> {
  const res = await fetch("/api/auth/me");
  if (!res.ok) return null;
  return res.json();
}

export async function updateCurrentUser(data: UserUpdate): Promise<User> {
  const res = await fetch("/api/users/me", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail ?? "Failed to update profile");
  }
  return res.json();
}
