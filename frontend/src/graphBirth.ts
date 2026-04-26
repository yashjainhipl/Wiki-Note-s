export const BIRTH_TOTAL_MS = 1400;

export function birthVisual(ms: number): { scale: number; tintAlpha: number } {
  const t = Math.max(0, Math.min(1, ms / BIRTH_TOTAL_MS));
  const ease = 1 - (1 - t) * (1 - t);
  return {
    scale: 1 + (1 - ease) * 1.4,
    tintAlpha: 1 - ease,
  };
}
