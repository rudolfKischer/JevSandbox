import { soundsText } from './notation.js';
import { esc } from './units.js';

function optionLabel(option, state, copy) {
  if (!option.pron) return option.label;
  return soundsText(option.pron.split(' '), state.notation, copy.silentSound).replace(/ \+ /g, ' · ');
}

export function pickLine(row, state, copy) {
  const chosen = row.options.find(option => option.key === row.pick);
  const hint = row.sense ? `<div class="pickline hint" data-tip="${esc(row.sense)}">${esc(row.sense)}</div>` : '';
  return `${hint}<div class="pickline">${esc(optionLabel(chosen, state, copy))}</div>`;
}

function optRow(row, option, state, copy) {
  const right = option.key === row.answer;
  const share = Math.round(option.p * 100);
  const mark = right ? `<span class="ok" data-tip="${esc(copy.task.answerTip)}">${copy.task.correct}</span>` : '<span class="ok"></span>';
  return `<div class="optrow${right ? ' right' : ''}">${mark}<span class="lbl">${esc(optionLabel(option, state, copy))}</span><span class="bar"><i style="--c:${share}%"></i></span><em>${share}%</em></div>`;
}

export function taskPanel(row, state, copy) {
  const head = `<div class="p-head"><span class="p-word">${esc(row.word)}</span></div>`;
  const sense = row.sense ? `<div class="chips"><span class="chip sense">${esc(row.sense)}</span></div>` : '';
  return head + sense + row.options.map(option => optRow(row, option, state, copy)).join('');
}
