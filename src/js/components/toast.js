/**
 * ==============================================================================
 * Toast Notification Component
 * ==============================================================================
 */

export function showToast(msg, type = 'info') {
  if (typeof document === 'undefined') return;
  const toast = document.getElementById('toast');
  const toastMsg = document.getElementById('toastMsg');
  if (!toast || !toastMsg) return;

  toastMsg.innerText = msg;
  toast.classList.remove('hidden');

  if (toast._timer) clearTimeout(toast._timer);
  toast._timer = setTimeout(() => {
    toast.classList.add('hidden');
  }, 3500);
}

if (typeof window !== 'undefined') {
  window.showToast = showToast;
}
