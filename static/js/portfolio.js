
const items    = Array.from(document.querySelectorAll('.gallery-item'));
const lightbox = document.getElementById('lightbox');
let currentIdx = 0;

function openLb(idx) {
  currentIdx = idx;
  const item = items[idx];
  document.getElementById('lbTitle').textContent = item.querySelector('.gallery-overlay h4').textContent;
  document.getElementById('lbMeta').textContent  = item.querySelector('.gallery-overlay span').textContent;
  const thumb = item.querySelector('.gallery-thumb');
  const bg = thumb.tagName === 'IMG'
    ? `url(${thumb.src}) center/cover`
    : window.getComputedStyle(thumb).background;
  document.getElementById('lbImg').style.background = bg;
  lightbox.classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeLb() { lightbox.classList.remove('open'); document.body.style.overflow = ''; }

items.forEach((item, i) => item.addEventListener('click', () => openLb(i)));
document.getElementById('lbClose').addEventListener('click', closeLb);
document.getElementById('lbPrev').addEventListener('click', () => openLb((currentIdx - 1 + items.length) % items.length));
document.getElementById('lbNext').addEventListener('click', () => openLb((currentIdx + 1) % items.length));
lightbox.addEventListener('click', e => { if (e.target === lightbox) closeLb(); });
document.addEventListener('keydown', e => {
  if (!lightbox.classList.contains('open')) return;
  if (e.key === 'Escape')      closeLb();
  if (e.key === 'ArrowLeft')  document.getElementById('lbPrev').click();
  if (e.key === 'ArrowRight') document.getElementById('lbNext').click();
});
