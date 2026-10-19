import { soundsText, soundText } from './notation.js';
import { esc } from './units.js';

function optionText(text, state) {
  return esc(text).replace(/\{(\w+)\}/g, (_, phone) => esc(soundText(phone, state.notation)));
}

function optionHtml(option, index, state) {
  const [text, share] = option;
  const shown = optionText(text, state).replace(/\[(.*?)\]/, '<b>$1</b>');
  return `<span class="opt${index === 0 ? ' top' : ''}">${shown}<em>${Math.round(share * 100)}%</em></span>`;
}

function labelOf(row, state, copy) {
  if (row.sounds?.length) return soundsText(row.sounds, state.notation, copy.silentSound);
  return row.text || '';
}

function rowHtml(row, state, copy) {
  const options = row.options.map((option, index) => optionHtml(option, index, state)).join('');
  return `<div class="why-row"><span class="why-sound">${esc(labelOf(row, state, copy))}</span>${options}</div>`;
}

export function whyHtml(row, state, copy) {
  const rows = row.detail?.rows || [];
  if (!rows.length) return `<div class="note">${esc(copy.why.none)}</div>`;
  return `<div class="why-body">${rows.map(item => rowHtml(item, state, copy)).join('')}</div>`;
}
