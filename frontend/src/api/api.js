// Detect if the build is production or development
const isProduction = import.meta.env.MODE === "production";

// Your ngrok / production base URL
export const BASE_URL = "https://leeann-symbolistical-unpreternaturally.ngrok-free.dev";

// Main backend URLs
export const BASE_URLS = {
  user: isProduction
    ? BASE_URL               // production user API
    : "http://localhost:5000",   // local user API

  admin: isProduction
    ? BASE_URL               // production admin API
    : "http://localhost:5001",   // local admin API
};

// Unified API fetch wrapper
export async function apiFetch(path, options = {}) {
  const base = BASE_URL;
  const url = path.startsWith("http") ? path : `${base}${path}`;
  const isFormData = options.body instanceof FormData;

  const res = await fetch(url, {
    mode: "cors",
    headers: {
      "ngrok-skip-browser-warning": "true",
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(options.headers || {}),
    },
    ...options,
  });

  const raw = await res.text();
  let data = null;
  try {
    data = raw ? JSON.parse(raw) : null;
  } catch (e) {}

  if (!res.ok) {
    const msg =
      (data && (data.message || data.error)) ||
      raw ||
      `HTTP ${res.status} ${res.statusText}`;
    throw new Error(msg);
  }

  return data ?? null;
}

export function apiGet(path) {
  return apiFetch(path, { method: "GET" });
}

export function apiPost(path, body) {
  return apiFetch(path, { method: "POST", body: JSON.stringify(body) });
}

export function apiPut(path, body) {
  return apiFetch(path, { method: "PUT", body: JSON.stringify(body) });
}

export function apiDelete(path) {
  return apiFetch(path, { method: "DELETE" });
}
