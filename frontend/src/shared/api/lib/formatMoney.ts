/**
 * Форматирует "13000.00" → "13 000,00 ₽"
 * Не использует Number(), чтобы не терять копейки.
 */
export function formatMoney(amountStr: string): string {
  if (!amountStr) return '0,00 ₽';
  const [whole, frac = '00'] = amountStr.split('.');
  const withSpaces = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  return `${withSpaces},${frac.padEnd(2, '0')} ₽`;
}