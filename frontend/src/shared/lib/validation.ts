export function isFutureDateTime(date: string, time: string): boolean {
  if (!date || !time) return false;
  const value = new Date(`${date}T${time}`);
  return !Number.isNaN(value.getTime()) && value.getTime() > Date.now();
}

export function isValidContact(value: string): boolean {
  const contact = value.trim();
  return contact.length >= 5 && (contact.includes('@') || /\d{5,}/.test(contact.replace(/\D/g, '')));
}
