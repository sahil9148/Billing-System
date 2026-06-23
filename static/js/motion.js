/**
 * BillFlow Pro — Motion Engine
 * Lightweight (~200 lines) premium animation layer.
 * Self-contained, no dependencies. Uses requestAnimationFrame,
 * IntersectionObserver, and MutationObserver for 60 fps effects.
 */

/* ───────────────────────────────────────────
   1. Particle Canvas (Login Page)
   ─────────────────────────────────────────── */
class ParticleEngine {
  constructor() {
    this.canvas = document.getElementById('particles-canvas');
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.particles = [];
    this.resize();
    this.init();
    this.animate();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    this.canvas.width = this.canvas.offsetWidth;
    this.canvas.height = this.canvas.offsetHeight;
  }

  init() {
    this.particles = [];
    for (let i = 0; i < 80; i++) {
      this.particles.push({
        x: Math.random() * this.canvas.width,
        y: Math.random() * this.canvas.height,
        vx: (Math.random() - 0.5) * 0.6,
        vy: (Math.random() - 0.5) * 0.6,
        size: Math.random() * 2 + 1,
        opacity: Math.random() * 0.5 + 0.2,
      });
    }
  }

  animate() {
    const { ctx, canvas, particles } = this;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Move & draw particles
    for (const p of particles) {
      p.x += p.vx;
      p.y += p.vy;
      // Wrap around edges
      if (p.x < 0) p.x = canvas.width;
      if (p.x > canvas.width) p.x = 0;
      if (p.y < 0) p.y = canvas.height;
      if (p.y > canvas.height) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(79,143,247,${p.opacity})`;
      ctx.fill();
    }

    // Draw connecting lines
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(79,143,247,${0.15 * (1 - dist / 120)})`;
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(() => this.animate());
  }
}

/* ───────────────────────────────────────────
   2. Mouse Parallax Tilt on Cards
   ─────────────────────────────────────────── */
function initParallaxTilt() {
  const container = document.getElementById('page-content');
  if (!container) return;

  const SELECTOR = '.kpi-card, .chart-card, .card';

  container.addEventListener('mousemove', (e) => {
    const card = e.target.closest(SELECTOR);
    if (!card) return;
    const rect = card.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;   // -0.5 … 0.5
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    card.style.willChange = 'transform';
    card.style.transform =
      `perspective(800px) rotateX(${(-y * 6).toFixed(2)}deg) rotateY(${(x * 6).toFixed(2)}deg)`;
  });

  container.addEventListener('mouseleave', (e) => {
    const card = e.target.closest(SELECTOR);
    if (card) {
      card.style.transform = 'perspective(800px) rotateX(0) rotateY(0)';
      card.style.willChange = 'auto';
    }
  }, true);
}

/* ───────────────────────────────────────────
   3. Scroll-Triggered Stagger Animations
   ─────────────────────────────────────────── */
function initScrollReveal() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
          entry.target.style.transitionDelay = `${index * 0.06}s`;
          entry.target.classList.add('revealed');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1, rootMargin: '0px 0px -30px 0px' }
  );

  function observeElements() {
    document
      .querySelectorAll(
        '.kpi-card, .card, .chart-card, .settings-section, .summary-card, tbody tr'
      )
      .forEach((el) => {
        if (!el.classList.contains('revealed') && !el.classList.contains('scroll-reveal')) {
          el.classList.add('scroll-reveal');
          observer.observe(el);
        }
      });
  }

  // Watch for DOM changes (SPA page navigation)
  const pageContent = document.getElementById('page-content');
  if (pageContent) {
    new MutationObserver(() => setTimeout(observeElements, 50)).observe(pageContent, {
      childList: true,
      subtree: true,
    });
  }

  observeElements();
}

/* ───────────────────────────────────────────
   4. Animated KPI Counters
   ─────────────────────────────────────────── */
function animateCounter(element) {
  const text = element.textContent;
  const match = text.match(/^([^\d]*?)([\d,.]+)(.*?)$/);
  if (!match) return;

  const prefix = match[1];
  const targetStr = match[2];
  const suffix = match[3];
  const target = parseFloat(targetStr.replace(/,/g, ''));
  const hasDecimals = targetStr.includes('.');
  const duration = 1500;
  const start = performance.now();

  function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  function update(now) {
    const progress = Math.min((now - start) / duration, 1);
    const current = target * easeOutCubic(progress);
    element.textContent =
      prefix +
      (hasDecimals
        ? current.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
        : Math.round(current).toLocaleString('en-IN')) +
      suffix;
    if (progress < 1) requestAnimationFrame(update);
  }

  element.textContent = prefix + '0' + suffix;
  requestAnimationFrame(update);
}

function initCounterAnimation() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && !entry.target.dataset.counted) {
          entry.target.dataset.counted = 'true';
          animateCounter(entry.target);
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.5 }
  );

  function observeKPIs() {
    document.querySelectorAll('.kpi-value').forEach((el) => {
      if (!el.dataset.counted) observer.observe(el);
    });
  }

  const pageContent = document.getElementById('page-content');
  if (pageContent) {
    new MutationObserver(() => setTimeout(observeKPIs, 80)).observe(pageContent, {
      childList: true,
      subtree: true,
    });
  }

  observeKPIs();
}

/* ───────────────────────────────────────────
   5. Magnetic Hover on Buttons
   ─────────────────────────────────────────── */
function initMagneticButtons() {
  document.addEventListener('mousemove', (e) => {
    document.querySelectorAll('.btn-primary, .chatbot-toggle').forEach((btn) => {
      const rect = btn.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const dx = e.clientX - cx;
      const dy = e.clientY - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist < 80) {
        const pull = (80 - dist) / 80;
        btn.style.transform = `translate(${(dx * pull * 0.15).toFixed(1)}px, ${(dy * pull * 0.15).toFixed(1)}px)`;
      } else if (!btn.classList.contains('chatbot-toggle')) {
        btn.style.transform = '';
      }
    });
  });
}

/* ───────────────────────────────────────────
   6. Smooth Page Transitions
   ─────────────────────────────────────────── */
function initPageTransitions() {
  const pageContent = document.getElementById('page-content');
  if (!pageContent) return;

  new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.type === 'childList' && m.addedNodes.length) {
        m.addedNodes.forEach((node) => {
          if (node.nodeType === 1) {
            node.style.opacity = '0';
            node.style.transform = 'translateY(8px)';
            node.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
            requestAnimationFrame(() => {
              node.style.opacity = '1';
              node.style.transform = 'translateY(0)';
            });
          }
        });
      }
    }
  }).observe(pageContent, { childList: true });
}

/* ───────────────────────────────────────────
   7. Ripple Effect on Buttons
   ─────────────────────────────────────────── */
function initRippleEffect() {
  // Inject keyframes once
  const style = document.createElement('style');
  style.textContent = '@keyframes rippleAnim{to{transform:scale(4);opacity:0}}';
  document.head.appendChild(style);

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.btn');
    if (!btn) return;

    const rect = btn.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const ripple = document.createElement('span');

    ripple.style.cssText = `
      position:absolute;
      width:${size}px;height:${size}px;
      left:${e.clientX - rect.left - size / 2}px;
      top:${e.clientY - rect.top - size / 2}px;
      background:rgba(255,255,255,0.2);
      border-radius:50%;
      transform:scale(0);
      animation:rippleAnim 0.6s ease-out forwards;
      pointer-events:none;`;

    btn.style.position = 'relative';
    btn.style.overflow = 'hidden';
    btn.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
  });
}

/* ───────────────────────────────────────────
   8. Bootstrap Everything on DOMContentLoaded
   ─────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  // Login particle background
  new ParticleEngine();

  // Three.js 3D scene (login page)
  initThreeScene();

  // Remaining effects — slight delay so the DOM is fully painted
  setTimeout(() => {
    initParallaxTilt();
    initScrollReveal();
    initCounterAnimation();
    initMagneticButtons();
    initRippleEffect();
    initPageTransitions();
  }, 100);
});

/* ───────────────────────────────────────────
   9. Three.js 3D Interactive Torus Knot Scene
   ─────────────────────────────────────────── */
function initThreeScene() {
  const canvas = document.getElementById('three-canvas');
  if (!canvas || typeof THREE === 'undefined') return;

  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.set(0, 0, 5);

  // Torus Knot Geometry
  const geometry = new THREE.TorusKnotGeometry(1.4, 0.38, 180, 24, 2, 3);
  const material = new THREE.MeshStandardMaterial({
    color: 0x4f8ff7,
    metalness: 0.7,
    roughness: 0.15,
    transparent: true,
    opacity: 0.25,
    wireframe: false,
  });
  const torusKnot = new THREE.Mesh(geometry, material);
  scene.add(torusKnot);

  // Wireframe overlay for 3D depth
  const wireMaterial = new THREE.MeshBasicMaterial({
    color: 0x7b5fd4,
    wireframe: true,
    transparent: true,
    opacity: 0.12,
  });
  const wireKnot = new THREE.Mesh(geometry, wireMaterial);
  scene.add(wireKnot);

  // Lights
  const ambientLight = new THREE.AmbientLight(0x4f8ff7, 0.6);
  scene.add(ambientLight);

  const pointLight1 = new THREE.PointLight(0x7b5fd4, 2, 15);
  pointLight1.position.set(4, 4, 4);
  scene.add(pointLight1);

  const pointLight2 = new THREE.PointLight(0x00d4ff, 1.5, 15);
  pointLight2.position.set(-4, -4, 2);
  scene.add(pointLight2);

  // Mouse parallax tracking
  let mouseX = 0, mouseY = 0;
  document.addEventListener('mousemove', (e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouseY = -(e.clientY / window.innerHeight - 0.5) * 2;
  });

  // Touch parallax tracking
  document.addEventListener('touchmove', (e) => {
    if (e.touches.length > 0) {
      mouseX = (e.touches[0].clientX / window.innerWidth - 0.5) * 2;
      mouseY = -(e.touches[0].clientY / window.innerHeight - 0.5) * 2;
    }
  }, { passive: true });

  // Handle resize
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  // Stop rendering once login page is hidden
  let isRunning = true;
  const loginPage = document.getElementById('login-page');

  // Render loop
  const clock = new THREE.Clock();
  function animate() {
    if (!isRunning) return;

    // Stop if login page is hidden
    if (loginPage && loginPage.classList.contains('hidden')) {
      isRunning = false;
      renderer.dispose();
      return;
    }

    requestAnimationFrame(animate);
    const t = clock.getElapsedTime();

    // Slow auto-rotation
    torusKnot.rotation.x = t * 0.18 + mouseY * 0.3;
    torusKnot.rotation.y = t * 0.12 + mouseX * 0.3;
    wireKnot.rotation.x = torusKnot.rotation.x;
    wireKnot.rotation.y = torusKnot.rotation.y;

    // Pulsating scale
    const pulse = 1 + Math.sin(t * 0.8) * 0.04;
    torusKnot.scale.setScalar(pulse);
    wireKnot.scale.setScalar(pulse);

    // Light orbit
    pointLight1.position.x = Math.cos(t * 0.5) * 5;
    pointLight1.position.y = Math.sin(t * 0.4) * 5;
    pointLight2.position.x = Math.cos(t * 0.4 + Math.PI) * 5;
    pointLight2.position.y = Math.sin(t * 0.5 + Math.PI) * 5;

    renderer.render(scene, camera);
  }

  animate();
}

