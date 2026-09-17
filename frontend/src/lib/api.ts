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
    throw new Error(await parseErrorBody(res));
  }

  // DELETE /notes/{id} answers 204 with no body. Calling res.json() on that
  // throws "Unexpected end of JSON input", so a delete that actually succeeded
  // was reported to the user as a failure and the list never refreshed.
  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

async function parseErrorBody(res: Response): Promise<string> {
  const body = await res.text();
  let detail: unknown = body;
  try {
    detail = JSON.parse(body)?.detail ?? body;
  } catch {
    // not JSON, keep raw text
  }
  if (Array.isArray(detail)) {
    detail = detail
      .map((e) =>
        typeof e?.msg === "string"
          ? `${e.msg} (${e?.loc?.join(".")})`
          : JSON.stringify(e),
      )
      .join("; ");
  } else if (typeof detail !== "string") {
    detail = JSON.stringify(detail);
  }
  return String(detail);
}

// File-download endpoints (StreamingResponse) return a binary body plus a
// Content-Disposition filename — request<T>'s res.json() would throw on
// that body, and it has nowhere to hand back the filename anyway.
async function requestBlob(
  path: string,
  init: RequestInit = {},
): Promise<{ blob: Blob; filename?: string }> {
  const token = getCurrentToken();

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });

  if (!res.ok) {
    throw new Error(await parseErrorBody(res));
  }

  const match = res.headers
    .get("Content-Disposition")
    ?.match(/filename="([^"]+)"/);

  return { blob: await res.blob(), filename: match?.[1] };
}

export const api = { request, requestBlob };
