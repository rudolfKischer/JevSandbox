const SCHWA = { plain: 'schwa', dictionary: 'ə', ipa: 'ə', arpabet: 'AH' };
const SHORT_U = { plain: 'short u', dictionary: 'ŭ', ipa: 'ʌ', arpabet: 'AH' };
let table = {};

export async function loadNotation() {
  table = await (await fetch('../data/notation.json')).json();
}

export function bare(phone) {
  return phone.replace(/\d/g, '');
}

export function soundText(phone, mode) {
  const symbol = bare(phone);
  if (symbol === 'AH') return (phone.endsWith('0') ? SCHWA : SHORT_U)[mode];
  if (mode === 'arpabet') return symbol;
  return table[symbol]?.[mode] || symbol;
}

export function soundsText(phones, mode, silent) {
  return phones.length ? phones.map(phone => soundText(phone, mode)).join(' + ') : silent;
}

export function example(phone) {
  return table[bare(phone)]?.example || '';
}
