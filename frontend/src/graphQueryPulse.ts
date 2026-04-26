export const QUERY_PULSE_TOTAL_MS = 1800;

export function queryPulseScale(ms: number): number {
  if (ms <= 0) return 1.28;
  if (ms >= QUERY_PULSE_TOTAL_MS) return 1;
  const t = ms / QUERY_PULSE_TOTAL_MS;
  const wave = Math.sin(t * Math.PI * 2.2) * (1 - t) * 0.18;
  return 1 + (1 - t) * 0.18 + wave;
}
