/**
 * Palazzo Usellini - Script Principale (Zero Dipendenze, 100% GDPR Compliant)
 * Funzionalità: Header dinamico, Navigazione Mobile, Scroll Reveal, Lightbox Touch
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Header con effetto blur allo scroll
  const header = document.querySelector('.site-header');
  const handleScroll = () => {
    if (window.scrollY > 40) {
      header?.classList.add('is-scrolled');
    } else {
      header?.classList.remove('is-scrolled');
    }
  };
  window.addEventListener('scroll', handleScroll, { passive: true });
  handleScroll();

  // 2. Menu Mobile Drawer
  const menuToggle = document.querySelector('.menu-toggle');
  if (menuToggle) {
    menuToggle.addEventListener('click', () => {
      const isOpen = document.body.classList.toggle('nav-open');
      menuToggle.setAttribute('aria-expanded', isOpen);
    });

    // Chiude il menu mobile quando si clicca su un link o fuori
    document.querySelectorAll('.site-nav a').forEach(link => {
      link.addEventListener('click', () => {
        document.body.classList.remove('nav-open');
        menuToggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // 3. Selettore Tema Scuro / Chiaro (Inizializzato subito per massima reattività)
  initThemeToggle();

  // 4. Scroll Reveal via IntersectionObserver (solo sotto la piega, zero ritardi all'apertura)
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!prefersReducedMotion && 'IntersectionObserver' in window) {
    const revealElements = document.querySelectorAll('.reveal, .reveal-stagger');
    const revealObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, {
      rootMargin: '0px 0px -40px 0px',
      threshold: 0.05
    });

    revealElements.forEach(el => revealObserver.observe(el));
  } else {
    // Se l'utente preferisce ridurre il movimento o il browser non supporta l'observer, mostra tutto subito
    document.querySelectorAll('.reveal, .reveal-stagger').forEach(el => el.classList.add('is-visible'));
  }

  // 4. Lightbox Modale Touch-Friendly
  initLightbox();

  // 5. Calendario Dinamico: Filtro con separatore fisico ed edizioni storiche
  initEventCalendar();

  // 6. Rilevamento Intelligente della Lingua (Default Inglese, Italiano se rilevato)
  initLanguagePreference();

  // 7. Mappa Interattiva OpenStreetMap / Leaflet (Zero Cookie)
  if (typeof L !== 'undefined') {
    initLeafletMap();
  } else {
    window.addEventListener('load', () => {
      if (typeof L !== 'undefined') initLeafletMap();
    });
  }
});

function initLeafletMap() {
  const mapEl = document.getElementById('osm-map');
  if (!mapEl || typeof L === 'undefined') return;

  // Coordinate esatte di Palazzo Usellini: Via Pertossi 12, Arona (NO) (OSM Way #455891521)
  const lat = 45.762615;
  const lng = 8.559467;

  const map = L.map('osm-map', {
    scrollWheelZoom: false,
    attributionControl: true
  }).setView([lat, lng], 17);

  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'
  }).addTo(map);

  const customIcon = L.icon({
    iconUrl: '/vendor/leaflet/marker-icon.png',
    shadowUrl: '/vendor/leaflet/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });

  const marker = L.marker([lat, lng], { icon: customIcon }).addTo(map);
  marker.bindPopup(`
    <div style="font-family: serif; font-size: 0.95rem; text-align: center; padding: 4px;">
      <strong style="color: #7E1E24; font-size: 1.05rem;">Palazzo Usellini</strong><br>
      Via Pertossi 12, Arona (NO)
    </div>
  `).openPopup();
}

function initEventCalendar() {
  const container = document.querySelector('.events-calendar-container');
  if (!container) return;

  const eventCards = Array.from(container.querySelectorAll('.calendar-event-card'));
  if (eventCards.length === 0) return;

  const statusBar = container.querySelector('.calendar-status-bar');
  const filterBtns = Array.from(container.querySelectorAll('.year-filter-btn'));
  const upcomingGroup = container.querySelector('.calendar-upcoming-group');
  const pastGroup = container.querySelector('.calendar-past-group');
  const divider = container.querySelector('.calendar-events-divider');
  const dividerLabel = divider ? divider.querySelector('.divider-label') : null;
  const isEnglish = document.documentElement.lang && document.documentElement.lang.startsWith('en');

  // Data odierna in formato YYYY-MM-DD
  const now = new Date();
  const currentYear = String(now.getFullYear());
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const todayStr = `${currentYear}-${month}-${day}`;

  // Distribuzione iniziale delle card nei due gruppi (Futuri in alto, Passati in basso)
  eventCards.forEach(card => {
    const eventDate = card.getAttribute('data-event-date');
    if (eventDate && eventDate < todayStr) {
      card.classList.add('is-past');
      if (pastGroup && card.parentElement !== pastGroup) {
        pastGroup.appendChild(card);
      }
    } else {
      card.classList.add('is-upcoming');
      if (upcomingGroup && card.parentElement !== upcomingGroup) {
        upcomingGroup.appendChild(card);
      }
    }
  });

  function renderView(selectedFilter) {
    let visibleCount = 0;
    let upcomingVisible = 0;
    let pastVisible = 0;

    eventCards.forEach(card => {
      const cardYear = card.getAttribute('data-event-year');
      const isPast = card.classList.contains('is-past');

      let matches = false;
      if (selectedFilter === 'current') {
        matches = (cardYear === '2026' || !isPast);
      } else if (selectedFilter === 'all') {
        matches = true;
      } else {
        matches = (cardYear === selectedFilter);
      }

      if (matches) {
        card.classList.remove('is-hidden-by-filter');
        visibleCount++;
        if (isPast) pastVisible++;
        else upcomingVisible++;
      } else {
        card.classList.add('is-hidden-by-filter');
      }
    });

    // Gestione del Separatore Fisico
    if (divider) {
      if (upcomingVisible > 0 && pastVisible > 0) {
        divider.style.display = 'flex';
        if (dividerLabel) {
          dividerLabel.textContent = isEnglish ? '✦ Past Events of the Season ✦' : '✦ Appuntamenti Conclusi della Stagione ✦';
        }
      } else if (selectedFilter !== 'current' && pastVisible > 0) {
        divider.style.display = 'flex';
        if (dividerLabel) {
          dividerLabel.textContent = selectedFilter === 'all' 
            ? (isEnglish ? '✦ Historical Archive (2020 – 2026) ✦' : '✦ Archivio Storico (2020 – 2026) ✦')
            : (isEnglish ? `✦ Edition ${selectedFilter} Archive ✦` : `✦ Archivio Edizione ${selectedFilter} ✦`);
        }
      } else {
        divider.style.display = 'none';
      }
    }

    if (!statusBar) return;
    statusBar.innerHTML = '';

    if (selectedFilter === 'current') {
      if (upcomingVisible > 0) {
        container.classList.remove('season-concluded');
        statusBar.innerHTML = `
          <div class="status-upcoming-wrap">
            <span class="pulse-indicator"></span>
            <span class="status-upcoming-text"><strong>${upcomingVisible}</strong> ${isEnglish ? 'upcoming live concerts scheduled' : 'prossimi appuntamenti in programma'}</span>
          </div>
        `;
      } else {
        container.classList.add('season-concluded');
        statusBar.innerHTML = `
          <div class="season-ended-banner">
            <span class="season-icon">🍂</span>
            <div class="season-text">
              <strong>${isEnglish ? 'The 2026 summer concert season has concluded.' : 'La rassegna concertistica estiva 2026 si è conclusa.'}</strong>
              <p>${isEnglish ? 'Thank you to all performers and attendees! Below is the 2026 season programme. Explore historical editions via the buttons above.' : 'Grazie a tutti i partecipanti! Di seguito il programma svolto dell\'edizione 2026. Seleziona gli anni sopra per esplorare l\'archivio delle passate edizioni.'}</p>
            </div>
          </div>
        `;
      }
    } else if (selectedFilter === 'all') {
      container.classList.remove('season-concluded');
      statusBar.innerHTML = `
        <div class="status-upcoming-wrap">
          <span class="status-upcoming-text">📜 <strong>${isEnglish ? 'Complete Historical Archive' : 'Archivio Storico Completo'}</strong>: ${visibleCount} ${isEnglish ? 'live concerts and performances at Casa Usellini (2020 – 2026)' : 'eventi e concerti dal vivo documentati a Casa Usellini (2020 – 2026)'}</span>
        </div>
      `;
    } else {
      container.classList.remove('season-concluded');
      statusBar.innerHTML = `
        <div class="status-upcoming-wrap">
          <span class="status-upcoming-text">🏛️ <strong>${isEnglish ? 'Edition ' + selectedFilter : 'Edizione ' + selectedFilter}</strong>: ${visibleCount} ${isEnglish ? 'cultural performances in the palace garden' : 'appuntamenti musicali e culturali nel giardino'}</span>
        </div>
      `;
    }
  }

  // Listener pulsanti filtro con transizione fluida cross-fade
  const prefersMotionReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      if (btn.classList.contains('is-active')) return;
      filterBtns.forEach(b => {
        b.classList.remove('is-active');
        b.setAttribute('aria-pressed', 'false');
      });
      btn.classList.add('is-active');
      btn.setAttribute('aria-pressed', 'true');
      const filterYear = btn.getAttribute('data-year');

      const list = container.querySelector('.calendar-events-list');
      if (list && !prefersMotionReduced) {
        list.classList.add('is-switching');
        setTimeout(() => {
          renderView(filterYear);
          list.classList.remove('is-switching');

          const visibleCards = container.querySelectorAll('.calendar-event-card:not(.is-hidden-by-filter)');
          visibleCards.forEach((c, idx) => {
            c.classList.remove('animate-in');
            void c.offsetWidth; // Reflow per riavviare keyframe
            c.style.animationDelay = `${Math.min(idx * 28, 160)}ms`;
            c.classList.add('animate-in');
          });
        }, 110);
      } else {
        renderView(filterYear);
      }
    });
  });

  // Vista predefinita
  renderView('current');
}

function initLanguagePreference() {
  const storageKey = 'palazzo_usellini_lang';
  const path = window.location.pathname;

  // Intercetta click sui link lingua — salva la preferenza PRIMA di navigare
  const langLinks = document.querySelectorAll('.lang-switcher .lang-link');
  langLinks.forEach(link => {
    link.addEventListener('click', () => {
      const label = link.textContent.trim().toUpperCase();
      try {
        if (label === 'EN') {
          localStorage.setItem(storageKey, 'en');
        } else if (label === 'IT') {
          localStorage.setItem(storageKey, 'it');
        }
      } catch (err) {}
      // Lascia il browser navigare normalmente dopo aver salvato la preferenza
    });
  });

  // Rilevamento automatico solo sulla radice "/" — mai sulle sotto-pagine
  // per non interferire con link diretti o navigazione manuale
  if (path !== '/' && path !== '/index.html') return;

  try {
    const savedLang = localStorage.getItem(storageKey);

    // Preferenza esplicita dell'utente: rispettarla sempre
    if (savedLang === 'it') return;
    if (savedLang === 'en') {
      window.location.replace('/en/');
      return;
    }

    // Prima visita: rilevamento browser, default inglese se non italiano
    const navLang = (navigator.languages && navigator.languages[0]) || navigator.language || '';
    if (!navLang.toLowerCase().startsWith('it')) {
      window.location.replace('/en/');
    }
  } catch (e) {}
}

function initLightbox() {
  const galleryLinks = Array.from(document.querySelectorAll('.photo-gallery-item a, .article-gallery-grid a, .page-gallery-section a'));
  if (galleryLinks.length === 0) return;

  const isEn = (document.documentElement.lang || '').toLowerCase().startsWith('en');
  const closeLabel = isEn ? 'Close' : 'Chiudi';
  const prevLabel = isEn ? 'Previous' : 'Precedente';
  const nextLabel = isEn ? 'Next' : 'Successivo';

  // Crea elemento modale nel DOM
  const modal = document.createElement('div');
  modal.className = 'lightbox-modal';
  modal.innerHTML = `
    <div class="lightbox-backdrop"></div>
    <div class="lightbox-content">
      <button class="lightbox-close" aria-label="${closeLabel}">&times;</button>
      <button class="lightbox-nav lightbox-prev" aria-label="${prevLabel}">&#10094;</button>
      <button class="lightbox-nav lightbox-next" aria-label="${nextLabel}">&#10095;</button>
      <div class="lightbox-figure">
        <img class="lightbox-img" src="" alt="">
        <p class="lightbox-caption"></p>
      </div>
    </div>
  `;
  document.body.appendChild(modal);

  const imgEl = modal.querySelector('.lightbox-img');
  const captionEl = modal.querySelector('.lightbox-caption');
  const closeBtn = modal.querySelector('.lightbox-close');
  const prevBtn = modal.querySelector('.lightbox-prev');
  const nextBtn = modal.querySelector('.lightbox-next');
  const backdrop = modal.querySelector('.lightbox-backdrop');

  let currentIndex = 0;

  const showImage = (index) => {
    if (index < 0) index = galleryLinks.length - 1;
    if (index >= galleryLinks.length) index = 0;
    currentIndex = index;

    const link = galleryLinks[currentIndex];
    const src = link.getAttribute('href');
    const childImg = link.querySelector('img');
    const captionParent = link.closest('figure')?.querySelector('figcaption');
    const alt = childImg?.getAttribute('alt') || '';
    const caption = captionParent ? captionParent.textContent : alt;

    imgEl.src = src;
    imgEl.alt = alt;
    captionEl.textContent = caption;
  };

  const openLightbox = (index) => {
    showImage(index);
    modal.classList.add('is-active');
    document.body.style.overflow = 'hidden';
  };

  const closeLightbox = () => {
    modal.classList.remove('is-active');
    document.body.style.overflow = '';
  };

  galleryLinks.forEach((link, idx) => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      openLightbox(idx);
    });
  });

  closeBtn.addEventListener('click', closeLightbox);
  backdrop.addEventListener('click', closeLightbox);
  prevBtn.addEventListener('click', () => showImage(currentIndex - 1));
  nextBtn.addEventListener('click', () => showImage(currentIndex + 1));

  // Supporto Tastiera
  window.addEventListener('keydown', (e) => {
    if (!modal.classList.contains('is-active')) return;
    if (e.key === 'Escape') closeLightbox();
    if (e.key === 'ArrowLeft') showImage(currentIndex - 1);
    if (e.key === 'ArrowRight') showImage(currentIndex + 1);
  });

  // Supporto Swipe Touch su smartphone
  let touchStartX = 0;
  modal.addEventListener('touchstart', (e) => {
    touchStartX = e.changedTouches[0].screenX;
  }, { passive: true });

  modal.addEventListener('touchend', (e) => {
    const touchEndX = e.changedTouches[0].screenX;
    const diff = touchEndX - touchStartX;
    if (Math.abs(diff) > 45) {
      if (diff > 0) {
        showImage(currentIndex - 1); // Swipe verso destra -> foto precedente
      } else {
        showImage(currentIndex + 1); // Swipe verso sinistra -> foto successiva
      }
    }
  }, { passive: true });
}

function initThemeToggle() {
  const toggleBtns = document.querySelectorAll('.theme-toggle-btn');
  if (toggleBtns.length === 0) return;

  const storageKey = 'palazzo_usellini_theme';
  const isEnglish = document.documentElement.lang && document.documentElement.lang.startsWith('en');

  const updateUI = (isDark) => {
    const visibleText = isEnglish ? (isDark ? 'Theme: Dark' : 'Theme: Light') : (isDark ? 'Tema: Scuro' : 'Tema: Chiaro');
    toggleBtns.forEach(btn => {
      const labelEl = btn.querySelector('.theme-toggle-label');
      if (labelEl) {
        labelEl.textContent = visibleText;
      }
      btn.setAttribute('aria-label', visibleText);
      btn.setAttribute('aria-pressed', isDark ? 'true' : 'false');
    });
  };

  const getEffectiveTheme = () => {
    const attr = document.documentElement.getAttribute('data-theme');
    if (attr === 'dark') return 'dark';
    if (attr === 'light') return 'light';
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  };

  updateUI(getEffectiveTheme() === 'dark');

  toggleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const current = getEffectiveTheme();
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try {
        localStorage.setItem(storageKey, next);
      } catch (e) {}
      updateUI(next === 'dark');
    });
  });

  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      try {
        if (!localStorage.getItem(storageKey)) {
          updateUI(e.matches);
        }
      } catch (err) {}
    });
  }
}
