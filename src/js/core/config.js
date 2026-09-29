/**
 * ==============================================================================
 * Centralized Application Configuration (Single Source of Truth)
 * Dynamically resolves Local vs Vercel Serverless vs GitHub Pages CDN routing
 * ==============================================================================
 */

export const APP_CONFIG = {
  get isLocal() {
    if (typeof window === 'undefined') return false;
    return window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  },
  get isVercel() {
    if (typeof window === 'undefined') return false;
    return window.location.hostname.includes('vercel.app');
  },
  get apiBaseUrl() {
    return (this.isLocal || this.isVercel) ? '' : 'https://ai-factcheck-portfolio.vercel.app';
  },
  dbProvider: 'Cloud DB',
  setDbProvider(name) {
    if (name && typeof name === 'string') {
      this.dbProvider = name;
    }
  },
  apiUrl(endpoint) {
    const clean = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
    return this.apiBaseUrl + clean;
  }
};

export const API_BASE = '';

export const ROUTES = {
  home: '#home',
  portfolio: '#/factchecks',
  news: '#/news',
  models: '#/models',
  graph: '#/graph',
  inbox: '#/inbox'
};

if (typeof window !== 'undefined') {
  window.APP_CONFIG = APP_CONFIG;
  window.API_BASE = API_BASE;
  window.ROUTES = ROUTES;
}
