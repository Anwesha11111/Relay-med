/**
 * Tiny typed fetch helper for the Relay-med backend.
 * Centralises the API base URL and bearer-token handling so auth and any
 * future data calls share one place.
 */
export const API_BASE: string =
  (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

async function parse(res: Response): Promise<any> {
  const text = await res.text();
  let data: any = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) {
    const detail =
      (data && typeof data === "object" && (data.detail || data.message)) ||
      (typeof data === "string" && data) ||
      `Request failed (${res.status})`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

export async function apiPost<T = any>(path: string, body?: unknown, token?: string | null): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (err: any) {
    throw new Error(
      `Cannot reach the server at ${API_BASE}. ` +
      `Please make sure the backend is running (uvicorn backend.main:app --port 8000). ` +
      `Original error: ${err?.message ?? err}`
    );
  }
  return parse(res);
}

export async function apiGet<T = any>(path: string, token?: string | null): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
  } catch (err: any) {
    throw new Error(
      `Cannot reach the server at ${API_BASE}. ` +
      `Please make sure the backend is running (uvicorn backend.main:app --port 8000). ` +
      `Original error: ${err?.message ?? err}`
    );
  }
  return parse(res);
}
