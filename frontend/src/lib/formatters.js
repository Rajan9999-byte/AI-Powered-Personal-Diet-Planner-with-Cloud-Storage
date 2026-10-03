export function formatNumber(value, suffix = '') {
  const number = Number(value || 0);
  return `${new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(number)}${suffix}`;
}

export function formatCalories(value) {
  return `${formatNumber(value)} kcal`;
}

export function progressPercent(current, target) {
  if (!target || target <= 0) return 0;
  return Math.min(100, Math.max(0, Math.round((Number(current || 0) / Number(target)) * 100)));
}

export function relativeDate(iso) {
  if (!iso) return 'Not yet';
  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' }).format(new Date(iso));
}
