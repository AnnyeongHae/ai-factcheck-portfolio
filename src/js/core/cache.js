/**
 * Lightweight, resilient Session SWR Cache
 * Tier 1: In-Memory Map (0ms, synchronous)
 * Tier 2: sessionStorage (Survives tab navigations & soft refreshes, 60s default TTL)
 * Graceful fallback: If sessionStorage is restricted or full, operates purely in memory.
 */

const memoryCache = new Map();
const DEFAULT_TTL_MS = 60 * 1000; // 60 seconds

export const ClientCache = {
  get(key, maxAgeMs = DEFAULT_TTL_MS) {
    const now = Date.now();
    // 1. Check in-memory map
    if (memoryCache.has(key)) {
      const entry = memoryCache.get(key);
      if (entry && (now - entry.timestamp) < maxAgeMs) {
        return entry.data;
      }
      memoryCache.delete(key);
    }

    // 2. Check sessionStorage
    try {
      if (typeof window !== 'undefined' && window.sessionStorage) {
        const raw = sessionStorage.getItem('fc_swr_' + key);
        if (raw) {
          const entry = JSON.parse(raw);
          if (entry && (now - entry.timestamp) < maxAgeMs) {
            memoryCache.set(key, entry); // populate memory
            return entry.data;
          }
          sessionStorage.removeItem('fc_swr_' + key);
        }
      }
    } catch (e) {
      // Ignore quota / security exceptions
    }

    return null;
  },

  set(key, data) {
    const now = Date.now();
    const entry = { data, timestamp: now };
    memoryCache.set(key, entry);

    try {
      if (typeof window !== 'undefined' && window.sessionStorage) {
        sessionStorage.setItem('fc_swr_' + key, JSON.stringify(entry));
      }
    } catch (e) {
      // Storage might be full or private browsing blocked; ignore safely
    }
  },

  clear(prefix = '') {
    memoryCache.clear();
    try {
      if (typeof window !== 'undefined' && window.sessionStorage) {
        if (!prefix) {
          const keysToRemove = [];
          for (let i = 0; i < sessionStorage.length; i++) {
            const k = sessionStorage.key(i);
            if (k && k.startsWith('fc_swr_')) keysToRemove.push(k);
          }
          keysToRemove.forEach(k => sessionStorage.removeItem(k));
        } else {
          sessionStorage.removeItem('fc_swr_' + prefix);
        }
      }
    } catch (e) {}
  }
};
