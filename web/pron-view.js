import { soundText, bare } from './notation.js';
import { esc } from './units.js';

const shown = phone => (phone === 'AH' ? 'AH0' : phone);

export function lcsMask(pred, truths) {
  let best = pred.map(() => false), score = -1;
  truths.forEach(truth => {
    const rows = Array.from({ length: pred.length + 1 }, () => new Array(truth.length + 1).fill(0));
    for (let i = 1; i <= pred.length; i++) for (let j = 1; j <= truth.length; j++) rows[i][j] = pred[i - 1] === truth[j - 1] ? rows[i - 1][j - 1] + 1 : Math.max(rows[i - 1][j], rows[i][j - 1]);
    if (rows[pred.length][truth.length] > score) {
      score = rows[pred.length][truth.length];
      const mask = pred.map(() => false);
      let i = pred.length, j = truth.length;
      while (i > 0 && j > 0) {
        if (pred[i - 1] === truth[j - 1]) { mask[i - 1] = true; i--; j--; } else if (rows[i - 1][j] >= rows[i][j - 1]) i--; else j--;
      }
      best = mask;
    }
  });
  return best;
}

export function phoneRow(phones, mode, mask, big = false) {
  if (!phones.length) return '<span class="chip">–</span>';
  return `<div class="ph-row">${phones.map((p, i) => `<span class="ph${big ? ' big' : ''}${mask && !mask[i] ? ' miss' : ''}">${esc(soundText(shown(bare(p)), mode))}</span>`).join('')}</div>`;
}

export function candidateRows(row, mode, truths) {
  return (row.candidates || []).map(c => {
    const right = truths.some(t => t.join(' ') === c.pron.join(' '));
    const bar = c.p ? `<span class="bar"><i style="--c:${Math.round(c.p * 100)}%"></i></span><em>${Math.round(c.p * 100)}%</em>` : '<span class="bar"></span><em></em>';
    return `<div class="cand${right ? ' right' : ''}"><span class="src">${esc(c.source)}${right ? ' ✓' : ''}</span>${phoneRow(c.pron, mode, null)}${bar}</div>`;
  }).join('');
}
