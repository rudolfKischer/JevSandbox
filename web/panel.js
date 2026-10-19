import { soundsText } from './notation.js';
import { markedUnits } from './diff.js';
import { esc, laneHtml, letterLaneHtml, soundsLaneHtml } from './units.js';
import { whyHtml } from './why.js';

function chipsHtml(row, state, copy) {
  const parts = [];
  const doubt = row.review ? null : state.doubts[row.id];
  if (row.review) parts.push(`<span class="chip reviewed" data-tip="${esc(row.review)}">${esc(copy.review.chip)}: ${esc(row.review.split(':')[0])}</span>`);
  const category = row.category_pred || row.category;
  if (category && category !== 'word') parts.push(`<span class="chip cat" data-tip="${esc(copy.categoryTips[category] || '')}">${esc(copy.category[category] || category)}</span>`);
  Object.entries(row.concepts || {}).forEach(([name, items]) => parts.push(`<span class="chip concept" data-tip="${esc(copy.conceptsTip)}">${esc(name)}: ${esc(items.join(', '))}</span>`));
  const ext = state.nettalk[row.id] || row.nettalk;
  if (ext && row.pred && row.nettalk_ok !== undefined && row.nettalk_ok !== null) parts.push(`<span class="chip ${row.nettalk_ok ? 'agree' : 'differs'}" data-tip="${esc(copy.nettalk.tip)}">${esc(row.nettalk_ok ? copy.nettalk.agree : copy.nettalk.differs)}</span>`);
  const judge = row.judge || state.judged[row.word];
  if (judge) parts.push(`<span class="chip judge ${judge.verdict}" data-tip="${esc(copy.judge.tip + (judge.note ? ' ' + judge.note : ''))}">${esc(copy.judge[judge.verdict])}${judge.pattern ? ' · ' + esc(judge.pattern) : ''}</span>`);
  if (doubt) parts.push(`<span class="chip doubt" data-tip="${esc(copy.doubt.tip)}">⚑ ${doubt.count} ${esc(copy.doubt.chip)}</span>`);
  (row.gap || []).forEach(unit => parts.push(`<span class="chip gap" data-tip="${esc(copy.gap.tip)}">${esc(copy.gap.chip)}: ${esc(unit)}</span>`));
  if (row.sense) parts.push(`<span class="chip sense">${esc(row.sense)}</span>`);
  if (row.dialect) parts.push(`<span class="chip dialect">${esc(row.dialect)}</span>`);
  row.tags.filter(tag => tag !== category).forEach(tag => parts.push(`<span class="chip">${esc(tag)}</span>`));
  return `<div class="chips">${parts.join('')}</div>`;
}

function pronText(row, state, copy) {
  return soundsText(row.pron.split(' '), state.notation, copy.silentSound).replace(/ \+ /g, ' · ');
}

function noteHtml(text) {
  return `<div class="note">${esc(text)}</div>`;
}

function abbreviationHtml(row, state, copy) {
  const parts = [noteHtml(copy.abbrevNote), soundsLaneHtml(copy.lanes.sounds, row, state, copy)];
  if (row.expansion && row.expansion_units) {
    parts.push(laneHtml(`${copy.lanes.expansion}: ${row.expansion}`, row.expansion_units.map(unit => ({ ...unit })), state, copy));
  } else {
    parts.push(noteHtml(copy.noExpansion));
  }
  return parts.join('');
}

function lanes(row, other, state, copy) {
  const gold = row.gold.map(unit => ({ ...unit }));
  const parts = [];
  const doubt = row.review ? null : state.doubts[row.id];
  const category = row.category_pred || row.category;
  if (category === 'abbreviation') return abbreviationHtml(row, state, copy);
  if (category === 'mixed' || category === 'unparsed') return noteHtml(category === 'mixed' ? copy.mixedNote : copy.unparsedNote) + soundsLaneHtml(copy.lanes.sounds, row, state, copy);
  if (row.letterism) parts.push(letterLaneHtml(copy.lanes.letters, row.letterism, state, copy));
  if (row.pred && !row.letterism) parts.push(laneHtml(copy.lanes.pred, markedUnits(row), state, copy));
  if (other?.pred) parts.push(laneHtml(copy.lanes.baseline, markedUnits(other), state, copy));
  if (doubt) parts.push(laneHtml(copy.lanes.consensus, doubt.units.map(unit => ({ ...unit })), state, copy));
  if (gold.length) parts.push(laneHtml(copy.lanes.gold, gold, state, copy));
  const ext = state.nettalk[row.id]?.units || row.nettalk;
  if (ext) parts.push(laneHtml(copy.lanes.nettalk, ext.map(unit => ({ ...unit })), state, copy));
  if (!row.pred) parts.unshift(noteHtml(row.unavailable ? copy.unavailable : copy.dry));
  return parts.join('');
}

function whySection(row, state, copy) {
  if (!row.pred) return '';
  const open = state.why;
  const body = open ? whyHtml(row, state, copy) : '';
  return `<div class="why"><button class="why-btn" data-act="why">${esc(open ? copy.why.close : copy.why.open)}</button>${body}</div>`;
}

export function panelHtml(row, other, state, copy, compare = '') {
  if (!row) return `<div class="empty">${esc(copy.empty)}</div>`;
  const head = `<div class="p-head"><span class="p-word">${esc(row.word)}</span><span class="p-pron">${esc(pronText(row, state, copy))}</span>${compare}</div>`;
  return head + chipsHtml(row, state, copy) + lanes(row, other, state, copy) + whySection(row, state, copy);
}
