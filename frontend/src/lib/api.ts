// Everything except auth goes through here, against our own FastAPI backend.

import { getCurrentToken } from "./authStore";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getCurrentToken();
  //we dont want to force application/json conent type
  const isFormData = init.body instanceof FormData;

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });

  if (!res.ok) {
    const body = await res.text();
    let detail = body;
    try {
      detail = JSON.parse(body)?.detail ?? body;
    } catch {
      // not JSON, keep raw text
    }
    throw new Error(detail);
  }

  return res.json() as Promise<T>;
}

export const api = { request };
