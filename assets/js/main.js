// ── Collapsible sections ──────────────────────────────────────────────────
document.querySelectorAll('.section-toggle').forEach(btn => {
  btn.addEventListener('click', () => {
    const body = btn.closest('.section').querySelector('.section-body');
    const collapsed = body.classList.toggle('collapsed');
    btn.textContent = collapsed ? 'Expand' : 'Collapse';
  });
});

// ── Smooth-scroll nav links with offset compensation ─────────────────────
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (!target) return;
    e.preventDefault();
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});

// ── Active nav link on scroll ─────────────────────────────────────────────
const sections = document.querySelectorAll('section[id]');
const navLinks  = document.querySelectorAll('.nav-links a[href^="#"]');

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      navLinks.forEach(l => l.style.color = '');
      const active = document.querySelector(`.nav-links a[href="#${entry.target.id}"]`);
      if (active) active.style.color = 'var(--accent)';
    }
  });
}, { rootMargin: '-30% 0px -60% 0px' });

sections.forEach(s => observer.observe(s));
