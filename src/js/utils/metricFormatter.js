/**
 * ==============================================================================
 * Metric Formatter & Normalization Utility
 * Standardized Cross-Platform Viral Normalizer & Platform Impact Hierarchy
 * ==============================================================================
 */

export function getPlatformImpactWeight(name = '') {
  const n = (name || '').toLowerCase();
  if (n.includes('github')) return 100;
  if (n.includes('space') || n.includes('hf space')) return 96;
  if (n.includes('hugging') || n.includes('hf')) return 95;
  if (n.includes('arxiv')) return 90;
  if (n.includes('hacker news') || n.includes('ycombinator')) return 85;
  if (n.includes('pytorch')) return 80;
  if (n.includes('geeknews') || n.includes('hada.io')) return 75;
  if (n.includes('reddit')) return 60;
  return 50;
}

export function cleanPlatformName(raw) {
  if (!raw) return 'News';
  let name = String(raw).trim();
  const m = name.match(/^(?:Press|News|YouTube)\s*\((.*?)\)$/i);
  if (m) name = m[1].trim();
  if (name.toLowerCase().startsWith('reddit')) return 'Reddit';
  if (name.includes('조코딩')) return 'YouTube (조코딩)';

  const map = {
    'the new york times': 'NYT',
    'the wall street journal': 'WSJ',
    'the guardian': 'The Guardian',
    'the verge': 'The Verge',
    'the verge ai': 'The Verge',
    'techcrunch ai': 'TechCrunch',
    'techcrunch': 'TechCrunch',
    'hacker news': 'HN',
    'geeknews': 'GeekNews',
    'reddit r/technology': 'Reddit',
    'reddit': 'Reddit',
    'reuters': 'Reuters',
    'bloomberg': 'Bloomberg',
    'politico': 'Politico',
    'bbc': 'BBC',
    'cnn': 'CNN',
    'cbs news': 'CBS',
    'abc news': 'ABC',
    'breaking news, latest news and videos': 'ABC News',
    'usa today': 'USA Today',
    'al jazeera': 'Al Jazeera',
    'axios': 'Axios',
    'cnet': 'CNET',
    'wired': 'WIRED',
    'ft.com': 'FT',
    'npr.org': 'NPR',
    'npr': 'NPR',
    'time.com': 'TIME',
    'time': 'TIME',
    'vietnam.vn': 'Vietnam.vn',
    'nextgov.com': 'NextGov',
    'newser': 'Newser'
  };
  const key = name.toLowerCase();
  return map[key] || name;
}

export function getPrimaryImpactPlatform(it, allSources = []) {
  let bestName = (it && it.source_platform) || 'Tech News';
  let maxW = getPlatformImpactWeight(bestName);

  if (Array.isArray(allSources)) {
    for (const s of allSources) {
      const p = s.platform || s.source_name || '';
      const w = getPlatformImpactWeight(p);
      if (w > maxW) {
        maxW = w;
        bestName = p;
      }
    }
  }
  return cleanPlatformName(bestName);
}

export function formatCleanMetricVal(valStr, currentLang = 'KO') {
  if (!valStr) return '';
  let clean = String(valStr).replace(/🔥/g, '').trim();
  clean = clean.replace(/\b(?:hn\s*)?points\b/gi, 'pts').replace(/\blikes\b/gi, 'likes').replace(/\bstars\b/gi, '★');
  // Compact long Reddit & discussion strings
  clean = clean.replace(/Reddit\s*Major\s*Discussion/gi, currentLang === 'KO' ? '💬 커뮤니티 토론' : (currentLang === 'ZH' ? '💬 社区讨论' : '💬 Discussion'));
  clean = clean.replace(/Major\s*Discussion/gi, currentLang === 'KO' ? '💬 토론' : (currentLang === 'ZH' ? '💬 讨论' : '💬 Discussion'));
  // Compact long news media report strings
  clean = clean.replace(/\(Trending\s*Demo\)/gi, '').trim();
  if (clean.length > 18 && clean.includes('보도')) {
    clean = clean.replace(/^(?:📰\s*)?(.*?)\s*보도$/, (match, p1) => {
      const shortName = p1.length > 8 ? p1.slice(0, 7) + '…' : p1;
      return `📰 ${shortName} 보도`;
    });
  }
  return clean;
}

export function calculateStandardizedViralScore(item) {
  if (!item) return 25;
  const src = item.source_platform || '';
  const metric = item.viral_metric || item.description || '';
  let rawNum = 0;

  const nums = (metric.replace(/,/g, '').match(/\d+/) || []);
  if (nums.length > 0) rawNum = parseInt(nums[0], 10);

  let normScore = 25; // Base fallback score

  if (src.includes('GitHub')) {
    normScore = rawNum > 0 ? (Math.log10(rawNum + 1) / Math.log10(5000)) * 100 : 25;
  } else if (src.includes('Hacker News')) {
    normScore = rawNum > 0 ? (Math.log10(rawNum + 1) / Math.log10(800)) * 100 : 30;
  } else if (src.includes('Hugging Face')) {
    normScore = rawNum > 0 ? (Math.log10(rawNum + 1) / Math.log10(300)) * 100 : 30;
  } else if (src.includes('GeekNews')) {
    normScore = rawNum > 0 ? (Math.log10(rawNum + 1) / Math.log10(100)) * 100 : 35;
  } else if (src.includes('ArXiv')) {
    normScore = 55; // Peer-reviewed academic baseline
  }

  normScore = Math.max(5, Math.min(100, Math.round(normScore)));

  // Blend AI enrichment rating if available (70% viral, 30% AI rating)
  const aiScore = item.ai_enrichment ? item.ai_enrichment.score : null;
  if (aiScore && aiScore > 0) {
    normScore = Math.round((normScore * 0.7) + ((aiScore * 20) * 0.3));
  }

  return normScore;
}

export function formatRadarPointBadge(it, currentLang = 'KO') {
  if (!it) return '';
  const vmRaw = (it.viral_metric || '').trim();
  const pf = (it.platform_family || it.platform || '').toLowerCase();

  // 1. Numeric Points (HN, Trending points, upvotes)
  // e.g. "🔥 1114 HN Points", "Trending 60 pts (❤️ 7037)", "236 pts"
  const ptMatch = vmRaw.match(/(\d[\d,]*)\s*(?:HN\s*)?(?:pts|Points|포인트)/i) || vmRaw.match(/(?:Trending|🔥)\s*(\d[\d,]*)\s*pts/i);
  if (ptMatch) {
    const num = parseInt(ptMatch[1].replace(/,/g, ''), 10);
    const displayNum = isNaN(num) ? ptMatch[1] : num.toLocaleString();
    return `<span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200 flex items-center gap-1 shadow-2xs" title="${vmRaw}"><i data-lucide="flame" class="w-3 h-3 text-rose-500"></i><span>${displayNum} pts</span></span>`;
  }

  // 2. GitHub Stars
  const starMatch = vmRaw.match(/(?:★|stars?)\s*(\d[\d,]*)/i);
  if (starMatch || pf.includes('github')) {
    const numMatch = vmRaw.match(/(\d[\d,]*)/);
    const displayStar = numMatch ? (parseInt(numMatch[1].replace(/,/g, ''), 10).toLocaleString()) : 'Trending';
    return `<span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1 shadow-2xs" title="${vmRaw}"><i data-lucide="star" class="w-3 h-3 text-amber-500 fill-amber-400"></i><span>${displayStar}</span></span>`;
  }

  // 3. Hugging Face / Demo Likes
  const likeMatch = vmRaw.match(/(?:❤️|likes?)\s*(\d[\d,]*)/i);
  if (likeMatch || pf.includes('hugging') || pf.includes('space')) {
    const numMatch = vmRaw.match(/(\d[\d,]*)/);
    const displayLike = numMatch ? (parseInt(numMatch[1].replace(/,/g, ''), 10).toLocaleString()) : 'Demo';
    return `<span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200 flex items-center gap-1 shadow-2xs" title="${vmRaw}"><i data-lucide="heart" class="w-3 h-3 text-rose-500 fill-rose-400"></i><span>${displayLike}</span></span>`;
  }

  // 4. Video / YouTube
  if (vmRaw.includes('영상') || vmRaw.includes('YouTube') || pf.includes('youtube')) {
    const label = currentLang === 'KO' ? '영상 브리핑' : (currentLang === 'ZH' ? '视频播报' : 'Video Brief');
    return `<span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-semibold bg-red-50 text-red-700 border border-red-200/80 flex items-center gap-1 shadow-2xs"><i data-lucide="play" class="w-2.5 h-2.5 text-red-600 fill-red-600"></i><span>${label}</span></span>`;
  }

  // 5. Community / Discussions (Reddit, GeekNews, PyTorchKR)
  if (vmRaw.includes('커뮤니티') || vmRaw.includes('큐레이션') || vmRaw.includes('토론') || vmRaw.includes('Discussion') || pf.includes('reddit') || pf.includes('geek') || pf.includes('pytorch')) {
    const label = currentLang === 'KO' ? '커뮤니티' : (currentLang === 'ZH' ? '社区热点' : 'Community');
    return `<span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/80 flex items-center gap-1 shadow-2xs"><i data-lucide="message-square" class="w-3 h-3 text-indigo-600"></i><span>${label}</span></span>`;
  }

  // 6. Press / News Reports
  if (vmRaw.includes('보도') || vmRaw.includes('Press') || vmRaw.includes('News') || pf.includes('press') || pf.includes('media')) {
    const label = currentLang === 'KO' ? '외신 보도' : (currentLang === 'ZH' ? '主流外媒' : 'Global Press');
    return `<span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-semibold bg-sky-50 text-sky-700 border border-sky-200/80 flex items-center gap-1 shadow-2xs"><i data-lucide="globe" class="w-3 h-3 text-sky-600"></i><span>${label}</span></span>`;
  }

  // 7. Academic / ArXiv Paper
  if (vmRaw.includes('Paper') || pf.includes('arxiv')) {
    const label = currentLang === 'KO' ? '학술 논문' : (currentLang === 'ZH' ? '学术论文' : 'Paper');
    return `<span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-semibold bg-violet-50 text-violet-700 border border-violet-200 flex items-center gap-1 shadow-2xs"><i data-lucide="book-open" class="w-3 h-3 text-violet-600"></i><span>${label}</span></span>`;
  }

  // 8. Fallback: Clean any broken Windows emoji glyphs
  let cleanFallback = vmRaw.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F1E6}-\u{1F1FF}]/gu, '').trim();
  if (!cleanFallback) cleanFallback = 'Trend';
  return `<span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center gap-1 shadow-2xs"><i data-lucide="zap" class="w-3 h-3 text-emerald-600"></i><span>${cleanFallback}</span></span>`;
}

if (typeof window !== 'undefined') {
  window.getPlatformImpactWeight = getPlatformImpactWeight;
  window.cleanPlatformName = cleanPlatformName;
  window.getPrimaryImpactPlatform = getPrimaryImpactPlatform;
  window.formatCleanMetricVal = formatCleanMetricVal;
  window.calculateStandardizedViralScore = calculateStandardizedViralScore;
  window.formatRadarPointBadge = formatRadarPointBadge;
}
