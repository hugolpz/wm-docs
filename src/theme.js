// Light/dark theme: starts light until the user picks one, then remembers the choice.
// The theme is the `data-theme` attribute on <html>, read by tokens.css.
const KEY = 'wm-docs-theme'

export function initialTheme() {
  try {
    const saved = localStorage.getItem(KEY)
    if (saved === 'light' || saved === 'dark') return saved
  } catch {
    /* storage unavailable */
  }
  return 'light'
}

export function currentTheme() {
  return document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'
}

export function applyTheme(name, { persist = true } = {}) {
  document.documentElement.dataset.theme = name
  if (!persist) return
  try {
    localStorage.setItem(KEY, name)
  } catch {
    /* storage unavailable */
  }
}
