export function formatMoney(amountStr: string): string {
  if (!amountStr) return '0,00 ₽';
  const parts = amountStr.split('.');
  const whole = parts[0];
  const frac = (parts[1] ?? '00').padEnd(2, '0').slice(0, 2);
  const withSpaces = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  return withSpaces + ',' + frac + ' ₽';
}
