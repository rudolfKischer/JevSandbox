const box = document.getElementById('tip');

function place(target) {
  const rect = target.getBoundingClientRect();
  box.style.left = Math.min(rect.left, window.innerWidth - 270) + 'px';
  box.style.top = rect.bottom + 6 + 'px';
}

document.addEventListener('mouseover', event => {
  const target = event.target.closest('[data-tip]');
  if (!target) return;
  box.textContent = target.dataset.tip;
  place(target);
  box.classList.add('on');
});

document.addEventListener('mouseout', event => {
  if (event.target.closest('[data-tip]')) box.classList.remove('on');
});
