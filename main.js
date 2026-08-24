(() => {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const isCoarsePointer = window.matchMedia('(pointer: coarse)').matches;

  /* ---------- Stagger index assignment ---------- */
  document.querySelectorAll('.stagger').forEach((group) => {
    Array.from(group.children).forEach((child, i) => {
      child.style.setProperty('--i', i);
    });
  });

  /* ---------- Reveal on scroll ---------- */
  const reveals = document.querySelectorAll('.reveal');
  if (prefersReducedMotion || !('IntersectionObserver' in window)) {
    reveals.forEach((el) => el.classList.add('is-visible'));
  } else {
    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -8% 0px' }
    );
    reveals.forEach((el) => revealObserver.observe(el));
  }

  /* ---------- Nav: scroll hide + glass intensity ---------- */
  const nav = document.querySelector('.topnav');
  const progressBar = document.querySelector('.scroll-progress span');
  let lastY = window.scrollY;
  let ticking = false;
  let drawerOpen = false;

  const updateScroll = () => {
    const y = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const progress = docHeight > 0 ? Math.min(100, Math.max(0, (y / docHeight) * 100)) : 0;

    if (progressBar) progressBar.style.width = progress + '%';

    if (nav) {
      nav.classList.toggle('is-scrolled', y > 12);
      if (!drawerOpen) {
        nav.classList.toggle('is-hidden', y > 120 && y > lastY);
      }
    }
    lastY = y;
    ticking = false;
  };

  window.addEventListener(
    'scroll',
    () => {
      if (!ticking) {
        window.requestAnimationFrame(updateScroll);
        ticking = true;
      }
    },
    { passive: true }
  );
  updateScroll();

  /* ---------- Smooth anchor scrolling ---------- */
  document.querySelectorAll('a[href^="#"]').forEach((link) => {
    link.addEventListener('click', (e) => {
      const id = link.getAttribute('href');
      if (!id || id === '#') return;
      const target = document.querySelector(id);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: prefersReducedMotion ? 'auto' : 'smooth', block: 'start' });
        closeDrawer();
      }
    });
  });

  /* ---------- Scrollspy ---------- */
  const navLinks = document.querySelectorAll('.nav-links a');
  const sections = Array.from(navLinks)
    .map((link) => document.querySelector(link.getAttribute('href')))
    .filter(Boolean);

  if (sections.length && 'IntersectionObserver' in window) {
    const spy = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const link = document.querySelector(`.nav-links a[href="#${entry.target.id}"]`);
          if (!link) return;
          if (entry.isIntersecting) {
            navLinks.forEach((l) => l.classList.remove('is-active'));
            link.classList.add('is-active');
          }
        });
      },
      { rootMargin: '-45% 0px -50% 0px', threshold: 0 }
    );
    sections.forEach((section) => spy.observe(section));
  }

  /* ---------- Theme toggle ---------- */
  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const root = document.documentElement;
      const current = root.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try {
        localStorage.setItem('theme', next);
      } catch (e) {
        /* storage unavailable */
      }
    });
  }

  /* ---------- Mobile nav drawer ---------- */
  const burger = document.getElementById('navBurger');
  const drawer = document.getElementById('navDrawer');

  function openDrawer() {
    if (!burger || !drawer) return;
    drawerOpen = true;
    drawer.classList.add('is-open');
    burger.setAttribute('aria-expanded', 'true');
    document.body.classList.add('no-scroll');
  }
  function closeDrawer() {
    if (!burger || !drawer) return;
    drawerOpen = false;
    drawer.classList.remove('is-open');
    burger.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('no-scroll');
  }
  if (burger && drawer) {
    burger.addEventListener('click', () => (drawerOpen ? closeDrawer() : openDrawer()));
  }

  /* ---------- Animated stat counters ---------- */
  const statEls = document.querySelectorAll('.stat-number');
  if (statEls.length) {
    const animateCount = (el) => {
      const target = parseFloat(el.getAttribute('data-count') || '0');
      const prefix = el.getAttribute('data-prefix') || '';
      const suffix = el.getAttribute('data-suffix') || '';
      if (prefersReducedMotion) {
        el.textContent = prefix + target + suffix;
        return;
      }
      const duration = 1100;
      const start = performance.now();
      const tick = (now) => {
        const p = Math.min(1, (now - start) / duration);
        const eased = 1 - Math.pow(1 - p, 3);
        const value = Math.round(target * eased);
        el.textContent = prefix + value + suffix;
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    };

    if ('IntersectionObserver' in window) {
      const statObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              animateCount(entry.target);
              statObserver.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.6 }
      );
      statEls.forEach((el) => statObserver.observe(el));
    } else {
      statEls.forEach(animateCount);
    }
  }

  /* ---------- Tilt + cursor glow on cards ---------- */
  if (!isCoarsePointer && !prefersReducedMotion) {
    const cardSelectors = '.project-card, .publication, .stack-card, .info-card, .contact-card';
    document.querySelectorAll(cardSelectors).forEach((card) => {
      card.classList.add('tilt-card');
      const glow = document.createElement('span');
      glow.className = 'card-glow';
      glow.setAttribute('aria-hidden', 'true');
      card.prepend(glow);

      const maxTilt = 6;
      card.addEventListener('mouseenter', () => card.classList.add('is-hovering'));
      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const px = (e.clientX - rect.left) / rect.width;
        const py = (e.clientY - rect.top) / rect.height;
        const rx = (0.5 - py) * maxTilt * 2;
        const ry = (px - 0.5) * maxTilt * 2;
        card.style.transform = `perspective(900px) rotateX(${rx}deg) rotateY(${ry}deg) translateY(-2px)`;
        card.style.setProperty('--mx', `${px * 100}%`);
        card.style.setProperty('--my', `${py * 100}%`);
      });
      card.addEventListener('mouseleave', () => {
        card.classList.remove('is-hovering');
        card.style.transform = '';
      });
    });
  }

  /* ---------- Magnetic buttons ---------- */
  if (!isCoarsePointer && !prefersReducedMotion) {
    document.querySelectorAll('.btn').forEach((btn) => {
      btn.addEventListener('mousemove', (e) => {
        const rect = btn.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        btn.style.transform = `translate(${x * 0.18}px, ${y * 0.32}px)`;
      });
      btn.addEventListener('mouseleave', () => {
        btn.style.transform = '';
      });
    });
  }

  /* ---------- Cursor glow ---------- */
  const cursorGlow = document.querySelector('.cursor-glow');
  if (cursorGlow && !isCoarsePointer && !prefersReducedMotion) {
    let raf = null;
    window.addEventListener(
      'mousemove',
      (e) => {
        if (raf) return;
        raf = requestAnimationFrame(() => {
          cursorGlow.style.setProperty('--gx', `${e.clientX}px`);
          cursorGlow.style.setProperty('--gy', `${e.clientY}px`);
          cursorGlow.classList.add('is-active');
          raf = null;
        });
      },
      { passive: true }
    );
    document.addEventListener('mouseleave', () => cursorGlow.classList.remove('is-active'));
  }

  /* ---------- Command palette ---------- */
  const paletteBtn = document.getElementById('paletteBtn');
  const paletteOverlay = document.getElementById('paletteOverlay');
  const paletteInput = document.getElementById('paletteInput');
  const paletteList = document.getElementById('paletteList');

  if (paletteBtn && paletteOverlay && paletteInput && paletteList) {
    const commands = [
      { label: 'About', hint: 'Section', action: () => scrollToId('about') },
      { label: 'Pets', hint: 'Section', action: () => scrollToId('pets') },
      { label: 'Research & Publications', hint: 'Section', action: () => scrollToId('research') },
      { label: 'Experience', hint: 'Section', action: () => scrollToId('experience') },
      { label: 'Projects', hint: 'Section', action: () => scrollToId('projects') },
      { label: 'Stack', hint: 'Section', action: () => scrollToId('stack') },
      { label: 'Education', hint: 'Section', action: () => scrollToId('education') },
      { label: 'Contact', hint: 'Section', action: () => scrollToId('contact') },
      { label: 'GitHub profile', hint: 'Open link', action: () => window.open('https://github.com/hugebenevolence', '_blank', 'noreferrer') },
      { label: 'LinkedIn profile', hint: 'Open link', action: () => window.open('https://www.linkedin.com/in/nhantran8104/', '_blank', 'noreferrer') },
      { label: 'Email me', hint: 'mailto', action: () => (window.location.href = 'mailto:nhantd.dev@gmail.com') },
      {
        label: 'Toggle theme',
        hint: 'Dark / light',
        action: () => {
          if (themeToggle) themeToggle.click();
        },
      },
    ];

    function scrollToId(id) {
      const target = document.getElementById(id);
      if (target) target.scrollIntoView({ behavior: prefersReducedMotion ? 'auto' : 'smooth', block: 'start' });
    }

    let selectedIndex = 0;
    let filtered = commands;

    function renderList() {
      paletteList.innerHTML = '';
      if (!filtered.length) {
        const empty = document.createElement('li');
        empty.className = 'palette-empty';
        empty.textContent = 'No matches.';
        paletteList.appendChild(empty);
        return;
      }
      filtered.forEach((cmd, i) => {
        const li = document.createElement('li');
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = i === selectedIndex ? 'is-selected' : '';
        btn.innerHTML = `<span>${cmd.label}</span><small>${cmd.hint}</small>`;
        btn.addEventListener('click', () => runCommand(cmd));
        li.appendChild(btn);
        paletteList.appendChild(li);
      });
    }

    function runCommand(cmd) {
      cmd.action();
      closePalette();
    }

    function openPalette() {
      paletteOverlay.hidden = false;
      paletteInput.value = '';
      filtered = commands;
      selectedIndex = 0;
      renderList();
      requestAnimationFrame(() => paletteInput.focus());
      document.body.classList.add('no-scroll');
    }

    function closePalette() {
      paletteOverlay.hidden = true;
      document.body.classList.remove('no-scroll');
    }

    paletteBtn.addEventListener('click', openPalette);
    paletteOverlay.addEventListener('click', (e) => {
      if (e.target === paletteOverlay) closePalette();
    });

    paletteInput.addEventListener('input', () => {
      const q = paletteInput.value.trim().toLowerCase();
      filtered = commands.filter((c) => c.label.toLowerCase().includes(q));
      selectedIndex = 0;
      renderList();
    });

    paletteInput.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        selectedIndex = Math.min(selectedIndex + 1, filtered.length - 1);
        renderList();
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        selectedIndex = Math.max(selectedIndex - 1, 0);
        renderList();
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filtered[selectedIndex]) runCommand(filtered[selectedIndex]);
      } else if (e.key === 'Escape') {
        closePalette();
      }
    });

    document.addEventListener('keydown', (e) => {
      const isMeta = e.metaKey || e.ctrlKey;
      if (isMeta && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (paletteOverlay.hidden) openPalette();
        else closePalette();
      } else if (e.key === 'Escape') {
        if (!paletteOverlay.hidden) closePalette();
        if (drawerOpen) closeDrawer();
      }
    });
  }
})();
