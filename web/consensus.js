import { signature } from './diff.js';

const MIN_AGREE = 3;
const SKIP = new Set(['baseline', 'e', 'senses', 'kinds']);

export function findDoubts(all) {
  const votes = {};
  Object.values(all).filter(run => !SKIP.has(run.method) && run.live).forEach(run => {
    run.words.filter(row => row.pred && (row.category || 'word') === 'word' && !row.review && row.gold && row.gold.length).forEach(row => {
      const bucket = (votes[row.id] = votes[row.id] || {});
      const key = signature(row.pred);
      (bucket[key] = bucket[key] || { count: 0, units: row.pred }).count += 1;
      bucket.gold = [row.gold, ...(row.accept || [])].map(signature);
    });
  });
  const doubts = {};
  Object.entries(votes).forEach(([id, bucket]) => {
    const { gold, ...options } = bucket;
    const top = Object.entries(options).sort((a, b) => b[1].count - a[1].count)[0];
    if (top && top[1].count >= MIN_AGREE && !gold.includes(top[0])) doubts[id] = { count: top[1].count, units: top[1].units };
  });
  return doubts;
}
