// Highest riskScore in the data is ~65 (run 1790180260), so the scale tops out
// there; with 100 the red end would never be used.
export const RISK_MAX = 65;

export function riskColor(score, max = RISK_MAX) {
  if (score == null) return "#bbbbbb";
  const s = Math.max(0, Math.min(1, score / max));
  return `hsl(${120 - s * 120}, 70%, 45%)`;
}
