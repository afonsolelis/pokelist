// Theme toggle with localStorage
(function() {
  const key = 'pokelist.theme'
  const html = document.documentElement
  const stored = localStorage.getItem(key)
  if (stored === 'light' || stored === 'dark') {
    html.setAttribute('data-theme', stored)
  } else {
    // default: dark; switch to light if prefers
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
      html.setAttribute('data-theme', 'light')
    } else {
      html.setAttribute('data-theme', 'dark')
    }
  }

  const btn = document.getElementById('themeToggle')
  if (btn) {
    btn.addEventListener('click', () => {
      const current = html.getAttribute('data-theme') === 'light' ? 'dark' : 'light'
      html.setAttribute('data-theme', current)
      localStorage.setItem(key, current)
      btn.innerHTML = current === 'light' ? '<i class="bi bi-moon-stars"></i>' : '<i class="bi bi-sun"></i>'
    })
    // set icon appropriately on load
    const current = html.getAttribute('data-theme')
    btn.innerHTML = current === 'light' ? '<i class="bi bi-moon-stars"></i>' : '<i class="bi bi-sun"></i>'
  }
})()

// Image zoom modal (Bootstrap)
; (function() {
  const modalEl = document.getElementById('imageModal')
  const imgEl = document.getElementById('imageModalImg')
  const titleEl = document.getElementById('imageModalTitle')
  if (!modalEl || !imgEl) return
  const Modal = window.bootstrap?.Modal
  const modal = Modal ? new Modal(modalEl) : null
  document.addEventListener('click', (e) => {
    const target = e.target
    if (!(target instanceof HTMLElement)) return
    if (target.classList.contains('js-zoom')) {
      const full = target.getAttribute('data-full') || target.getAttribute('src')
      const title = target.getAttribute('data-title') || 'Visualização'
      imgEl.src = full
      imgEl.alt = title
      if (titleEl) titleEl.textContent = title
      if (modal) modal.show()
    }
  })
})()

console.log('Pokélist JS loaded')
