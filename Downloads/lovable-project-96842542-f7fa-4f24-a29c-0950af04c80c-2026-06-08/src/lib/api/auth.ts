import { apiFetch, setToken } from "./client";

export type ApiUser = {
  id: string;
  email: string;
  full_name: string | null;
};

export async function signUp(email: string, password: string, fullName?: string) {
  const res = await apiFetch<{ access_token: string; user: ApiUser }>("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  setToken(res.access_token);
  return res;
}

export async function signIn(email: string, password: string) {
  const res = await apiFetch<{ access_token: string; user: ApiUser }>("/api/auth/signin", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(res.access_token);
  return res;
}

export async function getMe(): Promise<ApiUser | null> {
  try {
    return await apiFetch<ApiUser>("/api/auth/me");
  } catch {
    setToken(null);
    return null;
  }
}

export function signOut() {
  setToken(null);
}
