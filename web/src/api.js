const BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

async function get(path) {
  const res = await fetch(BASE + path);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `${res.status} ${res.statusText}`);
  }
  return res.json();
}

function query(params) {
  const clean = Object.entries(params).filter(([, v]) => v !== undefined && v !== null);
  return new URLSearchParams(clean).toString();
}

export const api = {
  rings: (params) => get(`/rings?${query(params)}`),
  ring: (id) => get(`/rings/${id}`),
  account: (id) => get(`/accounts/${encodeURIComponent(id)}`),
  accountRings: (id) => get(`/accounts/${encodeURIComponent(id)}/rings`),
  evaluation: () => get("/evaluation"),
  latestRun: () => get("/runs/latest"),
  riskHistogram: () => get("/analysis/risk-histogram"),
};
