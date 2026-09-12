/*
 * PWA module (Phase 7): service-worker status + offline affordances for
 * module pages. Registration itself stays in js/core.js (which owns the
 * install prompt and update flow); this module only *reports* state and
 * keeps a cache fresh where core.js is not loaded.
 */

const SW_PATH = '../sw.js';

export async function status() {
  if (!('serviceWorker' in navigator)) return 'unsupported';
  const registration = await navigator.serviceWorker.getRegistration();
  if (!registration) return 'unregistered';
  if (registration.installing) return 'installing';
  if (registration.waiting) return 'update-ready';
  return registration.active ? 'activated' : 'registered';
}

/** Ask the waiting worker to take over (core.js also handles this path). */
export async function skipWaiting() {
  const registration = await navigator.serviceWorker.getRegistration();
  if (registration && registration.waiting) registration.waiting.postMessage('skipWaiting');
}

function paintPill() {
  const pill = document.getElementById('pwaStatus');
  if (!pill) return;
  status().then(function (value) {
    pill.textContent =
      value === 'activated' ? 'Offline ready' : value === 'update-ready' ? 'Update available' : 'Online';
    pill.dataset.state = value;
  });
  window.addEventListener('online', function () {
    pill.textContent = 'Back online';
  });
  window.addEventListener('offline', function () {
    pill.textContent = 'Offline — serving cached data';
  });
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', paintPill);
  else paintPill();
}
