/* main.js — Global JS for Boundless Moments */

// ── NAV SCROLL ───────────────────────────────
const nav = document.querySelector('.nav');
if (nav) {
  // Always scrolled on inner pages
  if (document.body.querySelector('.page-hero') || window.location.pathname !== '/') {
    nav.classList.add('scrolled');
  }
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 40);
  });
}

// ── HAMBURGER ────────────────────────────────
const hamburger = document.querySelector('.hamburger');
const navLinks  = document.querySelector('.nav-links');
if (hamburger && navLinks) {
  hamburger.addEventListener('click', () => {
    const open = navLinks.classList.toggle('open');
    const [s1, s2, s3] = hamburger.querySelectorAll('span');
    s1.style.transform = open ? 'rotate(45deg) translate(5px,5px)' : '';
    s2.style.opacity   = open ? '0' : '1';
    s3.style.transform = open ? 'rotate(-45deg) translate(5px,-5px)' : '';
  });
  navLinks.querySelectorAll('a').forEach(a => a.addEventListener('click', () => navLinks.classList.remove('open')));
}

// ── FADE-UP OBSERVER ─────────────────────────
const fadeObs = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
}, { threshold: 0.12 });
document.querySelectorAll('.fade-up').forEach(el => fadeObs.observe(el));

// ── CURSOR GLOW (desktop only) ───────────────
if (window.matchMedia('(pointer: fine)').matches) {
  const glow = Object.assign(document.createElement('div'), { style: `
    position:fixed;width:300px;height:300px;border-radius:50%;pointer-events:none;z-index:9998;
    background:radial-gradient(circle,rgba(168,147,106,0.08) 0%,transparent 70%);
    transform:translate(-50%,-50%);transition:left 0.6s ease,top 0.6s ease;
  ` });
  document.body.appendChild(glow);
  document.addEventListener('mousemove', e => { glow.style.left = e.clientX + 'px'; glow.style.top = e.clientY + 'px'; });
}
