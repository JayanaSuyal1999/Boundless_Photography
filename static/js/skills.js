
const fills = document.querySelectorAll('.skill-bar-fill');
const barObs = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      const level = e.target.dataset.level || 0;
      e.target.style.width = level + '%';
      barObs.unobserve(e.target);
    }
  });
}, { threshold: 0.3 });

fills.forEach(f => barObs.observe(f));
