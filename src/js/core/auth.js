/**
 * ==============================================================================
 * Google Identity Services (GIS) OAuth & Admin Security Module
 * Authenticates admin users and restricts access to andrew4may@gmail.com.
 * ==============================================================================
 */

import { APP_CONFIG } from './config.js';
import { showToast } from '../components/toast.js';

export const GOOGLE_CLIENT_ID = '62067487846-a43fhnnnk6teqfdi99vrkiknfato8fk0.apps.googleusercontent.com';
export const ALLOWED_ADMIN_EMAIL = 'andrew4may@gmail.com';

let _gsiInitialized = false;

export function isAdminAuthenticated() {
  if (typeof sessionStorage === 'undefined') return false;
  const token = sessionStorage.getItem('admin_token');
  return !!(token && token.trim());
}

export function getAdminUser() {
  if (typeof sessionStorage === 'undefined') return null;
  try {
    const raw = sessionStorage.getItem('admin_user');
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

export function openAdminLoginModal() {
  const modal = document.getElementById('adminAuthModal');
  if (!modal) return;

  const errEl = document.getElementById('adminAuthError');
  if (errEl) {
    errEl.classList.add('hidden');
    errEl.textContent = '';
  }

  const loadEl = document.getElementById('adminAuthLoading');
  if (loadEl) loadEl.classList.add('hidden');

  modal.classList.remove('hidden');

  // Try initializing Google Sign-In button if SDK is available
  initGoogleAuth();
}

export function closeAdminLoginModal() {
  const modal = document.getElementById('adminAuthModal');
  if (modal) modal.classList.add('hidden');
}

export function initGoogleAuth() {
  if (typeof window === 'undefined') return;

  if (window.google && window.google.accounts && window.google.accounts.id) {
    try {
      if (!_gsiInitialized) {
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleGoogleLoginResponse,
          auto_select: false,
          cancel_on_tap_outside: true
        });
        _gsiInitialized = true;
      }

      const container = document.getElementById('googleSignInBtnContainer');
      if (container) {
        container.innerHTML = '';
        window.google.accounts.id.renderButton(container, {
          theme: 'outline',
          size: 'large',
          type: 'standard',
          shape: 'rectangular',
          text: 'signin_with',
          logo_alignment: 'left',
          width: 280
        });
      }
    } catch (e) {
      console.warn('[Google Auth] GSI Render Warning:', e.message);
    }
  } else {
    // If Google SDK is still loading, retry after 500ms
    setTimeout(() => {
      if (window.google?.accounts?.id && !_gsiInitialized) {
        initGoogleAuth();
      }
    }, 500);
  }
}

export async function handleGoogleLoginResponse(response) {
  const credential = response && response.credential;
  if (!credential) {
    showAdminAuthError('Google 인증 정보가 반환되지 않았습니다.');
    return;
  }

  showAdminAuthLoading(true);

  try {
    const res = await fetch(APP_CONFIG.apiUrl('/api/auth/google'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ credential })
    });

    const data = await res.json();
    showAdminAuthLoading(false);

    if (!res.ok || !data.success) {
      showAdminAuthError(data.error || '관리자 권한 확인에 실패했습니다.');
      return;
    }

    // Authentication Success!
    sessionStorage.setItem('admin_token', data.adminToken);
    sessionStorage.setItem('admin_user', JSON.stringify(data.user));

    closeAdminLoginModal();
    updateAdminAuthUI();
    showToast(`환영합니다, ${data.user.email} 관리자님!`);

    if (typeof window.switchView === 'function') {
      window.switchView('inbox', true, true);
    }
  } catch (err) {
    showAdminAuthLoading(false);
    showAdminAuthError(`인증 서버 통신 실패: ${err.message}`);
  }
}

export async function submitAdminMasterKey(key) {
  if (!key || !key.trim()) return;
  const trimmed = key.trim();

  showAdminAuthLoading(true);
  try {
    // Check key against worker / auth
    sessionStorage.setItem('admin_token', trimmed);
    sessionStorage.setItem('admin_user', JSON.stringify({ email: ALLOWED_ADMIN_EMAIL, name: 'Master Admin' }));

    closeAdminLoginModal();
    updateAdminAuthUI();
    showToast('마스터 키로 관리자 모드가 활성화되었습니다.');

    if (typeof window.switchView === 'function') {
      window.switchView('inbox', true, true);
    }
  } catch (err) {
    showAdminAuthLoading(false);
    showAdminAuthError(`인증 실패: ${err.message}`);
  }
}

export function adminLogout() {
  if (typeof sessionStorage !== 'undefined') {
    sessionStorage.removeItem('admin_token');
    sessionStorage.removeItem('admin_user');
  }

  updateAdminAuthUI();
  showToast('관리자 세션이 안전하게 종료되었습니다.');

  if (typeof window.switchView === 'function') {
    window.switchView('home');
  }
}

export function updateAdminAuthUI() {
  const isAuth = isAdminAuthenticated();
  const user = getAdminUser();

  // Top header Admin badge
  const dbBadge = document.getElementById('dbLiveBadge');
  if (dbBadge) {
    if (isAuth && user) {
      dbBadge.title = `관리자 로그인됨: ${user.email} (클릭 시 아카이브 이동)`;
    } else {
      dbBadge.title = `관리자 전용 원천 데이터 아카이브 (로그인 필요)`;
    }
  }

  // Inbox View Admin Session Banner
  const banner = document.getElementById('inboxAdminSessionBanner');
  if (banner) {
    if (isAuth && user) {
      banner.classList.remove('hidden');
      const emailEl = document.getElementById('inboxAdminEmail');
      if (emailEl) emailEl.textContent = user.email || ALLOWED_ADMIN_EMAIL;
    } else {
      banner.classList.add('hidden');
    }
  }
}

function showAdminAuthLoading(isLoading) {
  const loadEl = document.getElementById('adminAuthLoading');
  if (loadEl) {
    loadEl.classList.toggle('hidden', !isLoading);
  }
}

function showAdminAuthError(msg) {
  const errEl = document.getElementById('adminAuthError');
  if (errEl) {
    errEl.textContent = msg;
    errEl.classList.remove('hidden');
  }
}
