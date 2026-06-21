export interface CardInfo {
  type: string;
  display: string;
  pattern: RegExp;
  lengths: number[];
  cvcLength: number;
  format: number[];
}

const cards: CardInfo[] = [
  { type: 'visa', display: 'Visa', pattern: /^4/, lengths: [13, 16, 19], cvcLength: 3, format: [4, 4, 4, 4] },
  { type: 'mastercard', display: 'Mastercard', pattern: /^(5[1-5]|2[2-7])/, lengths: [16], cvcLength: 3, format: [4, 4, 4, 4] },
  { type: 'amex', display: 'American Express', pattern: /^3[47]/, lengths: [15], cvcLength: 4, format: [4, 6, 5] },
  { type: 'discover', display: 'Discover', pattern: /^(6011|65|64[4-9])/, lengths: [16, 19], cvcLength: 3, format: [4, 4, 4, 4] },
  { type: 'jcb', display: 'JCB', pattern: /^35(2[89]|[3-8])/, lengths: [16, 19], cvcLength: 3, format: [4, 4, 4, 4] },
  { type: 'unionpay', display: 'UnionPay', pattern: /^62/, lengths: [16, 17, 18, 19], cvcLength: 3, format: [4, 4, 4, 4] },
];

export function detectCardType(number: string): CardInfo | null {
  const cleaned = number.replace(/\D/g, '');
  for (const card of cards) {
    if (card.pattern.test(cleaned)) return card;
  }
  return null;
}

export function formatCardNumber(number: string, card: CardInfo | null): string {
  const cleaned = number.replace(/\D/g, '');
  if (!card) return cleaned;
  const parts: string[] = [];
  let pos = 0;
  for (const len of card.format) {
    if (pos >= cleaned.length) break;
    parts.push(cleaned.slice(pos, pos + len));
    pos += len;
  }
  return parts.join(' ');
}

export function formatExpiry(value: string): string {
  const cleaned = value.replace(/\D/g, '');
  if (cleaned.length <= 2) return cleaned;
  return cleaned.slice(0, 2) + ' / ' + cleaned.slice(2, 4);
}

export function isValidCardNumber(number: string, card: CardInfo | null): boolean {
  const cleaned = number.replace(/\D/g, '');
  if (!card) return false;
  if (!card.lengths.includes(cleaned.length)) return false;
  return luhnCheck(cleaned);
}

export function isValidExpiry(value: string): boolean {
  const cleaned = value.replace(/\D/g, '');
  if (cleaned.length !== 4) return false;
  const month = parseInt(cleaned.slice(0, 2), 10);
  const year = parseInt(cleaned.slice(2, 4), 10) + 2000;
  if (month < 1 || month > 12) return false;
  const now = new Date();
  const expiry = new Date(year, month);
  return expiry > now;
}

export function isValidCvc(value: string, card: CardInfo | null): boolean {
  const cleaned = value.replace(/\D/g, '');
  const len = card?.cvcLength || 3;
  return cleaned.length === len;
}

export function isValidPhone(value: string): boolean {
  const cleaned = value.replace(/[\s\-\(\)]/g, '');
  return cleaned.length >= 8 && /^\+?\d+$/.test(cleaned);
}

function luhnCheck(num: string): boolean {
  let sum = 0;
  let alternate = false;
  for (let i = num.length - 1; i >= 0; i--) {
    let digit = parseInt(num[i], 10);
    if (alternate) {
      digit *= 2;
      if (digit > 9) digit -= 9;
    }
    sum += digit;
    alternate = !alternate;
  }
  return sum % 10 === 0;
}

export const CARD_LOGOS: Record<string, string> = {
  visa: `<svg viewBox="0 0 24 16" class="w-10 h-6"><rect width="24" height="16" rx="2" fill="#1A1F71"/><text x="12" y="11" text-anchor="middle" fill="white" font-size="6" font-weight="bold" font-family="Arial">VISA</text></svg>`,
  mastercard: `<svg viewBox="0 0 24 16" class="w-10 h-6"><rect width="24" height="16" rx="2" fill="#231F20"/><circle cx="9" cy="8" r="4.5" fill="#EB001B"/><circle cx="15" cy="8" r="4.5" fill="#F79E1B" opacity="0.8"/></svg>`,
  amex: `<svg viewBox="0 0 24 16" class="w-10 h-6"><rect width="24" height="16" rx="2" fill="#2E77BC"/><text x="12" y="10" text-anchor="middle" fill="white" font-size="4" font-weight="bold" font-family="Arial">AMEX</text></svg>`,
  discover: `<svg viewBox="0 0 24 16" class="w-10 h-6"><rect width="24" height="16" rx="2" fill="url(#d-g)"/><linearGradient id="d-g"><stop offset="0%" stop-color="#E67E22"/><stop offset="100%" stop-color="#F39C12"/></linearGradient><text x="12" y="10" text-anchor="middle" fill="white" font-size="4" font-weight="bold" font-family="Arial">DISCOVER</text></svg>`,
};
