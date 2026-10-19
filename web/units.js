import { soundsText, example } from './notation.js';
import { markedUnits } from './diff.js';

export const esc = text => String(text ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function unitTip(unit, copy) {
  if (!unit.p.length) return copy.silentTip;
  return unit.p.map(phone => example(phone)).filter(Boolean).join(' · ');
}

function miniUnit(unit, state, copy) {
  const sound = soundsText(unit.p, state.notation, copy.silentSound);
  return `<span class="u${unit.miss ? ' miss' : ''}" data-tip="${esc(unitTip(unit, copy))}"><span class="g">${esc(unit.s)}</span><span class="p">${esc(sound)}</span></span>`;
}

function badgeHtml(row, copy) {
  const label = copy.category[row.category_pred || row.category] || row.category;
  const tip = copy.categoryTips[row.category_pred || row.category] || '';
  return `<span class="u cat" data-tip="${esc(tip)}"><span class="g">${esc(label)}</span></span>`;
}

export function miniHtml(row, state, copy) {
  const category = row.category_pred || row.category;
  if (category === 'abbreviation' || category === 'mixed' || category === 'unparsed') {
    const expansion = row.expansion ? `<span class="u"><span class="g">→ ${esc(row.expansion)}</span></span>` : '';
    return `<div class="mini">${badgeHtml(row, copy)}${expansion}${soundsMini(row, state, copy)}</div>`;
  }
  const units = row.pred ? markedUnits(row) : row.gold.map(unit => ({ ...unit, miss: false }));
  return `<div class="mini">${units.map(unit => miniUnit(unit, state, copy)).join('')}</div>`;
}

function soundsMini(row, state, copy) {
  const text = soundsText(row.pron.split(' '), state.notation, copy.silentSound).replace(/ \+ /g, ' · ');
  return `<span class="u"><span class="p">${esc(text)}</span></span>`;
}

function barHtml(unit, copy) {
  if (unit.c === undefined) return '';
  const low = unit.c < copy.lowBelow ? ' low' : '';
  return `<span class="bd-bar${low}" data-tip="${Math.round(unit.c * 100)}%"><i style="--c:${Math.round(unit.c * 100)}%"></i></span>`;
}

function bigUnit(unit, state, copy) {
  const sound = soundsText(unit.p, state.notation, copy.silentSound);
  const classes = `bd-unit${unit.p.length ? '' : ' silent'}${unit.miss ? ' miss' : ''}`;
  return `<div class="${classes}" data-tip="${esc(unitTip(unit, copy))}"><span class="bd-g">${esc(unit.s)}</span><span class="bd-p">${esc(sound)}</span>${barHtml(unit, copy)}</div>`;
}

function nameUnits(part, state, copy) {
  return part.units.map(unit => {
    const sound = soundsText(unit.p, state.notation, copy.silentSound);
    return `<span class="u"><span class="g">${esc(unit.s)}</span><span class="p">${esc(sound)}</span></span>`;
  }).join('');
}

export function letterLaneHtml(label, parts, state, copy) {
  const cells = parts.map(part => `<div class="bd-unit letter" data-tip="${esc(part.name)}"><span class="bd-g">${esc(part.letter)}</span><span class="bd-name">${esc(part.name)}</span><div class="mini">${nameUnits(part, state, copy)}</div></div>`);
  return `<div class="lane"><div class="lane-label">${esc(label)}</div><div class="bd">${cells.join('')}</div></div>`;
}

export function soundsLaneHtml(label, row, state, copy) {
  const text = soundsText(row.pron.split(' '), state.notation, copy.silentSound).replace(/ \+ /g, ' · ');
  return `<div class="lane"><div class="lane-label">${esc(label)}</div><div class="bd"><div class="bd-unit"><span class="bd-p">${esc(text)}</span></div></div></div>`;
}

export function laneHtml(label, units, state, copy) {
  return `<div class="lane"><div class="lane-label">${esc(label)}</div><div class="bd">${units.map(unit => bigUnit(unit, state, copy)).join('')}</div></div>`;
}

export function laneHtmlRaw(labelHtml, units, state, copy) {
  return `<div class="lane"><div class="lane-label">${labelHtml}</div><div class="bd">${units.map(unit => bigUnit(unit, state, copy)).join('')}</div></div>`;
}
