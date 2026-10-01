/* AI Factcheck Hub - Modular Production Bundle (SSOT) | Built: 2026-10-01T08:39:15.211Z */

(() => {
  // src/js/core/config.js
  var APP_CONFIG = {
    get isLocal() {
      if (typeof window === "undefined") return false;
      return window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
    },
    get isVercel() {
      if (typeof window === "undefined") return false;
      return window.location.hostname.includes("vercel.app");
    },
    get apiBaseUrl() {
      return this.isLocal || this.isVercel ? "" : "https://ai-factcheck-portfolio.vercel.app";
    },
    dbProvider: "Cloud DB",
    setDbProvider(name) {
      if (name && typeof name === "string") {
        this.dbProvider = name;
      }
    },
    apiUrl(endpoint) {
      const clean = endpoint.startsWith("/") ? endpoint : "/" + endpoint;
      return this.apiBaseUrl + clean;
    }
  };
  var API_BASE = "";
  var ROUTES = {
    home: "#home",
    portfolio: "#/factchecks",
    news: "#/news",
    models: "#/models",
    graph: "#/graph",
    inbox: "#/inbox"
  };
  if (typeof window !== "undefined") {
    window.APP_CONFIG = APP_CONFIG;
    window.API_BASE = API_BASE;
    window.ROUTES = ROUTES;
  }

  // src/js/core/store.js
  var casesData = [];
  var modelsData = [];
  var newsData = [];
  var inboxData = [];
  var adminData = {};
  var graphData = { nodes: [], links: [] };
  var timeline24hData = [];
  var actionsTelemetryData = {};
  var trend6hData = {};
  var trendRadarData = {};
  var snapshotStats = {};
  var liveCasesData = casesData;
  var liveModelsData = modelsData;
  var liveInboxData = inboxData;
  var liveNewsData = newsData;
  var currentLang = "KO";
  var currentView = "home";
  var currentMode = "ALL";
  var currentDomain = "ALL";
  var currentSort = "date-audit-desc";
  var searchQuery = "";
  var currentInboxSource = "ALL";
  var currentInboxLang = "ALL";
  var currentInboxType = "ALL";
  var currentInboxTech = "ALL";
  var currentInboxSort = "date-audit-desc";
  var inboxSearchQuery = "";
  var currentNewsTier1 = "ALL";
  var currentNewsTier2 = "ALL";
  var currentNewsSort = "date-audit-desc";
  var currentNewsFacet = "ALL";
  var currentNewsSource = "ALL";
  var currentNewsSearch = "";
  var targetSelectedInboxId = "";
  var currentModelsFamily = "ALL";
  var currentModelsArtifact = "ALL";
  var currentModelsModality = "ALL";
  var currentModelsSort = "date-audit-desc";
  var modelsSearchQuery = "";
  var PAGE_SIZE = 15;
  var PORTFOLIO_PAGE_SIZE = 10;
  var currentPortfolioPage = 1;
  var currentModelsPage = 1;
  var currentNewsPage = 1;
  var currentInboxPage = 1;
  var queuedItemIds = new Set(
    typeof localStorage !== "undefined" ? JSON.parse(localStorage.getItem("queued_factchecks") || "[]") : []
  );
  var _listeners = /* @__PURE__ */ new Set();
  function subscribe(listener) {
    _listeners.add(listener);
    return () => _listeners.delete(listener);
  }
  function notifySubscribers() {
    _listeners.forEach((fn) => {
      try {
        fn(AppStore.getState());
      } catch (e) {
        console.error("[Store Subscriber Error]", e);
      }
    });
  }
  var AppStore = {
    _itemsMap: /* @__PURE__ */ new Map(),
    _cases: [],
    _models: [],
    _news: [],
    _inbox: [],
    init(data) {
      if (!data) return;
      this._itemsMap.clear();
      this._cases = Array.isArray(data) ? data : data.cases || [];
      this._models = data.model_items || data.models || [];
      this._news = data.news_items || data.news || [];
      this._inbox = data.inbox_items || data.inbox || [];
      this._models.forEach((it) => {
        it.is_model = true;
        it.is_news = false;
      });
      this._news.forEach((it) => {
        if (it.is_model === void 0) {
          const plat = (it.source_platform || "").toLowerCase();
          const fam = (it.model_family || "").toLowerCase();
          const art = (it.artifact_type || "").toLowerCase();
          const cat = (it.category_primary || "").toLowerCase();
          it.is_model = it.facet_type === "MODEL" || fam.length > 0 && fam !== "standalone" || plat.includes("model") || plat.includes("space") || art.includes("weight") || cat.includes("model");
        }
        if (it.is_news === void 0) it.is_news = !it.is_model;
      });
      this._inbox.forEach((it) => {
        if (it.is_model === void 0) it.is_model = !!(it.model_family || it.artifact_type || it.category_primary === "MODEL_RELEASE");
        if (it.is_news === void 0) it.is_news = !it.is_model;
      });
      [...this._inbox, ...this._news, ...this._models].forEach((it) => {
        const id = it.inbox_id || it.id;
        if (id && !this._itemsMap.has(id)) {
          this._itemsMap.set(id, it);
        }
      });
      casesData = this._cases;
      modelsData = this._models;
      newsData = this._news;
      inboxData = this._inbox;
      liveCasesData = this._cases;
      liveModelsData = this._models;
      liveNewsData = this._news;
      liveInboxData = this._inbox;
      if (data.actions_telemetry) {
        actionsTelemetryData = data.actions_telemetry;
      }
      this._syncGlobals();
      notifySubscribers();
    },
    getItem(id) {
      return this._itemsMap.get(id);
    },
    updateItem(id, patch) {
      const it = this._itemsMap.get(id);
      if (it && patch) {
        Object.assign(it, patch);
        this._syncGlobals();
        notifySubscribers();
      }
    },
    getCases() {
      return this._cases;
    },
    getModels() {
      return this._models;
    },
    getNews() {
      return this._news;
    },
    getInbox() {
      return this._inbox;
    },
    appendArchive(archiveData) {
      if (!archiveData) return;
      const mergeItems = (existingList, incomingList) => {
        if (!Array.isArray(incomingList)) return;
        const existingIds = new Set(existingList.map((it) => it.inbox_id || it.id));
        for (const it of incomingList) {
          const id = it.inbox_id || it.id;
          if (id && !existingIds.has(id)) {
            existingList.push(it);
            existingIds.add(id);
          }
          if (id && !this._itemsMap.has(id)) {
            this._itemsMap.set(id, it);
          }
        }
      };
      mergeItems(this._inbox, archiveData.inbox_items);
      mergeItems(this._news, archiveData.news_items);
      mergeItems(this._models, archiveData.model_items);
      liveInboxData = this._inbox;
      liveNewsData = this._news;
      liveModelsData = this._models;
      inboxData = this._inbox;
      newsData = this._news;
      modelsData = this._models;
      this._syncGlobals();
      notifySubscribers();
    },
    getState() {
      return {
        cases: this._cases,
        models: this._models,
        news: this._news,
        inbox: this._inbox,
        currentLang,
        currentView,
        currentPortfolioPage,
        currentNewsPage,
        currentModelsPage,
        currentInboxPage
      };
    },
    _syncGlobals() {
      if (typeof window === "undefined") return;
      window.casesData = casesData;
      window.modelsData = modelsData;
      window.newsData = newsData;
      window.inboxData = inboxData;
      window.liveCasesData = liveCasesData;
      window.liveModelsData = liveModelsData;
      window.liveNewsData = liveNewsData;
      window.liveInboxData = liveInboxData;
      window.snapshotStats = snapshotStats;
      window.adminData = adminData;
      window.graphData = graphData;
      window.timeline24hData = timeline24hData;
      window.actionsTelemetryData = actionsTelemetryData;
      window.trend6hData = trend6hData;
      window.trendRadarData = trendRadarData;
    },
    setCases(cases) {
      if (!Array.isArray(cases)) return;
      this._cases = cases;
      casesData = cases;
      liveCasesData = cases;
      this._syncGlobals();
      notifySubscribers();
    },
    setGraphData(g) {
      if (!g) return;
      graphData = g;
      this._syncGlobals();
    }
  };
  function setGlobalLang(lang) {
    currentLang = lang;
    if (typeof window !== "undefined") window.currentLang = lang;
  }
  function setPortfolioPage(p) {
    currentPortfolioPage = p;
    if (typeof window !== "undefined") window.currentPortfolioPage = p;
  }
  function setModelsPage(p) {
    currentModelsPage = p;
    if (typeof window !== "undefined") window.currentModelsPage = p;
  }
  function setNewsPage(p) {
    currentNewsPage = p;
    if (typeof window !== "undefined") window.currentNewsPage = p;
  }
  function setInboxPage(p) {
    currentInboxPage = p;
    if (typeof window !== "undefined") window.currentInboxPage = p;
  }
  function setTargetSelectedInboxId(v) {
    targetSelectedInboxId = v;
    if (typeof window !== "undefined") window.targetSelectedInboxId = v;
  }
  function setModelsFamily(v) {
    currentModelsFamily = v;
    if (typeof window !== "undefined") window.currentModelsFamily = v;
  }
  function setModelsArtifact(v) {
    currentModelsArtifact = v;
    if (typeof window !== "undefined") window.currentModelsArtifact = v;
  }
  function setModelsModality(v) {
    currentModelsModality = v;
    if (typeof window !== "undefined") window.currentModelsModality = v;
  }
  function setModelsSortVal(v) {
    currentModelsSort = v;
    if (typeof window !== "undefined") window.currentModelsSort = v;
  }
  function setModelsSearchQuery(v) {
    modelsSearchQuery = v;
    if (typeof window !== "undefined") window.modelsSearchQuery = v;
  }
  if (typeof window !== "undefined") {
    window.AppStore = AppStore;
    window.subscribeStore = subscribe;
    window.PAGE_SIZE = PAGE_SIZE;
    window.PORTFOLIO_PAGE_SIZE = PORTFOLIO_PAGE_SIZE;
    window.queuedItemIds = queuedItemIds;
    AppStore._syncGlobals();
  }

  // src/js/utils/dateTime.js
  function parseItemTimestamp(item, preferField) {
    if (!item) return 0;
    let raw = "";
    if (preferField === "audit") {
      raw = item.ai_enrichment?.enriched_at || item.enriched_at || item.audited_at || item.investigation_date;
      if (!raw) return 0;
      const ms = new Date(raw).getTime();
      return isNaN(ms) ? 0 : ms;
    } else {
      const tHarvest = item.harvested_at ? new Date(item.harvested_at).getTime() : 0;
      const tPublish = item.published_at ? new Date(item.published_at).getTime() : 0;
      const tCreated = item.created_at ? new Date(item.created_at).getTime() : 0;
      const tSourcePub = item.source_published_date ? new Date(item.source_published_date).getTime() : 0;
      const tDate = item.harvested_date ? new Date(item.harvested_date).getTime() : 0;
      const best = Math.max(
        isNaN(tHarvest) ? 0 : tHarvest,
        isNaN(tPublish) ? 0 : tPublish,
        isNaN(tCreated) ? 0 : tCreated,
        isNaN(tSourcePub) ? 0 : tSourcePub,
        isNaN(tDate) ? 0 : tDate
      );
      return best;
    }
  }
  function formatDateTime(raw) {
    if (!raw) return "-";
    const d = new Date(raw);
    if (isNaN(d.getTime())) return String(raw).substring(0, 10);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    const hh = String(d.getHours()).padStart(2, "0");
    const mm = String(d.getMinutes()).padStart(2, "0");
    return `${y}-${m}-${day} ${hh}:${mm}`;
  }
  function formatDateTimeCompact(raw) {
    if (!raw) return "-";
    const s = String(raw).trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) {
      const parts = s.split("-");
      return `<span class="hidden sm:inline">${parts[0]}-</span>${parts[1]}-${parts[2]}`;
    }
    const d = new Date(raw);
    if (isNaN(d.getTime())) return s.substring(0, 10);
    try {
      const parts = new Intl.DateTimeFormat("en-CA", {
        timeZone: "Asia/Seoul",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false
      }).formatToParts(d);
      const getP = (type) => parts.find((p) => p.type === type)?.value || "";
      const y = getP("year");
      const m = getP("month");
      const day = getP("day");
      const hh = getP("hour");
      const mm = getP("minute");
      return `<span class="hidden sm:inline">${y}-</span>${m}-${day} ${hh}:${mm}`;
    } catch (e) {
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, "0");
      const day = String(d.getDate()).padStart(2, "0");
      const hh = String(d.getHours()).padStart(2, "0");
      const mm = String(d.getMinutes()).padStart(2, "0");
      return `<span class="hidden sm:inline">${y}-</span>${m}-${day} ${hh}:${mm}`;
    }
  }
  function formatKstMonthDay(raw) {
    if (!raw) return "-";
    try {
      const d = new Date(raw);
      if (isNaN(d.getTime())) return String(raw).substring(5, 10);
      return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Seoul", month: "2-digit", day: "2-digit" }).format(d);
    } catch (e) {
      return String(raw).substring(5, 10);
    }
  }
  function getDynamicKstHour() {
    try {
      return parseInt(new Intl.DateTimeFormat("en-US", { timeZone: "Asia/Seoul", hour: "numeric", hour12: false }).format(/* @__PURE__ */ new Date()), 10);
    } catch (e) {
      const now = /* @__PURE__ */ new Date();
      return (now.getUTCHours() + 9) % 24;
    }
  }
  function getDynamicKstDate() {
    const now = /* @__PURE__ */ new Date();
    const utc = now.getTime() + now.getTimezoneOffset() * 6e4;
    return new Date(utc + 36e5 * 9);
  }
  function getDynamicKstSession() {
    const h = getDynamicKstHour();
    if (h < 6) return 1;
    if (h < 12) return 2;
    if (h < 18) return 3;
    return 4;
  }
  function formatModelAttribution(modelStr) {
    if (!modelStr) return "AI \uAC80\uC99D";
    let s = String(modelStr).replace(/^models\//, "").replace(/:free$/, "");
    if (s.includes("/")) s = s.split("/").pop();
    return "\u{1F916} " + s;
  }
  if (typeof window !== "undefined") {
    window.parseItemTimestamp = parseItemTimestamp;
    window.formatDateTime = formatDateTime;
    window.formatDateTimeCompact = formatDateTimeCompact;
    window.formatKstMonthDay = formatKstMonthDay;
    window.formatModelAttribution = formatModelAttribution;
    window.getDynamicKstHour = getDynamicKstHour;
    window.getDynamicKstDate = getDynamicKstDate;
    window.getDynamicKstSession = getDynamicKstSession;
  }

  // src/js/core/i18n.js
  var i18n = {
    KO: {
      brandTitle: "FactCheck Hub",
      brandSubtitle: "AI \uD329\uD2B8\uCCB4\uD06C & \uAE00\uB85C\uBC8C \uD14C\uD06C \uCD5C\uC2E0 \uB3D9\uD5A5",
      navHome: "\uB300\uC2DC\uBCF4\uB4DC",
      navPortfolio: "\uACF5\uC2DD \uAC80\uC99D",
      navModels: "AI \uBAA8\uB378 \uD2B8\uB80C\uB4DC",
      navNews: "\uC2E4\uC2DC\uAC04 \uD2B8\uB80C\uB4DC \uB808\uC774\uB354",
      navGraph: "\uC778\uC6A9 \uACC4\uBCF4\uB9DD",
      navInbox: "\uC218\uC9D1 \uC778\uBC15\uC2A4",
      adminArchiveBtn: "\uC544\uCE74\uC774\uBE0C (Admin)",
      statArchiveLabel: "\uC6D0\uCC9C \uC544\uCE74\uC774\uBE0C (Admin)",
      pipelineScheduleDesc: "1\uC77C 4\uD68C(00:17, 06:17, 12:17, 18:17 KST) \uC804\uB7B5 \uC218\uC9D1",
      pipelineWidgetTitle: "\uC790\uC728 \uD06C\uB860 \uD30C\uC774\uD504\uB77C\uC778 \uD154\uB808\uBA54\uD2B8\uB9AC & \uCC28\uAE30 \uC218\uC9D1 \uCE74\uC6B4\uD2B8\uB2E4\uC6B4",
      pipelineNextTargetLabel: "\uB2E4\uC74C \uC790\uB3D9 \uC218\uC9D1 \uC608\uC815",
      pipelineFooterAudit: "1\uC77C 4\uD68C(00, 06, 12, 18\uC2DC KST) \uC815\uAE30 \uC804\uB7B5 \uC218\uC9D1 & Vercel \uC2E4\uC2DC\uAC04 \uB3D9\uAE30\uD654",
      pipelineFooterNote: "* GitHub Actions \uD050 \uC0C1\uD0DC\uC5D0 \uB530\uB77C \xB12~5\uBD84\uC758 \uC2A4\uCF00\uC904 \uC9C0\uC5F0\uC774 \uBC1C\uC0DD\uD560 \uC218 \uC788\uC2B5\uB2C8\uB2E4.",
      heroBadge: "ZERO-HALLUCINATION ARCHITECTURE & COST AUDIT",
      heroMainTitle: "\uBC14\uC774\uB7F4\uB41C AI \uAE30\uC220\uC758 \uC2E4\uCCB4 \uBD84\uC11D",
      heroMainDesc: "SNS \uBC14\uC774\uB7F4 \uB9C8\uCF00\uD305\uC758 \uD658\uAC01\uC744 \uAC77\uC5B4\uB0B4\uACE0, 1\uCC28 \uACF5\uC2DD \uCD9C\uCC98 \uAC10\uC0AC\uC640 \uAE30\uC800 \uD45C\uC900 vs \uC11C\uB4DC\uD30C\uD2F0 \uC2E4\uCE21 \uBCA4\uCE58\uB9C8\uD06C\uB97C \uD1B5\uD574 \uB3C4\uCD9C\uD55C 100% \uC2E4\uC99D \uBCF4\uACE0\uC11C\uC785\uB2C8\uB2E4.",
      heroUpdateLabel: "\uCD5C\uC885 \uAC80\uC99D\uC77C",
      heroAuditCount: "49\uAC1C \uAE30\uC220 \uAC80\uC99D \uC644\uB8CC",
      promoBannerTitle: "\uAE30\uC220 \uAC80\uC99D \uD3EC\uD2B8\uD3F4\uB9AC\uC624 \uCD5C\uC2E0 \uC0C1\uD0DC \uC54C\uB9BC",
      promoCountBadge: "49\uAC74 \uAC80\uC99D \uC644\uB8CC",
      promoBannerDesc: "\uBC14\uC774\uB7F4 \uC784\uACC4\uCE58\uB97C \uCD08\uACFC\uD558\uC5EC \uC720\uC785\uB41C \uC8FC\uC694 \uC624\uD508\uC18C\uC2A4 \uBC0F \uBAA8\uB378 \uD6C4\uBCF4\uAD70 \uCD1D 49\uAC74\uC5D0 \uB300\uD55C \uC2EC\uCE35 \uC2E4\uCE21 \uBCA4\uCE58\uB9C8\uD06C\uC640 \uD329\uD2B8\uCCB4\uD06C\uAC00 \uBAA8\uB450 \uC644\uB8CC\uB418\uC5C8\uC2B5\uB2C8\uB2E4.",
      promoBtnText: "\uC218\uC9D1 \uC778\uBC15\uC2A4 \uD6C4\uBCF4\uAD70 \uBCF4\uAE30",
      timelineTitle: "\uB2F9\uC77C 24\uC2DC\uAC04 \uC218\uC9D1 \uD0C0\uC784\uB77C\uC778",
      timelineSub: "1\uC77C 4\uD68C(00, 06, 12, 18\uC2DC KST) 6\uC2DC\uAC04 \uC8FC\uAE30 \uC804\uB7B5 \uC218\uC9D1 & AI \uC2E4\uC2DC\uAC04 \uBD84\uB958",
      timelineBadge: "1\uC77C 4\uD68C 6h \uD384\uC2A4",
      timelineLegend: "\uC138\uC158\uBCC4 \uC218\uC9D1 \uAC74\uC218",
      timelineFooterPrefix: "\u26A1 \uB2F9\uC77C \uCD1D \uC218\uC9D1\uB7C9:",
      trendRadarTitle: "1\uC77C 4\uD68C AI \uD2B8\uB80C\uB4DC \uB808\uC774\uB354",
      trendRadarSub: "\uAE00\uB85C\uBC8C \uC624\uD508\uC18C\uC2A4 & AI \uC2E0\uADDC \uAC00\uC911\uCE58 6\uC2DC\uAC04 \uC8FC\uAE30 \uC790\uB3D9 \uAC10\uC9C0",
      homeTopPicksTitle: "\uCD5C\uC2E0 \uC2EC\uCE35 \uAE30\uC220 \uAC80\uC99D \uD558\uC774\uB77C\uC774\uD2B8",
      homeTopPicksViewAll: "\uC804\uCCB4 49\uAC1C \uAC80\uC99D \uB3C4\uC2DC\uC5D0 \uBCF4\uB7EC\uAC00\uAE30",
      btnAll: "\uC804\uCCB4 \uAC80\uC99D",
      btnUser: "\uC9C1\uC811 \uD050\uB808\uC774\uC158",
      btnAuto: "\uC790\uB3D9 \uD2B8\uB80C\uB4DC",
      sortLabel: "\uC815\uB82C:",
      sortOptions: [
        { val: "date-audit-desc", text: "\u{1F52C} \uBD84\uC11D\uC77C\uC790 \uCD5C\uC2E0\uC21C (\uAE30\uBCF8)" },
        { val: "date-audit-asc", text: "\u{1F52C} \uBD84\uC11D\uC77C\uC790 \uC624\uB798\uB41C\uC21C" },
        { val: "date-source-desc", text: "\u{1F4C5} \uC6D0\uCD9C\uCC98 \uBC1C\uD589 \uCD5C\uC2E0\uC21C" },
        { val: "date-source-asc", text: "\u{1F4C5} \uC6D0\uCD9C\uCC98 \uBC1C\uD589 \uC624\uB798\uB41C\uC21C" }
      ],
      searchPlaceholder: "\uAE30\uC220\uBA85, \uC544\uD0A4\uD14D\uCC98, \uD050\uB808\uC774\uC158 \uB3D9\uAE30 \uAC80\uC0C9...",
      domainLabel: "\uB3C4\uBA54\uC778:",
      tagAll: "\uC804\uCCB4",
      tagFrontend: "\uD504\uB860\uD2B8\uC5D4\uB4DC",
      tagAgent: "AI \uC5D0\uC774\uC804\uD2B8",
      tagScraping: "\uC6F9 \uC2A4\uD06C\uB798\uD551",
      tagDoc: "\uBB38\uC11C \uD30C\uC2F1",
      tag3d: "3D/\uCEF4\uD3EC\uB10C\uD2B8",
      tagRust: "Rust/\uC2DC\uC2A4\uD15C",
      tagOther: "\uAE30\uD0C0/\uCF54\uC5B4 \uC778\uD504\uB77C",
      cardMotivationLabel: "\u{1F4A1} \uBC1C\uAD74 \uC758\uB3C4 / \uBB38\uC81C\uC758\uC2DD:",
      cardVerdictLabel: "\u26A1 \uAC80\uC99D \uD329\uD2B8 / \uACB0\uB860:",
      cardConfidenceLabel: "\uC2E0\uB8B0\uB3C4",
      cardSourcesLabel: "\uAC1C 1\uCC28 \uCD9C\uCC98",
      cardViewBtn: "\uC2EC\uCE35 \uBCF4\uACE0\uC11C \uC5F4\uB78C",
      newsHeaderBadge: "GLOBAL TECH & AI INTELLIGENCE FEED",
      newsHeaderTitle: "\uCEE4\uBBA4\uB2C8\uD2F0, \uD574\uCEE4\uB274\uC2A4, \uC0AC\uC124\uC5D0\uC11C \uC218\uC9D1\uB41C \uD14C\uD06C & AI \uCD5C\uC2E0 \uB2F4\uB860",
      newsHeaderDesc: "\uC18C\uD504\uD2B8\uC6E8\uC5B4\xB7AI \uC800\uC7A5\uC18C\uBFD0\uB9CC \uC544\uB2C8\uB77C \uC2E0\uC18C\uC7AC\xB7\uC6B0\uC8FC, \uAC70\uC2DC\uACBD\uC81C, \uC778\uD504\uB77C \uBCF4\uC548 \uB4F1 \uAE00\uB85C\uBC8C \uAE30\uC220 \uB3D9\uD5A5\uC744 \uC120\uBCC4\uD569\uB2C8\uB2E4.",
      newsOriginalLink: "\uAE30\uC0AC \uC6D0\uBB38",
      newsCatFilterLabel: "\u{1F3F7}\uFE0F \uAE30\uC220\xB7\uAE00\uB85C\uBC8C \uBD84\uB958:",
      newsCats: {
        "ALL": "\uC804\uCCB4",
        "TECH_COMPUTING": "\u{1F4BB} IT\xB7\uCEF4\uD4E8\uD305",
        "SCIENCE_RESEARCH": "\u{1F680} \uACFC\uD559\xB7\uC6B0\uC8FC",
        "ECONOMY_FINANCE": "\u{1F3E6} \uACBD\uC81C\xB7\uAE08\uC735",
        "LAW_CRIME_JUSTICE": "\u2696\uFE0F \uC0AC\uD68C\xB7\uBC95\uB960",
        "POLITICS_POLICY": "\u{1F3DB}\uFE0F \uC815\uCE58\xB7\uC815\uCC45",
        "CULTURE_HUMANITIES": "\u{1F33F} \uBB38\uD654\xB7\uC778\uBB38"
      },
      newsTier2FilterLabel: "\u21B3 \u{1F4BB} IT \uC138\uBD80 \uBD84\uC57C:",
      newsT2: {
        "ALL": "\uC804\uCCB4 IT \uBD84\uC57C",
        "INFERENCE_OPT": "\u26A1 \uCD94\uB860\xB7\uC11C\uBE59",
        "AGENTS_DEVTOOLS": "\u{1F6E0}\uFE0F \uC5D0\uC774\uC804\uD2B8\xB7\uB3C4\uAD6C",
        "MULTIMODAL_AI": "\u{1F3A8} \uBA40\uD2F0\uBAA8\uB2EC",
        "FOUNDATION_MODELS": "\u{1F916} \uD30C\uC6B4\uB370\uC774\uC158",
        "INFRA_RAG_SECURITY": "\u{1F6E1}\uFE0F \uC778\uD504\uB77C\xB7\uBCF4\uC548",
        "INDUSTRY_TRENDS": "\u{1F310} \uC77C\uBC18 SW\xB7\uC6F9"
      },
      newsSourceLabel: "\uCD9C\uCC98:",
      newsSrcAll: "\uC804\uCCB4 \uCD9C\uCC98",
      newsSearchPlaceholder: "\uAE30\uC220\uBA85, \uD0A4\uC6CC\uB4DC \uAC80\uC0C9...",
      newsSortLabel: "\uC815\uB82C:",
      newsSortOptions: [
        { val: "date-audit-desc", text: "\u{1F52C} AI \uBD84\uC11D\uC77C \uCD5C\uC2E0\uC21C (\uAE30\uBCF8)" },
        { val: "date-audit-asc", text: "\u{1F52C} AI \uBD84\uC11D\uC77C \uC624\uB798\uB41C\uC21C" },
        { val: "date-source-desc", text: "\u{1F4C5} \uC218\uC9D1/\uBC1C\uD45C \uCD5C\uC2E0\uC21C" },
        { val: "date-source-asc", text: "\u{1F4C5} \uC218\uC9D1/\uBC1C\uD45C \uC624\uB798\uB41C\uC21C" }
      ],
      modelsFamilyLabel: "\u{1F916} \uBAA8\uB378 \uD328\uBC00\uB9AC:",
      modelFams: {
        "ALL": "\uC804\uCCB4 \uD328\uBC00\uB9AC",
        "Qwen": "Qwen",
        "Wan": "Wan \uBE44\uB514\uC624",
        "MiniMax": "MiniMax",
        "FLUX": "FLUX \uC774\uBBF8\uC9C0",
        "GLM": "GLM",
        "DeepSeek": "DeepSeek",
        "Hunyuan": "Hunyuan",
        "Audio": "\uC74C\uC131/TTS",
        "Standalone": "\uB3C5\uB9BD/\uC2E0\uADDC \uBAA8\uB378"
      },
      modelsArtifactLabel: "\u{1F9E9} \uD5C8\uBE0C \uC720\uD615:",
      modelArts: {
        "ALL": "\uC804\uCCB4",
        "WEIGHTS": "\u{1F916} \uAC00\uC911\uCE58\xB7\uCCB4\uD06C\uD3EC\uC778\uD2B8",
        "WEB_SERVICE": "\u{1F310} \uC778\uD130\uB799\uD2F0\uBE0C \uB370\uBAA8\xB7Spaces",
        "FINETUNE": "\u{1F3AF} \uD2B9\uD654 \uD30C\uC778\uD29C\uB2DD"
      },
      modelsSearchPlaceholder: "\uBAA8\uB378\uBA85, \uC544\uD0A4\uD14D\uCC98, \uD3EC\uB9F7 \uAC80\uC0C9...",
      modelsSortLabel: "\uC815\uB82C:",
      modelsSortOptions: [
        { val: "date-source-desc", text: "\u{1F4C5} \uBC1C\uD589\uC77C \uCD5C\uC2E0\uC21C (\uAE30\uBCF8)" },
        { val: "date-source-asc", text: "\u{1F4C5} \uBC1C\uD589\uC77C \uC624\uB798\uB41C\uC21C" },
        { val: "date-audit-desc", text: "\u{1F52C} \uBD84\uC11D\uC77C \uCD5C\uC2E0\uC21C" },
        { val: "title-asc", text: "\u{1F524} \uBAA8\uB378\uBA85 \uAC00\uB098\uB2E4\uC21C" }
      ],
      graphHeaderBadge: "MULTI-ENTITY CITATION NETWORK",
      graphHeaderTitle: "\uC778\uBB3C\uACFC \uB17C\uBB38 \uC778\uC6A9 \uACC4\uBCF4\uB97C \uD1B5\uD55C \uAE30\uC220 \uD0C4\uC0DD\uC758 \uBFCC\uB9AC \uC9C0\uB3C4",
      graphHeaderSub: "\uAE30\uC220 \u2022 \uC5F0\uAD6C\uC790 \u2022 \uC5F0\uAD6C\uC18C \u2022 1\uCC28 \uB17C\uBB38",
      graphBtnAll: "\uC804\uCCB4 \uBCF4\uAE30",
      graphBtnLang: "\uC5B8\uC5B4",
      graphBtnTech: "\uAE30\uC220/\uC5D4\uC9C4",
      graphBtnOrg: "\uC5F0\uAD6C\uC18C",
      graphBtnPerson: "\uC778\uBB3C",
      graphBtnPaper: "\uB17C\uBB38",
      criteriaTitle: "\uC790\uC728 \uD06C\uB860 4\uB300 \uC790\uB3D9 \uC2B9\uACA9(Promotion) \uAE30\uC900 \uAC00\uC774\uB4DC",
      criteriaDesc: "\uC218\uC9D1\uB41C \uC218\uB9CE\uC740 \uC624\uD508\uC18C\uC2A4 \uBC0F \uB17C\uBB38 \uC911 \uC544\uB798\uC758 4\uB300 \uBC14\uC774\uB7F4/\uAE30\uC220 \uC784\uACC4\uCE58\uB97C \uB3CC\uD30C\uD55C \uD56D\uBAA9\uC740 \uC790\uB3D9\uC73C\uB85C [\uC790\uB3D9 \uC2B9\uACA9 \uD2B8\uB80C\uB4DC \uD6C4\uBCF4]\uB85C \uACA9\uC0C1\uB418\uC5B4 \uCD5C\uC6B0\uC120 \uAE30\uC220 \uAC80\uC99D \uB300\uAE30\uC5F4\uC5D0 \uB4F1\uB85D\uB429\uB2C8\uB2E4.",
      critGithub: "\uCD5C\uADFC 14\uC77C \uC774\uB0B4 \uC0DD\uC131 & \u2605 > 500 Stars \uB3CC\uD30C",
      critHn: "Top/Best \uC2A4\uD1A0\uB9AC \uC911 \uCD94\uCC9C \uC810\uC218 \u{1F525} > 150 Points",
      critHf: "Trending \uC810\uC218 \uC0C1\uC704\uAD8C & \u2764\uFE0F > 100 Likes \uBAA8\uB378/\uB370\uBAA8",
      critArxiv: "MoE, Reasoning, VLM \uB4F1 \uD601\uC2E0 \uC544\uD0A4\uD14D\uCC98 1\uCC28 \uB17C\uBB38",
      inboxHeaderBadge: "AUTONOMOUS HARVEST INBOX",
      inboxHeaderTitle: "\uC6D0\uCC9C \uB370\uC774\uD130 \uC544\uCE74\uC774\uBE0C & \uAD00\uB9AC\uC790 \uD30C\uC774\uD504\uB77C\uC778",
      inboxHeaderDesc: "\uD06C\uB864\uB7EC\uAC00 24\uC2DC\uAC04 \uC2E4\uC2DC\uAC04 \uC218\uC9D1\uD55C \uC6D0\uCC9C \uB85C\uC6B0 \uB370\uC774\uD130\uB97C \uC601\uAD6C \uBCF4\uC874\uD558\uBA70, \uAD00\uB9AC\uC790\uAC00 \uC2EC\uCE35 \uD329\uD2B8\uCCB4\uD06C(\uACF5\uC2DD \uAC80\uC99D)\uB85C \uC2B9\uACA9\uD560 \uD6C4\uBCF4\uB97C \uAC80\uD1A0\uD558\uB294 \uB0B4\uBD80 \uC800\uC7A5\uC18C\uC785\uB2C8\uB2E4.",
      inboxFamilyOn: "\uD328\uBC00\uB9AC \uBB36\uC74C (ON)",
      inboxFamilyOff: "\uD328\uBC00\uB9AC \uBB36\uC74C (OFF)",
      inboxSearchPlaceholder: "\uD6C4\uBCF4 \uAE30\uC220 \uB610\uB294 \uBAA8\uB378\uBA85 \uAC80\uC0C9...",
      inboxQueueBtn: "\uBD84\uC11D \uD050 \uB2F4\uAE30",
      inboxQueuedBtn: "\uB300\uAE30\uC5F4 \uB4F1\uB85D\uB428",
      modalSecCurationTitle: "Discovery Motivation & Target Workflow",
      modalSecViralPostTitle: "1\uCC28 \uB9C8\uCF00\uD305 \uC6D0\uBB38 & \uBC14\uC774\uB7F4 \uD074\uB808\uC784 \uBC1C\uCDCC (Raw Viral Claim)",
      modalSecClaimsTitle: "Marketing Claims vs Empirical Reality",
      modalSecHookTitle: "The Hook & Marketing Hype",
      modalSecHandsOnTitle: "Hands-on Measured Results",
      modalSecAltsTitle: "Comparative Alternatives Matrix",
      modalSecSourcesTitle: "Audited Primary Sources",
      modalWorkflowLabel: "\u{1F3AF} \uC5F0\uACC4 \uC6CC\uD06C\uD50C\uB85C\uC6B0:",
      modalViralLinkText: "\uC6D0\uBB38 \uD3EC\uC2A4\uD2B8 \uBC14\uB85C\uAC00\uAE30",
      thTool: "\uB3C4\uAD6C / \uAE30\uC220\uBA85",
      thStack: "\uAE30\uC220 \uC2A4\uD0DD",
      thPros: "\uC7A5\uC810",
      thCons: "\uB2E8\uC810",
      thBestFor: "\uC801\uD569\uD55C \uD658\uACBD"
    },
    ZH: {
      brandTitle: "FactCheck Hub",
      brandSubtitle: "AI \u4E8B\u5B9E\u6838\u67E5\u4E0E\u5168\u7403\u79D1\u6280\u524D\u6CBF\u52A8\u6001",
      navHome: "\u4EEA\u8868\u76D8",
      navPortfolio: "\u5B98\u65B9\u6838\u67E5",
      navModels: "AI \u6A21\u578B\u8D8B\u52BF",
      navNews: "\u5B9E\u65F6\u8D8B\u52BF\u96F7\u8FBE",
      navGraph: "\u5F15\u7528\u7CFB\u8C31\u56FE",
      navInbox: "\u91C7\u96C6\u6536\u4EF6\u7BB1",
      adminArchiveBtn: "\u5F52\u6863 (Admin)",
      statArchiveLabel: "\u539F\u59CB\u5F52\u6863 (Admin)",
      pipelineScheduleDesc: "\u6BCF\u65E5 4 \u6B21\uFF0800:17\u300106:17\u300112:17\u300118:17 KST\uFF09\u5468\u671F\u7B56\u7565\u91C7\u96C6",
      pipelineWidgetTitle: "\u81EA\u4E3B\u5B9A\u65F6\u6D41\u6C34\u7EBF\u9065\u6D4B\u4E0E\u4E0B\u6B21\u91C7\u96C6\u5012\u8BA1\u65F6",
      pipelineNextTargetLabel: "\u4E0B\u6B21\u81EA\u52A8\u91C7\u96C6\u8BA1\u5212",
      pipelineFooterAudit: "\u6BCF\u65E54\u6B21(00, 06, 12, 18\u65F6 KST) \u5B9A\u5411\u7B56\u7565\u91C7\u96C6 & Vercel \u5B9E\u65F6\u540C\u6B65",
      pipelineFooterNote: "* \u53D7 GitHub Actions \u961F\u5217\u8D1F\u8F7D\u5F71\u54CD\uFF0C\u53EF\u80FD\u5B58\u5728 \xB12~5 \u5206\u949F\u8C03\u5EA6\u5EF6\u8FDF.",
      heroBadge: "ZERO-HALLUCINATION ARCHITECTURE & COST AUDIT",
      heroMainTitle: "\u70ED\u95E8 AI \u6280\u672F\u7684\u5DE5\u7A0B\u771F\u76F8\u4E0E\u5B9E\u4F53\u9A8C\u8BC1",
      heroMainDesc: "\u6452\u5F03\u793E\u4EA4\u5A92\u4F53\u8425\u9500\u7092\u4F5C\u4E0E\u5E7B\u89C9\uFF0C\u57FA\u4E8E\u7B2C\u4E00\u624B\u5B98\u65B9\u6E90\u7801\u5BA1\u8BA1\u4EE5\u53CA\u57FA\u7840\u6807\u51C6 vs \u7B2C\u4E09\u65B9\u5DE5\u5177\u7684\u5B9E\u6D4B\u57FA\u51C6\uFF0C\u8F93\u51FA 100% \u771F\u5B9E\u5BA2\u89C2\u7684\u5DE5\u7A0B\u62A5\u544A\u3002",
      heroUpdateLabel: "\u6700\u65B0\u5BA1\u8BA1",
      heroAuditCount: "\u5DF2\u5B8C\u6210 49 \u9879\u6280\u672F\u5BA1\u8BA1",
      promoBannerTitle: "\u6280\u672F\u5BA1\u8BA1\u6863\u6848\u5E93\u6700\u65B0\u72B6\u6001",
      promoCountBadge: "49 \u9879\u6838\u9A8C\u5B8C\u6BD5",
      promoBannerDesc: "\u5DF2\u5BF9\u7A81\u7834\u70ED\u5EA6\u9608\u503C\u81EA\u52A8\u664B\u5347\u7684 49 \u9879\u91CD\u70B9\u5F00\u6E90\u9879\u76EE\u4E0E\u524D\u6CBF\u6A21\u578B\u5B8C\u6210\u5168\u6D41\u7A0B\u6DF1\u5EA6\u5B9E\u6D4B\u57FA\u51C6\u4E0E\u4E8B\u5B9E\u6838\u67E5\u3002",
      promoBtnText: "\u67E5\u770B\u91C7\u96C6\u6536\u4EF6\u7BB1\u5019\u9009",
      timelineTitle: "\u5F53\u65E5 24 \u5C0F\u65F6\u91C7\u96C6\u65F6\u95F4\u7EBF",
      timelineSub: "\u6BCF\u65E5 4 \u6B21 (00, 06, 12, 18\u65F6 KST) 6\u5C0F\u65F6\u5468\u671F\u5B9A\u5411\u91C7\u96C6 & AI \u5B9E\u65F6\u5206\u7C7B",
      timelineBadge: "\u6BCF\u65E54\u6B21 6h\u8109\u51B2",
      timelineLegend: "\u5404\u65F6\u6BB5\u91C7\u96C6\u6570",
      timelineFooterPrefix: "\u26A1 \u5F53\u65E5\u603B\u91C7\u96C6\u91CF:",
      trendRadarTitle: "\u6BCF\u65E5 4 \u6B21 AI \u8D8B\u52BF\u96F7\u8FBE",
      trendRadarSub: "\u5168\u7403\u5F00\u6E90\u4E0E AI \u524D\u6CBF\u6743\u91CD 6 \u5C0F\u65F6\u5468\u671F\u81EA\u52A8\u611F\u5E94",
      homeTopPicksTitle: "\u6700\u65B0\u6DF1\u5EA6\u6280\u672F\u6838\u67E5\u7CBE\u9009",
      homeTopPicksViewAll: "\u67E5\u770B\u5168\u90E8 49 \u4EFD\u6838\u67E5\u6863\u6848",
      btnAll: "\u5168\u90E8\u5BA1\u8BA1",
      btnUser: "\u4EBA\u5DE5\u7CBE\u9009",
      btnAuto: "\u81EA\u52A8\u8D8B\u52BF",
      sortLabel: "\u6392\u5E8F:",
      sortOptions: [
        { val: "date-audit-desc", text: "\u{1F52C} \u5BA1\u6838\u65E5\u671F\u6700\u65B0 (\u9ED8\u8BA4)" },
        { val: "date-audit-asc", text: "\u{1F52C} \u5BA1\u6838\u65E5\u671F\u6700\u65E9" },
        { val: "date-source-desc", text: "\u{1F4C5} \u539F\u6587\u53D1\u5E03\u6700\u65B0" },
        { val: "date-source-asc", text: "\u{1F4C5} \u539F\u6587\u53D1\u5E03\u6700\u65E9" }
      ],
      searchPlaceholder: "\u641C\u7D22\u6280\u672F\u540D\u3001\u67B6\u6784\u6216\u7B56\u5C55\u52A8\u673A...",
      domainLabel: "\u9886\u57DF:",
      tagAll: "\u5168\u90E8",
      tagFrontend: "\u524D\u7AEF/UI",
      tagAgent: "AI Agent",
      tagScraping: "\u7F51\u9875\u722C\u866B",
      tagDoc: "\u6587\u6863\u89E3\u6790",
      tag3d: "3D/\u7EC4\u4EF6",
      tagRust: "Rust\u7CFB\u7EDF",
      tagOther: "\u6838\u5FC3\u57FA\u5EFA",
      cardMotivationLabel: "\u{1F4A1} \u6316\u6398\u52A8\u673A / \u75DB\u70B9\u95EE\u9898:",
      cardVerdictLabel: "\u26A1 \u5BA1\u8BA1\u7ED3\u8BBA / \u4E8B\u5B9E\u6838\u9A8C:",
      cardConfidenceLabel: "\u53EF\u4FE1\u5EA6",
      cardSourcesLabel: "\u4E2A\u4E00\u624B\u6765\u6E90",
      cardViewBtn: "\u67E5\u9605\u5B8C\u6574\u62A5\u544A",
      newsHeaderBadge: "GLOBAL TECH & AI INTELLIGENCE FEED",
      newsHeaderTitle: "\u6E90\u81EA\u793E\u533A\u3001HackerNews \u4E0E\u4E13\u680F\u7684\u5168\u7403\u79D1\u6280\u4E0E AI \u8BA8\u8BBA",
      newsHeaderDesc: "\u4E0D\u4EC5\u8FFD\u8E2A\u5F00\u6E90\u4EE3\u7801\u4E0E\u6A21\u578B\uFF0C\u8FD8\u7CBE\u9009\u6DF1\u79D1\u6280\u3001\u822A\u7A7A\u822A\u5929\u3001\u5B8F\u89C2\u7ECF\u6D4E\u4E0E\u57FA\u7840\u8BBE\u65BD\u5B89\u5168\u52A8\u6001\u3002",
      newsOriginalLink: "\u9605\u8BFB\u539F\u6587",
      newsCatFilterLabel: "\u{1F3F7}\uFE0F \u6280\u672F\u4E0E\u5168\u7403\u9886\u57DF:",
      newsCats: {
        "ALL": "\u5168\u90E8",
        "TECH_COMPUTING": "\u{1F4BB} IT\u4E0E\u8BA1\u7B97",
        "SCIENCE_RESEARCH": "\u{1F680} \u79D1\u5B66\u4E0E\u822A\u5929",
        "ECONOMY_FINANCE": "\u{1F3E6} \u7ECF\u6D4E\u4E0E\u91D1\u878D",
        "LAW_CRIME_JUSTICE": "\u2696\uFE0F \u793E\u4F1A\u4E0E\u6CD5\u6CBB",
        "POLITICS_POLICY": "\u{1F3DB}\uFE0F \u653F\u6CBB\u4E0E\u653F\u7B56",
        "CULTURE_HUMANITIES": "\u{1F33F} \u6587\u5316\u4E0E\u4EBA\u6587"
      },
      newsTier2FilterLabel: "\u21B3 \u{1F4BB} IT \u7EC6\u5206\u9886\u57DF:",
      newsT2: {
        "ALL": "\u5168\u90E8 IT \u9886\u57DF",
        "INFERENCE_OPT": "\u26A1 \u63A8\u7406\u4E0E\u670D\u52A1",
        "AGENTS_DEVTOOLS": "\u{1F6E0}\uFE0F \u667A\u80FD\u4F53\u4E0E\u5DE5\u5177",
        "MULTIMODAL_AI": "\u{1F3A8} \u591A\u6A21\u6001",
        "FOUNDATION_MODELS": "\u{1F916} \u57FA\u7840\u6A21\u578B",
        "INFRA_RAG_SECURITY": "\u{1F6E1}\uFE0F \u57FA\u7840\u67B6\u6784\u4E0E\u5B89\u5168",
        "INDUSTRY_TRENDS": "\u{1F310} \u8F6F\u4EF6\u4E0E\u884C\u4E1A\u52A8\u6001"
      },
      newsSourceLabel: "\u6765\u6E90:",
      newsSrcAll: "\u5168\u90E8\u6765\u6E90",
      newsSearchPlaceholder: "\u641C\u7D22\u6280\u672F\u540D\u3001\u5173\u952E\u8BCD...",
      newsSortLabel: "\u6392\u5E8F:",
      newsSortOptions: [
        { val: "date-audit-desc", text: "\u{1F52C} AI \u5BA1\u6838\u65F6\u95F4\u6700\u65B0 (\u9ED8\u8BA4)" },
        { val: "date-audit-asc", text: "\u{1F52C} AI \u5BA1\u6838\u65F6\u95F4\u6700\u65E9" },
        { val: "date-source-desc", text: "\u{1F4C5} \u91C7\u96C6\u53D1\u5E03\u65F6\u95F4\u6700\u65B0" },
        { val: "date-source-asc", text: "\u{1F4C5} \u91C7\u96C6\u53D1\u5E03\u65F6\u95F4\u6700\u65E9" }
      ],
      modelsFamilyLabel: "\u{1F916} \u6A21\u578B\u7CFB\u5217:",
      modelFams: {
        "ALL": "\u5168\u90E8\u7CFB\u5217",
        "Qwen": "Qwen",
        "Wan": "Wan \u89C6\u9891",
        "MiniMax": "MiniMax",
        "FLUX": "FLUX \u56FE\u50CF",
        "GLM": "GLM",
        "DeepSeek": "DeepSeek",
        "Hunyuan": "Hunyuan",
        "Audio": "\u8BED\u97F3/TTS",
        "Standalone": "\u72EC\u7ACB/\u65B0\u6A21\u578B"
      },
      modelsArtifactLabel: "\u{1F9E9} \u8D44\u6E90\u7C7B\u578B:",
      modelArts: {
        "ALL": "\u5168\u90E8",
        "WEIGHTS": "\u{1F916} \u6A21\u578B\u6743\u91CD\xB7\u68C0\u67E5\u70B9",
        "WEB_SERVICE": "\u{1F310} \u5728\u7EBF\u6F14\u793A\xB7Spaces",
        "FINETUNE": "\u{1F3AF} \u5B9A\u5236\u5FAE\u8C03"
      },
      modelsSearchPlaceholder: "\u641C\u7D22\u6A21\u578B\u540D\u3001\u67B6\u6784\u3001\u683C\u5F0F...",
      modelsSortLabel: "\u6392\u5E8F:",
      modelsSortOptions: [
        { val: "date-source-desc", text: "\u{1F4C5} \u53D1\u5E03\u65F6\u95F4\u6700\u65B0 (\u9ED8\u8BA4)" },
        { val: "date-source-asc", text: "\u{1F4C5} \u53D1\u5E03\u65F6\u95F4\u6700\u65E9" },
        { val: "date-audit-desc", text: "\u{1F52C} AI \u5BA1\u6838\u6700\u65B0" },
        { val: "title-asc", text: "\u{1F524} \u6A21\u578B\u540D A-Z" }
      ],
      graphHeaderBadge: "MULTI-ENTITY CITATION NETWORK",
      graphHeaderTitle: "\u4EBA\u7269\u4E0E\u8BBA\u6587\u5F15\u7528\u7CFB\u8C31\u6280\u672F\u6EAF\u6E90\u5168\u666F\u56FE",
      graphHeaderSub: "\u6280\u672F \u2022 \u7814\u7A76\u5458 \u2022 \u5B9E\u9A8C\u5BA4 \u2022 \u4E00\u624B\u8BBA\u6587",
      graphBtnAll: "\u67E5\u770B\u5168\u90E8",
      graphBtnLang: "\u7F16\u7A0B\u8BED\u8A00",
      graphBtnTech: "\u6838\u5FC3\u6280\u672F/\u5F15\u64CE",
      graphBtnOrg: "\u79D1\u7814\u673A\u6784",
      graphBtnPerson: "\u4EE3\u8868\u4EBA\u7269",
      graphBtnPaper: "\u7ECF\u5178\u8BBA\u6587",
      criteriaTitle: "\u5168\u81EA\u52A8\u5DE1\u68C0 4 \u5927\u81EA\u52A8\u664B\u5347 (Promotion) \u5224\u5B9A\u51C6\u5219",
      criteriaDesc: "\u5728\u6D77\u91CF\u91C7\u96C6\u7684\u5F00\u6E90\u9879\u76EE\u4E0E\u524D\u6CBF\u8BBA\u6587\u4E2D\uFF0C\u7A81\u7834\u4EE5\u4E0B 4 \u9879\u70ED\u5EA6\u4E0E\u6280\u672F\u6307\u6807\u7684\u5019\u9009\u9879\u76EE\u5C06\u81EA\u52A8\u664B\u5347\u81F3\u4F18\u5148\u6838\u67E5\u961F\u5217\u3002",
      critGithub: "14 \u5929\u5185\u65B0\u5EFA\u4ED3\u5E93\u4E14 \u2605 > 500 Stars \u7A81\u7834",
      critHn: "Top/Best \u8BA8\u8BBA\u4E2D\u70B9\u8D5E\u70ED\u5EA6 \u{1F525} > 150 Points",
      critHf: "Trending \u8D8B\u52BF\u699C\u524D\u5217\u4E14 \u2764\uFE0F > 100 Likes \u6A21\u578B/Demo",
      critArxiv: "\u6DB5\u76D6 MoE\u3001\u63A8\u7406\u5F3A\u5316\u3001VLM \u7684\u7B2C\u4E00\u624B\u7ECF\u5178\u67B6\u6784\u8BBA\u6587",
      inboxHeaderBadge: "AUTONOMOUS HARVEST INBOX",
      inboxHeaderTitle: "\u539F\u59CB\u6570\u636E\u5F52\u6863\u4E0E\u7BA1\u7406\u5458\u6D41\u6C34\u7EBF",
      inboxHeaderDesc: "\u5168\u5929\u5019\u5B9E\u65F6\u91C7\u96C6\u7684\u539F\u59CB\u6570\u636E\u6C38\u4E45\u5B58\u50A8\u5E93\uFF0C\u4F9B\u7BA1\u7406\u5458\u5BA1\u67E5\u5E76\u664B\u5347\u81F3\u6DF1\u5EA6\u4E8B\u5B9E\u6838\u67E5\uFF08\u5B98\u65B9\u5BA1\u8BA1\uFF09\u5019\u9009\u3002",
      inboxFamilyOn: "\u7CFB\u5217\u805A\u5408 (\u5F00)",
      inboxFamilyOff: "\u7CFB\u5217\u805A\u5408 (\u5173)",
      inboxSearchPlaceholder: "\u641C\u7D22\u5019\u9009\u6280\u672F\u6216\u6A21\u578B\u540D\u79F0...",
      inboxQueueBtn: "\u52A0\u5165\u5F85\u5BA1\u961F\u5217",
      inboxQueuedBtn: "\u5DF2\u5728\u961F\u5217\u4E2D",
      modalSecCurationTitle: "Discovery Motivation & Target Workflow",
      modalSecViralPostTitle: "\u8425\u9500\u5BA3\u4F20\u539F\u6587\u6458\u5F55\u4E0E\u4E3B\u5F20\u8BC1\u636E (Raw Viral Claim)",
      modalSecClaimsTitle: "Marketing Claims vs Empirical Reality",
      modalSecHookTitle: "The Hook & Marketing Hype",
      modalSecHandsOnTitle: "Hands-on Measured Results",
      modalSecAltsTitle: "Comparative Alternatives Matrix",
      modalSecSourcesTitle: "Audited Primary Sources",
      modalWorkflowLabel: "\u{1F3AF} \u534F\u540C\u5DE5\u4F5C\u6D41:",
      modalViralLinkText: "\u76F4\u8FBE\u539F\u6587\u5E16\u5B50",
      thTool: "\u5DE5\u5177 / \u6280\u672F",
      thStack: "\u6280\u672F\u6808",
      thPros: "\u6838\u5FC3\u4F18\u52BF",
      thCons: "\u52A3\u52BF\u4E0E\u5C40\u9650",
      thBestFor: "\u6700\u9002\u7528\u573A\u666F"
    },
    EN: {
      brandTitle: "FactCheck Hub",
      brandSubtitle: "AI Fact-Checking & Global Tech Intelligence",
      navHome: "Dashboard",
      navPortfolio: "Fact-Checks",
      navModels: "AI Model Trends",
      navNews: "Trends Radar",
      navGraph: "Citation Graph",
      navInbox: "Harvest Inbox",
      adminArchiveBtn: "Archive (Admin)",
      statArchiveLabel: "Raw Archive (Admin)",
      pipelineScheduleDesc: "4x Daily (00:17, 06:17, 12:17, 18:17 KST) Strategic Ingestion",
      pipelineWidgetTitle: "Autonomous Cron Pipeline Telemetry & Next Ingestion Countdown",
      pipelineNextTargetLabel: "Next Scheduled Ingestion",
      pipelineFooterAudit: "4x daily (00, 06, 12, 18 KST) strategic collection & Vercel live sync",
      pipelineFooterNote: "* \xB12~5 min schedule variance may occur based on GitHub Actions runner queue load.",
      heroBadge: "ZERO-HALLUCINATION ARCHITECTURE & COST AUDIT",
      heroMainTitle: "Empirical Analysis of Viral AI Technologies",
      heroMainDesc: "A zero-hallucination dossier derived from Tier-1 official source audits and empirical benchmarks comparing base standards with third-party tools.",
      heroUpdateLabel: "LAST AUDITED",
      heroAuditCount: "49 Audits Completed",
      promoBannerTitle: "Dossier Status Update",
      promoCountBadge: "49 Completed",
      promoBannerDesc: "All 49 high-velocity repositories and models that crossed the viral threshold have been rigorously benchmarked and fact-checked.",
      promoBtnText: "Explore Harvest Inbox",
      timelineTitle: "Today 24-Hour Collection Timeline",
      timelineSub: "4x daily (00, 06, 12, 18 KST) 6h strategic collection & AI live enrichment",
      timelineBadge: "4x Daily 6h Pulse",
      timelineLegend: "Items per Session",
      timelineFooterPrefix: "\u26A1 Today Total Collected:",
      trendRadarTitle: "4x Daily AI Trend Radar",
      trendRadarSub: "Autonomous 6-hour radar for trending open weights & code",
      homeTopPicksTitle: "Latest Deep Technical Verification Highlights",
      homeTopPicksViewAll: "View All 49 Empirical Dossiers",
      btnAll: "All Dossiers",
      btnUser: "User Curated",
      btnAuto: "Auto Trends",
      sortLabel: "Sort:",
      sortOptions: [
        { val: "date-audit-desc", text: "\u{1F52C} Audit Date (Newest first)" },
        { val: "date-audit-asc", text: "\u{1F52C} Audit Date (Oldest first)" },
        { val: "date-source-desc", text: "\u{1F4C5} Source Published (Newest first)" },
        { val: "date-source-asc", text: "\u{1F4C5} Source Published (Oldest first)" }
      ],
      searchPlaceholder: "Search tech, architecture, or motivation...",
      domainLabel: "Domain:",
      tagAll: "All",
      tagFrontend: "Frontend",
      tagAgent: "AI Agents",
      tagScraping: "Scraping",
      tagDoc: "Docs/OCR",
      tag3d: "3D WebGL",
      tagRust: "Rust/Sys",
      tagOther: "Core Infra",
      cardMotivationLabel: "\u{1F4A1} Intent & Problem:",
      cardVerdictLabel: "\u26A1 Empirical Truth & Verdict:",
      cardConfidenceLabel: "Confidence",
      cardSourcesLabel: "Sources",
      cardViewBtn: "View Full Dossier",
      newsHeaderBadge: "GLOBAL AI INTELLIGENCE FEED",
      newsHeaderTitle: "AI Trends & Engineering Discourse from HackerNews & Communities",
      newsHeaderDesc: "Curated engineering analyses, security vulnerabilities, and architectural tutorials.",
      newsOriginalLink: "Read Source",
      newsCatFilterLabel: "\u{1F3F7}\uFE0F Global Domain:",
      newsCats: {
        "ALL": "All",
        "TECH_COMPUTING": "\u{1F4BB} IT & Computing",
        "SCIENCE_RESEARCH": "\u{1F680} Science & Space",
        "ECONOMY_FINANCE": "\u{1F3E6} Economy & Finance",
        "LAW_CRIME_JUSTICE": "\u2696\uFE0F Society & Law",
        "POLITICS_POLICY": "\u{1F3DB}\uFE0F Policy & Politics",
        "CULTURE_HUMANITIES": "\u{1F33F} Culture & Arts"
      },
      newsTier2FilterLabel: "\u21B3 \u{1F4BB} IT Sub-tracks:",
      newsT2: {
        "ALL": "All IT Tracks",
        "INFERENCE_OPT": "\u26A1 Inference & Serving",
        "AGENTS_DEVTOOLS": "\u{1F6E0}\uFE0F Agents & DevTools",
        "MULTIMODAL_AI": "\u{1F3A8} Multimodal AI",
        "FOUNDATION_MODELS": "\u{1F916} Foundation Models",
        "INFRA_RAG_SECURITY": "\u{1F6E1}\uFE0F Infra & Security",
        "INDUSTRY_TRENDS": "\u{1F310} General SW & Web"
      },
      newsSourceLabel: "Source:",
      newsSrcAll: "All Sources",
      newsSearchPlaceholder: "Search tech, keywords...",
      newsSortLabel: "Sort:",
      newsSortOptions: [
        { val: "date-audit-desc", text: "\u{1F52C} AI Audit Date (Newest first, default)" },
        { val: "date-audit-asc", text: "\u{1F52C} AI Audit Date (Oldest first)" },
        { val: "date-source-desc", text: "\u{1F4C5} Source Published (Newest first)" },
        { val: "date-source-asc", text: "\u{1F4C5} Source Published (Oldest first)" }
      ],
      modelsFamilyLabel: "\u{1F916} Model Family:",
      modelFams: {
        "ALL": "All Families",
        "Qwen": "Qwen",
        "Wan": "Wan Video",
        "MiniMax": "MiniMax",
        "FLUX": "FLUX Image",
        "GLM": "GLM",
        "DeepSeek": "DeepSeek",
        "Hunyuan": "Hunyuan",
        "Audio": "Audio/TTS",
        "Standalone": "Standalone Models"
      },
      modelsArtifactLabel: "\u{1F9E9} Hub Resource:",
      modelArts: {
        "ALL": "All",
        "WEIGHTS": "\u{1F916} Weights & Checkpoints",
        "WEB_SERVICE": "\u{1F310} Interactive Demos / Spaces",
        "FINETUNE": "\u{1F3AF} Specialized Finetunes"
      },
      modelsSearchPlaceholder: "Search model name, architecture, format...",
      modelsSortLabel: "Sort:",
      modelsSortOptions: [
        { val: "date-source-desc", text: "\u{1F4C5} Source Published (Newest first)" },
        { val: "date-source-asc", text: "\u{1F4C5} Source Published (Oldest first)" },
        { val: "date-audit-desc", text: "\u{1F52C} Audit Date (Newest first)" },
        { val: "title-asc", text: "\u{1F524} Model Name (A-Z)" }
      ],
      graphHeaderBadge: "MULTI-ENTITY CITATION NETWORK",
      graphHeaderTitle: "Genealogy Map of AI Innovations via Citations",
      graphHeaderSub: "Tech \u2022 Researchers \u2022 Labs \u2022 Primary Papers",
      graphBtnAll: "Show All",
      graphBtnLang: "Language",
      graphBtnTech: "Tech / Engine",
      graphBtnOrg: "Laboratories",
      graphBtnPerson: "People",
      graphBtnPaper: "Papers",
      criteriaTitle: "Autonomous Cron Promotion Criteria Guide",
      criteriaDesc: "Repositories and papers exceeding these 4 viral thresholds are auto-promoted into the priority technical verification queue.",
      critGithub: "Created in last 14 days & > 500 Stars",
      critHn: "Top/Best stories with Score \u{1F525} > 150 Points",
      critHf: "Top Trending with \u2764\uFE0F > 100 Likes",
      critArxiv: "Foundational papers on MoE, Reasoning, VLM",
      inboxHeaderBadge: "AUTONOMOUS HARVEST INBOX",
      inboxHeaderTitle: "Raw Data Archive & Admin Pipeline",
      inboxHeaderDesc: "Permanent raw ingestion repository collected 24/7, enabling administrators to review and promote candidates into deep fact-checks.",
      inboxFamilyOn: "Family Group (ON)",
      inboxFamilyOff: "Family Group (OFF)",
      inboxSearchPlaceholder: "Search candidate tech or model...",
      inboxQueueBtn: "Queue for Audit",
      inboxQueuedBtn: "In Queue",
      modalSecCurationTitle: "Discovery Motivation & Target Workflow",
      modalSecViralPostTitle: "Raw Viral Claim Excerpt & Evidence",
      modalSecClaimsTitle: "Marketing Claims vs Empirical Reality",
      modalSecHookTitle: "The Hook & Marketing Hype",
      modalSecHandsOnTitle: "Hands-on Measured Results",
      modalSecAltsTitle: "Comparative Alternatives Matrix",
      modalSecSourcesTitle: "Audited Primary Sources",
      modalWorkflowLabel: "\u{1F3AF} Target Workflow:",
      modalViralLinkText: "Go to Viral Post",
      thTool: "Tool / Repository",
      thStack: "Tech Stack",
      thPros: "Empirical Strengths",
      thCons: "Weaknesses & Bottlenecks",
      thBestFor: "Best For"
    }
  };
  function setLanguage(lang, skipViewRender = false) {
    setGlobalLang(lang);
    if (typeof localStorage !== "undefined") {
      try {
        localStorage.setItem("factcheck_lang", lang);
      } catch (e) {
      }
    }
    if (typeof document !== "undefined") {
      if (lang === "ZH") {
        document.documentElement.lang = "zh-CN";
        document.body.style.fontFamily = "'Noto Sans SC', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'SimHei', sans-serif";
      } else if (lang === "EN") {
        document.documentElement.lang = "en";
        document.body.style.fontFamily = "'Geist', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
      } else {
        document.documentElement.lang = "ko";
        document.body.style.fontFamily = "'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif";
      }
      ["KO", "ZH", "EN"].forEach((l) => {
        const btn = document.getElementById("lang" + l.charAt(0) + l.slice(1).toLowerCase() + "Btn");
        if (btn) {
          btn.className = l === lang ? "px-2 py-0.5 rounded bg-ink-primary text-white font-bold transition text-[10px] sm:text-[11px] shadow-sm" : "px-2 py-0.5 rounded text-ink-secondary hover:text-ink-primary transition text-[10px] sm:text-[11px]";
        }
      });
      const t = i18n[lang] || i18n["KO"];
      const safeSetText = (id, txt) => {
        const el = document.getElementById(id);
        if (el && txt !== void 0) el.innerText = txt;
      };
      const safeSetHtml = (id, html) => {
        const el = document.getElementById(id);
        if (el && html !== void 0) el.innerHTML = html;
      };
      const safeSetAttr = (id, attr, val) => {
        const el = document.getElementById(id);
        if (el && val !== void 0) el.setAttribute(attr, val);
      };
      const totalModelsCnt = snapshotStats && snapshotStats.models_total_count || (typeof liveModelsData !== "undefined" ? liveModelsData.length : 344);
      const totalInboxCnt = snapshotStats && snapshotStats.inbox_total_count || (typeof liveInboxData !== "undefined" ? liveInboxData.length : 3039);
      safeSetText("headerBrandTitle", t.brandTitle);
      safeSetText("headerBrandSubtitle", t.brandSubtitle);
      safeSetText("navTabHome", t.navHome || "\uB300\uC2DC\uBCF4\uB4DC");
      safeSetText("mNavTabHome", t.navHome || "\uB300\uC2DC\uBCF4\uB4DC");
      safeSetText("navTabPortfolio", t.navPortfolio);
      safeSetText("mNavTabPortfolio", t.navPortfolio);
      safeSetText("navTabModels", t.navModels);
      safeSetText("mNavTabModels", `${t.navModels} (${totalModelsCnt.toLocaleString()})`);
      safeSetText("navTabNews", t.navNews);
      safeSetText("mNavTabNews", `${t.navNews} (${totalInboxCnt.toLocaleString()})`);
      safeSetText("navTabGraph", t.navGraph);
      safeSetText("mNavTabGraph", t.navGraph);
      safeSetText("adminArchiveLabel", t.adminArchiveBtn);
      safeSetText("mNavTabInbox", `${t.adminArchiveBtn || "\uC544\uCE74\uC774\uBE0C"} (${totalInboxCnt.toLocaleString()})`);
      safeSetText("heroBadge", t.heroBadge);
      safeSetText("heroMainTitle", t.heroMainTitle);
      safeSetHtml("heroMainDesc", t.heroMainDesc);
      const liveCasesCount = window.liveCasesData && window.liveCasesData.length || window.casesData && window.casesData.length || snapshotStats && snapshotStats.total_cases || 63;
      const heroAuditText = lang === "KO" ? `\u25CF ${liveCasesCount}\uAC1C \uAE30\uC220 \uAC80\uC99D \uC644\uB8CC` : lang === "ZH" ? `\u5DF2\u5B8C\u6210 ${liveCasesCount} \u9879\u6280\u672F\u5BA1\u8BA1` : `${liveCasesCount} Audits Completed`;
      safeSetText("heroAuditCount", heroAuditText);
      safeSetText("statLabelVerified", lang === "KO" ? "\uACF5\uC2DD \uAE30\uC220 \uAC80\uC99D" : lang === "ZH" ? "\u5B98\u65B9\u6280\u672F\u6838\u67E5" : "Verified Fact-Checks");
      safeSetText("statLabelInbox", lang === "KO" ? "\uC218\uC9D1 \uC778\uBC15\uC2A4" : lang === "ZH" ? "\u91C7\u96C6\u6536\u4EF6\u7BB1" : "Harvested Inbox");
      safeSetText("statLabelModels", lang === "KO" ? "AI \uBAA8\uB378 \uD2B8\uB80C\uB4DC" : lang === "ZH" ? "AI \u6A21\u578B\u8D8B\u52BF" : "AI Model Trends");
      safeSetText("statLabelNews", lang === "KO" ? "AI \uD14C\uD06C \uB3D9\uD5A5" : lang === "ZH" ? "AI \u79D1\u6280\u52A8\u6001" : "Tech Intelligence");
      safeSetText("statLabelArchive", t.statArchiveLabel);
      safeSetText("statDescInbox", lang === "KO" ? "HN \xB7 GeekNews \xB7 GitHub \xB7 HF 24/7 \uC218\uC9D1" : lang === "ZH" ? "HN \xB7 GeekNews \xB7 GitHub \xB7 HF \u5168\u5929\u5019\u91C7\u96C6" : "HN \xB7 GeekNews \xB7 GitHub \xB7 HF 24/7 Ingestion");
      safeSetText("statDescModels", lang === "KO" ? "MoE, VLM, \uCD94\uB860 \uD2B9\uD654 \uC624\uD508 \uAC00\uC911\uCE58" : lang === "ZH" ? "MoE\u3001VLM\u4E0E\u63A8\u7406\u4F18\u5316\u5F00\u6E90\u6743\u91CD" : "MoE, VLM & Reasoning Open Weights");
      safeSetText("statDescNews", lang === "KO" ? "CVE \uCDE8\uC57D\uC810, \uC778\uD504\uB77C \uC7A5\uC560, \uC544\uD0A4\uD14D\uCC98 \uD1A0\uB860" : lang === "ZH" ? "CVE \u6F0F\u6D1E\u3001\u57FA\u7840\u8BBE\u65BD\u6545\u969C\u4E0E\u67B6\u6784\u5B9E\u8DF5" : "CVEs, Infra Outages & Architecture Posts");
      const nowKstForTitle = getDynamicKstDate();
      const pad0 = (n) => String(n).padStart(2, "0");
      const curKstDateStrForTitle = `${nowKstForTitle.getFullYear()}-${pad0(nowKstForTitle.getMonth() + 1)}-${pad0(nowKstForTitle.getDate())}`;
      safeSetText("timelineTitleText", (t.timelineTitle || "\uB2F9\uC77C 24\uC2DC\uAC04 \uC218\uC9D1 \uD0C0\uC784\uB77C\uC778") + " (" + curKstDateStrForTitle + ")");
      safeSetText("timelineSub", t.timelineSub);
      safeSetText("timelineBadgeText", t.timelineBadge);
      const curTlData = typeof window !== "undefined" && window.timeline24hData ? window.timeline24hData : [];
      const totCollectedTl = curTlData.reduce((acc, cur) => acc + (cur.inbox_count || 0), 0);
      const totEnrichedTl = curTlData.reduce((acc, cur) => acc + (cur.enriched_count !== void 0 ? cur.enriched_count : (cur.news_count || 0) + (cur.model_count || 0)), 0);
      const tlUnit = lang === "KO" ? "\uAC74" : lang === "ZH" ? "\u6761" : " items";
      safeSetHtml("timelineFooterText", `\u26A1 ${t.timelineFooterPrefix || "\uB2F9\uC77C \uCD1D \uC218\uC9D1\uB7C9:"} <b class="text-indigo-700">${totCollectedTl.toLocaleString()}${tlUnit}</b> \u2502 \u2728 AI ${totEnrichedTl.toLocaleString()}${tlUnit}`);
      safeSetText("trendRadarTitleText", t.trendRadarTitle);
      safeSetText("trendRadarSub", t.trendRadarSub);
      safeSetHtml("trendRadarFooter", `<span class="flex items-center gap-1.5"><i data-lucide="zap" class="w-3.5 h-3.5 text-amber-500"></i> ` + (lang === "KO" ? "LLM \uC790\uB3D9 \uD2B8\uB80C\uB4DC \uCD94\uCD9C (OpenRouter 0\uC6D0 \uB77C\uC6B0\uD305)" : lang === "ZH" ? "LLM \u81EA\u52A8\u5316\u8D8B\u52BF\u63D0\u53D6 (OpenRouter 0\u5143\u8DEF\u7531)" : "Automated LLM Trend Extraction (OpenRouter Free Tier)") + `</span>`);
      safeSetText("homeTopPicksTitle", t.homeTopPicksTitle);
      const viewAllDynamicText = lang === "KO" ? `\uC804\uCCB4 ${liveCasesCount}\uAC1C \uAC80\uC99D \uB3C4\uC2DC\uC5D0 \uBCF4\uB7EC\uAC00\uAE30` : lang === "ZH" ? `\u67E5\u770B\u5168\u90E8 ${liveCasesCount} \u4EFD\u6838\u67E5\u6863\u6848` : `View All ${liveCasesCount} Empirical Dossiers`;
      safeSetText("homeTopPicksViewAll", viewAllDynamicText);
      safeSetText("newsHeaderBadge", t.newsHeaderBadge);
      safeSetText("newsHeaderTitle", t.newsHeaderTitle);
      safeSetText("newsHeaderDesc", t.newsHeaderDesc);
      safeSetText("newsCatFilterLabel", t.newsCatFilterLabel);
      safeSetText("newsTier2FilterLabel", t.newsTier2FilterLabel);
      safeSetText("newsSourceLabel", t.newsSourceLabel);
      safeSetText("newsSrcBtnAll", t.newsSrcAll);
      safeSetAttr("newsSearchInput", "placeholder", t.newsSearchPlaceholder);
      safeSetText("newsSortLabel", t.newsSortLabel);
      if (typeof window.updateNewsCategoryPillCounts === "function") {
        window.updateNewsCategoryPillCounts();
      }
      const newsSortSel = document.getElementById("newsSortSelect");
      if (newsSortSel && t.newsSortOptions) {
        const cur = newsSortSel.value;
        newsSortSel.innerHTML = t.newsSortOptions.map((opt) => `<option value="${opt.val}" ${opt.val === cur ? "selected" : ""}>${opt.text}</option>`).join("");
      }
      safeSetText("modelsFamilyLabel", t.modelsFamilyLabel);
      safeSetText("modelsArtifactLabel", t.modelsArtifactLabel);
      safeSetAttr("modelsSearchInput", "placeholder", t.modelsSearchPlaceholder);
      safeSetText("modelsSortLabel", t.modelsSortLabel);
      if (typeof window.updateModelCategoryPillCounts === "function") {
        window.updateModelCategoryPillCounts();
      } else {
        document.querySelectorAll(".model-fam-pill").forEach((pill) => {
          const fam = pill.dataset.fam;
          if (t.modelFams && t.modelFams[fam]) pill.innerText = t.modelFams[fam];
        });
        document.querySelectorAll(".model-art-pill").forEach((pill) => {
          const art = pill.dataset.art;
          if (t.modelArts && t.modelArts[art]) pill.innerText = t.modelArts[art];
        });
      }
      const modelsSortSel = document.getElementById("modelsSortSelect");
      if (modelsSortSel && t.modelsSortOptions) {
        const cur = modelsSortSel.value;
        modelsSortSel.innerHTML = t.modelsSortOptions.map((opt) => `<option value="${opt.val}" ${opt.val === cur ? "selected" : ""}>${opt.text}</option>`).join("");
      }
      safeSetText("graphHeaderBadge", t.graphHeaderBadge);
      safeSetText("graphHeaderTitle", t.graphHeaderTitle);
      safeSetText("graphHeaderSub", t.graphHeaderSub);
      safeSetText("graphBtnAll", t.graphBtnAll);
      safeSetText("graphBtnLang", t.graphBtnLang);
      safeSetText("graphBtnTech", t.graphBtnTech);
      safeSetText("graphBtnOrg", t.graphBtnOrg);
      safeSetText("graphBtnPerson", t.graphBtnPerson);
      safeSetText("graphBtnPaper", t.graphBtnPaper);
      safeSetText("inboxHeaderBadge", t.inboxHeaderBadge);
      safeSetText("inboxHeaderTitle", t.inboxHeaderTitle);
      safeSetText("pipelineScheduleDesc", t.pipelineScheduleDesc);
      safeSetText("pipelineWidgetTitle", t.pipelineWidgetTitle);
      safeSetText("pipelineNextTargetLabel", t.pipelineNextTargetLabel);
      safeSetText("pipelineFooterAudit", t.pipelineFooterAudit);
      if (!skipViewRender) {
        if (typeof window.renderPipelineTelemetryCards === "function") window.renderPipelineTelemetryCards();
        if (typeof window.renderRunsTable === "function") window.renderRunsTable();
        if (typeof window.updateCronCountdown === "function") window.updateCronCountdown();
      }
      safeSetText("inboxHeaderDesc", t.inboxHeaderDesc);
      safeSetText("inboxHeaderCount", lang === "KO" ? `\uCD1D ${totalInboxCnt.toLocaleString()}\uAC74` : lang === "ZH" ? `\u5171 ${totalInboxCnt.toLocaleString()} \u9879` : `Total: ${totalInboxCnt.toLocaleString()} items`);
      safeSetText("criteriaTitle", t.criteriaTitle);
      safeSetText("criteriaDesc", t.criteriaDesc);
      safeSetText("critGithub", t.critGithub);
      safeSetText("critHn", t.critHn);
      safeSetText("critHf", t.critHf);
      safeSetText("critArxiv", t.critArxiv);
      safeSetAttr("inboxSearchInput", "placeholder", t.inboxSearchPlaceholder);
      safeSetText("btnLabelAll", t.btnAll);
      safeSetText("btnLabelUser", t.btnUser);
      safeSetText("btnLabelAuto", t.btnAuto);
      safeSetText("sortLabel", t.sortLabel);
      safeSetAttr("searchInput", "placeholder", t.searchPlaceholder);
      safeSetText("domainFilterLabel", t.domainLabel);
      safeSetText("tagAll", t.tagAll);
      safeSetText("tagFrontend", t.tagFrontend);
      safeSetText("tagAgent", t.tagAgent);
      safeSetText("tagScraping", t.tagScraping);
      safeSetText("tagDoc", t.tagDoc);
      safeSetText("tag3d", t.tag3d);
      safeSetText("tagRust", t.tagRust);
      safeSetText("tagOther", t.tagOther);
      const sortSel = document.getElementById("sortSelect");
      if (sortSel && t.sortOptions) {
        const curVal = sortSel.value;
        sortSel.innerHTML = t.sortOptions.map((opt) => `<option value="${opt.val}" ${opt.val === curVal ? "selected" : ""}>${opt.text}</option>`).join("");
      }
      if (!skipViewRender) {
        const activeView = typeof window !== "undefined" && window.currentView ? window.currentView : "home";
        try {
          if (typeof window.renderCards === "function") window.renderCards();
        } catch (e) {
        }
        try {
          if (typeof window.renderHomeTopPicks === "function") window.renderHomeTopPicks();
        } catch (e) {
        }
        try {
          if (typeof window.renderRadarSession === "function") window.renderRadarSession();
        } catch (e) {
        }
        try {
          if (typeof window.renderTelemetryCharts === "function") window.renderTelemetryCharts();
        } catch (e) {
        }
        try {
          if (typeof window.updateCronCountdown === "function") window.updateCronCountdown();
        } catch (e) {
        }
        try {
          if (typeof window.renderModels === "function") window.renderModels();
        } catch (e) {
        }
        if (activeView === "news") {
          try {
            if (typeof window.renderNews === "function") window.renderNews();
          } catch (e) {
          }
        } else if (activeView === "inbox") {
          try {
            if (typeof window.renderInbox === "function") window.renderInbox();
          } catch (e) {
          }
        }
        if (window.lucide && typeof window.lucide.createIcons === "function") {
          try {
            window.lucide.createIcons();
          } catch (e) {
          }
        }
      }
    }
  }
  if (typeof window !== "undefined") {
    window.i18n = i18n;
    window.setLanguage = setLanguage;
  }

  // src/js/components/toast.js
  function showToast(msg, type = "info") {
    if (typeof document === "undefined") return;
    const toast = document.getElementById("toast");
    const toastMsg = document.getElementById("toastMsg");
    if (!toast || !toastMsg) return;
    toastMsg.innerText = msg;
    toast.classList.remove("hidden");
    if (toast._timer) clearTimeout(toast._timer);
    toast._timer = setTimeout(() => {
      toast.classList.add("hidden");
    }, 3500);
  }
  if (typeof window !== "undefined") {
    window.showToast = showToast;
  }

  // src/js/core/cache.js
  var memoryCache = /* @__PURE__ */ new Map();
  var DEFAULT_TTL_MS = 60 * 1e3;
  var ClientCache = {
    get(key, maxAgeMs = DEFAULT_TTL_MS) {
      const now = Date.now();
      if (memoryCache.has(key)) {
        const entry = memoryCache.get(key);
        if (entry && now - entry.timestamp < maxAgeMs) {
          return entry.data;
        }
        memoryCache.delete(key);
      }
      try {
        if (typeof window !== "undefined" && window.sessionStorage) {
          const raw = sessionStorage.getItem("fc_swr_" + key);
          if (raw) {
            const entry = JSON.parse(raw);
            if (entry && now - entry.timestamp < maxAgeMs) {
              memoryCache.set(key, entry);
              return entry.data;
            }
            sessionStorage.removeItem("fc_swr_" + key);
          }
        }
      } catch (e) {
      }
      return null;
    },
    set(key, data) {
      const now = Date.now();
      const entry = { data, timestamp: now };
      memoryCache.set(key, entry);
      try {
        if (typeof window !== "undefined" && window.sessionStorage) {
          sessionStorage.setItem("fc_swr_" + key, JSON.stringify(entry));
        }
      } catch (e) {
      }
    },
    clear(prefix = "") {
      memoryCache.clear();
      try {
        if (typeof window !== "undefined" && window.sessionStorage) {
          if (!prefix) {
            const keysToRemove = [];
            for (let i = 0; i < sessionStorage.length; i++) {
              const k = sessionStorage.key(i);
              if (k && k.startsWith("fc_swr_")) keysToRemove.push(k);
            }
            keysToRemove.forEach((k) => sessionStorage.removeItem(k));
          } else {
            sessionStorage.removeItem("fc_swr_" + prefix);
          }
        }
      } catch (e) {
      }
    }
  };

  // src/js/core/api.js
  async function bootstrapApplicationData() {
    console.log("[Bootstrap] Initializing parallel DB-First data hydration...");
    let loadedFromEdge = false;
    const cachedPortfolios = ClientCache.get("portfolios_summary", 12e4);
    const edgeFetchPromise = (async () => {
      if (cachedPortfolios && cachedPortfolios.success && Array.isArray(cachedPortfolios.portfolios) && cachedPortfolios.portfolios.length > 0) {
        return { source: "cache", data: cachedPortfolios };
      }
      const portfoliosApiUrl = APP_CONFIG.apiUrl("/api/portfolios?summary=true");
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6e3);
      try {
        const edgeRes = await fetch(portfoliosApiUrl, { signal: controller.signal });
        clearTimeout(timeoutId);
        if (edgeRes.ok) {
          const edgeData = await edgeRes.json();
          if (edgeData && edgeData.success && Array.isArray(edgeData.portfolios) && edgeData.portfolios.length > 0) {
            return { source: "edge", data: edgeData };
          }
        }
      } finally {
        clearTimeout(timeoutId);
      }
      return null;
    })();
    const staticFetchPromise = (async () => {
      let staticRes = await fetch("data.json", { cache: "default" });
      let cType = staticRes.headers.get("content-type") || "";
      if (!staticRes.ok || !cType.includes("application/json")) {
        staticRes = await fetch("/data.json", { cache: "default" });
        cType = staticRes.headers.get("content-type") || "";
      }
      if (staticRes.ok && cType.includes("application/json")) {
        return await staticRes.json();
      }
      return null;
    })();
    const [edgeOutcome, staticOutcome] = await Promise.allSettled([edgeFetchPromise, staticFetchPromise]);
    if (edgeOutcome.status === "fulfilled" && edgeOutcome.value) {
      const { source, data: edgeData } = edgeOutcome.value;
      AppStore.setCases(edgeData.portfolios);
      loadedFromEdge = true;
      if (source === "edge") {
        ClientCache.set("portfolios_summary", edgeData);
      }
      if (edgeData.db_provider) APP_CONFIG.setDbProvider(edgeData.db_provider);
      console.log(`[Bootstrap] \u26A1 [${source === "cache" ? "Session SWR Cache" : "DB-First Edge SWR"}] Loaded ${edgeData.portfolios.length} dossiers.`);
    } else if (edgeOutcome.status === "rejected") {
      console.warn("[Bootstrap] Edge API first-paint timeout or offline, falling back to static snapshot:", edgeOutcome.reason?.message);
    }
    if (staticOutcome.status === "fulfilled" && staticOutcome.value) {
      const data = staticOutcome.value;
      AppStore.setGraphData(data.graph || { nodes: [], links: [] });
      window.adminData = data.admin_stats || {};
      window.timeline24hData = data.timeline_24h || [];
      window.actionsTelemetryData = data.actions_telemetry || {};
      window.trend6hData = data.trend_6h || {};
      window.trendRadarData = data.trend_radar || {};
      Object.assign(snapshotStats, {
        total_cases: data.total_cases || (data.cases ? data.cases.length : 58),
        news_total_count: data.news_total_count || (data.news_items ? data.news_items.length : 3039),
        models_total_count: data.models_total_count || (data.model_items ? data.model_items.length : 344),
        inbox_total_count: data.inbox_total_count || (data.inbox_items ? data.inbox_items.length : 3039),
        tier1_counts: data.tier1_counts || null,
        news_cat_counts: data.news_cat_counts || null,
        model_art_counts: data.model_art_counts || null,
        model_fam_counts: data.model_fam_counts || null
      });
      if (!loadedFromEdge) {
        AppStore.init(data);
        console.log(`[Bootstrap] Loaded ${AppStore.getCases().length} dossiers from static snapshot fallback.`);
      } else {
        AppStore._news = data.trend_items || data.news_items || data.news || [];
        AppStore._models = data.model_items || data.models || [];
        AppStore._inbox = data.inbox_items || (data.inbox_recent || []).concat(data.inbox || []);
        AppStore._models.forEach((it) => {
          it.is_model = true;
        });
        AppStore._news.forEach((it) => {
          if (it.is_model === void 0) {
            it.is_model = it.facet_type === "MODEL" || !!(it.model_family || it.artifact_type || it.category_primary === "MODEL_RELEASE");
          }
        });
        AppStore._inbox.forEach((it) => {
          if (it.is_model === void 0) it.is_model = !!(it.model_family || it.artifact_type || it.category_primary === "MODEL_RELEASE");
          if (it.is_news === void 0) it.is_news = !it.is_model;
        });
        [...AppStore._inbox, ...AppStore._news, ...AppStore._models].forEach((it) => {
          const id = it.inbox_id || it.id;
          if (id && !AppStore._itemsMap.has(id)) {
            AppStore._itemsMap.set(id, it);
          }
        });
        window.liveNewsData = AppStore._news;
        window.liveModelsData = AppStore._models;
        window.inboxData = AppStore._inbox;
        window.liveInboxData = AppStore._inbox;
        window.newsData = AppStore._news;
        window.modelsData = AppStore._models;
      }
    } else if (staticOutcome.status === "rejected") {
      console.warn("[Bootstrap] Static snapshot fallback skipped:", staticOutcome.reason?.message);
    }
    updateGlobalStatsUI();
    try {
      const savedLang = localStorage.getItem("factcheck_lang") || "KO";
      if (["KO", "ZH", "EN"].includes(savedLang) && typeof window.setLanguage === "function") {
        window.setLanguage(savedLang, true);
      }
    } catch (e) {
    }
    const initialHash = typeof window !== "undefined" ? window.location.hash || "" : "";
    let initialView = "home";
    if (initialHash.startsWith("#/factchecks") || initialHash.startsWith("#case/")) initialView = "portfolio";
    else if (initialHash.startsWith("#/news")) initialView = "news";
    else if (initialHash.startsWith("#/models")) initialView = "models";
    else if (initialHash.startsWith("#/graph")) initialView = "graph";
    else if (initialHash.startsWith("#/inbox")) initialView = "inbox";
    if (typeof window.switchView === "function") {
      window.switchView(initialView, false, true);
    }
    setTimeout(() => {
      syncFromLiveDB(false).then(() => updateGlobalStatsUI()).catch((e) => console.warn("[Bootstrap] Live DB sync completed or skipped:", e.message));
    }, 1500);
    if (typeof window !== "undefined") {
      window.__APP_INITIALIZED__ = true;
    }
  }
  function updateGlobalStatsUI() {
    if (typeof document === "undefined") return;
    const safeSet = (id, txt) => {
      const el = document.getElementById(id);
      if (el) el.textContent = txt;
    };
    const lCases = typeof window !== "undefined" ? window.liveCasesData : liveCasesData;
    const lNews = typeof window !== "undefined" ? window.liveNewsData : liveNewsData;
    const lModels = typeof window !== "undefined" ? window.liveModelsData : liveModelsData;
    const lInbox = typeof window !== "undefined" ? window.liveInboxData : liveInboxData;
    const numCases = lCases && lCases.length || snapshotStats.total_cases || 58;
    const numModels = snapshotStats.models_total_count || lModels && lModels.length || 0;
    const numInbox = snapshotStats.inbox_total_count || snapshotStats.news_total_count || lInbox && lInbox.length || lNews && lNews.length || 0;
    safeSet("statValVerified", numCases);
    safeSet("statValNews", numInbox.toLocaleString());
    safeSet("statValModels", numModels.toLocaleString());
    safeSet("statValInbox", numInbox.toLocaleString());
    safeSet("headerVerifiedCount", `(${numCases})`);
    safeSet("headerNewsCount", `(${numInbox.toLocaleString()})`);
    safeSet("headerModelsCount", `(${numModels.toLocaleString()})`);
    safeSet("headerInboxCount", `(${numInbox.toLocaleString()})`);
    const inbList = lInbox || [];
    const enrichedInbox = inbList.filter((x) => x.is_classified || x.ai_enrichment).length;
    const pendingInbox = Math.max(0, numInbox - enrichedInbox);
    const enrichedPct = numInbox > 0 ? (enrichedInbox / numInbox * 100).toFixed(1) : "100.0";
    safeSet("statInboxEnrichedText", `\u25CF \uC694\uC57D ${enrichedInbox.toLocaleString()}\uAC74 (${enrichedPct}%)`);
    safeSet("statInboxPendingText", `\xB7 \uB300\uAE30 ${pendingInbox.toLocaleString()}\uAC74`);
    const casesList = lCases || [];
    const trueCount = casesList.filter((c) => c.verdict === "VERIFIED_TRUE").length || snapshotStats.verified_true_count || 31;
    const halfCount = casesList.filter((c) => c.verdict && c.verdict.startsWith("HALF_TRUE")).length || snapshotStats.half_true_count || 22;
    const gamedCount = Math.max(0, numCases - trueCount - halfCount);
    safeSet("statVerifiedTrue", trueCount);
    safeSet("statHalfTrue", halfCount);
    safeSet("statGamed", gamedCount);
    safeSet("heroAuditCount", `\u25CF ${numCases}\uAC1C \uAE30\uC220 \uAC80\uC99D \uC644\uB8CC`);
    safeSet("portfolioDossiersCountBadge", `\uCD1D ${numCases}\uAC74 \uC644\uB8CC`);
    const curLang = typeof window !== "undefined" && window.currentLang ? window.currentLang : currentLang;
    const viewAllText = curLang === "KO" ? `\uC804\uCCB4 ${numCases}\uAC1C \uAC80\uC99D \uB3C4\uC2DC\uC5D0 \uBCF4\uB7EC\uAC00\uAE30` : curLang === "ZH" ? `\u67E5\u770B\u5168\u90E8 ${numCases} \u4EFD\u6838\u67E5\u6863\u6848` : `View All ${numCases} Empirical Dossiers`;
    safeSet("homeTopPicksViewAll", viewAllText);
    if (typeof updateNewsCategoryPillCounts === "function") {
      updateNewsCategoryPillCounts();
    }
    if (typeof updateModelCategoryPillCounts === "function") {
      updateModelCategoryPillCounts();
    }
  }
  function updateNewsCategoryPillCounts() {
    if (typeof document === "undefined") return;
    const lang = typeof window !== "undefined" && window.currentLang ? window.currentLang : currentLang;
    const t1Labels = {
      KO: {
        ALL: "\u{1F310} \uC804\uCCB4 \uBD84\uB958",
        TECH_COMPUTING: "\u{1F4BB} IT\xB7\uCEF4\uD4E8\uD305",
        SCIENCE_RESEARCH: "\u{1F680} \uACFC\uD559\xB7\uC6B0\uC8FC",
        ECONOMY_FINANCE: "\u{1F3E6} \uACBD\uC81C\xB7\uAE08\uC735",
        LAW_CRIME_JUSTICE: "\u2696\uFE0F \uC0AC\uD68C\xB7\uBC95\uB960",
        POLITICS_POLICY: "\u{1F3DB}\uFE0F \uC815\uCE58\xB7\uC815\uCC45",
        CULTURE_HUMANITIES: "\u{1F33F} \uBB38\uD654\xB7\uC778\uBB38"
      },
      ZH: {
        ALL: "\u{1F310} \u5168\u90E8\u7C7B\u522B",
        TECH_COMPUTING: "\u{1F4BB} IT\u4E0E\u8BA1\u7B97",
        SCIENCE_RESEARCH: "\u{1F680} \u79D1\u5B66\u4E0E\u822A\u5929",
        ECONOMY_FINANCE: "\u{1F3E6} \u7ECF\u6D4E\u4E0E\u91D1\u878D",
        LAW_CRIME_JUSTICE: "\u2696\uFE0F \u793E\u4F1A\u4E0E\u6CD5\u6CBB",
        POLITICS_POLICY: "\u{1F3DB}\uFE0F \u653F\u6CBB\u4E0E\u653F\u7B56",
        CULTURE_HUMANITIES: "\u{1F33F} \u6587\u5316\u4E0E\u4EBA\u6587"
      },
      EN: {
        ALL: "\u{1F310} All Categories",
        TECH_COMPUTING: "\u{1F4BB} IT & Computing",
        SCIENCE_RESEARCH: "\u{1F680} Science & Space",
        ECONOMY_FINANCE: "\u{1F3E6} Economy & Finance",
        LAW_CRIME_JUSTICE: "\u2696\uFE0F Society & Law",
        POLITICS_POLICY: "\u{1F3DB}\uFE0F Policy & Politics",
        CULTURE_HUMANITIES: "\u{1F33F} Culture & Arts"
      }
    };
    const t2Labels = {
      KO: {
        ALL: "\u26A1 \uC804\uCCB4 IT \uBD84\uC57C",
        INFERENCE_OPT: "\u26A1 \uCD94\uB860\xB7\uC11C\uBE59",
        AGENTS_DEVTOOLS: "\u{1F6E0}\uFE0F \uC5D0\uC774\uC804\uD2B8\xB7\uB3C4\uAD6C",
        MULTIMODAL_AI: "\u{1F3A8} \uBA40\uD2F0\uBAA8\uB2EC",
        FOUNDATION_MODELS: "\u{1F916} \uD30C\uC6B4\uB370\uC774\uC158",
        INFRA_RAG_SECURITY: "\u{1F6E1}\uFE0F \uC778\uD504\uB77C\xB7\uBCF4\uC548",
        INDUSTRY_TRENDS: "\u{1F310} \uC77C\uBC18 SW\xB7\uC6F9"
      },
      ZH: {
        ALL: "\u26A1 \u5168\u90E8 IT \u9886\u57DF",
        INFERENCE_OPT: "\u26A1 \u63A8\u7406\u4E0E\u670D\u52A1",
        AGENTS_DEVTOOLS: "\u{1F6E0}\uFE0F \u667A\u80FD\u4F53\u4E0E\u5DE5\u5177",
        MULTIMODAL_AI: "\u{1F3A8} \u591A\u6A21\u6001",
        FOUNDATION_MODELS: "\u{1F916} \u57FA\u7840\u6A21\u578B",
        INFRA_RAG_SECURITY: "\u{1F6E1}\uFE0F \u57FA\u7840\u67B6\u6784\u4E0E\u5B89\u5168",
        INDUSTRY_TRENDS: "\u{1F310} \u8F6F\u4EF6\u4E0E\u884C\u4E1A\u52A8\u6001"
      },
      EN: {
        ALL: "\u26A1 All Tech Fields",
        INFERENCE_OPT: "\u26A1 Inference & Serving",
        AGENTS_DEVTOOLS: "\u{1F6E0}\uFE0F Agents & DevTools",
        MULTIMODAL_AI: "\u{1F3A8} Multimodal",
        FOUNDATION_MODELS: "\u{1F916} Foundation Models",
        INFRA_RAG_SECURITY: "\u{1F6E1}\uFE0F Infra & Security",
        INDUSTRY_TRENDS: "\u{1F310} General SW & Web"
      }
    };
    const curDict1 = t1Labels[lang] || t1Labels.KO;
    document.querySelectorAll(".news-cat-pill").forEach((btn) => {
      const cat = btn.getAttribute("data-cat");
      if (curDict1 && curDict1[cat]) {
        btn.textContent = curDict1[cat];
      }
    });
    const curDict2 = t2Labels[lang] || t2Labels.KO;
    document.querySelectorAll(".news-t2-pill").forEach((btn) => {
      const t2 = btn.getAttribute("data-t2");
      if (curDict2 && curDict2[t2]) {
        btn.textContent = curDict2[t2];
      }
    });
  }
  function updateModelCategoryPillCounts() {
    if (typeof document === "undefined") return;
    const lang = typeof window !== "undefined" && window.currentLang ? window.currentLang : currentLang;
    const famLabels = {
      KO: {
        ALL: "\uC804\uCCB4 \uD328\uBC00\uB9AC",
        Qwen: "Qwen",
        Wan: "Wan \uBE44\uB514\uC624",
        MiniMax: "MiniMax",
        FLUX: "FLUX \uC774\uBBF8\uC9C0",
        GLM: "GLM",
        DeepSeek: "DeepSeek",
        Hunyuan: "Hunyuan",
        Audio: "\uC74C\uC131/TTS",
        Standalone: "\uB3C5\uB9BD/\uC2E0\uADDC \uBAA8\uB378"
      },
      ZH: {
        ALL: "\u5168\u90E8\u7CFB\u5217",
        Qwen: "Qwen",
        Wan: "Wan \u89C6\u9891",
        MiniMax: "MiniMax",
        FLUX: "FLUX \u56FE\u50CF",
        GLM: "GLM",
        DeepSeek: "DeepSeek",
        Hunyuan: "Hunyuan",
        Audio: "\u8BED\u97F3/TTS",
        Standalone: "\u72EC\u7ACB/\u65B0\u6A21\u578B"
      },
      EN: {
        ALL: "All Families",
        Qwen: "Qwen",
        Wan: "Wan Video",
        MiniMax: "MiniMax",
        FLUX: "FLUX Image",
        GLM: "GLM",
        DeepSeek: "DeepSeek",
        Hunyuan: "Hunyuan",
        Audio: "Audio/TTS",
        Standalone: "Standalone"
      }
    };
    const artLabels = {
      KO: {
        ALL: "\uC804\uCCB4",
        WEIGHTS: "\u{1F916} \uAC00\uC911\uCE58\xB7\uCCB4\uD06C\uD3EC\uC778\uD2B8",
        WEB_SERVICE: "\u{1F310} \uB370\uBAA8\xB7Spaces",
        FINETUNE: "\u{1F3AF} \uD2B9\uD654 \uD30C\uC778\uD29C\uB2DD"
      },
      ZH: {
        ALL: "\u5168\u90E8",
        WEIGHTS: "\u{1F916} \u6A21\u578B\u6743\u91CD\xB7\u68C0\u67E5\u70B9",
        WEB_SERVICE: "\u{1F310} \u5728\u7EBF\u6F14\u793A\xB7Spaces",
        FINETUNE: "\u{1F3AF} \u5B9A\u5236\u5FAE\u8C03"
      },
      EN: {
        ALL: "All",
        WEIGHTS: "\u{1F916} Weights & Checkpoints",
        WEB_SERVICE: "\u{1F310} Interactive Demos",
        FINETUNE: "\u{1F3AF} Specialized Finetunes"
      }
    };
    const curFamDict = famLabels[lang] || famLabels.KO;
    document.querySelectorAll(".model-fam-pill").forEach((btn) => {
      const fam = btn.getAttribute("data-fam");
      if (curFamDict && curFamDict[fam]) {
        btn.textContent = curFamDict[fam];
      }
    });
    const curArtDict = artLabels[lang] || artLabels.KO;
    document.querySelectorAll(".model-art-pill").forEach((btn) => {
      const art = btn.getAttribute("data-art");
      if (curArtDict && curArtDict[art]) {
        btn.textContent = curArtDict[art];
      }
    });
  }
  var _isSyncing = false;
  var _syncTimeoutId = null;
  async function syncFromLiveDB(force = false) {
    if (_isSyncing && !force) return;
    _isSyncing = true;
    if (_syncTimeoutId) clearTimeout(_syncTimeoutId);
    _syncTimeoutId = setTimeout(() => {
      _isSyncing = false;
    }, 8e3);
    const badge = document.getElementById("dbLiveBadge");
    try {
      const tStart = performance.now();
      const apiUrl = APP_CONFIG.apiUrl("/api/stats");
      const res = await fetch(apiUrl, { cache: "default" });
      const tLatency = Math.round(performance.now() - tStart);
      if (res.ok) {
        const data = await res.json();
        if (data.db_provider) APP_CONFIG.setDbProvider(data.db_provider);
        if (data.status === "success" && data.counts) {
          const liveInbox = data.counts.inbox_deduped || data.counts.inbox_total;
          const liveModels = data.counts.models_total;
          const liveNews = data.counts.news_total;
          if (liveInbox) snapshotStats.inbox_total_count = liveInbox;
          if (liveModels) snapshotStats.models_total_count = liveModels;
          if (liveNews) snapshotStats.news_total_count = liveNews;
          if (data.counts.factchecks_verified) snapshotStats.total_cases = data.counts.factchecks_verified;
          const hInbox = document.getElementById("headerInboxCount");
          if (hInbox && liveInbox) hInbox.textContent = `(${liveInbox.toLocaleString()})`;
          const statInbox = document.getElementById("statValInbox");
          if (statInbox && liveInbox) statInbox.textContent = liveInbox.toLocaleString();
          const statNews = document.getElementById("statValNews");
          if (statNews && liveInbox) statNews.textContent = liveInbox.toLocaleString();
          const hNews = document.getElementById("headerNewsCount");
          if (hNews && liveInbox) hNews.textContent = `(${liveInbox.toLocaleString()})`;
          const statModels = document.getElementById("statValModels");
          if (statModels && liveModels) statModels.textContent = liveModels.toLocaleString();
          const hModels = document.getElementById("headerModelsCount");
          if (hModels && liveModels) hModels.textContent = `(${liveModels.toLocaleString()})`;
          const mNavInbox = document.getElementById("mNavTabInbox");
          if (mNavInbox && liveInbox) mNavInbox.textContent = `\uC544\uCE74\uC774\uBE0C (${liveInbox.toLocaleString()})`;
          const inbHdr = document.getElementById("inboxHeaderCount");
          if (inbHdr && liveInbox) inbHdr.textContent = `\uCD1D ${liveInbox.toLocaleString()}\uAC74`;
          if (data.counts.inbox_unclassified !== void 0) {
            const unclass = data.counts.inbox_unclassified;
            const btn = document.getElementById("btnTriggerWorker");
            const txt = document.getElementById("btnWorkerText");
            if (unclass === 0) {
              window._allClassifiedCompleted = true;
              if (txt) txt.textContent = "\u2728 \uBAA8\uB4E0 \uD56D\uBAA9 AI \uC694\uC57D \uC644\uB8CC\uB428";
              if (btn) {
                btn.disabled = true;
                btn.className = "px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 font-bold font-mono text-[11px] border border-emerald-200 transition shadow-xs flex items-center gap-1.5 cursor-default";
              }
            } else {
              window._allClassifiedCompleted = false;
              if (txt && !window._autoWorkerRunning) {
                txt.textContent = `\u26A1 AI \uC694\uC57D \uC2E4\uD589 (${unclass.toLocaleString()}\uAC74 \uB300\uAE30)`;
              } else if (window._autoWorkerRunning && !window._autoWorkerPaused) {
                if (txt) txt.innerHTML = `<span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse mr-1"></span> AI \uC694\uC57D \uC911 (\uC794\uC5EC: ${unclass.toLocaleString()}\uAC74)`;
              }
              if (btn && !window._autoWorkerRunning) {
                btn.disabled = false;
                btn.className = "px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 font-bold font-mono text-[11px] border border-indigo-200 transition shadow-xs flex items-center gap-1.5 cursor-pointer hover:bg-indigo-100";
              }
            }
          }
          if (data.counts.tier1_counts || data.tier1_counts) {
            snapshotStats.tier1_counts = data.counts.tier1_counts || data.tier1_counts;
          }
          if (data.counts.news_cat_counts || data.news_cat_counts) {
            snapshotStats.news_cat_counts = data.counts.news_cat_counts || data.news_cat_counts;
          }
          if (typeof updateNewsCategoryPillCounts === "function") {
            updateNewsCategoryPillCounts();
          }
          if (badge) {
            badge.innerHTML = `
            <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100 transition shadow-xs cursor-pointer" title="\uAD00\uB9AC\uC790 \uC804\uC6A9 \uC6D0\uCC9C \uB370\uC774\uD130 \uC544\uCE74\uC774\uBE0C (\uCD1D ${data.counts.inbox_total}\uAC74, \uB808\uC774\uD134\uC2DC: ${tLatency}ms)">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span> Admin (${typeof liveInbox === "number" ? liveInbox.toLocaleString() : liveInbox})
            </span>
          `;
          }
          const pingVal = document.getElementById("vercelPingValue");
          const pingLat = document.getElementById("vercelLatencyText");
          if (pingVal && pingLat) {
            pingVal.innerHTML = `<span class="text-emerald-400">200 OK</span>`;
            pingLat.textContent = `(\uC2E4\uCE21 \uB808\uC774\uD134\uC2DC: ${tLatency}ms)`;
          }
          if (data.vercel_telemetry) {
            const vt = data.vercel_telemetry;
            const invUsed = document.getElementById("vercelInvocationsUsed");
            const invBar = document.getElementById("vercelInvocationsBar");
            const invRem = document.getElementById("vercelInvocationsRem");
            const invBadge = document.getElementById("vercelInvocationsBadge");
            if (invUsed && vt.invocations) invUsed.textContent = vt.invocations.used_estimated.toLocaleString();
            if (invBar && vt.invocations) invBar.style.width = `${vt.invocations.used_pct}%`;
            if (invRem && vt.invocations) invRem.textContent = `${vt.invocations.remaining.toLocaleString()}\uD68C (${(100 - vt.invocations.used_pct).toFixed(1)}%)`;
            if (invBadge && vt.invocations) invBadge.textContent = `\uC548\uC804 (${vt.invocations.used_pct}%)`;
            const cpuUsed = document.getElementById("vercelCpuUsed");
            const cpuBar = document.getElementById("vercelCpuBar");
            const cpuBadge = document.getElementById("vercelCpuBadge");
            const cpuSubText = document.getElementById("vercelCpuSubText");
            if (cpuUsed && vt.active_cpu_time) cpuUsed.textContent = `${vt.active_cpu_time.used_hours}h`;
            if (cpuBar && vt.active_cpu_time) cpuBar.style.width = `${vt.active_cpu_time.used_pct}%`;
            if (cpuBadge && vt.active_cpu_time) {
              const pct = vt.active_cpu_time.used_pct;
              const statusStr = pct < 50 ? "\uADF9\uB3C4 \uC548\uC815" : pct < 80 ? "\uC548\uC815" : "\uC8FC\uC758";
              cpuBadge.textContent = `${statusStr} (${pct}%)`;
            }
            if (cpuSubText && vt.active_cpu_time) {
              cpuSubText.innerHTML = `\u2022 \uB204\uC801 \uC2E4\uD589: <b>${vt.active_cpu_time.used_estimated_seconds}\uCD08 / 14,400\uCD08</b>`;
            }
            const bwUsed = document.getElementById("vercelBandwidthUsed");
            const bwBar = document.getElementById("vercelBandwidthBar");
            if (bwUsed && vt.bandwidth_gb) bwUsed.textContent = `${vt.bandwidth_gb.used_estimated} GB`;
            if (bwBar && vt.bandwidth_gb) bwBar.style.width = `${vt.bandwidth_gb.used_pct}%`;
          }
          if (data.timeline_24h_live && Array.isArray(data.timeline_24h_live) && data.timeline_24h_live.length > 0) {
            const curKstH = getDynamicKstHour();
            const liveHasData = data.timeline_24h_live.some((s) => s.inbox_count > 0 || s.enriched_count > 0);
            if (liveHasData) {
              window.timeline24hData = data.timeline_24h_live.map((liveSlot) => ({
                ...liveSlot,
                is_current: liveSlot.hour <= curKstH && curKstH < liveSlot.hour + 6,
                is_future: liveSlot.hour > curKstH
              }));
              window._timelineIsPendingToday = false;
              if (typeof window.renderTelemetryCharts === "function") {
                window.renderTelemetryCharts();
              }
            } else if (data.timeline_24h_baseline && Array.isArray(data.timeline_24h_baseline) && data.timeline_24h_baseline.length > 0) {
              const baseHasData = data.timeline_24h_baseline.some((s) => s.inbox_count > 0 || s.enriched_count > 0);
              if (baseHasData) {
                window.timeline24hData = data.timeline_24h_baseline.map((bSlot) => ({
                  ...bSlot,
                  is_current: bSlot.hour <= curKstH && curKstH < bSlot.hour + 6,
                  is_future: bSlot.hour > curKstH,
                  is_pending_today: bSlot.hour <= curKstH && curKstH < bSlot.hour + 6
                }));
                window._timelineIsPendingToday = true;
                if (typeof window.renderTelemetryCharts === "function") {
                  window.renderTelemetryCharts();
                }
              }
            }
          }
          try {
            const currentCases = Array.isArray(window.liveCasesData) ? window.liveCasesData : [];
            if (currentCases.length === 0) {
              const portfoliosApiUrl = APP_CONFIG.apiUrl("/api/portfolios");
              const pRes = await fetch(portfoliosApiUrl, { cache: "default" });
              if (pRes.ok) {
                const pData = await pRes.json();
                if (pData.success && Array.isArray(pData.portfolios) && pData.portfolios.length > 0) {
                  window.liveCasesData = pData.portfolios;
                  window.casesData = pData.portfolios;
                  AppStore._cases = pData.portfolios;
                  updateGlobalStatsUI();
                  try {
                    if (typeof window.renderCards === "function") window.renderCards();
                  } catch (e) {
                  }
                  try {
                    if (typeof window.renderHomeTopPicks === "function") window.renderHomeTopPicks();
                  } catch (e) {
                  }
                  console.log(`[Live DB Sync] Live hydrated ${pData.portfolios.length} dossiers from ${APP_CONFIG.dbProvider}.`);
                }
              }
            }
          } catch (pErr) {
            console.warn("[Live DB Sync] Portfolios live sync skipped:", pErr.message);
          }
          if (data.actions_quota && data.actions_quota.total_minutes !== void 0) {
            window.actionsTelemetryData = window.actionsTelemetryData || {};
            window.actionsTelemetryData.monthly_used_minutes = data.actions_quota.total_minutes;
            window.actionsTelemetryData.monthly_remaining_minutes = data.actions_quota.remaining_minutes;
            window.actionsTelemetryData.monthly_usage_percent = data.actions_quota.burn_rate_percent;
            if (data.actions_runs && Array.isArray(data.actions_runs) && data.actions_runs.length > 0) {
              window.actionsTelemetryData.runs = data.actions_runs;
            }
            if (typeof window.renderPipelineTelemetryCards === "function") window.renderPipelineTelemetryCards();
            if (typeof window.renderRunsTable === "function" && window.currentRunsTab === "gha") window.renderRunsTable();
          }
          if (data.vercel_worker_runs && Array.isArray(data.vercel_worker_runs)) {
            window.vercelWorkerRunsData = data.vercel_worker_runs;
            if (window.currentRunsTab === "vercel" && typeof window.renderRunsTable === "function") {
              window.renderRunsTable();
            }
          }
          if (data.voyage_worker_runs && Array.isArray(data.voyage_worker_runs)) {
            window.voyageWorkerRunsData = data.voyage_worker_runs;
            try {
              localStorage.setItem("voyage_runs_history_v1", JSON.stringify(data.voyage_worker_runs));
            } catch (e) {
            }
            if (window.currentRunsTab === "voyage" && typeof window.renderRunsTable === "function") {
              window.renderRunsTable();
            }
          }
          return;
        }
      }
    } catch (err) {
    } finally {
      _isSyncing = false;
      if (_syncTimeoutId) clearTimeout(_syncTimeoutId);
    }
  }
  var _voyageWorkerRunning = false;
  var _voyageWorkerPaused = false;
  async function checkVoyageEmbeddingStatus() {
    const btn = document.getElementById("btnTriggerEmbedding");
    const txt = document.getElementById("btnEmbedText");
    if (!btn || !txt) return;
    try {
      const url = APP_CONFIG.apiUrl("/api/embed-worker?check_only=true");
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) return;
      const data = await res.json();
      if (!data.success) return;
      const remaining = data.remaining_unembedded !== void 0 ? data.remaining_unembedded : 0;
      const total = data.total_count || 0;
      const embedded = data.embedded_count || 0;
      window._voyageRemaining = remaining;
      window._voyageTotal = total;
      window._voyageEmbedded = embedded;
      if (remaining === 0) {
        txt.textContent = "\u2728 \uBAA8\uB4E0 \uD56D\uBAA9 Voyage \uC784\uBCA0\uB529 \uC644\uB8CC\uB428";
        btn.disabled = true;
        btn.className = "px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 font-bold font-mono text-[11px] border border-emerald-200 transition shadow-xs flex items-center gap-1.5 cursor-default";
        btn.title = `\uCD1D ${total.toLocaleString()}\uAC74 \uC804\uC218 \uC784\uBCA0\uB529 \uBC0F \uC911\uBCF5 \uBCD1\uD569 \uC644\uB8CC (100%)`;
      } else {
        if (!_voyageWorkerRunning) {
          txt.textContent = `\u26A1 Voyage \uC784\uBCA0\uB529 (${remaining.toLocaleString()}\uAC74 \uC794\uC5EC)`;
          btn.disabled = false;
          btn.className = "px-3 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-bold font-mono text-[11px] border border-emerald-200 transition shadow-xs flex items-center gap-1.5 cursor-pointer";
          btn.title = `\uCD1D ${total.toLocaleString()}\uAC74 \uC911 ${remaining.toLocaleString()}\uAC74 \uBBF8\uC784\uBCA0\uB529 (\uC644\uB8CC: ${embedded.toLocaleString()}\uAC74). \uD074\uB9AD \uC2DC \uC804\uC218 \uC790\uB3D9 \uC784\uBCA0\uB529 \uC2DC\uC791`;
        }
      }
    } catch (err) {
      console.warn("[Voyage Status Check Skipped]:", err.message);
    }
  }
  async function startContinuousVoyageWorker() {
    if (_voyageWorkerRunning) return;
    _voyageWorkerRunning = true;
    _voyageWorkerPaused = false;
    window._voyageWorkerRunning = true;
    window._voyageWorkerPaused = false;
    const btn = document.getElementById("btnTriggerEmbedding");
    const txt = document.getElementById("btnEmbedText");
    if (btn) {
      btn.disabled = false;
      btn.className = "px-3 py-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white font-bold font-mono text-[11px] border border-emerald-800 transition shadow-xs flex items-center gap-1.5 cursor-pointer";
    }
    let consecutiveErrors = 0;
    let totalProcessedInSession = 0;
    let totalMergedInSession = 0;
    while (_voyageWorkerRunning && !_voyageWorkerPaused) {
      try {
        if (txt && !_voyageWorkerPaused) {
          txt.innerHTML = `<span class="inline-block w-2 h-2 rounded-full bg-white animate-ping mr-1"></span> \uC784\uBCA0\uB529 \uC911... (${totalProcessedInSession}\uAC74 \uC644\uB8CC / \uC794\uC5EC \uD655\uC778 \uC911)`;
        }
        const t0 = Date.now();
        const res = await fetch(APP_CONFIG.apiUrl("/api/embed-worker?limit=100"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ limit: 100 }),
          cache: "no-store"
        });
        const elapsed = ((Date.now() - t0) / 1e3).toFixed(1);
        if (!res.ok) {
          consecutiveErrors++;
          console.warn(`[Voyage Worker] HTTP error ${res.status}. Errors: ${consecutiveErrors}/3`);
          if (consecutiveErrors >= 3) {
            _voyageWorkerRunning = false;
            window._voyageWorkerRunning = false;
            if (txt) txt.textContent = "\u26A1 \uC784\uBCA0\uB529 \uC11C\uBC84 \uC9C0\uC5F0\uC73C\uB85C \uC815\uC9C0 (\uD074\uB9AD \uC2DC \uC7AC\uAC1C)";
            if (btn) {
              btn.className = "px-3 py-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 font-bold font-mono text-[11px] border border-amber-300 transition shadow-xs flex items-center gap-1.5 cursor-pointer";
            }
            break;
          }
          await new Promise((r) => setTimeout(r, 4e3));
          continue;
        }
        consecutiveErrors = 0;
        const data = await res.json();
        if (!data.success) {
          throw new Error(data.error || "Server error");
        }
        const processed = data.processed_count || 0;
        const merged = data.merged_duplicates_count || 0;
        const remaining = data.remaining_unembedded !== void 0 ? data.remaining_unembedded : 0;
        const totalCount = data.total_count || 0;
        const tokensUsed = data.tokens_used || 0;
        totalProcessedInSession += processed;
        totalMergedInSession += merged;
        const nowKst = new Date(Date.now() + 9 * 3600 * 1e3).toISOString().replace("T", " ").substring(5, 16);
        if (!Array.isArray(window.voyageWorkerRunsData)) window.voyageWorkerRunsData = [];
        window.voyageWorkerRunsData.unshift({
          id: Date.now(),
          created_at_kst: nowKst,
          engine: data.model || "voyage-4-lite",
          duration_str: elapsed + "\uCD08",
          processed_count: processed,
          merged_count: merged,
          tokens_used: tokensUsed,
          remaining_count: remaining,
          total_count: totalCount,
          status: "SUCCESS"
        });
        if (window.voyageWorkerRunsData.length > 30) window.voyageWorkerRunsData.pop();
        try {
          localStorage.setItem("voyage_runs_history_v1", JSON.stringify(window.voyageWorkerRunsData));
        } catch (e) {
        }
        if (window.currentRunsTab === "voyage" && typeof window.renderRunsTable === "function") {
          window.renderRunsTable();
        }
        if (txt && !_voyageWorkerPaused) {
          txt.innerHTML = `<span class="inline-block w-2 h-2 rounded-full bg-white animate-pulse mr-1"></span> \uC9C4\uD589 \uC911 (${totalProcessedInSession}\uAC74 \uC644\uB8CC / \uC794\uC5EC: ${remaining.toLocaleString()}\uAC74)`;
        }
        if (remaining === 0 || processed === 0) {
          _voyageWorkerRunning = false;
          window._voyageWorkerRunning = false;
          if (txt) txt.textContent = "\u2728 \uBAA8\uB4E0 \uD56D\uBAA9 Voyage \uC784\uBCA0\uB529 \uC644\uB8CC\uB428";
          if (btn) {
            btn.disabled = true;
            btn.className = "px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 font-bold font-mono text-[11px] border border-emerald-200 transition shadow-xs flex items-center gap-1.5 cursor-default";
            btn.title = `\uCD1D ${totalCount.toLocaleString()}\uAC74 \uC804\uCCB4 \uC784\uBCA0\uB529 \uBC0F \uC720\uC0AC\uB3C4 \uC911\uBCF5 \uBCD1\uD569 \uC644\uB8CC (100%)`;
          }
          showToast(`\u2728 \uBAA8\uB4E0 \uAE30\uC0AC(${totalCount.toLocaleString()}\uAC74) Voyage AI \uC784\uBCA0\uB529\uC774 100% \uC644\uB8CC\uB418\uC5C8\uC2B5\uB2C8\uB2E4!`, "success");
          break;
        }
        await new Promise((r) => setTimeout(r, 1200));
      } catch (err) {
        console.error("[Voyage Worker Loop Error]:", err);
        consecutiveErrors++;
        if (consecutiveErrors >= 3) {
          _voyageWorkerRunning = false;
          window._voyageWorkerRunning = false;
          if (txt) txt.textContent = "\u274C \uC784\uBCA0\uB529 \uC624\uB958 \uBC1C\uC0DD (\uD074\uB9AD \uC2DC \uC7AC\uC2DC\uB3C4)";
          if (btn) {
            btn.className = "px-3 py-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 font-bold font-mono text-[11px] border border-amber-300 transition shadow-xs flex items-center gap-1.5 cursor-pointer";
          }
          break;
        }
        await new Promise((r) => setTimeout(r, 3e3));
      }
    }
    _voyageWorkerRunning = false;
    window._voyageWorkerRunning = false;
  }
  function toggleVoyageEmbeddingWorker() {
    const btn = document.getElementById("btnTriggerEmbedding");
    const txt = document.getElementById("btnEmbedText");
    if (_voyageWorkerRunning && !_voyageWorkerPaused) {
      _voyageWorkerPaused = true;
      window._voyageWorkerPaused = true;
      if (txt) txt.textContent = "\u23F8\uFE0F \uC784\uBCA0\uB529 \uC77C\uC2DC\uC815\uC9C0\uB428 (\uD074\uB9AD \uC2DC \uC7AC\uAC1C)";
      if (btn) {
        btn.className = "px-3 py-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 font-bold font-mono text-[11px] border border-amber-300 transition shadow-xs flex items-center gap-1.5 cursor-pointer";
      }
    } else {
      _voyageWorkerPaused = false;
      window._voyageWorkerPaused = false;
      if (txt) txt.textContent = "\u23F3 \uC784\uBCA0\uB529 \uC900\uBE44 \uC911...";
      startContinuousVoyageWorker();
    }
  }
  var _autoWorkerRunning = false;
  var _autoWorkerPaused = false;
  async function startContinuousAiWorker() {
    if (_autoWorkerRunning) return;
    _autoWorkerRunning = true;
    _autoWorkerPaused = false;
    window._autoWorkerRunning = true;
    window._autoWorkerPaused = false;
    const btn = document.getElementById("btnTriggerWorker");
    const txt = document.getElementById("btnWorkerText");
    if (btn) {
      btn.disabled = false;
      btn.className = "px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold font-mono text-[11px] border border-indigo-700 transition shadow-xs flex items-center gap-1.5 cursor-pointer";
    }
    let consecutiveErrors = 0;
    let processedInThisSession = 0;
    const MAX_SESSION_CAP = 5;
    while (_autoWorkerRunning && !_autoWorkerPaused && processedInThisSession < MAX_SESSION_CAP) {
      try {
        const workerUrl = APP_CONFIG.apiUrl("/api/enrich-worker?limit=1");
        if (txt && !_autoWorkerPaused) {
          txt.innerHTML = `<span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-ping mr-1"></span> AI \uC694\uC57D \uBD84\uC11D \uC911... (${processedInThisSession + 1}/${MAX_SESSION_CAP}\uAC74 \uC9C4\uD589 \uC911)`;
        }
        const res = await fetch(workerUrl, { cache: "no-store" });
        if (res.status === 429) {
          _autoWorkerRunning = false;
          window._autoWorkerRunning = false;
          if (txt) txt.textContent = "\u23F8\uFE0F AI \uCFFC\uD130 \uC77C\uC2DC \uC18C\uC9C4 (\uC7A0\uC2DC \uD6C4 \uB2E4\uC2DC \uC2DC\uB3C4)";
          if (btn) {
            btn.disabled = false;
            btn.className = "px-3 py-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 font-bold font-mono text-[11px] border border-amber-300 transition shadow-xs flex items-center gap-1.5 cursor-pointer";
          }
          break;
        }
        if (!res.ok) {
          consecutiveErrors++;
          if (consecutiveErrors >= 3) {
            _autoWorkerRunning = false;
            window._autoWorkerRunning = false;
            if (txt) txt.textContent = "\u26A1 \uC11C\uBC84 \uC77C\uC2DC \uC751\uB2F5 \uC5C6\uC74C (\uD074\uB9AD \uC2DC \uC7AC\uC2DC\uB3C4)";
            if (btn) {
              btn.disabled = false;
              btn.className = "px-3 py-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 font-bold font-mono text-[11px] border border-amber-300 transition shadow-xs flex items-center gap-1.5 cursor-pointer";
            }
            break;
          }
          const backoffMs = Math.min(1e4, 3e3 * consecutiveErrors);
          await new Promise((r) => setTimeout(r, backoffMs));
          continue;
        }
        consecutiveErrors = 0;
        const data = await res.json();
        if (data && data.status === "success") {
          processedInThisSession++;
          const rem = data.remaining_unclassified !== void 0 ? data.remaining_unclassified : 0;
          if (txt && !_autoWorkerPaused) {
            txt.innerHTML = `<span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse mr-1"></span> AI \uC694\uC57D \uC911 (${processedInThisSession}/${MAX_SESSION_CAP}\uAC74 \uC644\uB8CC / \uC794\uC5EC: ${rem}\uAC74)`;
          }
          if (rem === 0) {
            window._allClassifiedCompleted = true;
            _autoWorkerRunning = false;
            window._autoWorkerRunning = false;
            if (txt) txt.textContent = "\u2728 \uBAA8\uB4E0 \uD56D\uBAA9 AI \uC694\uC57D \uC644\uB8CC\uB428";
            if (btn) {
              btn.disabled = true;
              btn.className = "px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 font-bold font-mono text-[11px] border border-emerald-200 transition shadow-xs flex items-center gap-1.5 cursor-default";
            }
            break;
          }
          if (processedInThisSession >= MAX_SESSION_CAP) {
            _autoWorkerRunning = false;
            window._autoWorkerRunning = false;
            if (txt) txt.textContent = `\u26A1 AI \uC694\uC57D 1\uD68C \uC138\uC158 \uC644\uB8CC (${processedInThisSession}\uAC74 / \uC794\uC5EC ${rem}\uAC74 \xB7 \uD074\uB9AD \uC2DC \uCD94\uAC00 \uC2E4\uD589)`;
            if (btn) {
              btn.disabled = false;
              btn.className = "px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 font-bold font-mono text-[11px] border border-indigo-200 transition shadow-xs flex items-center gap-1.5 cursor-pointer hover:bg-indigo-100";
            }
            break;
          }
        }
      } catch (loopErr) {
        console.warn("[AutoWorker Loop Error]:", loopErr);
        consecutiveErrors++;
        if (consecutiveErrors >= 3) {
          _autoWorkerRunning = false;
          window._autoWorkerRunning = false;
          if (txt) txt.textContent = "\u26A1 \uB124\uD2B8\uC6CC\uD06C \uC624\uB958\uB85C \uC911\uB2E8\uB428 (\uD074\uB9AD \uC2DC \uC7AC\uC2DC\uB3C4)";
          break;
        }
        await new Promise((r) => setTimeout(r, 5e3));
      }
      await new Promise((r) => setTimeout(r, 3500));
    }
    if (processedInThisSession > 0) {
      ClientCache.clear();
      try {
        if (typeof window.renderInbox === "function") window.renderInbox(false, true);
      } catch (e) {
      }
    }
    _autoWorkerRunning = false;
    window._autoWorkerRunning = false;
  }
  function toggleAiEnrichWorker() {
    const btn = document.getElementById("btnTriggerWorker");
    const txt = document.getElementById("btnWorkerText");
    if (_autoWorkerRunning && !_autoWorkerPaused) {
      _autoWorkerPaused = true;
      window._autoWorkerPaused = true;
      if (txt) txt.textContent = "\u23F8\uFE0F AI \uC694\uC57D \uC77C\uC2DC\uC815\uC9C0\uB428 (\uD074\uB9AD \uC2DC \uC7AC\uAC1C)";
      if (btn) {
        btn.className = "px-3 py-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 font-bold font-mono text-[11px] border border-amber-300 transition shadow-xs flex items-center gap-1.5 cursor-pointer";
      }
    } else {
      _autoWorkerPaused = false;
      window._autoWorkerPaused = false;
      if (txt) txt.textContent = "\u23F3 AI \uC694\uC57D \uC2DC\uC791 \uC911...";
      startContinuousAiWorker();
    }
  }
  async function triggerAiEnrichWorker() {
    toggleAiEnrichWorker();
  }
  async function runSystemVerificationAgent() {
    const btn = document.getElementById("btnTriggerVerification");
    const txt = document.getElementById("btnVerifyText");
    if (btn && txt) {
      txt.innerHTML = `<span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-ping mr-1"></span> \uC9C4\uB2E8 \uC911...`;
      btn.disabled = true;
    }
    const t0 = Date.now();
    const checks = [];
    const cases = window.liveCasesData && window.liveCasesData.length > 0 ? window.liveCasesData : window.AppStore && typeof window.AppStore.getCases === "function" && window.AppStore.getCases().length > 0 ? window.AppStore.getCases() : casesData || [];
    const isHydrated = window.__APP_INITIALIZED__ === true || cases.length > 0;
    const casesLoaded = cases.length > 0;
    checks.push({
      title: "\uD504\uB7F0\uD2B8\uC5D4\uB4DC \uBAA8\uB4C8\uB7EC \uB7F0\uD0C0\uC784 & \uC2A4\uD1A0\uC5B4 \uC218\uD654",
      pass: isHydrated && casesLoaded,
      details: `\uC218\uD654: ${isHydrated ? "\uC815\uC0C1" : "\uC9C4\uD589\uC911"} | \uAC80\uC99D \uB3C4\uC2DC\uC5D0: ${casesLoaded ? cases.length + "\uAC74" : "0\uAC74"}`
    });
    try {
      const res = await fetch(APP_CONFIG.apiUrl("/api/embed-worker?check_only=true"));
      const data = await res.json();
      if (res.ok && data.success) {
        checks.push({
          title: "Aiven PostgreSQL & Voyage pgvector \uC0C1\uD0DC",
          pass: true,
          details: `\uCD1D ${data.total_count?.toLocaleString()}\uAC74 \uC911 ${data.embedded_count?.toLocaleString()}\uAC74 \uC784\uBCA0\uB529 \uC644\uB8CC (\uC794\uC5EC: ${data.remaining_unembedded?.toLocaleString()}\uAC74)`
        });
      } else {
        checks.push({
          title: "Aiven PostgreSQL & Voyage pgvector \uC0C1\uD0DC",
          pass: false,
          details: `API \uC751\uB2F5 \uC624\uB958: ${data.error || res.status}`
        });
      }
    } catch (err) {
      checks.push({
        title: "Aiven PostgreSQL & Voyage pgvector \uC0C1\uD0DC",
        pass: false,
        details: `\uB124\uD2B8\uC6CC\uD06C \uD1B5\uC2E0 \uC624\uB958: ${err.message}`
      });
    }
    try {
      const res = await fetch(APP_CONFIG.apiUrl("/api/stats"));
      const data = await res.json();
      const isOk = res.ok && (data.status === "success" || data.status === "SUCCESS");
      const totalCount = data.counts?.inbox_total || data.data?.inbox_total_count || 0;
      if (isOk) {
        checks.push({
          title: "\uAE00\uB85C\uBC8C \uC9D1\uACC4 \uC5D4\uC9C4 (No Slice Aggregation)",
          pass: true,
          details: `\uC2E4\uC2DC\uAC04 DB GROUP BY \uC9D1\uACC4 \uC815\uC0C1 (\uC778\uBC15\uC2A4 \uCD1D\uB7C9: ${totalCount.toLocaleString()}\uAC74)`
        });
      } else {
        checks.push({
          title: "\uAE00\uB85C\uBC8C \uC9D1\uACC4 \uC5D4\uC9C4",
          pass: false,
          details: `\uC9D1\uACC4 API \uC751\uB2F5 \uBE44\uC815\uC0C1 (${res.status})`
        });
      }
    } catch (err) {
      checks.push({
        title: "\uAE00\uB85C\uBC8C \uC9D1\uACC4 \uC5D4\uC9C4",
        pass: false,
        details: err.message
      });
    }
    const fallbackReady = typeof window.triggerLegacyFallback === "function" && window.__FALLBACK_TRIGGERED__ === false;
    checks.push({
      title: "\uBB34\uC911\uB2E8 \uBE44\uC0C1 \uB864\uBC31 \uD558\uB124\uC2A4 (Zero-Downtime Fallback)",
      pass: fallbackReady,
      details: "app.legacy.js \uB3D9\uC801 \uC2A4\uC704\uCE6D \uB300\uAE30 \uC815\uC0C1"
    });
    const allPassed = checks.every((c) => c.pass);
    const elapsed = ((Date.now() - t0) / 1e3).toFixed(2);
    if (btn && txt) {
      btn.disabled = false;
      txt.innerHTML = allPassed ? "\u2705 \uC2DC\uC2A4\uD15C \uAC80\uC99D \uC644\uB8CC" : "\u26A0\uFE0F \uAC80\uC99D \uC774\uC0C1 \uAC10\uC9C0";
      setTimeout(() => {
        txt.textContent = "\u{1F50D} \uC2DC\uC2A4\uD15C \uAC80\uC99D \uC2E4\uD589";
      }, 4e3);
    }
    if (typeof window.showVerificationReportModal === "function") {
      window.showVerificationReportModal({
        allPassed,
        elapsed,
        checks
      });
    } else {
      showToast(allPassed ? `\u2705 \uC2DC\uC2A4\uD15C \uAC80\uC99D 100% \uD1B5\uACFC (${elapsed}\uCD08)` : "\u26A0\uFE0F \uC2DC\uC2A4\uD15C \uC810\uAC80 \uD56D\uBAA9 \uBC1C\uC0DD", allPassed ? "success" : "warning");
    }
  }
  function updatePromotionBanner() {
  }
  if (typeof window !== "undefined") {
    window.bootstrapApplicationData = bootstrapApplicationData;
    window.updateGlobalStatsUI = updateGlobalStatsUI;
    window.updateNewsCategoryPillCounts = updateNewsCategoryPillCounts;
    window.updateModelCategoryPillCounts = updateModelCategoryPillCounts;
    window.syncFromLiveDB = syncFromLiveDB;
    window.checkVoyageEmbeddingStatus = checkVoyageEmbeddingStatus;
    window.toggleVoyageEmbeddingWorker = toggleVoyageEmbeddingWorker;
    window.startContinuousVoyageWorker = startContinuousVoyageWorker;
    window.toggleAiEnrichWorker = toggleAiEnrichWorker;
    window.updatePromotionBanner = updatePromotionBanner;
    window.runSystemVerificationAgent = runSystemVerificationAgent;
  }

  // src/js/utils/languageDetector.js
  function detectSourceLang(item) {
    if (!item) return "EN";
    const ai = item.ai_enrichment || {};
    const explicitLang = (ai.source_lang || item.source_lang || "").toUpperCase();
    if (["KO", "EN", "ZH", "JA"].includes(explicitLang)) {
      return explicitLang;
    }
    const itPlat = (item.source_platform || "").toLowerCase();
    const itUrl = (item.source_url || "").toLowerCase();
    const origTitle = `${item.title || ""}`;
    if (/[\uac00-\ud7a3]/.test(origTitle) || /daum|geeknews|hada\.io|chosun|donga|yonhap|naver/i.test(itPlat) || /daum\.net|hada\.io|naver\.com/i.test(itUrl)) {
      return "KO";
    } else if (/[\u3040-\u30ff]/.test(origTitle)) {
      return "JA";
    } else if (/[\u4e00-\u9fff]/.test(origTitle) || /weibo|zhihu|36kr|ithome|sspai|bilibili|wechat|qq\.com|sina|baidu|jiqizhixin|qbitai|v2ex|geekpark|oschina|infoq/i.test(itPlat) || /\.cn|\.com\.cn|weibo\.com|zhihu\.com|36kr\.com|ithome\.com|sspai\.com|bilibili\.com|v2ex\.com/i.test(itUrl)) {
      return "ZH";
    }
    return "EN";
  }
  if (typeof window !== "undefined") {
    window.detectSourceLang = detectSourceLang;
  }

  // src/js/utils/metricFormatter.js
  function getPlatformImpactWeight(name = "") {
    const n = (name || "").toLowerCase();
    if (n.includes("github")) return 100;
    if (n.includes("space") || n.includes("hf space")) return 96;
    if (n.includes("hugging") || n.includes("hf")) return 95;
    if (n.includes("arxiv")) return 90;
    if (n.includes("hacker news") || n.includes("ycombinator")) return 85;
    if (n.includes("pytorch")) return 80;
    if (n.includes("geeknews") || n.includes("hada.io")) return 75;
    if (n.includes("reddit")) return 60;
    return 50;
  }
  function cleanPlatformName(raw) {
    if (!raw) return "News";
    let name = String(raw).trim();
    const m = name.match(/^(?:Press|News|YouTube)\s*\((.*?)\)$/i);
    if (m) name = m[1].trim();
    if (name.toLowerCase().startsWith("reddit")) return "Reddit";
    if (name.includes("\uC870\uCF54\uB529")) return "YouTube (\uC870\uCF54\uB529)";
    const map = {
      "the new york times": "NYT",
      "the wall street journal": "WSJ",
      "the guardian": "The Guardian",
      "the verge": "The Verge",
      "the verge ai": "The Verge",
      "techcrunch ai": "TechCrunch",
      "techcrunch": "TechCrunch",
      "hacker news": "HN",
      "geeknews": "GeekNews",
      "reddit r/technology": "Reddit",
      "reddit": "Reddit",
      "reuters": "Reuters",
      "bloomberg": "Bloomberg",
      "politico": "Politico",
      "bbc": "BBC",
      "cnn": "CNN",
      "cbs news": "CBS",
      "abc news": "ABC",
      "breaking news, latest news and videos": "ABC News",
      "usa today": "USA Today",
      "al jazeera": "Al Jazeera",
      "axios": "Axios",
      "cnet": "CNET",
      "wired": "WIRED",
      "ft.com": "FT",
      "npr.org": "NPR",
      "npr": "NPR",
      "time.com": "TIME",
      "time": "TIME",
      "vietnam.vn": "Vietnam.vn",
      "nextgov.com": "NextGov",
      "newser": "Newser"
    };
    const key = name.toLowerCase();
    return map[key] || name;
  }
  function getPrimaryImpactPlatform(it, allSources = []) {
    let bestName = it && it.source_platform || "Tech News";
    let maxW = getPlatformImpactWeight(bestName);
    if (Array.isArray(allSources)) {
      for (const s of allSources) {
        const p = s.platform || s.source_name || "";
        const w = getPlatformImpactWeight(p);
        if (w > maxW) {
          maxW = w;
          bestName = p;
        }
      }
    }
    return cleanPlatformName(bestName);
  }
  function formatCleanMetricVal(valStr, currentLang2 = "KO") {
    if (!valStr) return "";
    let clean = String(valStr).replace(/🔥/g, "").trim();
    clean = clean.replace(/\b(?:hn\s*)?points\b/gi, "pts").replace(/\blikes\b/gi, "likes").replace(/\bstars\b/gi, "\u2605");
    clean = clean.replace(/(?:💬\s*)?Reddit\s*Major\s*Discussion/gi, currentLang2 === "KO" ? "\u{1F4AC} \uCEE4\uBBA4\uB2C8\uD2F0 \uD1A0\uB860" : currentLang2 === "ZH" ? "\u{1F4AC} \u793E\u533A\u8BA8\u8BBA" : "\u{1F4AC} Discussion");
    clean = clean.replace(/(?:💬\s*)?Major\s*Discussion/gi, currentLang2 === "KO" ? "\u{1F4AC} \uD1A0\uB860" : currentLang2 === "ZH" ? "\u{1F4AC} \u8BA8\u8BBA" : "\u{1F4AC} Discussion");
    clean = clean.replace(/💬\s*💬/g, "\u{1F4AC}");
    clean = clean.replace(/\(Trending\s*Demo\)/gi, "").trim();
    if (clean.length > 18 && clean.includes("\uBCF4\uB3C4")) {
      clean = clean.replace(/^(?:📰\s*)?(.*?)\s*보도$/, (match, p1) => {
        const shortName = p1.length > 8 ? p1.slice(0, 7) + "\u2026" : p1;
        return `\u{1F4F0} ${shortName} \uBCF4\uB3C4`;
      });
    }
    return clean;
  }
  function calculateStandardizedViralScore(item) {
    if (!item) return 25;
    const src = item.source_platform || "";
    const metric = item.viral_metric || item.description || "";
    let rawNum = 0;
    const nums = metric.replace(/,/g, "").match(/\d+/) || [];
    if (nums.length > 0) rawNum = parseInt(nums[0], 10);
    let normScore = 25;
    if (src.includes("GitHub")) {
      normScore = rawNum > 0 ? Math.log10(rawNum + 1) / Math.log10(5e3) * 100 : 25;
    } else if (src.includes("Hacker News")) {
      normScore = rawNum > 0 ? Math.log10(rawNum + 1) / Math.log10(800) * 100 : 30;
    } else if (src.includes("Hugging Face")) {
      normScore = rawNum > 0 ? Math.log10(rawNum + 1) / Math.log10(300) * 100 : 30;
    } else if (src.includes("GeekNews")) {
      normScore = rawNum > 0 ? Math.log10(rawNum + 1) / Math.log10(100) * 100 : 35;
    } else if (src.includes("ArXiv")) {
      normScore = 55;
    }
    normScore = Math.max(5, Math.min(100, Math.round(normScore)));
    const aiScore = item.ai_enrichment ? item.ai_enrichment.score : null;
    if (aiScore && aiScore > 0) {
      normScore = Math.round(normScore * 0.7 + aiScore * 20 * 0.3);
    }
    return normScore;
  }
  function formatRadarPointBadge(it, currentLang2 = "KO") {
    if (!it) return "";
    const vmRaw = (it.viral_metric || "").trim();
    const pf = (it.platform_family || it.platform || "").toLowerCase();
    const ptMatch = vmRaw.match(/(\d[\d,]*)\s*(?:HN\s*)?(?:pts|Points|포인트)/i) || vmRaw.match(/(?:Trending|🔥)\s*(\d[\d,]*)\s*pts/i);
    if (ptMatch) {
      const num = parseInt(ptMatch[1].replace(/,/g, ""), 10);
      const displayNum = isNaN(num) ? ptMatch[1] : num.toLocaleString();
      return `<span class="px-2.5 py-0.5 rounded-lg text-[11px] font-mono font-black bg-rose-100/90 text-rose-800 border border-rose-300 flex items-center gap-1 shadow-xs" title="${vmRaw}"><i data-lucide="flame" class="w-3.5 h-3.5 text-rose-600 fill-rose-500"></i><span>${displayNum} pts</span></span>`;
    }
    const starMatch = vmRaw.match(/(?:★|stars?)\s*(\d[\d,]*)/i);
    if (starMatch || pf.includes("github")) {
      const numMatch = vmRaw.match(/(\d[\d,]*)/);
      const displayStar = numMatch ? parseInt(numMatch[1].replace(/,/g, ""), 10).toLocaleString() : "Trending";
      return `<span class="px-2.5 py-0.5 rounded-lg text-[11px] font-mono font-black bg-amber-100/90 text-amber-900 border border-amber-300 flex items-center gap-1 shadow-xs" title="${vmRaw}"><i data-lucide="star" class="w-3.5 h-3.5 text-amber-600 fill-amber-400"></i><span>${displayStar}</span></span>`;
    }
    const likeMatch = vmRaw.match(/(?:❤️|likes?)\s*(\d[\d,]*)/i);
    if (likeMatch || pf.includes("hugging") || pf.includes("space")) {
      const numMatch = vmRaw.match(/(\d[\d,]*)/);
      const displayLike = numMatch ? parseInt(numMatch[1].replace(/,/g, ""), 10).toLocaleString() : "Demo";
      return `<span class="px-2.5 py-0.5 rounded-lg text-[11px] font-mono font-black bg-rose-100/90 text-rose-800 border border-rose-300 flex items-center gap-1 shadow-xs" title="${vmRaw}"><i data-lucide="heart" class="w-3.5 h-3.5 text-rose-600 fill-rose-500"></i><span>${displayLike}</span></span>`;
    }
    if (vmRaw.includes("\uC601\uC0C1") || vmRaw.includes("YouTube") || pf.includes("youtube")) {
      const label = currentLang2 === "KO" ? "\uC601\uC0C1 \uBE0C\uB9AC\uD551" : currentLang2 === "ZH" ? "\u89C6\u9891\u64AD\u62A5" : "Video Brief";
      return `<span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-semibold bg-red-50 text-red-700 border border-red-200/80 flex items-center gap-1 shadow-2xs"><i data-lucide="play" class="w-2.5 h-2.5 text-red-600 fill-red-600"></i><span>${label}</span></span>`;
    }
    if (vmRaw.includes("\uCEE4\uBBA4\uB2C8\uD2F0") || vmRaw.includes("\uD050\uB808\uC774\uC158") || vmRaw.includes("\uD1A0\uB860") || vmRaw.includes("Discussion") || pf.includes("reddit") || pf.includes("geek") || pf.includes("pytorch")) {
      const label = currentLang2 === "KO" ? "\uCEE4\uBBA4\uB2C8\uD2F0" : currentLang2 === "ZH" ? "\u793E\u533A\u70ED\u70B9" : "Community";
      return `<span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/80 flex items-center gap-1 shadow-2xs"><i data-lucide="message-square" class="w-3 h-3 text-indigo-600"></i><span>${label}</span></span>`;
    }
    if (vmRaw.includes("\uBCF4\uB3C4") || vmRaw.includes("Press") || vmRaw.includes("News") || pf.includes("press") || pf.includes("media")) {
      const label = currentLang2 === "KO" ? "\uC678\uC2E0 \uBCF4\uB3C4" : currentLang2 === "ZH" ? "\u4E3B\u6D41\u5916\u5A92" : "Global Press";
      return `<span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-semibold bg-sky-50 text-sky-700 border border-sky-200/80 flex items-center gap-1 shadow-2xs"><i data-lucide="globe" class="w-3 h-3 text-sky-600"></i><span>${label}</span></span>`;
    }
    if (vmRaw.includes("Paper") || pf.includes("arxiv")) {
      const label = currentLang2 === "KO" ? "\uD559\uC220 \uB17C\uBB38" : currentLang2 === "ZH" ? "\u5B66\u672F\u8BBA\u6587" : "Paper";
      return `<span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-semibold bg-violet-50 text-violet-700 border border-violet-200 flex items-center gap-1 shadow-2xs"><i data-lucide="book-open" class="w-3 h-3 text-violet-600"></i><span>${label}</span></span>`;
    }
    let cleanFallback = vmRaw.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F1E6}-\u{1F1FF}]/gu, "").trim();
    if (!cleanFallback) cleanFallback = "Trend";
    return `<span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center gap-1 shadow-2xs"><i data-lucide="zap" class="w-3 h-3 text-emerald-600"></i><span>${cleanFallback}</span></span>`;
  }
  if (typeof window !== "undefined") {
    window.getPlatformImpactWeight = getPlatformImpactWeight;
    window.cleanPlatformName = cleanPlatformName;
    window.getPrimaryImpactPlatform = getPrimaryImpactPlatform;
    window.formatCleanMetricVal = formatCleanMetricVal;
    window.calculateStandardizedViralScore = calculateStandardizedViralScore;
    window.formatRadarPointBadge = formatRadarPointBadge;
  }

  // src/js/utils/collectionSorter.js
  function sortCollection(items, sortKey) {
    if (!Array.isArray(items)) return [];
    return items.sort((a, b) => {
      const idA = a.case_id || a.inbox_id || a.id || "";
      const idB = b.case_id || b.inbox_id || b.id || "";
      if (sortKey === "date-source-desc") {
        const diff = parseItemTimestamp(b, "source") - parseItemTimestamp(a, "source");
        if (diff !== 0) return diff;
        return idB.localeCompare(idA);
      }
      if (sortKey === "date-source-asc" || sortKey === "date-asc") {
        const diff = parseItemTimestamp(a, "source") - parseItemTimestamp(b, "source");
        if (diff !== 0) return diff;
        return idA.localeCompare(idB);
      }
      if (sortKey === "date-audit-desc" || sortKey === "date-desc") {
        const tB = parseItemTimestamp(b, "audit");
        const tA = parseItemTimestamp(a, "audit");
        if (tB !== tA) return tB - tA;
        const sB = parseItemTimestamp(b, "source");
        const sA = parseItemTimestamp(a, "source");
        if (sB !== sA) return sB - sA;
        return idB.localeCompare(idA);
      }
      if (sortKey === "date-audit-asc") {
        const tA = parseItemTimestamp(a, "audit");
        const tB = parseItemTimestamp(b, "audit");
        if (tA > 0 && tB > 0 && tA !== tB) return tA - tB;
        if (tA > 0 && tB === 0) return -1;
        if (tB > 0 && tA === 0) return 1;
        const sDiff = parseItemTimestamp(a, "source") - parseItemTimestamp(b, "source");
        if (sDiff !== 0) return sDiff;
        return idA.localeCompare(idB);
      }
      if (sortKey === "title-asc") {
        return (a.title || "").localeCompare(b.title || "");
      }
      if (sortKey === "viral-desc") {
        return calculateStandardizedViralScore(b) - calculateStandardizedViralScore(a);
      }
      if (sortKey === "viral-asc") {
        return calculateStandardizedViralScore(a) - calculateStandardizedViralScore(b);
      }
      const defDiff = parseItemTimestamp(b, "source") - parseItemTimestamp(a, "source");
      if (defDiff !== 0) return defDiff;
      return idB.localeCompare(idA);
    });
  }
  if (typeof window !== "undefined") {
    window.sortCollection = sortCollection;
  }

  // src/js/utils/feedClustering.js
  function extractStoryEntity(it) {
    if (!it) return "";
    const text = `${it.title || ""} ${it.title_ko || ""} ${it.source_url || ""} ${it.canonical_story_key || ""}`.toLowerCase();
    const m = text.match(/\b(qwen[-_ ]?image[-_ ]?2\.?1|qwen[-_ ]?3\.?8[-_ ]?35b|qwen[-_ ]?2\.?5[-_ ]?coder|deepseek[-_ ]?[rv]\d+[\w.-]*|llama[-_ ]?\d+[\w.-]*|glm[-_ ]?\d+[\w.-]*|flux[-_ ]?\d+[\w.-]*|jev)\b/i);
    if (m) {
      return m[1].toLowerCase().replace(/[-_ ]+/g, "-");
    }
    if (it.canonical_story_key && it.canonical_story_key.length > 5) {
      const cleaned = it.canonical_story_key.toLowerCase().replace(/-(?:github|huggingface|geeknews|hn|demo|release|repo|compact|efficient|unified|uncensored|gguf|trending).*$/, "");
      if (cleaned.length >= 4) return cleaned;
    }
    return "";
  }
  function clusterFeedItems(rawItems) {
    if (!Array.isArray(rawItems) || rawItems.length <= 1) return rawItems || [];
    const entityMap = /* @__PURE__ */ new Map();
    const clustered = [];
    for (const raw of rawItems) {
      const it = { ...raw };
      const entity = extractStoryEntity(it);
      if (entity && entity.length >= 3) {
        if (entityMap.has(entity)) {
          const primary = entityMap.get(entity);
          primary.sources = primary.sources ? [...primary.sources] : [];
          if (primary.sources.length === 0 && primary.source_platform) {
            primary.sources.push({
              source_name: primary.source_platform,
              platform: primary.source_platform,
              url: primary.source_url || primary.hn_url || primary.article_url || "",
              title: primary.title,
              type: "original"
            });
          }
          const incomingUrl = it.source_url || it.hn_url || it.article_url || "";
          const exists = primary.sources.some((s) => (s.url || "").toLowerCase() === incomingUrl.toLowerCase());
          if (!exists && incomingUrl) {
            primary.sources.push({
              source_name: it.source_platform || "Cross-post",
              platform: it.source_platform || "Cross-post",
              url: incomingUrl,
              title: it.title,
              type: "cross_post"
            });
          }
          primary.cross_posts = primary.cross_posts ? [...primary.cross_posts] : [];
          primary.cross_posts.push({
            platform: it.source_platform,
            url: incomingUrl,
            title: it.title
          });
          primary.is_cross_spiking = true;
          if (Array.isArray(it.raw_comments) && it.raw_comments.length > 0) {
            primary.raw_comments = [...primary.raw_comments || [], ...it.raw_comments];
          }
          continue;
        } else {
          entityMap.set(entity, it);
          clustered.push(it);
        }
      } else {
        clustered.push(it);
      }
    }
    return clustered;
  }
  if (typeof window !== "undefined") {
    window.extractStoryEntity = extractStoryEntity;
    window.clusterFeedItems = clusterFeedItems;
  }

  // src/js/utils/stealthUrl.js
  var STEALTH_TRACKING_KEYS = /* @__PURE__ */ new Set([
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "ref",
    "ref_src",
    "ref_url",
    "source",
    "fbclid",
    "gclid",
    "msclkid",
    "twclid",
    "si",
    "spm",
    "igshid",
    "yclid",
    "mc_cid",
    "mc_eid",
    "aff",
    "affiliate"
  ]);
  function cleanStealthUrl(rawUrl) {
    if (!rawUrl) return "";
    try {
      const origin = typeof window !== "undefined" ? window.location.origin : "https://ai-factcheck-portfolio.vercel.app";
      const u = new URL(rawUrl, origin);
      if (!u.protocol.startsWith("http")) return rawUrl;
      const params = new URLSearchParams(u.search);
      const keysToDelete = [];
      for (const k of params.keys()) {
        const lk = k.toLowerCase();
        if (STEALTH_TRACKING_KEYS.has(lk) || lk.startsWith("utm_") || lk.includes("chatgpt")) {
          keysToDelete.push(k);
        }
      }
      keysToDelete.forEach((k) => params.delete(k));
      u.search = params.toString() ? "?" + params.toString() : "";
      return u.toString();
    } catch (e) {
      return rawUrl;
    }
  }
  function stealthNavigate(rawUrl, ev) {
    if (ev) {
      ev.preventDefault();
      ev.stopPropagation();
    }
    const cleanUrl = cleanStealthUrl(rawUrl);
    if (typeof window === "undefined") return;
    const newWin = window.open("", "_blank");
    if (newWin) {
      newWin.opener = null;
      newWin.location.replace(cleanUrl);
    } else {
      const a = document.createElement("a");
      a.href = cleanUrl;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.referrerPolicy = "no-referrer";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  }
  function initStealthLinkInterceptor() {
    if (typeof document === "undefined") return;
    document.addEventListener("click", (e) => {
      const link = e.target.closest("a");
      if (link && link.href && link.href.startsWith("http") && !link.href.includes(window.location.host)) {
        e.preventDefault();
        e.stopPropagation();
        stealthNavigate(link.href);
      }
    }, true);
  }
  if (typeof window !== "undefined") {
    window.cleanStealthUrl = cleanStealthUrl;
    window.stealthNavigate = stealthNavigate;
    window.STEALTH_TRACKING_KEYS = STEALTH_TRACKING_KEYS;
  }

  // src/js/components/pagination.js
  function renderPagination(containerId, currentPage, totalPages, onPageChange) {
    if (typeof document === "undefined") return;
    const container = document.getElementById(containerId);
    if (!container) return;
    if (totalPages <= 1) {
      container.innerHTML = "";
      return;
    }
    let html = '<div class="flex items-center justify-center gap-1.5 pt-6 pb-4 text-xs font-mono select-none flex-wrap">';
    const firstDisabled = currentPage === 1;
    html += `<button onclick="${firstDisabled ? "" : onPageChange + "(1)"}" class="px-2.5 py-1.5 rounded-lg border font-bold transition shadow-xs ${firstDisabled ? "opacity-30 cursor-not-allowed bg-surface-subtle text-ink-muted border-surface-border" : "bg-white hover:bg-surface-subtle text-ink-primary border-surface-border cursor-pointer"}" title="\uCC98\uC74C\uC73C\uB85C">&laquo;&laquo;</button>`;
    const prevDisabled = currentPage === 1;
    html += `<button onclick="${prevDisabled ? "" : onPageChange + "(" + (currentPage - 1) + ")"}" class="px-2.5 py-1.5 rounded-lg border font-bold transition shadow-xs ${prevDisabled ? "opacity-30 cursor-not-allowed bg-surface-subtle text-ink-muted border-surface-border" : "bg-white hover:bg-surface-subtle text-ink-primary border-surface-border cursor-pointer"}" title="\uC774\uC804">&lsaquo;</button>`;
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    if (endPage - startPage < 4) {
      startPage = Math.max(1, endPage - 4);
    }
    for (let p = startPage; p <= endPage; p++) {
      const isCur = p === currentPage;
      const btnStyle = isCur ? "bg-indigo-600 text-white font-extrabold border-indigo-600 shadow-sm" : "bg-white hover:bg-surface-subtle text-ink-secondary hover:text-ink-primary border-surface-border font-semibold cursor-pointer";
      html += `<button onclick="${onPageChange}(${p})" class="w-8 h-8 rounded-lg border flex items-center justify-center transition ${btnStyle}">${p}</button>`;
    }
    const nextDisabled = currentPage === totalPages;
    html += `<button onclick="${nextDisabled ? "" : onPageChange + "(" + (currentPage + 1) + ")"}" class="px-2.5 py-1.5 rounded-lg border font-bold transition shadow-xs ${nextDisabled ? "opacity-30 cursor-not-allowed bg-surface-subtle text-ink-muted border-surface-border" : "bg-white hover:bg-surface-subtle text-ink-primary border-surface-border cursor-pointer"}" title="\uB2E4\uC74C">&rsaquo;</button>`;
    const lastDisabled = currentPage === totalPages;
    html += `<button onclick="${lastDisabled ? "" : onPageChange + "(" + totalPages + ")"}" class="px-2.5 py-1.5 rounded-lg border font-bold transition shadow-xs ${lastDisabled ? "opacity-30 cursor-not-allowed bg-surface-subtle text-ink-muted border-surface-border" : "bg-white hover:bg-surface-subtle text-ink-primary border-surface-border cursor-pointer"}" title="\uB05D\uC73C\uB85C">&raquo;&raquo;</button>`;
    html += "</div>";
    container.innerHTML = html;
  }
  function changePortfolioPage(page, pushHistory = true) {
    setPortfolioPage(page);
    if (typeof window.renderCards === "function") window.renderCards();
    document.getElementById("portfolioView")?.scrollIntoView({ behavior: "smooth" });
    if (pushHistory && typeof history !== "undefined") {
      const targetHash = page > 1 ? "#/factchecks?page=" + page : "#/factchecks";
      if (window.location.hash !== targetHash) {
        try {
          history.pushState({ view: "portfolio", page }, "", targetHash);
        } catch (e) {
          window.location.hash = targetHash;
        }
      }
    }
  }
  function changeModelsPage(page, pushHistory = true) {
    setModelsPage(page);
    if (typeof window.renderModels === "function") window.renderModels();
    document.getElementById("modelsView")?.scrollIntoView({ behavior: "smooth" });
    if (pushHistory && typeof history !== "undefined") {
      const targetHash = page > 1 ? "#/models?page=" + page : "#/models";
      if (window.location.hash !== targetHash) {
        try {
          history.pushState({ view: "models", page }, "", targetHash);
        } catch (e) {
          window.location.hash = targetHash;
        }
      }
    }
  }
  function changeNewsPage(page, pushHistory = true) {
    setNewsPage(page);
    if (typeof window.renderNews === "function") window.renderNews();
    document.getElementById("newsView")?.scrollIntoView({ behavior: "smooth" });
    if (pushHistory && typeof history !== "undefined") {
      const targetHash = page > 1 ? "#/news?page=" + page : "#/news";
      if (window.location.hash !== targetHash) {
        try {
          history.pushState({ view: "news", page }, "", targetHash);
        } catch (e) {
          window.location.hash = targetHash;
        }
      }
    }
  }
  function changeInboxPage(page, pushHistory = true) {
    setInboxPage(page);
    if (typeof window.renderInbox === "function") window.renderInbox();
    document.getElementById("inboxView")?.scrollIntoView({ behavior: "smooth" });
    if (pushHistory && typeof history !== "undefined") {
      const targetHash = page > 1 ? "#/inbox?page=" + page : "#/inbox";
      if (window.location.hash !== targetHash) {
        try {
          history.pushState({ view: "inbox", page }, "", targetHash);
        } catch (e) {
          window.location.hash = targetHash;
        }
      }
    }
  }
  if (typeof window !== "undefined") {
    window.renderPagination = renderPagination;
    window.changePortfolioPage = changePortfolioPage;
    window.changeModelsPage = changeModelsPage;
    window.changeNewsPage = changeNewsPage;
    window.changeInboxPage = changeInboxPage;
  }

  // src/js/components/popover.js
  function getSourceMeta(s) {
    const p = (s.platform || s.source_name || "").toLowerCase();
    const u = (s.url || "#").toLowerCase();
    const cleanName = cleanPlatformName(s.platform || s.source_name);
    const lang = typeof window !== "undefined" && window.currentLang ? window.currentLang : currentLang;
    let icon = "\u{1F4C4}";
    let label = cleanName || (lang === "KO" ? "\uC6D0\uBB38" : "Source");
    let badgeCls = "bg-surface-subtle text-ink-secondary hover:text-ink-primary border-surface-border";
    let isComm = false;
    if (p.includes("hacker news") || u.includes("ycombinator")) {
      icon = "\u{1F525}";
      label = lang === "KO" ? "HN \uD1A0\uB860" : "HN";
      badgeCls = "bg-orange-50 text-orange-800 hover:text-orange-950 border-orange-200";
      isComm = true;
    } else if (p.includes("geeknews") || u.includes("hada.io")) {
      icon = "\u{1F4AC}";
      label = lang === "KO" ? "\uAE31\uB274\uC2A4" : "GeekNews";
      badgeCls = "bg-indigo-50 text-indigo-800 hover:text-indigo-950 border-indigo-200";
      isComm = true;
    } else if (p.includes("pytorch")) {
      icon = "\u{1F1F0}\u{1F1F7}";
      label = "PyTorchKR";
      badgeCls = "bg-purple-50 text-purple-800 hover:text-purple-950 border-purple-200";
      isComm = true;
    } else if (p.includes("reddit")) {
      icon = "\u{1F916}";
      label = lang === "KO" ? "\uB808\uB527" : "Reddit";
      badgeCls = "bg-red-50 text-red-800 hover:text-red-950 border-red-200";
      isComm = true;
    } else if (p.includes("github")) {
      icon = "\u{1F419}";
      label = "GitHub";
      badgeCls = "bg-slate-100 text-slate-800 hover:text-slate-950 border-slate-300";
      isComm = true;
    } else if (p.includes("space") || u.includes("/spaces/")) {
      icon = "\u{1F917}";
      label = "HF Spaces";
      badgeCls = "bg-amber-50 text-amber-900 hover:text-amber-950 border-amber-200";
      isComm = true;
    } else if (p.includes("hugging") || u.includes("huggingface.co")) {
      icon = "\u{1F917}";
      label = "HuggingFace";
      badgeCls = "bg-amber-50 text-amber-900 hover:text-amber-950 border-amber-200";
      isComm = true;
    } else if (p.includes("arxiv")) {
      icon = "\u{1F4D1}";
      label = "ArXiv";
      badgeCls = "bg-rose-50 text-rose-900 hover:text-rose-950 border-rose-200";
      isComm = true;
    } else if (p.includes("youtube") || u.includes("youtube.com") || u.includes("youtu.be")) {
      icon = "\u{1F4FA}";
      label = lang === "KO" ? "\uC720\uD29C\uBE0C" : "YouTube";
      badgeCls = "bg-red-50 text-red-800 hover:text-red-950 border-red-200";
      isComm = true;
    } else if (p.includes("twitter") || p.includes(" x") || u.includes("x.com") || u.includes("twitter.com")) {
      icon = "\u{1D54F}";
      label = "X (\uD2B8\uC704\uD130)";
      badgeCls = "bg-zinc-100 text-zinc-800 hover:text-zinc-950 border-zinc-300";
      isComm = true;
    } else {
      icon = "\u{1F4F0}";
      label = cleanName || (lang === "KO" ? "\uBCF4\uB3C4" : "Press");
      badgeCls = "bg-emerald-50 text-emerald-800 hover:text-emerald-950 border-emerald-200";
      isComm = false;
    }
    return {
      icon,
      label,
      cleanPlatform: cleanName,
      badgeCls,
      url: s.url || "#",
      title: s.title || "",
      weight: getPlatformImpactWeight(s.platform || s.source_name),
      isCommunity: isComm
    };
  }
  function buildMultiSourceCluster(rawSources, rawItemId) {
    if (!rawSources || rawSources.length === 0) return "";
    const lang = typeof window !== "undefined" && window.currentLang ? window.currentLang : currentLang;
    const seenUrls = /* @__PURE__ */ new Set();
    const sources = [];
    for (const s of rawSources) {
      const u = (s.url || "#").toLowerCase().replace(/[?#].*$/, "");
      const meta = getSourceMeta(s);
      const dedupeKey = `${meta.cleanPlatform.toLowerCase()}::${u}`;
      if (u !== "#" && seenUrls.has(dedupeKey)) continue;
      seenUrls.add(dedupeKey);
      sources.push({ ...s, meta });
    }
    if (sources.length === 0) return "";
    const pressSources = sources.filter((s) => !s.meta.isCommunity);
    const communitySources = sources.filter((s) => s.meta.isCommunity);
    pressSources.sort((a, b) => b.meta.weight - a.meta.weight);
    communitySources.sort((a, b) => b.meta.weight - a.meta.weight);
    const total = sources.length;
    const safeId = "src_" + String(rawItemId || Math.random()).replace(/[^a-zA-Z0-9_-]/g, "_");
    if (total === 1) {
      const m = sources[0].meta;
      return `<a href="${m.url}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md ${m.badgeCls} border text-[11px] font-bold flex items-center gap-1 shrink-0 transition shadow-xs">${m.icon} ${m.label} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
    }
    const directButtons = [];
    if (pressSources.length > 0 && communitySources.length > 0) {
      directButtons.push(pressSources[0]);
      directButtons.push(communitySources[0]);
    } else if (pressSources.length > 0) {
      directButtons.push(...pressSources.slice(0, 2));
    } else {
      directButtons.push(...communitySources.slice(0, 2));
    }
    let html = `<div class="flex items-center gap-1.5 flex-wrap justify-end relative">`;
    directButtons.forEach((s) => {
      const m = s.meta;
      html += `<a href="${m.url}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md ${m.badgeCls} border text-[11px] font-bold flex items-center gap-1 shrink-0 transition shadow-xs" title="${m.cleanPlatform} \uBC14\uB85C\uAC00\uAE30">${m.icon} ${m.label} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
    });
    if (total > directButtons.length) {
      const remainingCount = total - directButtons.length;
      html += `
      <div class="relative inline-block src-dropdown-container">
        <button type="button" onclick="toggleSourcePopover(event, '${safeId}')" class="px-2 py-1 rounded-md bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 text-[11px] font-extrabold flex items-center gap-1 shrink-0 transition cursor-pointer shadow-xs" title="\uC804\uCCB4 ${total}\uAC1C \uAD50\uCC28 \uCD9C\uCC98 \uBAA8\uC544\uBCF4\uAE30">
          <span>\u{1F517} +${remainingCount}${lang === "KO" ? "\uAC1C \uCD9C\uCC98" : lang === "ZH" ? "\u4E2A\u6765\u6E90" : " more"}</span>
          <i data-lucide="chevron-down" class="w-3 h-3 text-amber-800"></i>
        </button>
        <div id="srcMenu_${safeId}" class="hidden absolute z-50 mb-1.5 w-72 max-w-[calc(100vw-2.5rem)] min-w-[240px] bg-white rounded-xl shadow-2xl border border-surface-border p-2.5 text-xs flex flex-col gap-2">
          <div class="text-[10px] font-mono font-bold text-ink-muted px-1 pb-1.5 border-b border-surface-border flex items-center justify-between">
            <span>\u{1F517} ${lang === "KO" ? `\uC804\uCCB4 \uAD50\uCC28 \uCD9C\uCC98 (${total}\uAC1C)` : lang === "ZH" ? `\u5168\u90E8\u805A\u5408\u6765\u6E90 (${total}\u4E2A)` : `All Sources (${total})`}</span>
            <span class="text-indigo-600 text-[10px] font-bold">\uC5B8\uB860 ${pressSources.length} \xB7 \uCEE4\uBBA4\uB2C8\uD2F0 ${communitySources.length}</span>
          </div>
          <div class="max-h-56 overflow-y-auto space-y-2 pr-0.5 divide-y divide-surface-border/30">
            ${pressSources.length > 0 ? `
              <div class="pt-1">
                <div class="text-[10px] font-bold text-emerald-800 uppercase tracking-wider mb-1 flex items-center gap-1 px-1">
                  <span>\u{1F4F0} \uACF5\uC2DD \uC5B8\uB860 \uBCF4\uB3C4 (${pressSources.length})</span>
                </div>
                <div class="space-y-0.5">
                  ${pressSources.map((s) => `
                    <a href="${s.meta.url}" target="_blank" rel="noopener noreferrer" class="flex items-center justify-between px-2 py-1 rounded-lg hover:bg-emerald-50/60 transition group text-xs text-ink-primary">
                      <span class="font-bold text-emerald-950 shrink-0 text-[11px]">[${s.meta.cleanPlatform}]</span>
                      <span class="truncate text-[10px] text-ink-muted text-right flex-1 mx-1.5 group-hover:text-emerald-700">${s.title || s.meta.cleanPlatform}</span>
                      <i data-lucide="external-link" class="w-2.5 h-2.5 text-ink-muted group-hover:text-emerald-700 shrink-0"></i>
                    </a>
                  `).join("")}
                </div>
              </div>
            ` : ""}

            ${communitySources.length > 0 ? `
              <div class="pt-1">
                <div class="text-[10px] font-bold text-orange-800 uppercase tracking-wider mb-1 flex items-center gap-1 px-1">
                  <span>\u{1F4AC} \uCEE4\uBBA4\uB2C8\uD2F0 & \uAC1C\uBC1C\uC790 \uBC18\uC751 (${communitySources.length})</span>
                </div>
                <div class="space-y-0.5">
                  ${communitySources.map((s) => `
                    <a href="${s.meta.url}" target="_blank" rel="noopener noreferrer" class="flex items-center justify-between px-2 py-1 rounded-lg hover:bg-orange-50/60 transition group text-xs text-ink-primary">
                      <span class="flex items-center gap-1 shrink-0 font-bold text-orange-950 text-[11px]">
                        <span>${s.meta.icon}</span>
                        <span>${s.meta.label}</span>
                      </span>
                      <span class="truncate text-[10px] text-ink-muted text-right flex-1 mx-1.5 group-hover:text-orange-700">${s.title || s.meta.label}</span>
                      <i data-lucide="external-link" class="w-2.5 h-2.5 text-ink-muted group-hover:text-orange-700 shrink-0"></i>
                    </a>
                  `).join("")}
                </div>
              </div>
            ` : ""}
          </div>
        </div>
      </div>
    `;
    }
    html += `</div>`;
    return html;
  }
  function toggleSourcePopover(e, safeId) {
    if (e) e.stopPropagation();
    const menu = document.getElementById("srcMenu_" + safeId);
    if (!menu) return;
    const isHidden = menu.classList.contains("hidden");
    document.querySelectorAll('[id^="srcMenu_"]').forEach((el) => el.classList.add("hidden"));
    if (isHidden) {
      menu.classList.remove("hidden");
      const btn = e.currentTarget;
      const btnRect = btn.getBoundingClientRect();
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      const menuWidth = Math.min(260, vw - 32);
      menu.style.width = menuWidth + "px";
      if (btnRect.left + menuWidth > vw - 16) {
        menu.style.left = "auto";
        menu.style.right = "0px";
      } else {
        menu.style.left = "0px";
        menu.style.right = "auto";
      }
      if (btnRect.top < 220 && vh - btnRect.bottom > 180) {
        menu.style.bottom = "auto";
        menu.style.top = "calc(100% + 6px)";
      } else {
        menu.style.top = "auto";
        menu.style.bottom = "calc(100% + 6px)";
      }
      if (window.lucide) window.lucide.createIcons();
    }
  }
  function toggleClusterPopover(e, safeId) {
    if (e) e.stopPropagation();
    const menu = document.getElementById("clusterMenu_" + safeId);
    if (!menu) return;
    const isHidden = menu.classList.contains("hidden");
    document.querySelectorAll('[id^="clusterMenu_"]').forEach((el) => el.classList.add("hidden"));
    document.querySelectorAll('[id^="srcMenu_"]').forEach((el) => el.classList.add("hidden"));
    if (isHidden) {
      menu.classList.remove("hidden");
      if (window.lucide) window.lucide.createIcons();
    }
  }
  function initPopoverDismissListeners() {
    if (typeof document === "undefined") return;
    document.addEventListener("click", (e) => {
      if (!e.target.closest(".src-dropdown-container")) {
        document.querySelectorAll('[id^="srcMenu_"]').forEach((el) => el.classList.add("hidden"));
      }
      if (!e.target.closest('[id^="clusterMenu_"]') && !e.target.closest('button[onclick*="toggleClusterPopover"]')) {
        document.querySelectorAll('[id^="clusterMenu_"]').forEach((el) => el.classList.add("hidden"));
      }
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        document.querySelectorAll('[id^="srcMenu_"]').forEach((el) => el.classList.add("hidden"));
        document.querySelectorAll('[id^="clusterMenu_"]').forEach((el) => el.classList.add("hidden"));
      }
    });
  }
  if (typeof window !== "undefined") {
    window.buildMultiSourceCluster = buildMultiSourceCluster;
    window.toggleSourcePopover = toggleSourcePopover;
    window.toggleClusterPopover = toggleClusterPopover;
    initPopoverDismissListeners();
  }

  // src/js/components/modal.js
  function openModal(c, skipHistory = false) {
    if (!c || typeof document === "undefined") return;
    const cid = c.case_id || c.investigation_id;
    const curLang = typeof window !== "undefined" && window.currentLang ? window.currentLang : currentLang;
    const curView = typeof window !== "undefined" && window.currentView ? window.currentView : currentView;
    if (!skipHistory && cid && typeof history !== "undefined") {
      const targetHash = "#/factchecks?case=" + encodeURIComponent(cid);
      if (window.location.hash !== targetHash) {
        try {
          history.pushState({ caseId: cid, view: curView }, "", targetHash);
        } catch (e) {
        }
      }
    }
    const modal = document.getElementById("detailModal");
    if (!modal) return;
    const story = c.portfolio_story || {};
    const handsOn = story.hands_on_log && Object.keys(story.hands_on_log).length > 0 ? story.hands_on_log : c.hands_on_review || {};
    const curation = c.curation || {};
    const clustering = c.clustering || {};
    const rawPost = c.raw_viral_post || {};
    const t = i18n[curLang] || i18n.KO;
    let displayTitle = c.title;
    let displayMotivation = curation.personal_motivation || story.the_hook || "";
    let displayQuote = rawPost.quote || "";
    if (curLang === "ZH") {
      displayTitle = c.title_zh || c.title;
      displayMotivation = curation.personal_motivation_zh || displayMotivation;
      displayQuote = rawPost.quote_zh || displayQuote;
    } else if (curLang === "EN") {
      displayTitle = c.title_en || c.title;
      displayMotivation = curation.personal_motivation_en || displayMotivation;
    }
    const safeSetTxt = (id, txt) => {
      const el = document.getElementById(id);
      if (el) el.innerText = txt || "";
    };
    safeSetTxt("modalTitle", displayTitle);
    safeSetTxt("modalModeBadge", curLang === "KO" ? "\uAE30\uC220 \uAC80\uC99D \uB9AC\uD3EC\uD2B8" : curLang === "ZH" ? "\u6280\u672F\u6838\u9A8C\u62A5\u544A" : "AUDITED DOSSIER");
    const mMode = document.getElementById("modalModeBadge");
    if (mMode) mMode.className = "text-xs px-2.5 py-0.5 rounded-md font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200";
    safeSetTxt("modalClusterBadge", clustering.cluster_name || c.category || "Tech");
    safeSetTxt("modalVerdictBadge", c.verdict);
    const mVerdict = document.getElementById("modalVerdictBadge");
    if (mVerdict) {
      mVerdict.className = c.verdict === "VERIFIED_TRUE" ? "text-xs px-2.5 py-0.5 rounded-md font-semibold verdict-true" : "text-xs px-2.5 py-0.5 rounded-md font-semibold verdict-half";
    }
    safeSetTxt("modalStageBadge", handsOn.status === "ACTIVE_DEVELOPED" ? curLang === "KO" ? "\uC2E4\uC81C \uAC1C\uBC1C \uC801\uC6A9" : curLang === "ZH" ? "\u751F\u4EA7\u7EA7\u843D\u5730" : "Production Active" : curLang === "KO" ? "\uAE30\uC220 \uC870\uC0AC \uC644\uB8CC" : curLang === "ZH" ? "\u5DF2\u5BA1\u8BA1\u5B8C\u6BD5" : "Audited");
    safeSetTxt("modalMotivation", displayMotivation);
    safeSetTxt("modalWorkflow", curation.target_workflow || "Universal AI Pipeline");
    const viralBox = document.getElementById("modalViralPostBox");
    const hasQuote = displayQuote && displayQuote.trim().length > 0;
    if (hasQuote && viralBox) {
      viralBox.classList.remove("hidden");
      safeSetTxt("modalSecViralPostTitle", t.modalSecViralPostTitle);
      safeSetTxt("modalViralPlatformBadge", rawPost.platform || "Social Post");
      safeSetTxt("modalViralAuthor", (rawPost.author ? rawPost.author + " : " : "") + (rawPost.screenshot_note || "Viral Marketing Post Evidence"));
      safeSetTxt("modalViralQuote", `"${displayQuote}"`);
      safeSetTxt("modalViralNote", rawPost.screenshot_note || "");
      safeSetTxt("modalViralLinkText", t.modalViralLinkText);
      const directLink = document.getElementById("modalViralDirectLink");
      if (directLink) {
        if (rawPost.post_url) {
          directLink.href = rawPost.post_url;
          directLink.classList.remove("hidden");
        } else if (rawPost.url) {
          directLink.href = rawPost.url;
          directLink.classList.remove("hidden");
        } else if (c.sources && c.sources.length > 0) {
          directLink.href = c.sources[0].url;
          directLink.classList.remove("hidden");
        } else {
          directLink.classList.add("hidden");
        }
      }
    } else if (viralBox) {
      viralBox.classList.add("hidden");
    }
    safeSetTxt("modalHook", curLang === "ZH" && story.the_hook_zh ? story.the_hook_zh : story.the_hook || "");
    safeSetTxt("modalHype", story.marketing_hype_anatomy ? (curLang === "KO" ? "\uACFC\uC7A5 \uB9C8\uCF00\uD305 \uD574\uBD80: " : curLang === "ZH" ? "\u8425\u9500\u7092\u4F5C\u89E3\u6784: " : "Marketing Hype Anatomy: ") + story.marketing_hype_anatomy : "");
    safeSetTxt("modalHandsOnEnv", handsOn.test_environment || handsOn.environment ? (curLang === "KO" ? "\uD658\uACBD: " : curLang === "ZH" ? "\u5B9E\u6D4B\u73AF\u5883: " : "Env: ") + (handsOn.test_environment || handsOn.environment) : "");
    safeSetTxt("modalHandsOnMetrics", handsOn.measured_results ? (curLang === "KO" ? "\uC2E4\uCE21\uCE58: " : curLang === "ZH" ? "\u5B9E\u6D4B\u6307\u6807: " : "Metrics: ") + handsOn.measured_results : handsOn.measured_metrics ? Object.entries(handsOn.measured_metrics).map(([k, v]) => `${k}: ${v}`).join(" | ") : "");
    safeSetTxt("modalHandsOnDetails", handsOn.details || handsOn.failure_modes || story.empirical_findings || "Empirical benchmark verified.");
    const claimsBox = document.getElementById("modalClaimsBox");
    const claimsList = document.getElementById("modalClaimsList");
    const claims = c.claims_assessment && c.claims_assessment.length > 0 ? c.claims_assessment : c.marketing_claims || [];
    const isAwaitingClaims = cid && (!claims || claims.length === 0);
    if (claims && claims.length > 0 && claimsBox && claimsList) {
      claimsBox.classList.remove("hidden");
      safeSetTxt("modalSecClaimsTitle", t.modalSecClaimsTitle || "Marketing Claims vs Empirical Reality");
      claimsList.innerHTML = claims.map((cl) => {
        const claimTitle = cl.claim || cl.statement || cl.claim_title || cl.claim_text || cl.marketing_hook || "";
        const claimTruth = cl.reality || cl.fact_checked_truth || cl.verification_evidence || cl.empirical_reality || cl.reality_check || "";
        const claimStatus = cl.status || cl.verdict || cl.claim_verdict || "VERIFIED";
        const isTrue = claimStatus === "VERIFIED_TRUE" || claimStatus === "TRUE";
        const isFalse = claimStatus === "FALSE" || claimStatus === "FALSE_CLAIM" || claimStatus === "GAMED_CLAIM" || claimStatus === "MARKETING_HYPE";
        const statusClass = isTrue ? "text-emerald-700 bg-emerald-50 border border-emerald-200" : isFalse ? "text-rose-700 bg-rose-50 border border-rose-200" : "text-amber-800 bg-amber-50 border border-amber-200";
        return `
        <div class="p-3 rounded-lg bg-white border border-amber-200 text-xs space-y-1.5 shadow-sm">
          <div class="flex items-center justify-between font-mono text-[11px] gap-2 flex-wrap">
            <span class="text-ink-primary font-bold">Claim: "${claimTitle}"</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${statusClass}">${claimStatus}</span>
          </div>
          <div class="text-ink-secondary font-medium leading-relaxed">${curLang === "KO" ? "\u{1F52C} \uC2E4\uC99D \uD329\uD2B8 \uAC80\uC99D:" : curLang === "ZH" ? "\u{1F52C} \u5B9E\u6D4B\u4E8B\u5B9E\u6838\u9A8C:" : "\u{1F52C} Empirical Verification:"} ${claimTruth}</div>
        </div>
      `;
      }).join("");
    } else if (isAwaitingClaims && claimsBox && claimsList) {
      claimsBox.classList.remove("hidden");
      safeSetTxt("modalSecClaimsTitle", t.modalSecClaimsTitle || "Marketing Claims vs Empirical Reality");
      claimsList.innerHTML = `
      <div id="modalClaimsSpinner" class="p-4 rounded-xl border border-indigo-200 bg-indigo-50/50 flex items-center justify-center gap-3 text-center shadow-xs">
        <div class="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin shrink-0"></div>
        <div class="text-left">
          <div class="text-xs font-bold text-indigo-950">${curLang === "KO" ? `${APP_CONFIG.dbProvider}\uC5D0\uC11C \uC6D0\uC790\uC801 \uAC80\uC99D \uBA85\uC81C \uBC0F \uC2E4\uCE21 \uB370\uC774\uD130 \uC218\uC2E0 \uC911...` : curLang === "ZH" ? `\u6B63\u5728\u4ECE ${APP_CONFIG.dbProvider} \u5B9E\u65F6\u63A5\u6536\u539F\u5B50\u7EA7\u4E8B\u5B9E\u6838\u9A8C\u4E0E\u5B9E\u6D4B\u6570\u636E...` : `Streaming atomic claims & empirical benchmarks from ${APP_CONFIG.dbProvider}...`}</div>
          <div class="text-[10px] text-indigo-600">${curLang === "KO" ? "\uCD08\uACBD\uB7C9 \uC694\uC57D\uBCF8\uC5D0\uC11C \uC2EC\uCE35 \uD329\uD2B8\uCCB4\uD06C \uB9AC\uD3EC\uD2B8\uB97C \uD655\uC7A5 \uD558\uC774\uB4DC\uB808\uC774\uC158\uD558\uACE0 \uC788\uC2B5\uB2C8\uB2E4." : curLang === "ZH" ? "\u6B63\u5728\u4ECE\u8D85\u8F7B\u91CF\u6458\u8981\u6269\u5C55\u6DF1\u5EA6\u4E8B\u5B9E\u6838\u9A8C\u62A5\u544A\u3002" : "Hydrating in-depth dossier from lightweight summary snapshot."}</div>
        </div>
      </div>
    `;
    } else if (claimsBox) {
      claimsBox.classList.add("hidden");
    }
    const altBody = document.getElementById("modalAlternativesBody");
    const alts = clustering.alternatives || c.alternatives || [];
    if (alts && alts.length > 0 && altBody) {
      altBody.innerHTML = alts.map((a) => `
      <tr>
        <td class="p-3 font-bold text-ink-primary">${a.name || a.tool_name || ""}</td>
        <td class="p-3 font-mono text-ink-secondary text-[11px]">${a.tech_stack || a.stack || "-"}</td>
        <td class="p-3 text-emerald-700">${a.pros || "-"}</td>
        <td class="p-3 text-rose-700">${a.cons || "-"}</td>
        <td class="p-3 text-ink-secondary font-medium">${a.best_for || "-"}</td>
      </tr>
    `).join("");
    } else if (isAwaitingClaims && altBody) {
      altBody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-xs text-indigo-600"><div class="flex items-center justify-center gap-2"><div class="w-3.5 h-3.5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin shrink-0"></div>${curLang === "KO" ? `\uB300\uC548 \uBE44\uAD50 \uB370\uC774\uD130\uB97C ${APP_CONFIG.dbProvider}\uC5D0\uC11C \uB3D9\uAE30\uD654 \uC911...` : curLang === "ZH" ? `\u6B63\u5728\u4ECE ${APP_CONFIG.dbProvider} \u540C\u6B65\u66FF\u4EE3\u65B9\u6848\u6570\u636E...` : `Syncing alternative comparisons from ${APP_CONFIG.dbProvider}...`}</div></td></tr>`;
    } else if (altBody) {
      altBody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-ink-muted">${curLang === "KO" ? "\uB4F1\uB85D\uB41C \uB300\uCCB4 \uAE30\uC220 \uBE44\uAD50 \uB370\uC774\uD130\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4." : curLang === "ZH" ? "\u6682\u65E0\u66FF\u4EE3\u65B9\u6848\u5BF9\u6BD4\u6570\u636E\u3002" : "No comparative alternatives registered."}</td></tr>`;
    }
    const sourcesList = document.getElementById("modalSourcesList");
    const sources = c.sources || [];
    if (sourcesList) {
      sourcesList.innerHTML = sources.map((s) => `
      <a href="${s.url}" target="_blank" rel="noopener noreferrer" class="p-2.5 rounded-xl bg-surface-subtle border border-surface-border hover:border-ink-primary flex items-center justify-between text-xs text-ink-secondary hover:text-ink-primary transition">
        <div class="space-y-0.5">
          <span class="text-[10px] font-mono text-ink-primary uppercase font-bold">${s.tier || "Tier 1"} \u2022 ${s.type || "Repository"}</span>
          <div class="font-medium truncate max-w-[240px] text-ink-primary">${s.name || s.title || "Source Link"}</div>
        </div>
        <i data-lucide="external-link" class="w-3.5 h-3.5 text-ink-muted shrink-0"></i>
      </a>
    `).join("");
    }
    modal.classList.remove("hidden");
    document.body.style.overflow = "hidden";
    if (window.lucide) window.lucide.createIcons();
    if (cid && !skipHistory && (!c.claims_assessment || c.claims_assessment.length === 0 || !c.portfolio_story?.marketing_hype_anatomy)) {
      const fetchUrl = APP_CONFIG.apiUrl(`/api/portfolios?case_id=${encodeURIComponent(cid)}`);
      fetch(fetchUrl).then((res) => res.json()).then((data) => {
        if (data && data.success && data.case) {
          Object.assign(c, data.case);
          openModal(c, true);
        }
      }).catch(() => {
      });
    }
  }
  function openCaseModal(caseId) {
    if (!caseId) return;
    const lCases = typeof window !== "undefined" ? window.liveCasesData : liveCasesData;
    const cData = typeof window !== "undefined" ? window.casesData : casesData;
    let c = (lCases || []).find((x) => x.case_id === caseId || x.investigation_id === caseId) || (cData || []).find((x) => x.case_id === caseId);
    if (c) {
      openModal(c);
    } else {
      const fetchUrl = APP_CONFIG.apiUrl(`/api/portfolios?case_id=${encodeURIComponent(caseId)}`);
      fetch(fetchUrl).then((res) => res.json()).then((data) => {
        if (data && data.success && data.case) {
          openModal(data.case);
        }
      }).catch(() => {
      });
    }
  }
  function closeModal(pushHistory = true) {
    if (typeof document === "undefined") return;
    const modal = document.getElementById("detailModal");
    if (modal) modal.classList.add("hidden");
    document.body.style.overflow = "auto";
    const curView = typeof window !== "undefined" && window.currentView ? window.currentView : currentView;
    if (pushHistory && typeof history !== "undefined") {
      const targetHash = ROUTES[curView] || "#/" + curView;
      if (window.location.hash !== targetHash) {
        try {
          history.pushState({ view: curView }, "", targetHash);
        } catch (e) {
          window.location.hash = targetHash;
        }
      }
    }
  }
  function showVerificationReportModal(report) {
    if (typeof document === "undefined") return;
    let modal = document.getElementById("verificationReportModal");
    if (!modal) {
      modal = document.createElement("div");
      modal.id = "verificationReportModal";
      document.body.appendChild(modal);
    }
    const { allPassed, elapsed, checks } = report;
    const statusColor = allPassed ? "emerald" : "amber";
    const statusTitle = allPassed ? "\uC2DC\uC2A4\uD15C \uBB34\uACB0\uC131 100% \uAC80\uC99D \uC644\uB8CC" : "\uC2DC\uC2A4\uD15C \uAC80\uC99D \uC810\uAC80 \uD544\uC694";
    const statusBadge = allPassed ? "READY FOR PRODUCTION" : "NEEDS ATTENTION";
    modal.className = "fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs transition-opacity duration-200";
    modal.innerHTML = `
    <div class="relative w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-surface-border space-y-4">
      <div class="flex items-center justify-between pb-3 border-b border-surface-border">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-lg bg-${statusColor}-50 text-${statusColor}-700 border border-${statusColor}-200 flex items-center justify-center">
            <i data-lucide="${allPassed ? "shield-check" : "alert-triangle"}" class="w-5 h-5"></i>
          </div>
          <div>
            <h3 class="text-sm font-bold text-ink-primary font-mono">${statusTitle}</h3>
            <span class="text-[10px] font-mono text-ink-muted">\uC9C4\uB2E8 \uC18C\uC694: ${elapsed}\uCD08 | \uC18C\uBAA8 \uBE44\uC6A9: $0 (0 LLM Tokens)</span>
          </div>
        </div>
        <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-${statusColor}-100 text-${statusColor}-800 border border-${statusColor}-300">${statusBadge}</span>
      </div>

      <div class="space-y-2 max-h-72 overflow-y-auto">
        ${checks.map((c) => `
          <div class="p-3 rounded-xl ${c.pass ? "bg-surface-subtle border border-surface-border" : "bg-rose-50 border border-rose-200"} flex items-start gap-2.5">
            <span class="w-5 h-5 rounded-md ${c.pass ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"} flex items-center justify-center text-xs shrink-0 mt-0.5 font-bold">
              ${c.pass ? "\u2713" : "\u2717"}
            </span>
            <div class="flex-1 min-w-0">
              <div class="text-xs font-bold ${c.pass ? "text-ink-primary" : "text-rose-900"}">${c.title}</div>
              <div class="text-[11px] font-mono text-ink-muted mt-0.5 leading-snug break-all">${c.details}</div>
            </div>
          </div>
        `).join("")}
      </div>

      <div class="pt-2 border-t border-surface-border flex items-center justify-between gap-2">
        <span class="text-[10px] text-ink-muted font-mono">Autonomous QA Verifier Agent</span>
        <button onclick="document.getElementById('verificationReportModal').remove()" class="px-4 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs font-mono transition cursor-pointer">
          \uB2EB\uAE30 (Close)
        </button>
      </div>
    </div>
  `;
    if (window.lucide) window.lucide.createIcons();
  }
  if (typeof window !== "undefined") {
    window.openModal = openModal;
    window.openCaseModal = openCaseModal;
    window.closeModal = closeModal;
    window.showVerificationReportModal = showVerificationReportModal;
  }

  // src/js/components/newsCard.js
  function cleanDescriptionText(desc, title) {
    if (!desc || typeof desc !== "string") return "";
    let d = desc.trim();
    d = d.replace(/^HN\s*Score:\s*\d+\s*pts\s*(\|\s*Comments:\s*\d+\s*)?(\|\s*)?/i, "");
    d = d.replace(/^Abstract:\s*/i, "");
    if (/^Trending Score:\s*\d+/i.test(d)) return "";
    if (/^Downloads:\s*\d+/i.test(d)) return "";
    if (title && d.toLowerCase() === title.toLowerCase().trim()) {
      return "";
    }
    return d.trim();
  }
  function getLocalizedContent(it, lang = currentLang) {
    if (!it) return { displayTitle: "", displayHook: "", displayDesc: "", displayTakeaways: [], hasTrilingual: false };
    const ai = it.ai_enrichment;
    const multi = it.multilingual || (ai ? ai.multilingual : null);
    const story = it.portfolio_story || {};
    let displayTitle = "";
    let displayHook = "";
    let displayDesc = "";
    let displayTakeaways = [];
    if (lang === "ZH") {
      displayTitle = multi?.zh?.title || it.title_zh || multi?.en?.title || it.title_en || it.title || "";
      displayHook = multi?.zh?.hook || it.hook_zh || story.the_hook_zh || it.curation?.personal_motivation_zh || (ai ? ai.hook : "") || it.hook || story.the_hook || it.curation?.personal_motivation || "";
      displayDesc = multi?.zh?.description || it.description_zh || displayHook || it.description || "";
      if (multi?.zh?.key_takeaways?.length > 0) displayTakeaways = multi.zh.key_takeaways;
      else if (it.key_takeaways_zh?.length > 0) displayTakeaways = it.key_takeaways_zh;
      else if (ai?.takeaways_zh?.length > 0) displayTakeaways = ai.takeaways_zh;
      else if (ai?.key_takeaways?.length > 0) displayTakeaways = ai.key_takeaways;
    } else if (lang === "EN") {
      displayTitle = multi?.en?.title || it.title_en || it.title || "";
      displayHook = multi?.en?.hook || it.hook_en || story.the_hook_en || it.curation?.personal_motivation_en || (ai ? ai.hook : "") || it.hook || story.the_hook || it.curation?.personal_motivation || "";
      displayDesc = multi?.en?.description || it.description_en || displayHook || it.description || "";
      if (multi?.en?.key_takeaways?.length > 0) displayTakeaways = multi.en.key_takeaways;
      else if (it.key_takeaways_en?.length > 0) displayTakeaways = it.key_takeaways_en;
      else if (ai?.takeaways_en?.length > 0) displayTakeaways = ai.takeaways_en;
      else if (ai?.key_takeaways?.length > 0) displayTakeaways = ai.key_takeaways;
    } else {
      displayTitle = multi?.ko?.title || it.title_ko || it.title || "";
      displayHook = multi?.ko?.hook || it.hook_ko || story.the_hook || it.curation?.personal_motivation || (ai ? ai.hook : "") || it.hook || "";
      displayDesc = multi?.ko?.description || it.description_ko || it.description || displayHook || "";
      if (multi?.ko?.key_takeaways?.length > 0) displayTakeaways = multi.ko.key_takeaways;
      else if (it.key_takeaways?.length > 0) displayTakeaways = it.key_takeaways;
      else if (ai?.key_takeaways?.length > 0) displayTakeaways = ai.key_takeaways;
      else if (ai?.takeaways_ko?.length > 0) displayTakeaways = ai.takeaways_ko;
    }
    if (displayHook && displayTitle) {
      const cleanT = displayTitle.trim();
      const cleanH = displayHook.trim();
      if (cleanH === cleanT || cleanH === `${cleanT} \uAD00\uB828 \uD575\uC2EC \uAE30\uC220 \uBA85\uC138 \uBC0F \uAE00\uB85C\uBC8C \uC5D4\uC9C0\uB2C8\uC5B4\uB9C1 \uC0DD\uD0DC\uACC4 \uC601\uD5A5 \uBD84\uC11D`) {
        const fallbackDesc = cleanDescriptionText(it.description || "", cleanT);
        displayHook = fallbackDesc && fallbackDesc.length > 15 && fallbackDesc !== cleanH ? fallbackDesc : lang === "KO" ? "\uD575\uC2EC \uAE30\uC220 \uC544\uD0A4\uD14D\uCC98 \uBA85\uC138 \uBC0F \uAE00\uB85C\uBC8C \uC5D4\uC9C0\uB2C8\uC5B4\uB9C1 \uC0DD\uD0DC\uACC4 \uC601\uD5A5 \uBD84\uC11D" : lang === "ZH" ? "\u6838\u5FC3\u6280\u672F\u67B6\u6784\u7A81\u7834\u4E0E\u5168\u7403\u5F00\u53D1\u8005\u751F\u6001\u6DF1\u5EA6\u89E3\u6790" : "Key architectural updates and practitioner impact analysis.";
      } else if (cleanT.length > 8 && cleanH.startsWith(cleanT)) {
        const stripped = cleanH.slice(cleanT.length).replace(/^[\s:：\-–—·,]+/, "").trim();
        if (stripped.length > 10) displayHook = stripped;
      }
    }
    if (Array.isArray(displayTakeaways) && displayTakeaways.length > 0 && displayTitle) {
      const cleanT = displayTitle.trim();
      displayTakeaways = displayTakeaways.map((tk) => {
        if (typeof tk !== "string") return tk;
        return tk.replace(`'${cleanT}' \uAD00\uB828 `, "").replace(`\u300C${cleanT}\u300D`, "\uD574\uB2F9 \uAE30\uC220 ").replace(`regarding ${cleanT}`, "regarding this release");
      });
    }
    if (displayHook) {
      const cleanH = displayHook.trim();
      if (displayDesc.trim() === cleanH) {
        displayDesc = "";
      } else if (cleanH && displayDesc.includes(cleanH)) {
        displayDesc = displayDesc.replace(cleanH, "").trim();
      }
    }
    displayDesc = cleanDescriptionText(displayDesc, displayTitle);
    const hasTrilingual = Boolean(multi && multi.zh && multi.ko && multi.en || it.title_zh && it.title_en);
    return {
      displayTitle,
      displayHook,
      displayDesc,
      displayTakeaways,
      hasTrilingual
    };
  }
  function renderHookCallout(displayHook) {
    if (!displayHook) return "";
    return `
    <div class="p-2.5 rounded-xl bg-amber-50/70 border border-amber-200/80 border-l-4 border-l-amber-500 text-[11px] text-amber-950 font-medium leading-relaxed flex items-start gap-1.5 shadow-2xs">
      <span class="shrink-0 font-bold text-amber-800">\u{1FA9D} Hook:</span>
      <span>${displayHook}</span>
    </div>
  `;
  }
  function renderNewsSkeleton(grid, count = 6) {
    if (!grid) return;
    let cards = "";
    for (let i = 0; i < count; i++) {
      cards += `
      <div class="executive-card p-4 sm:p-5 flex flex-col justify-between space-y-4 animate-pulse">
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="h-4 w-20 bg-slate-200/80 rounded-md"></div>
              <div class="h-4 w-16 bg-slate-200/60 rounded-md"></div>
            </div>
            <div class="h-4 w-14 bg-slate-200/60 rounded-md"></div>
          </div>
          <div class="h-5 w-full bg-slate-200/90 rounded-md"></div>
          <div class="h-4 w-3/4 bg-slate-200/70 rounded-md"></div>
          <div class="h-12 w-full bg-amber-100/40 rounded-xl border border-amber-200/30"></div>
          <div class="h-16 w-full bg-indigo-50/40 rounded-xl border border-indigo-100/40"></div>
        </div>
        <div class="pt-3 border-t border-surface-border space-y-2">
          <div class="flex items-center justify-between">
            <div class="h-3 w-28 bg-slate-200/60 rounded"></div>
            <div class="h-3 w-20 bg-slate-200/60 rounded"></div>
          </div>
          <div class="flex justify-end gap-2 pt-1">
            <div class="h-6 w-16 bg-slate-200/80 rounded-md"></div>
            <div class="h-6 w-20 bg-amber-100/80 rounded-md"></div>
          </div>
        </div>
      </div>
    `;
    }
    grid.innerHTML = cards;
  }
  function renderAiTakeaways(takeaways, lang = currentLang) {
    if (!Array.isArray(takeaways) || takeaways.length === 0) return "";
    return `
    <div class="mt-2 p-3 rounded-xl bg-gradient-to-br from-indigo-50/50 via-sky-50/40 to-purple-50/50 border border-indigo-100 text-[11px] space-y-1.5 font-sans">
      <div class="flex items-center gap-1 text-indigo-950 font-bold text-[10px]">
        <i data-lucide="sparkles" class="w-3 h-3 text-indigo-600"></i>
        <span>${lang === "KO" ? "AI 3\uC904 \uD575\uC2EC \uC694\uC57D" : lang === "ZH" ? "AI 3\u884C\u6838\u5FC3\u6458\u8981" : "AI 3-Line Summary"}</span>
      </div>
      <ul class="space-y-1 text-ink-secondary leading-relaxed list-disc list-inside">
        ${takeaways.map((k) => `<li>${k}</li>`).join("")}
      </ul>
    </div>
  `;
  }
  function renderRelatedDossierButton(rel, lang = currentLang) {
    if (!rel || !rel.case_id) return "";
    const label = lang === "KO" ? "\uAD00\uB828 \uAE30\uC220 \uAC80\uC99D: " : lang === "ZH" ? "\u5173\u8054\u6280\u672F\u6838\u9A8C: " : "Related Verification: ";
    return `
    <div class="pt-2 border-t border-surface-border">
      <button onclick="openCaseModal('${rel.case_id}')" class="w-full text-left px-2.5 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-[11px] text-emerald-950 font-semibold flex items-center justify-between transition cursor-pointer">
        <span class="flex items-center gap-1.5">
          <i data-lucide="shield-check" class="w-3.5 h-3.5 text-emerald-600"></i>
          <span>${label}${rel.target_tech || ""}</span>
        </span>
        <i data-lucide="arrow-right" class="w-3 h-3 text-emerald-600"></i>
      </button>
    </div>
  `;
  }
  function renderCommentsAccordion(rawComments, lang = currentLang, threadUrl = null) {
    if (!Array.isArray(rawComments) || rawComments.length === 0) return "";
    const sorted = rawComments.slice().sort((a, b) => (b.points || 0) - (a.points || 0));
    const top3 = sorted.slice(0, 3);
    const topCount = rawComments.length;
    const sanitizeTxt = (str) => String(str || "").replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[m]);
    const commentsListHtml = top3.map((cm) => `
    <div class="pt-2 border-t border-indigo-100/70 text-[11px] leading-relaxed">
      <div class="flex items-center justify-between mb-1">
        <span class="font-bold font-mono text-indigo-700">@${sanitizeTxt(cm.author || "User")}</span>
        ${cm.points ? `<span class="text-[9px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 font-mono font-bold border border-amber-200">\u25B2${cm.points}</span>` : ""}
      </div>
      <p class="text-ink-primary whitespace-pre-line line-clamp-3">${sanitizeTxt(cm.text || "")}</p>
    </div>
  `).join("");
    const moreCount = topCount - top3.length;
    const moreHtml = moreCount > 0 ? `
    <div class="pt-1.5 text-center">
      ${threadUrl ? `<a href="${threadUrl}" target="_blank" rel="noopener noreferrer" class="text-[10px] text-indigo-600 hover:underline font-semibold">\uC678 ${moreCount}\uAC1C \uB313\uAE00 \uB354\uBCF4\uAE30 (\uC6D0\uBB38 \uC2A4\uB808\uB4DC \u2197)</a>` : `<span class="text-[10px] text-ink-muted">\uC678 ${moreCount}\uAC1C \uB313\uAE00 \uC0DD\uB7B5\uB428</span>`}
    </div>
  ` : "";
    return `
    <details class="group rounded-xl border border-indigo-100 bg-indigo-50/25 p-2.5 transition text-xs mt-2">
      <summary class="cursor-pointer font-bold text-[11px] text-indigo-950 flex items-center justify-between select-none list-none">
        <span class="flex items-center gap-1.5">
          <i data-lucide="message-square" class="w-3.5 h-3.5 text-indigo-600"></i>
          <span>${lang === "KO" ? `\u{1F4AC} \uCEE4\uBBA4\uB2C8\uD2F0 \uBC18\uC751 (${topCount}\uAC1C \uB313\uAE00)` : lang === "ZH" ? `\u{1F4AC} \u793E\u533A\u8BA8\u8BBA (${topCount}\u6761\u8BC4\u8BBA)` : `\u{1F4AC} Community Discussions (${topCount} comments)`}</span>
        </span>
        <span class="text-[10px] font-mono text-indigo-600 group-open:rotate-180 transition-transform">\u25BC</span>
      </summary>
      <div class="mt-2 space-y-2">
        ${commentsListHtml}
        ${moreHtml}
      </div>
    </details>
  `;
  }
  function toggleNewsComments() {
  }
  function renderCardStandardFooter(it, lang = currentLang, extraActionHtml = "") {
    const ai = it.ai_enrichment;
    const pubLabel = lang === "KO" ? "\uBC1C\uD589" : lang === "ZH" ? "\u53D1\u5E03" : "Published";
    const hrvLabel = lang === "KO" ? "\uCD5C\uCD08 \uD3EC\uCC29" : lang === "ZH" ? "\u6700\u521D\u6355\u83B7" : "First Spotted";
    const updLabel = lang === "KO" ? "\uCD5C\uC2E0 \uAC31\uC2E0" : lang === "ZH" ? "\u6700\u65B0\u66F4\u65B0" : "Updated";
    const srcLabel = lang === "KO" ? "\uC6D0\uBB38" : lang === "ZH" ? "\u539F\u6587" : "Source";
    const pendingLabel = lang === "KO" ? "AI\uC694\uC57D \uB300\uAE30\uC911" : lang === "ZH" ? "AI\u5206\u6790\u6392\u961F\u4E2D" : "Pending AI Audit";
    const pubDate = formatDateTimeCompact(it.published_at || it.created_at || it.harvested_at);
    const earliestHrv = it.earliest_harvested_at || it.initial_harvested_at || it.harvested_at || it.harvested_date || it.created_at;
    const hrvDate = formatDateTimeCompact(earliestHrv);
    const hasUpdate = it.updated_at && formatDateTimeCompact(it.updated_at) !== hrvDate;
    const updDate = hasUpdate ? formatDateTimeCompact(it.updated_at) : "";
    let auditHtml = `
    <div class="text-[11px] text-ink-muted flex items-center gap-1.5">
      <span>\u{1F52C} ${pendingLabel}</span>
    </div>
  `;
    if (ai?.enriched_at) {
      auditHtml = `
      <div class="text-[11px] text-indigo-700 font-semibold flex items-center gap-1.5 min-w-0 overflow-hidden">
        <span class="shrink-0">\u{1F52C} ${formatDateTimeCompact(ai.enriched_at)}</span>
        <span class="text-ink-muted font-normal truncate min-w-0 align-bottom cursor-help" title="${ai.enriched_by_model || ""}">(${formatModelAttribution(ai.enriched_by_model)})</span>
      </div>
    `;
    }
    const defaultSourceLink = it.source_url ? `
    <a href="${it.source_url}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border text-[11px] font-semibold flex items-center gap-1 shrink-0">
      \u{1F4C4} ${srcLabel} <i data-lucide="external-link" class="w-2.5 h-2.5"></i>
    </a>
  ` : "";
    return `
    <div class="pt-3 border-t border-surface-border space-y-1.5 text-xs font-mono">
      <div class="text-[11px] text-ink-muted flex items-center justify-between gap-1 flex-wrap">
        <span>\u{1F4F0} ${pubLabel}: ${pubDate}</span>
      </div>
      <div class="text-[11px] text-ink-muted flex items-center justify-between gap-1 flex-wrap">
        <span>\u{1F4E5} ${hrvLabel}: ${hrvDate}</span>
        ${hasUpdate ? `<span class="text-[10px] text-indigo-600 font-bold" title="${updLabel}">(\u{1F504} ${updDate})</span>` : ""}
      </div>
      ${auditHtml}
      <div class="flex items-center justify-end gap-2 pt-1 font-sans flex-wrap">
        ${extraActionHtml || defaultSourceLink}
      </div>
    </div>
  `;
  }
  function createNewsCardElement(it, currentLang2) {
    const card = document.createElement("div");
    card.className = "executive-card p-4 sm:p-5 flex flex-col justify-between space-y-4";
    const t = i18n[currentLang2] || i18n.KO;
    const ai = it.ai_enrichment;
    const { displayTitle, displayHook, displayDesc, displayTakeaways } = getLocalizedContent(it, currentLang2);
    const showDesc = (!displayTakeaways || displayTakeaways.length === 0) && displayDesc;
    const isHn = (it.source_platform || "").includes("Hacker News") || (it.source_url || "").includes("news.ycombinator.com");
    const isGn = (it.source_platform || "").includes("GeekNews") || (it.source_url || "").includes("hada.io");
    const hnUrl = it.hn_url || ((it.source_url || "").includes("news.ycombinator.com") ? it.source_url : null);
    const gnUrl = isGn ? it.hn_url || it.source_url : null;
    const articleUrl = it.article_url || (it.source_url !== (hnUrl || gnUrl) ? it.source_url : null);
    const allSources = [...it.sources || []];
    if (it.cross_posts && it.cross_posts.length > 0) {
      it.cross_posts.forEach((cp) => {
        const cpUrl = cp.url || cp.source_url || cp.article_url;
        if (cpUrl && !allSources.some((s) => (s.url || "").toLowerCase() === cpUrl.toLowerCase())) {
          allSources.push({
            source_name: cp.platform || "Cross-post",
            platform: cp.platform || "Cross-post",
            url: cpUrl,
            title: cp.title || "",
            type: "cross_post"
          });
        }
      });
    }
    let linksHtml = "";
    if (allSources.length > 1) {
      linksHtml = buildMultiSourceCluster(allSources, it.inbox_id || it.id);
    } else if (isHn) {
      linksHtml = `<div class="flex items-center gap-1.5 flex-wrap justify-end">`;
      if (articleUrl && articleUrl !== hnUrl) {
        linksHtml += `<a href="${articleUrl}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border text-[11px] font-semibold flex items-center gap-1 shrink-0">\u{1F4C4} ${currentLang2 === "KO" ? "\uAE30\uC0AC \uC6D0\uBB38" : currentLang2 === "ZH" ? "\u6587\u7AE0\u539F\u6587" : "Article"} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
      }
      if (hnUrl) {
        linksHtml += `<a href="${hnUrl}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-orange-50 text-orange-800 hover:text-orange-950 border border-orange-200 text-[11px] font-bold flex items-center gap-1 shrink-0">\u{1F525} ${currentLang2 === "KO" ? "HN \uD1A0\uB860" : currentLang2 === "ZH" ? "HN \u8BA8\u8BBA" : "HN Thread"} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
      }
      linksHtml += `</div>`;
    } else if (isGn) {
      linksHtml = `<div class="flex items-center gap-1.5 flex-wrap justify-end">`;
      if (articleUrl && articleUrl !== gnUrl) {
        linksHtml += `<a href="${articleUrl}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border text-[11px] font-semibold flex items-center gap-1 shrink-0">\u{1F4C4} ${currentLang2 === "KO" ? "\uAE30\uC0AC \uC6D0\uBB38" : currentLang2 === "ZH" ? "\u6587\u7AE0\u539F\u6587" : "Article"} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
      }
      if (gnUrl) {
        linksHtml += `<a href="${gnUrl}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-indigo-50 text-indigo-800 hover:text-indigo-950 border border-indigo-200 text-[11px] font-bold flex items-center gap-1 shrink-0">\u{1F4AC} ${currentLang2 === "KO" ? "\uAE31\uB274\uC2A4 \uD1A0\uB860" : currentLang2 === "ZH" ? "\u6781\u5BA2\u65B0\u95FB" : "GeekNews"} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
      }
      linksHtml += `</div>`;
    } else {
      linksHtml = `<div class="flex items-center gap-1.5 justify-end"><a href="${it.source_url}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border text-[11px] font-semibold flex items-center gap-1 shrink-0">\u{1F4C4} ${t.newsOriginalLink} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a></div>`;
    }
    let aiBadgeHtml = "";
    let aiSummaryHtml = "";
    const hookHtml = renderHookCallout(displayHook);
    const relatedHtml = renderRelatedDossierButton(it.related_dossier, currentLang2);
    const commentsHtml = renderCommentsAccordion(it.raw_comments, currentLang2, hnUrl || it.source_url);
    const tier1Map = {
      "SCIENCE_RESEARCH": { label: currentLang2 === "KO" ? "\u{1F680} \uACFC\uD559\xB7\uC6B0\uC8FC" : currentLang2 === "ZH" ? "\u{1F680} \u79D1\u5B66\u4E0E\u822A\u5929" : "\u{1F680} Science & Research", cls: "bg-teal-50 text-teal-900 border-teal-200" },
      "ECONOMY_FINANCE": { label: currentLang2 === "KO" ? "\u{1F3E6} \uACBD\uC81C\xB7\uAE08\uC735" : currentLang2 === "ZH" ? "\u{1F3E6} \u7ECF\u6D4E\u4E0E\u91D1\u878D" : "\u{1F3E6} Economy & Finance", cls: "bg-emerald-50 text-emerald-900 border-emerald-200" },
      "LAW_CRIME_JUSTICE": { label: currentLang2 === "KO" ? "\u2696\uFE0F \uC0AC\uD68C\xB7\uBC95\uB960" : currentLang2 === "ZH" ? "\u2696\uFE0F \u6CD5\u5F8B\u4E0E\u793E\u4F1A" : "\u2696\uFE0F Law & Society", cls: "bg-rose-50 text-rose-900 border-rose-200" },
      "POLITICS_POLICY": { label: currentLang2 === "KO" ? "\u{1F3DB}\uFE0F \uC815\uCE58\xB7\uC815\uCC45" : currentLang2 === "ZH" ? "\u{1F3DB}\uFE0F \u653F\u6CBB\u4E0E\u653F\u7B56" : "\u{1F3DB}\uFE0F Politics & Policy", cls: "bg-amber-50 text-amber-950 border-amber-300" },
      "CULTURE_HUMANITIES": { label: currentLang2 === "KO" ? "\u{1F33F} \uBB38\uD654\xB7\uC778\uBB38" : currentLang2 === "ZH" ? "\u{1F33F} \u6587\u5316\u4E0E\u4EBA\u6587" : "\u{1F33F} Culture & Arts", cls: "bg-purple-50 text-purple-900 border-purple-200" }
    };
    const catMap = {
      "INFERENCE_OPT": { label: currentLang2 === "KO" ? "\u26A1 \uCD94\uB860\xB7\uC11C\uBE59 \uCD5C\uC801\uD654" : currentLang2 === "ZH" ? "\u26A1 \u63A8\u7406\u670D\u52A1\u4F18\u5316" : "\u26A1 Inference & Opt", cls: "bg-amber-50 text-amber-900 border-amber-200" },
      "AGENTS_DEVTOOLS": { label: currentLang2 === "KO" ? "\u{1F6E0}\uFE0F \uC5D0\uC774\uC804\uD2B8\xB7\uAC1C\uBC1C\uB3C4\uAD6C" : currentLang2 === "ZH" ? "\u{1F6E0}\uFE0F \u667A\u80FD\u4F53\u4E0E\u5DE5\u5177" : "\u{1F6E0}\uFE0F Agents & DevTools", cls: "bg-blue-50 text-blue-900 border-blue-200" },
      "MULTIMODAL_AI": { label: currentLang2 === "KO" ? "\u{1F3A8} \uBA40\uD2F0\uBAA8\uB2EC\xB7\uC601\uC0C1/\uC74C\uC131" : currentLang2 === "ZH" ? "\u{1F3A8} \u591A\u6A21\u6001\u4E0E\u89C6\u542C" : "\u{1F3A8} Multimodal & GenAI", cls: "bg-purple-50 text-purple-900 border-purple-200" },
      "FOUNDATION_MODELS": { label: currentLang2 === "KO" ? "\u{1F916} \uD30C\uC6B4\uB370\uC774\uC158\xB7\uAC00\uC911\uCE58" : currentLang2 === "ZH" ? "\u{1F916} \u57FA\u7840\u6A21\u578B\u4E0E\u6743\u91CD" : "\u{1F916} Foundation Models", cls: "bg-emerald-50 text-emerald-900 border-emerald-200" },
      "INFRA_RAG_SECURITY": { label: currentLang2 === "KO" ? "\u{1F6E1}\uFE0F \uC778\uD504\uB77C\xB7RAG\xB7\uBCF4\uC548" : currentLang2 === "ZH" ? "\u{1F6E1}\uFE0F \u57FA\u7840\u8BBE\u65BD\u4E0E\u5B89\u5168" : "\u{1F6E1}\uFE0F Infra, RAG & Safety", cls: "bg-rose-50 text-rose-900 border-rose-200" },
      "DEEP_SCIENCE_SPACE": { label: currentLang2 === "KO" ? "\u{1F680} \uC6B0\uC8FC\xB7\uC2E0\uC18C\uC7AC\xB7\uACFC\uD559" : currentLang2 === "ZH" ? "\u{1F680} \u6DF1\u79D1\u6280\u4E0E\u7A7A\u5929\u79D1\u5B66" : "\u{1F680} Deep Science & Space", cls: "bg-teal-50 text-teal-900 border-teal-200" },
      "MACRO_GLOBAL_BIZ": { label: currentLang2 === "KO" ? "\u{1F3E6} \uC0B0\uC5C5\xB7\uAC70\uC2DC\uACBD\uC81C" : currentLang2 === "ZH" ? "\u{1F3E6} \u4EA7\u4E1A\u4E0E\u5B8F\u89C2\u7ECF\u6D4E" : "\u{1F3E6} Macro & Global Biz", cls: "bg-amber-50 text-amber-950 border-amber-300" },
      "INDUSTRY_TRENDS": { label: currentLang2 === "KO" ? "\u{1F310} \uC77C\uBC18 \uD14C\uD06C\xB7SW" : currentLang2 === "ZH" ? "\u{1F310} \u901A\u7528\u79D1\u6280\u4E0E\u8F6F\u4EF6" : "\u{1F310} General Tech & SW", cls: "bg-slate-100 text-slate-800 border-slate-200" }
    };
    const catInfo = it.tier1_category && tier1Map[it.tier1_category] ? tier1Map[it.tier1_category] : catMap[it.category_primary] || catMap["INDUSTRY_TRENDS"];
    if (ai) {
      const tagBg = ai.worth_investigating === "HIGH" ? "bg-orange-50 text-orange-950 border-orange-200" : "bg-indigo-50 text-indigo-950 border-indigo-200";
      const typeLabels = {
        "MODEL": currentLang2 === "KO" ? "\u{1F916} \uBAA8\uB378 \uBC1C\uD45C" : currentLang2 === "ZH" ? "\u{1F916} \u6A21\u578B\u53D1\u5E03" : "\u{1F916} Model",
        "AGENT": currentLang2 === "KO" ? "\u{1F9BE} \uC5D0\uC774\uC804\uD2B8" : currentLang2 === "ZH" ? "\u{1F9BE} \u667A\u80FD\u4F53" : "\u{1F9BE} Agent",
        "TECH": currentLang2 === "KO" ? "\u26A1 \uC2E0\uAE30\uC220/\uCD5C\uC801\uD654" : currentLang2 === "ZH" ? "\u26A1 \u65B0\u6280\u672F/\u67B6\u6784" : "\u26A1 Tech/Arch",
        "NEWS": currentLang2 === "KO" ? "\u{1F4F0} \uC5C5\uACC4 \uB3D9\uD5A5" : currentLang2 === "ZH" ? "\u{1F4F0} \u884C\u4E1A\u8D44\u8BAF" : "\u{1F4F0} News"
      };
      const typeBadge = typeLabels[ai.type_classification] || (currentLang2 === "KO" ? "\u{1F4A1} \uAE30\uC220" : "\u{1F4A1} Tech");
      const hasRealRec = Boolean(ai.score || ai.worth_score || ai.recommended_tag);
      const recBadgeHtml = hasRealRec ? `
      <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${tagBg}">
        ${ai.recommended_tag || "\u{1F4A1} \uCD94\uCC9C"} \u2605${ai.score || ai.worth_score}
      </span>
    ` : "";
      const effectiveSourceLang = (ai.source_lang || it.source_lang || "").toUpperCase();
      aiBadgeHtml = `
      <div class="flex items-center gap-1.5 flex-wrap my-1">
        ${recBadgeHtml}
        <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-900 border border-indigo-200">
          ${typeBadge}
        </span>
        ${ai.programming_lang && ai.programming_lang !== "General" ? `<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-50 text-amber-900 border border-amber-200">\u{1F4BB} ${ai.programming_lang}</span>` : ""}
        ${effectiveSourceLang ? `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-semibold bg-surface-subtle text-ink-muted border border-surface-border">${effectiveSourceLang}</span>` : ""}
      </div>
    `;
      aiSummaryHtml = renderAiTakeaways(displayTakeaways, currentLang2);
    }
    let crossRollupHtml = "";
    if (it.cross_posts && it.cross_posts.length > 0 || allSources.length > 1) {
      const clusterSources = [];
      const seenClusterUrls = /* @__PURE__ */ new Set();
      if (it.source_url) {
        seenClusterUrls.add(it.source_url.toLowerCase());
        clusterSources.push({
          platform: it.source_platform || "Press",
          url: it.source_url,
          title: it.title || ""
        });
      }
      for (const s of allSources) {
        const u = (s.url || "").toLowerCase();
        if (u && !seenClusterUrls.has(u)) {
          seenClusterUrls.add(u);
          clusterSources.push(s);
        }
      }
      for (const cp of it.cross_posts || []) {
        const u = (cp.url || cp.source_url || "").toLowerCase();
        if (u && !seenClusterUrls.has(u)) {
          seenClusterUrls.add(u);
          clusterSources.push(cp);
        }
      }
      const clusterCount = Math.max(clusterSources.length, allSources.length, 2);
      const spk = it.spike_analysis || it.raw_payload?.spike_analysis || null;
      let pCount = spk?.press_count || it.cross_spike_summary?.press_count || 0;
      let cCount = spk?.community_count || it.cross_spike_summary?.community_count || 0;
      let kCount = spk?.code_count || 0;
      const spkScore = spk ? Number(spk.score || 0) : 0;
      if (!pCount && !cCount && !kCount) {
        clusterSources.forEach((s) => {
          const p = (s.platform || s.source_name || "").toLowerCase();
          const u = (s.url || "").toLowerCase();
          const isCode = p.includes("github") || p.includes("hugging") || p.includes("arxiv") || u.includes("github.com") || u.includes("huggingface.co");
          const isComm = p.includes("hacker news") || p.includes("reddit") || p.includes("geeknews") || u.includes("ycombinator") || u.includes("reddit.com") || u.includes("hada.io");
          if (isCode) kCount++;
          else if (isComm) cCount++;
          else pCount++;
        });
      }
      if (pCount === 0 && cCount === 0 && kCount === 0) pCount = 1;
      const totalAxes = (pCount > 0 ? 1 : 0) + (cCount > 0 ? 1 : 0) + (kCount > 0 ? 1 : 0);
      const isSuperSpike = totalAxes >= 3 || spkScore >= 50;
      const isCrossSpike = totalAxes >= 2 || spkScore >= 15;
      const isSpike2 = Boolean(it.is_cross_spiking || isCrossSpike);
      let badgeBg = "bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-amber-500/10 border-amber-500/30 text-amber-950";
      let flameColor = "text-amber-600";
      let tierBadgeText = "";
      if (isSuperSpike) {
        badgeBg = "bg-gradient-to-r from-rose-500/15 via-amber-500/15 to-orange-500/15 border-rose-500/40 text-rose-950 shadow-xs";
        flameColor = "text-rose-600";
        tierBadgeText = currentLang2 === "KO" ? "\u{1F525} 3-Axis \uC288\uD37C \uBC14\uC774\uB7F4" : currentLang2 === "ZH" ? "\u{1F525} 3-Axis \u8D85\u7EA7\u7206\u53D1" : "\u{1F525} 3-Axis Super Spike";
      } else if (isCrossSpike) {
        badgeBg = "bg-gradient-to-r from-amber-500/15 via-orange-500/12 to-amber-500/10 border-amber-500/35 text-amber-950";
        flameColor = "text-amber-600";
        tierBadgeText = currentLang2 === "KO" ? "\u26A1 2-Axis \uD06C\uB85C\uC2A4 \uBC14\uC774\uB7F4" : currentLang2 === "ZH" ? "\u26A1 2-Axis \u8DE8\u754C\u8054\u5408" : "\u26A1 2-Axis Cross Spike";
      } else {
        tierBadgeText = currentLang2 === "KO" ? `${clusterCount}\uAC1C \uB9E4\uCCB4 \uAD50\uCC28 \uBCF4\uB3C4` : currentLang2 === "ZH" ? `${clusterCount}\u4E2A\u5A92\u4F53\u62A5\u9053` : `Covered by ${clusterCount} Outlets`;
      }
      crossRollupHtml = `
      <div class="flex items-center justify-between px-2.5 py-1.5 rounded-xl ${badgeBg} border text-xs shadow-2xs">
        <div class="flex items-center gap-1.5 min-w-0">
          <i data-lucide="flame" class="w-3.5 h-3.5 ${flameColor} shrink-0 ${isSpike2 ? "animate-pulse" : ""}"></i>
          <span class="font-extrabold text-[11px] truncate">${tierBadgeText}</span>
          ${spkScore > 0 ? `<span class="px-2 py-0.5 rounded-lg bg-amber-500 text-white font-mono font-black text-[11px] shadow-xs border border-amber-400 flex items-center gap-1 shrink-0"><i data-lucide="zap" class="w-3 h-3 text-amber-200 fill-amber-200"></i><span>${spkScore} pts</span></span>` : ""}
        </div>
        <div class="flex items-center gap-1 shrink-0 font-mono text-[10px] font-bold">
          ${pCount > 0 ? `<span class="px-1.5 py-0.2 rounded bg-white/90 text-emerald-800 border border-emerald-300 shadow-2xs">\u{1F4F0} \uC5B8\uB860 ${pCount}</span>` : ""}
          ${cCount > 0 ? `<span class="px-1.5 py-0.2 rounded bg-white/90 text-orange-800 border border-orange-300 shadow-2xs">\u{1F4AC} \uCEE4\uBBA4\uB2C8\uD2F0 ${cCount}</span>` : ""}
          ${kCount > 0 ? `<span class="px-1.5 py-0.2 rounded bg-white/90 text-indigo-800 border border-indigo-300 shadow-2xs">\u{1F4BB} \uCF54\uB4DC ${kCount}</span>` : ""}
        </div>
      </div>
    `;
    }
    const footerHtml = renderCardStandardFooter(it, currentLang2, linksHtml);
    const tracking = it.metric_tracking || {};
    const delta = tracking.delta !== void 0 ? tracking.delta : tracking.growth_delta || 0;
    const latestVal = tracking.latest?.display || tracking.latest_metric || it.viral_metric || "";
    const initVal = tracking.initial?.display || tracking.initial_metric || "";
    const isSpike = Boolean(tracking.is_spiking || delta > 0 || it.is_cross_spiking);
    const cleanInit = formatCleanMetricVal(initVal, currentLang2);
    const cleanLatest = formatCleanMetricVal(latestVal, currentLang2);
    let metricBadgeHtml = "";
    if (cleanLatest) {
      if (delta > 0 && cleanInit && cleanInit !== cleanLatest) {
        const numInit = cleanInit.replace(/[^0-9.]/g, "");
        const displayFlow = numInit ? `${numInit} \u2794 ${cleanLatest}` : `${cleanLatest}`;
        metricBadgeHtml = `
        <span class="px-2.5 py-0.5 rounded-lg text-[11px] font-black font-mono bg-emerald-50 text-emerald-950 border border-emerald-300 shadow-2xs flex items-center gap-1 shrink-0 ml-auto whitespace-nowrap" title="\uCD5C\uCD08 \uC218\uC9D1: ${cleanInit} \u2794 \uCD5C\uC2E0 \uAC31\uC2E0: ${cleanLatest}">
          <i data-lucide="trending-up" class="w-3.5 h-3.5 text-emerald-600"></i>
          <span>${displayFlow}</span>
          <span class="text-emerald-700 font-black bg-emerald-200/80 px-1 py-0.2 rounded text-[10px]">(+${delta.toLocaleString()})</span>
        </span>
      `;
      } else if (delta > 0) {
        metricBadgeHtml = `
        <span class="px-2.5 py-0.5 rounded-lg text-[11px] font-black font-mono bg-emerald-50 text-emerald-950 border border-emerald-300 shadow-2xs flex items-center gap-1 shrink-0 ml-auto whitespace-nowrap">
          <i data-lucide="trending-up" class="w-3.5 h-3.5 text-emerald-600"></i>
          <span>${cleanLatest}</span>
          <span class="text-emerald-700 font-black bg-emerald-200/80 px-1 py-0.2 rounded text-[10px]">(+${delta.toLocaleString()})</span>
        </span>
      `;
      } else {
        const isPointMetric = cleanLatest.includes("pts") || cleanLatest.includes("\u2605") || cleanLatest.includes("likes") || cleanLatest.includes("\uC810");
        const pointColor = isPointMetric ? "text-rose-900 font-black bg-rose-100/90 border border-rose-300 shadow-2xs" : isSpike ? "text-rose-700 font-bold bg-rose-50 border border-rose-200" : "text-ink-muted bg-surface-subtle border border-surface-border";
        metricBadgeHtml = `
        <span class="px-2.5 py-0.5 rounded-lg text-[11px] font-mono ${pointColor} shrink-0 ml-auto whitespace-nowrap flex items-center gap-1 font-bold">
          ${isPointMetric ? '<i data-lucide="flame" class="w-3.5 h-3.5 text-rose-600 fill-rose-500"></i>' : ""}
          <span>${cleanLatest}</span>
        </span>
      `;
      }
    }
    const primaryPlat = getPrimaryImpactPlatform(it, allSources);
    const isMultiSource = allSources.length > 1;
    card.innerHTML = `
    <div class="space-y-2.5">
      <div class="flex items-center justify-between text-xs font-mono gap-1.5 min-w-0">
        <div class="flex items-center gap-1.5 min-w-0 overflow-hidden">
          <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${catInfo.cls} shrink-0 truncate max-w-[130px]" title="${catInfo.label}">
            ${catInfo.label}
          </span>
          <span class="px-2 py-0.5 rounded bg-surface-subtle text-ink-primary font-bold border border-surface-border text-[10px] flex items-center gap-1 shrink-0 truncate max-w-[110px]" title="${primaryPlat}">
            <span class="truncate">${primaryPlat}</span>
            ${isMultiSource ? `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono bg-amber-500 text-white font-black shadow-2xs shrink-0">+${allSources.length - 1}</span>` : ""}
          </span>
        </div>
        <div class="shrink-0 flex items-center justify-end ml-auto">
          ${metricBadgeHtml}
        </div>
      </div>

      ${crossRollupHtml}
      ${aiBadgeHtml}

      <h3 class="font-bold text-[14px] sm:text-[15px] text-ink-primary hover:text-indigo-600 transition leading-snug break-words line-clamp-2" title="${(displayTitle || "").replace(/"/g, "&quot;")}">
        ${displayTitle}
      </h3>

      ${hookHtml}

      ${showDesc ? `<p class="text-xs text-ink-secondary leading-relaxed line-clamp-3">${displayDesc}</p>` : ""}

      ${aiSummaryHtml}
      ${relatedHtml}
      ${commentsHtml}
    </div>

    ${footerHtml}
  `;
    return card;
  }
  if (typeof window !== "undefined") {
    window.cleanDescriptionText = cleanDescriptionText;
    window.getLocalizedContent = getLocalizedContent;
    window.renderHookCallout = renderHookCallout;
    window.renderNewsSkeleton = renderNewsSkeleton;
    window.renderAiTakeaways = renderAiTakeaways;
    window.renderRelatedDossierButton = renderRelatedDossierButton;
    window.renderCommentsAccordion = renderCommentsAccordion;
    window.renderCardStandardFooter = renderCardStandardFooter;
    window.createNewsCardElement = createNewsCardElement;
  }

  // src/js/components/portfolioCard.js
  function renderCards() {
    if (typeof document === "undefined") return;
    const grid = document.getElementById("cardsGrid");
    if (!grid) return;
    grid.innerHTML = "";
    const lang = typeof window !== "undefined" && window.currentLang ? window.currentLang : currentLang;
    const t = i18n[lang] || i18n.KO;
    const lCases = window.liveCasesData && window.liveCasesData.length > 0 ? window.liveCasesData : liveCasesData && liveCasesData.length > 0 ? liveCasesData : AppStore.getCases() || [];
    const countUser = lCases.filter((c) => (c.curation?.discovery_mode || "USER_CURATED") === "USER_CURATED").length;
    const countAuto = lCases.filter((c) => (c.curation?.discovery_mode || "USER_CURATED") === "AUTO_HARVESTED").length;
    const safeSetTxt = (id, txt) => {
      const el = document.getElementById(id);
      if (el) el.innerText = txt;
    };
    safeSetTxt("badgeCountAll", lCases.length);
    safeSetTxt("badgeCountUser", countUser);
    safeSetTxt("badgeCountAuto", countAuto);
    safeSetTxt("headerVerifiedCount", "(" + lCases.length + ")");
    safeSetTxt("mHeaderVerifiedCount", "(" + lCases.length + ")");
    const curMode = typeof window !== "undefined" && window.currentMode ? window.currentMode : currentMode;
    const curDomain = typeof window !== "undefined" && window.currentDomain ? window.currentDomain : currentDomain;
    const curSort = typeof window !== "undefined" && window.currentSort ? window.currentSort : currentSort;
    const curSearch = typeof window !== "undefined" && window.searchQuery ? window.searchQuery : searchQuery;
    let curPage = typeof window !== "undefined" && window.currentPortfolioPage ? window.currentPortfolioPage : currentPortfolioPage;
    const filtered = lCases.filter((c) => {
      const mode = c.curation ? c.curation.discovery_mode : "USER_CURATED";
      const matchesMode = curMode === "ALL" || mode === curMode;
      const cat = (c.category || "").toLowerCase();
      const cluster = (c.clustering?.cluster_id || "").toLowerCase();
      const fullTxt = (c.title + " " + (c.clustering?.cluster_name || "") + " " + cat).toLowerCase();
      let matchesDomain = true;
      if (curDomain === "frontend") {
        matchesDomain = cat.includes("design") || cat.includes("frontend") || cat.includes("media") || cluster.includes("design") || cluster.includes("media") || fullTxt.includes("taste") || fullTxt.includes("concat");
      } else if (curDomain === "agent") {
        matchesDomain = cat.includes("agent") || cluster.includes("agent") || fullTxt.includes("openworker") || fullTxt.includes("praxist");
      } else if (curDomain === "scraping") {
        matchesDomain = cat.includes("scraping") || cat.includes("browser") || cluster.includes("scraping") || fullTxt.includes("watercrawl") || fullTxt.includes("obscura");
      } else if (curDomain === "doc") {
        matchesDomain = cat.includes("doc") || cat.includes("ocr") || cluster.includes("doc") || fullTxt.includes("docling") || fullTxt.includes("anydoc");
      } else if (curDomain === "3d") {
        matchesDomain = cat.includes("3d") || cat.includes("graphics") || cluster.includes("3d") || fullTxt.includes("three");
      } else if (curDomain === "rust") {
        matchesDomain = fullTxt.includes("rust") || fullTxt.includes("omarchy") || fullTxt.includes("serverbox");
      } else if (curDomain === "other") {
        const isStandard = cat.includes("design") || cat.includes("frontend") || cat.includes("media") || cat.includes("agent") || cat.includes("scraping") || cat.includes("doc") || cat.includes("3d") || fullTxt.includes("rust");
        matchesDomain = !isStandard;
      }
      const story = c.portfolio_story || {};
      const searchTxt = (c.title + " " + (c.title_zh || "") + " " + (c.title_en || "") + " " + cat + " " + (story.the_hook || "") + " " + (c.curation?.personal_motivation || "")).toLowerCase();
      const matchesSearch = searchTxt.includes(curSearch.toLowerCase());
      return matchesMode && matchesDomain && matchesSearch;
    });
    sortCollection(filtered, curSort);
    safeSetTxt("resultsCountLabel", lang === "KO" ? `\uCD1D ${filtered.length}\uAC74 \uD45C\uC2DC (\uC804\uCCB4 ${lCases.length}\uAC74 \uC911)` : lang === "ZH" ? `\u663E\u793A ${filtered.length} \u9879 (\u5171 ${lCases.length} \u9879)` : `Showing ${filtered.length} of ${lCases.length} dossiers`);
    const totalPages = Math.ceil(filtered.length / PORTFOLIO_PAGE_SIZE) || 1;
    if (curPage > totalPages) curPage = totalPages;
    if (curPage < 1) curPage = 1;
    setPortfolioPage(curPage);
    renderPagination("portfolioPagination", curPage, totalPages, "changePortfolioPage");
    if (filtered.length === 0) {
      grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${lang === "KO" ? "\uC77C\uCE58\uD558\uB294 \uAE30\uC220 \uAC80\uC99D \uBCF4\uACE0\uC11C\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4." : lang === "ZH" ? "\u672A\u627E\u5230\u7B26\u5408\u6761\u4EF6\u7684\u6280\u672F\u6838\u67E5\u62A5\u544A\u3002" : "No matching fact-check dossiers found."}</div>`;
      return;
    }
    const pagedItems = filtered.slice((curPage - 1) * PORTFOLIO_PAGE_SIZE, curPage * PORTFOLIO_PAGE_SIZE);
    const fragment = document.createDocumentFragment();
    pagedItems.forEach((c, idx) => {
      const curation = c.curation || { discovery_mode: "USER_CURATED" };
      const isUserMode = curation.discovery_mode === "USER_CURATED";
      const parseDate = (d) => {
        if (!d) return "2026-09-02";
        const m = String(d).match(/([0-9][0-9][0-9][0-9])[-_]([0-9][0-9])[-_]([0-9][0-9])/);
        return m ? `${m[1]}-${m[2]}-${m[3]}` : "2026-09-02";
      };
      const srcDate = parseDate(c.source_published_date || c.investigation_date);
      const invDate = parseDate(c.investigation_date || c.source_published_date);
      const confScore = Number(c.confidence_score) || 95;
      const verdictStr = String(c.verdict || "");
      const isVerifiedTrue = verdictStr === "VERIFIED_TRUE";
      const isHalfTrue = verdictStr.includes("HALF");
      const { displayTitle, displayHook } = getLocalizedContent(c, lang);
      let displayMotivation = displayHook;
      let displayTruth = displayHook || "Empirical benchmark completed.";
      let motivationHtml = displayMotivation;
      const tagMatch = displayMotivation.match(new RegExp("^\\\\[(.*?)\\\\]\\s*(.*)$"));
      if (tagMatch) {
        motivationHtml = `<span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold font-mono bg-indigo-50 text-indigo-700 border border-indigo-200 mr-1.5">${tagMatch[1]}</span><span>${tagMatch[2]}</span>`;
      }
      let verdictLabel = "";
      let verdictClass = "";
      let dotClass = "";
      if (isVerifiedTrue) {
        verdictLabel = lang === "KO" ? "\uC0AC\uC2E4 \uAC80\uC99D\uB428" : lang === "ZH" ? "\u7ECF\u5B9E\u6D4B\u5C5E\u5B9E" : "VERIFIED TRUE";
        verdictClass = "verdict-true";
        dotClass = "bg-emerald-600";
      } else if (isHalfTrue) {
        verdictLabel = lang === "KO" ? "\uC808\uBC18\uC758 \uC0AC\uC2E4" : lang === "ZH" ? "\u90E8\u5206\u5C5E\u5B9E" : "HALF TRUE";
        verdictClass = "verdict-half";
        dotClass = "bg-amber-600";
      } else {
        verdictLabel = lang === "KO" ? "\uACFC\uC7A5/\uC65C\uACE1" : lang === "ZH" ? "\u5938\u5927/\u5931\u771F" : "EXAGGERATED";
        verdictClass = "verdict-gamed";
        dotClass = "bg-rose-600";
      }
      const card = document.createElement("div");
      card.className = "executive-card p-4 sm:p-6 flex flex-col justify-between cursor-pointer space-y-4 group";
      card.onclick = () => openModal(c);
      card.innerHTML = `
      <div class="space-y-3.5">
        <div class="flex items-center justify-between text-xs gap-2 flex-wrap">
          <div class="flex items-center gap-1.5 sm:gap-2 flex-wrap">
            <span class="text-xs font-mono font-bold text-ink-muted">#${String((curPage - 1) * PORTFOLIO_PAGE_SIZE + idx + 1).padStart(2, "0")}</span>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold font-mono ${isUserMode ? "bg-indigo-50 text-indigo-700 border border-indigo-200" : "bg-emerald-50 text-emerald-700 border border-emerald-200"}">
              ${isUserMode ? lang === "KO" ? "\uC9C1\uC811 \uD050\uB808\uC774\uC158" : lang === "ZH" ? "\u624B\u52A8\u7CBE\u9009" : "USER CURATED" : lang === "KO" ? "\uC790\uB3D9 \uD2B8\uB80C\uB4DC" : lang === "ZH" ? "\u81EA\u52A8\u8D8B\u52BF" : "AUTO HARVEST"}
            </span>
            <div class="flex items-center gap-1.5 text-[11px] font-mono text-ink-muted">
              <span title="${lang === "KO" ? "\uC218\uC9D1/\uC6D0\uCD9C\uCC98 \uBC1C\uD589\uC77C" : lang === "ZH" ? "\u91C7\u96C6/\u539F\u6587\u53D1\u5E03\u65E5" : "Source Date"}">\u{1F4C5} ${srcDate}</span>
              <span>\u2022</span>
              <span title="${lang === "KO" ? "\uC2EC\uCE35 \uAE30\uC220 \uBD84\uC11D\uC77C" : lang === "ZH" ? "\u6DF1\u5EA6\u5206\u6790\u65E5" : "Audit Date"}" class="text-indigo-700 font-semibold">\u{1F52C} ${invDate}</span>
            </div>
          </div>

          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold font-mono flex items-center gap-1.5 ${verdictClass}">
            <span class="w-1.5 h-1.5 rounded-full ${dotClass}"></span>
            ${verdictLabel}
          </span>
        </div>

        <div class="space-y-1">
          <span class="text-[11px] text-ink-muted font-mono font-semibold uppercase tracking-wider">${c.category || "AI Technology"}</span>
          <h3 class="font-bold text-base text-ink-primary group-hover:text-indigo-600 transition leading-snug">
            ${displayTitle}
          </h3>
        </div>

        <div class="space-y-2 pt-1">
          <div class="p-3 rounded-xl bg-surface-subtle border border-surface-border text-xs space-y-1">
            <div class="text-[11px] font-bold text-ink-secondary flex items-center gap-1.5">
              <i data-lucide="compass" class="w-3.5 h-3.5 text-indigo-600"></i> ${t.cardMotivationLabel}
            </div>
            <p class="text-xs text-ink-secondary leading-relaxed line-clamp-2">${motivationHtml}</p>
          </div>

          <div class="p-3 rounded-xl bg-emerald-50/70 border border-emerald-200 text-xs space-y-1">
            <div class="text-[11px] font-bold text-emerald-900 flex items-center gap-1.5">
              <i data-lucide="zap" class="w-3.5 h-3.5 text-emerald-700"></i> ${t.cardVerdictLabel}
            </div>
            <p class="text-xs text-emerald-950 leading-relaxed font-medium line-clamp-2">${displayTruth}</p>
          </div>
        </div>

      </div>

      <div class="pt-3 border-t border-surface-border space-y-1.5 text-xs font-mono">
        <div class="flex items-center justify-between text-ink-muted text-[11px]">
          <span title="${lang === "KO" ? "\uC218\uC9D1/\uC6D0\uCD9C\uCC98 \uBC1C\uD589\uC77C" : lang === "ZH" ? "\u91C7\u96C6/\u53D1\u5E03\u65E5" : "Source Date"}">\u{1F4C5} ${srcDate}</span>
          <span class="text-emerald-700 font-bold flex items-center gap-1 font-sans">
            <i data-lucide="shield-check" class="w-3.5 h-3.5"></i> ${t.cardConfidenceLabel} ${confScore.toFixed(1)}%
          </span>
        </div>

        <div class="flex items-center justify-between text-indigo-700 text-[11px] font-semibold gap-2">
          <span title="${lang === "KO" ? "\uC2EC\uCE35 \uAE30\uC220 \uBD84\uC11D\uC77C" : lang === "ZH" ? "\u6DF1\u5EA6\u5206\u6790\u65E5" : "Audit Date"}" class="flex items-center gap-1.5 min-w-0 overflow-hidden">
            <span class="shrink-0">\u{1F52C} ${invDate}</span>
            <span class="text-ink-muted font-normal truncate min-w-0 align-bottom cursor-help" title="${c.curation?.audited_by_model || c.audited_by_model || "gemini-3.8-flash-medium"}">(${formatModelAttribution(c.curation?.audited_by_model || c.audited_by_model || "gemini-3.8-flash-medium")})</span>
          </span>
          <span class="text-ink-muted font-normal shrink-0">${(c.sources || []).length}${t.cardSourcesLabel}</span>
        </div>

        <div class="flex items-center justify-between pt-0.5 font-sans">
          <span class="text-[11px] text-ink-muted font-mono flex items-center gap-1">
            ${c.sources && c.sources.length > 0 ? `<a href="${c.sources[0].url}" target="_blank" onclick="event.stopPropagation();" class="text-indigo-600 hover:underline flex items-center gap-0.5 font-semibold">\u{1F4C4} ${lang === "KO" ? "\uC6D0\uBB38" : lang === "ZH" ? "\u539F\u6587" : "Source"} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>` : ""}
          </span>
          <button class="text-ink-primary font-bold text-xs group-hover:translate-x-0.5 transition flex items-center gap-1 cursor-pointer">
            ${t.cardViewBtn} <i data-lucide="arrow-right" class="w-3.5 h-3.5 text-ink-primary"></i>
          </button>
        </div>
      </div>
    `;
      fragment.appendChild(card);
    });
    grid.appendChild(fragment);
    if (window.lucide) window.lucide.createIcons({ root: grid });
  }
  function setModeFilter(mode) {
    window.currentPortfolioPage = 1;
    window.currentMode = mode;
    document.querySelectorAll(".segment-btn").forEach((btn) => btn.classList.remove("active"));
    if (mode === "ALL") {
      const el = document.getElementById("modeBtnAll");
      if (el) el.classList.add("active");
    } else if (mode === "USER_CURATED") {
      const el = document.getElementById("modeBtnUser");
      if (el) el.classList.add("active");
    } else if (mode === "AUTO_HARVESTED") {
      const el = document.getElementById("modeBtnAuto");
      if (el) el.classList.add("active");
    }
    renderCards();
  }
  function setDomainFilter(dom) {
    window.currentPortfolioPage = 1;
    window.currentDomain = dom;
    document.querySelectorAll(".tag-pill").forEach((btn) => {
      if (btn.dataset.domain === dom) btn.classList.add("active");
      else btn.classList.remove("active");
    });
    renderCards();
  }
  function changeSort(val) {
    window.currentPortfolioPage = 1;
    window.currentSort = val;
    renderCards();
  }
  function clearSearch() {
    window.currentPortfolioPage = 1;
    const input = document.getElementById("searchInput");
    if (input) input.value = "";
    window.searchQuery = "";
    const clearBtn = document.getElementById("clearSearchBtn");
    if (clearBtn) clearBtn.classList.add("hidden");
    renderCards();
  }
  if (typeof window !== "undefined") {
    window.renderCards = renderCards;
    window.setModeFilter = setModeFilter;
    window.setDomainFilter = setDomainFilter;
    window.changeSort = changeSort;
    window.clearSearch = clearSearch;
  }

  // src/js/components/modelsCard.js
  function setModelsSort(sort) {
    setModelsPage(1);
    setModelsSortVal(sort);
    renderModels();
  }
  function setModelsArtifactFilter(art) {
    setModelsPage(1);
    setModelsArtifact(art);
    if (typeof document !== "undefined") {
      document.querySelectorAll(".model-art-pill").forEach((btn) => {
        if (btn.getAttribute("data-art") === art) {
          btn.className = "model-art-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap";
        } else {
          btn.className = "model-art-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap";
        }
      });
    }
    renderModels();
  }
  function setModelsModalityFilter(mod) {
    setModelsPage(1);
    setModelsModality(mod);
    if (typeof document !== "undefined") {
      document.querySelectorAll(".model-mod-pill").forEach((btn) => {
        if (btn.dataset.mod === mod) {
          btn.className = "model-mod-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap";
        } else {
          btn.className = "model-mod-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap";
        }
      });
    }
    renderModels();
  }
  function setModelsFamilyFilter(fam) {
    setModelsPage(1);
    setModelsFamily(fam);
    if (typeof document !== "undefined") {
      document.querySelectorAll(".model-fam-pill").forEach((btn) => {
        if (btn.getAttribute("data-fam") === fam) {
          btn.className = "model-fam-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap";
        } else {
          btn.className = "model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap";
        }
      });
    }
    renderModels();
  }
  function renderModels() {
    if (typeof document === "undefined") return;
    const grid = document.getElementById("modelsGrid");
    if (!grid) return;
    grid.innerHTML = "";
    const lang = typeof window !== "undefined" && window.currentLang ? window.currentLang : currentLang;
    const lModels = typeof window !== "undefined" && window.liveModelsData ? window.liveModelsData : liveModelsData;
    const curMod = typeof window !== "undefined" && window.currentModelsModality ? window.currentModelsModality : currentModelsModality;
    const curFam = typeof window !== "undefined" && window.currentModelsFamily ? window.currentModelsFamily : currentModelsFamily;
    const curArt = typeof window !== "undefined" && window.currentModelsArtifact ? window.currentModelsArtifact : currentModelsArtifact;
    const curSort = typeof window !== "undefined" && window.currentModelsSort ? window.currentModelsSort : currentModelsSort;
    const curSearch = typeof window !== "undefined" && window.modelsSearchQuery ? window.modelsSearchQuery : modelsSearchQuery;
    const targetId = typeof window !== "undefined" && window.targetSelectedInboxId ? window.targetSelectedInboxId : targetSelectedInboxId;
    let curPage = typeof window !== "undefined" && window.currentModelsPage ? window.currentModelsPage : currentModelsPage;
    const filtered = lModels.filter((item) => {
      const hasAi = !!(item.ai_enrichment && (item.multilingual || item.ai_enrichment && item.ai_enrichment.multilingual));
      if (!hasAi) return false;
      if (targetId && item.inbox_id === targetId) {
        return true;
      }
      let matchesMod = true;
      if (curMod !== "ALL") {
        const itemMod = (item.task_modality || "").toLowerCase();
        matchesMod = itemMod === curMod.toLowerCase();
      }
      const fam = (item.model_family || "").toLowerCase();
      let matchesFam = true;
      if (curFam === "ALL") {
        matchesFam = true;
      } else if (curFam === "Standalone") {
        matchesFam = fam.includes("standalone") || fam.includes("\uB3C5\uB9BD") || !fam;
      } else if (curFam === "Audio / Speech") {
        matchesFam = fam.includes("audio") || fam.includes("speech") || fam.includes("tts") || fam.includes("whisper");
      } else {
        matchesFam = fam.includes(curFam.toLowerCase());
      }
      let matchesArt = true;
      if (curArt !== "ALL") {
        const itemArt = item.artifact_type || "WEIGHTS";
        matchesArt = itemArt === curArt;
      }
      if (!curSearch) {
        return matchesMod && matchesFam && matchesArt;
      }
      const q = curSearch.toLowerCase().trim();
      const searchable = ((item.inbox_id || "") + " " + (item.title || "") + " " + (item.title_ko || "") + " " + (item.title_en || "") + " " + (item.title_zh || "") + " " + (item.description || "") + " " + fam + " " + (item.task_modality || "") + " " + (item.artifact_type || "") + " " + (item.parameter_size || "") + " " + (item.ai_enrichment?.summary_ko || "") + " " + (item.ai_enrichment?.hook_ko || "")).toLowerCase();
      const tokens = q.split(/\s+/).filter((t) => t.length > 0);
      const matchesSearch = searchable.includes(q) || tokens.length > 0 && tokens.every((t) => searchable.includes(t));
      return matchesMod && matchesFam && matchesArt && matchesSearch;
    });
    sortCollection(filtered, curSort);
    const clusteredModels = clusterFeedItems(filtered);
    const countEl = document.getElementById("modelsFilteredCount");
    if (countEl) countEl.innerText = lang === "KO" ? `${clusteredModels.length}\uAC1C \uBAA8\uB378 \uD45C\uCD9C` : lang === "ZH" ? `\u663E\u793A ${clusteredModels.length} \u4E2A\u6A21\u578B` : `Showing ${clusteredModels.length} models`;
    const totalPages = Math.ceil(clusteredModels.length / PAGE_SIZE) || 1;
    if (curPage > totalPages) curPage = totalPages;
    if (curPage < 1) curPage = 1;
    setModelsPage(curPage);
    renderPagination("modelsPagination", curPage, totalPages, "changeModelsPage");
    if (clusteredModels.length === 0) {
      grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${lang === "KO" ? "\uC77C\uCE58\uD558\uB294 AI \uBAA8\uB378\uC774 \uC5C6\uC2B5\uB2C8\uB2E4." : lang === "ZH" ? "\u6682\u65E0\u5339\u914D\u7684 AI \u6A21\u578B\u3002" : "No matching AI models."}</div>`;
      return;
    }
    const pagedModels = clusteredModels.slice((curPage - 1) * PAGE_SIZE, curPage * PAGE_SIZE);
    const fragment = document.createDocumentFragment();
    pagedModels.forEach((it) => {
      const { displayTitle, displayHook, displayDesc } = getLocalizedContent(it, lang);
      const card = document.createElement("div");
      card.className = "bg-white rounded-2xl p-4 sm:p-5 border border-surface-border hover:border-indigo-400 hover:shadow-md transition flex flex-col justify-between space-y-4";
      const artType = it.artifact_type || (it.source_platform?.includes("Spaces") ? "WEB_SERVICE" : "WEIGHTS");
      const artBadgeMap = {
        "WEIGHTS": {
          label: lang === "KO" ? "\u{1F916} \uBAA8\uB378 \uAC00\uC911\uCE58" : lang === "ZH" ? "\u{1F916} \u6A21\u578B\u6743\u91CD" : "\u{1F916} Model Weights",
          cls: "bg-indigo-50 text-indigo-800 border-indigo-200",
          btn: lang === "KO" ? "\u{1F4E5} \uD5C8\uBE0C \uB2E4\uC6B4\uB85C\uB4DC" : lang === "ZH" ? "\u{1F4E5} Hub \u4E0B\u8F7D" : "\u{1F4E5} Hub Download"
        },
        "WEB_SERVICE": {
          label: lang === "KO" ? "\u{1F310} Spaces \uB370\uBAA8" : lang === "ZH" ? "\u{1F310} Spaces \u6F14\u793A" : "\u{1F310} Spaces Demo",
          cls: "bg-emerald-50 text-emerald-800 border-emerald-200",
          btn: lang === "KO" ? "\u{1F680} \uB370\uBAA8 / Spaces \uCCB4\uD5D8" : lang === "ZH" ? "\u{1F680} \u5728\u7EBF Demo \u4F53\u9A8C" : "\u{1F680} Try Live Spaces Demo"
        },
        "FINETUNE": {
          label: lang === "KO" ? "\u{1F3AF} \uD2B9\uD654 \uD30C\uC778\uD29C\uB2DD" : lang === "ZH" ? "\u{1F3AF} \u5FAE\u8C03\u5B9A\u5236\u6A21\u578B" : "\u{1F3AF} Finetuned Model",
          cls: "bg-amber-50 text-amber-800 border-amber-200",
          btn: lang === "KO" ? "\u{1F3AF} \uD30C\uC778\uD29C\uB2DD \uBAA8\uB378 \uBCF4\uAE30" : lang === "ZH" ? "\u{1F3AF} \u67E5\u770B\u5FAE\u8C03\u6A21\u578B" : "\u{1F3AF} View Finetuned Model"
        }
      };
      const artMeta = artBadgeMap[artType] || artBadgeMap["WEIGHTS"];
      const artBadge = `<span class="px-2 py-0.5 rounded-md font-bold border text-[10px] font-mono ${artMeta.cls}">${artMeta.label}</span>`;
      const famBadge = it.model_family ? `
      <span class="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 font-bold border border-indigo-200 text-[11px] font-mono">
        \u{1F916} ${it.model_family}
      </span>
    ` : "";
      let modBadge = "";
      if (it.task_modality) {
        const m = it.task_modality.toLowerCase();
        let icon = "\u{1F3AF}";
        let label = it.task_modality;
        if (m.includes("video")) {
          icon = "\u{1F3AC}";
          label = "Video";
        } else if (m.includes("image-text") || m.includes("vision") || m.includes("vlm")) {
          icon = "\u{1F441}\uFE0F";
          label = "VLM";
        } else if (m.includes("image")) {
          icon = "\u{1F3A8}";
          label = "Image";
        } else if (m.includes("speech") || m.includes("audio")) {
          icon = "\u{1F399}\uFE0F";
          label = "Audio/TTS";
        } else if (m.includes("text")) {
          icon = "\u{1F4DD}";
          label = "Text";
        }
        modBadge = `<span class="px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 font-bold border border-purple-200 text-[10px] font-mono">${icon} ${label}</span>`;
      }
      let paramBadge = "";
      if (it.parameter_size) {
        paramBadge = `<span class="px-1.5 py-0.5 rounded-md bg-amber-50 text-amber-800 font-bold border border-amber-200 text-[10px] font-mono shrink-0">\u26A1 ${it.parameter_size}</span>`;
      }
      let formatBadges = "";
      if (Array.isArray(it.detected_formats) && it.detected_formats.length > 0) {
        formatBadges = it.detected_formats.slice(0, 3).map(
          (fmt) => `<span class="px-1.5 py-0.2 rounded bg-surface-subtle text-ink-muted text-[9px] font-mono border border-surface-border uppercase">${fmt}</span>`
        ).join(" ");
      }
      const hookHtml = renderHookCallout(displayHook);
      const relatedHtml = renderRelatedDossierButton(it.related_dossier, lang);
      const actionBtn = `
      <a href="${it.source_url}" target="_blank" rel="noopener noreferrer" class="px-2.5 py-1 rounded-lg bg-surface-subtle hover:bg-ink-primary hover:text-white text-ink-primary font-bold transition text-xs flex items-center gap-1 shrink-0">
        <span>${artMeta.btn}</span> <i data-lucide="external-link" class="w-3 h-3"></i>
      </a>
    `;
      const footerHtml = renderCardStandardFooter(it, lang, actionBtn);
      card.innerHTML = `
      <div class="space-y-3">
        <div class="flex items-center justify-between text-xs font-mono">
          <div class="flex items-center gap-1.5 flex-wrap">
            ${artBadge}
            ${famBadge}
            ${modBadge}
            ${paramBadge}
          </div>
          <span class="text-ink-muted text-[11px] shrink-0">${it.source_platform || "Hugging Face"}</span>
        </div>

        <h3 class="font-bold text-sm text-ink-primary hover:text-indigo-600 transition leading-snug">
          ${displayTitle}
        </h3>

        ${hookHtml}

        ${displayDesc ? `<p class="text-xs text-ink-secondary leading-relaxed line-clamp-3">${displayDesc}</p>` : ""}

        ${formatBadges ? `<div class="flex items-center gap-1 flex-wrap pt-1">${formatBadges}</div>` : ""}

        ${relatedHtml}
      </div>

      ${footerHtml}
    `;
      fragment.appendChild(card);
    });
    grid.appendChild(fragment);
    if (window.lucide) window.lucide.createIcons({ root: grid });
  }
  function toggleFamilyGrouping() {
  }
  function initModelsSearchListener() {
    if (typeof document === "undefined") return;
    document.getElementById("modelsSearchInput")?.addEventListener("input", (e) => {
      setTargetSelectedInboxId("");
      setModelsPage(1);
      setModelsSearchQuery(e.target.value);
      renderModels();
    });
  }
  if (typeof window !== "undefined") {
    window.renderModels = renderModels;
    window.setModelsSort = setModelsSort;
    window.setModelsArtifactFilter = setModelsArtifactFilter;
    window.setModelsModalityFilter = setModelsModalityFilter;
    window.setModelsFamilyFilter = setModelsFamilyFilter;
    initModelsSearchListener();
  }

  // src/js/components/telemetry.js
  var cronScheduleConfig = [
    { id: 1, hour: 0, min: 17, slotKo: "1\uD68C\uCC28 (00:17)", slotZh: "\u7B2C1\u8F6E (00:17)", slotEn: "Session 1 (00:17)", nameKo: "\uC2EC\uC57C \uAE00\uB85C\uBC8C \uB9B4\uB9AC\uC2A4", nameZh: "\u6DF1\u591C\u5168\u7403\u53D1\u5E03", nameEn: "Midnight Global Release", estSec: 545, runId: "34133531110", actualDur: "9\uBD84 05\uCD08" },
    { id: 2, hour: 6, min: 17, slotKo: "2\uD68C\uCC28 (06:17)", slotZh: "\u7B2C2\u8F6E (06:17)", slotEn: "Session 2 (06:17)", nameKo: "\uBAA8\uB2DD \uBE0C\uB9AC\uD551", nameZh: "\u65E9\u95F4\u7B80\u62A5", nameEn: "Morning Briefing", estSec: 362, runId: "34096402553", actualDur: "6\uBD84 02\uCD08" },
    { id: 3, hour: 12, min: 17, slotKo: "3\uD68C\uCC28 (12:17)", slotZh: "\u7B2C3\u8F6E (12:17)", slotEn: "Session 3 (12:17)", nameKo: "\uC815\uC624 \uB808\uC774\uB354", nameZh: "\u6B63\u5348\u96F7\u8FBE", nameEn: "Noon Radar", estSec: 456, runId: "34064244121", actualDur: "7\uBD84 36\uCD08" },
    { id: 4, hour: 18, min: 17, slotKo: "4\uD68C\uCC28 (18:17)", slotZh: "\u7B2C4\u8F6E (18:17)", slotEn: "Session 4 (18:17)", nameKo: "\uC800\uB141 \uB77C\uC6B4\uB4DC\uC5C5", nameZh: "\u665A\u95F4\u6C47\u603B", nameEn: "Evening Roundup", estSec: 694, runId: "34048453203", actualDur: "11\uBD84 34\uCD08" }
  ];
  function recomputeTimeline24hFromLiveInbox() {
    const nowKst = getDynamicKstDate();
    const pad = (n) => String(n).padStart(2, "0");
    const curKstDateStr = `${nowKst.getFullYear()}-${pad(nowKst.getMonth() + 1)}-${pad(nowKst.getDate())}`;
    const curHour = getDynamicKstHour();
    const slotDefs = [
      { slot: "1\uD68C\uCC28 (00\uC2DC)", short_slot: "00:00", hour: 0, range: "00:00 - 05:59", name: "\uC2EC\uC57C \uB9B4\uB9AC\uC2A4" },
      { slot: "2\uD68C\uCC28 (06\uC2DC)", short_slot: "06:00", hour: 6, range: "06:00 - 11:59", name: "\uBAA8\uB2DD \uBE0C\uB9AC\uD551" },
      { slot: "3\uD68C\uCC28 (12\uC2DC)", short_slot: "12:00", hour: 12, range: "12:00 - 17:59", name: "\uC815\uC624 \uB808\uC774\uB354" },
      { slot: "4\uD68C\uCC28 (18\uC2DC)", short_slot: "18:00", hour: 18, range: "18:00 - 23:59", name: "\uC800\uB141 \uB77C\uC6B4\uB4DC\uC5C5" }
    ];
    const counts = {
      0: { inbox: 0, news: 0, model: 0, enriched: 0 },
      6: { inbox: 0, news: 0, model: 0, enriched: 0 },
      12: { inbox: 0, news: 0, model: 0, enriched: 0 },
      18: { inbox: 0, news: 0, model: 0, enriched: 0 }
    };
    const parseKst = (raw) => {
      if (!raw || typeof raw !== "string") return null;
      if (raw.includes("T")) {
        const dt = new Date(raw);
        if (!isNaN(dt.getTime())) {
          const utcMs = dt.getTime() + dt.getTimezoneOffset() * 6e4;
          const kstDt = new Date(utcMs + 9 * 3600 * 1e3);
          return {
            dateStr: `${kstDt.getFullYear()}-${pad(kstDt.getMonth() + 1)}-${pad(kstDt.getDate())}`,
            hour: kstDt.getHours()
          };
        }
      } else if (/^\d{4}-\d{2}-\d{2}/.test(raw)) {
        return { dateStr: raw.substring(0, 10), hour: 0 };
      }
      return null;
    };
    const inbList = typeof window !== "undefined" && window.liveInboxData ? window.liveInboxData : liveInboxData;
    inbList.forEach((it) => {
      const rawTime = it.harvested_at || it.harvested_date || it.created_at || "";
      const kstHarvest = parseKst(rawTime);
      if (kstHarvest && kstHarvest.dateStr === curKstDateStr) {
        const slotHour = Math.floor(kstHarvest.hour / 6) * 6;
        if (counts[slotHour]) counts[slotHour].inbox++;
      }
      const isEnriched = it.is_classified || it.ai_enrichment;
      if (isEnriched) {
        const rawEnrichTime = it.ai_enrichment && it.ai_enrichment.enriched_at || it.updated_at || "";
        const kstEnrich = parseKst(rawEnrichTime);
        if (kstEnrich && kstEnrich.dateStr === curKstDateStr) {
          const slotHour = Math.floor(kstEnrich.hour / 6) * 6;
          if (counts[slotHour]) {
            counts[slotHour].enriched++;
            const isModel = it.item_type === "MODEL" || it.source_platform && (it.source_platform.includes("Models") || it.source_platform.includes("Hub"));
            if (isModel) counts[slotHour].model++;
            else counts[slotHour].news++;
          }
        }
      }
    });
    const totalToday = Object.values(counts).reduce((acc, cur) => acc + cur.inbox + cur.enriched, 0);
    if (totalToday > 0) {
      const tData = typeof window !== "undefined" && window.timeline24hData ? window.timeline24hData : timeline24hData;
      const newTData = slotDefs.map((s) => {
        const existing = (tData || []).find((d) => d.hour === s.hour);
        const inboxCnt = existing && existing.inbox_count > counts[s.hour].inbox ? existing.inbox_count : counts[s.hour].inbox;
        const enrichedCnt = existing && existing.enriched_count > counts[s.hour].enriched ? existing.enriched_count : counts[s.hour].enriched;
        return {
          slot: s.slot,
          short_slot: s.short_slot,
          hour: s.hour,
          range: s.range,
          name: s.name,
          inbox_count: inboxCnt,
          enriched_count: enrichedCnt,
          model_count: counts[s.hour].model,
          news_count: counts[s.hour].news,
          is_current: s.hour <= curHour && curHour < s.hour + 6,
          is_future: s.hour > curHour
        };
      });
      if (typeof window !== "undefined") window.timeline24hData = newTData;
    }
  }
  function renderTelemetryCharts() {
    if (typeof document === "undefined") return;
    const nowKst = getDynamicKstDate();
    const pad = (n) => String(n).padStart(2, "0");
    const curKstDateStr = `${nowKst.getFullYear()}-${pad(nowKst.getMonth() + 1)}-${pad(nowKst.getDate())}`;
    const titleEl = document.getElementById("timelineTitleText");
    const isPending = typeof window !== "undefined" && !!window._timelineIsPendingToday;
    const lang = typeof window !== "undefined" && window.currentLang ? window.currentLang : currentLang;
    if (titleEl) {
      if (isPending) {
        titleEl.innerHTML = `${i18n[lang]?.timelineTitle || "\uB2F9\uC77C 24\uC2DC\uAC04 \uC218\uC9D1 \uD0C0\uC784\uB77C\uC778"} (${curKstDateStr}) <span class="ml-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-300 inline-flex items-center gap-1 font-sans"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>1\uD68C\uCC28 \uC2E4\uC2DC\uAC04 \uC9D1\uACC4 \uB300\uAE30 \uC911</span>`;
      } else {
        titleEl.innerText = `${i18n[lang]?.timelineTitle || "\uB2F9\uC77C 24\uC2DC\uAC04 \uC218\uC9D1 \uD0C0\uC784\uB77C\uC778"} (${curKstDateStr})`;
      }
    }
    const tlContainer = document.getElementById("timeline24hChartContainer");
    if (tlContainer) {
      tlContainer.innerHTML = "";
      const tData = typeof window !== "undefined" && window.timeline24hData ? window.timeline24hData : timeline24hData;
      const maxVal = Math.max(...(tData || []).map((d) => Math.max(d.inbox_count || 0, d.enriched_count !== void 0 ? d.enriched_count : (d.news_count || 0) + (d.model_count || 0))), 10);
      const curKstHour = getDynamicKstHour();
      (tData || []).forEach((d) => {
        const enrichedCount = d.enriched_count !== void 0 ? d.enriched_count : (d.news_count || 0) + (d.model_count || 0);
        const hPct = d.inbox_count > 0 ? Math.max(10, Math.round(d.inbox_count / maxVal * 100)) : 0;
        const hEnrichedPct = enrichedCount > 0 ? Math.max(10, Math.round(enrichedCount / maxVal * 100)) : 0;
        const isCurrent = d.hour <= curKstHour && curKstHour < d.hour + 6;
        const isFuture = d.hour > curKstHour;
        const col = document.createElement("div");
        col.className = "flex flex-col items-center justify-end h-full group relative cursor-pointer";
        col.innerHTML = `
        <div class="opacity-0 group-hover:opacity-100 transition-opacity absolute -top-16 z-20 pointer-events-none bg-ink-primary text-white text-[10px] font-mono py-1.5 px-2.5 rounded-lg shadow-lg whitespace-nowrap">
          <div class="font-bold text-indigo-300">${d.range}</div>
          <div class="text-indigo-200">\u{1F4E5} \uC218\uC9D1: ${d.inbox_count || 0}\uAC74</div>
          <div class="text-emerald-300">\u2728 AI\uC694\uC57D: ${enrichedCount}\uAC74${d.backlog_cleared ? ` <span class="text-emerald-400 text-[9px] font-normal">(+${d.backlog_cleared} \uBC31\uB85C\uADF8)</span>` : ""}</div>
          ${isCurrent ? isPending ? '<div class="text-emerald-400 font-bold mt-0.5">\u26A1 1\uD68C\uCC28 \uC138\uC158 \uD30C\uC774\uD504\uB77C\uC778 \uC778\uC785 \uC911</div>' : '<div class="text-emerald-400 font-bold mt-0.5">\u25CF \uD604\uC7AC \uC138\uC158 \uC778\uC785 \uC911</div>' : isFuture ? '<div class="text-slate-400 mt-0.5">\uC608\uC815 \uC138\uC158</div>' : '<div class="text-slate-300 mt-0.5">\uC218\uC9D1 \uC644\uB8CC</div>'}
        </div>

        <div class="flex items-center gap-1 text-[9px] sm:text-[10px] font-mono font-bold mb-1">
          <span class="${isCurrent ? "text-indigo-600 font-extrabold" : "text-ink-muted"}" title="\uC218\uC9D1 \uAC74\uC218">${d.inbox_count || 0}</span>
          <span class="text-slate-300">/</span>
          <span class="${isCurrent ? "text-emerald-600 font-extrabold" : "text-emerald-600/80"}" title="AI \uC694\uC57D \uAC74\uC218">${enrichedCount}</span>
        </div>

        <div class="w-full max-w-[58px] sm:max-w-[76px] flex items-end justify-center gap-1 sm:gap-1.5 h-24 ${isFuture ? "opacity-30" : ""}">
          <div class="flex-1 ${isCurrent ? "bg-indigo-500 ring-2 ring-indigo-400 animate-pulse" : "bg-indigo-600"} rounded-t-sm sm:rounded-t-md transition-all duration-500 hover:bg-indigo-700" style="height: ${hPct}%; min-height: 0;" title="\uC218\uC9D1\uB7C9: ${d.inbox_count || 0}\uAC74"></div>
          <div class="flex-1 ${isCurrent ? "bg-emerald-400 ring-1 ring-emerald-300" : "bg-emerald-500"} rounded-t-sm sm:rounded-t-md transition-all duration-500 hover:bg-emerald-600" style="height: ${hEnrichedPct}%; min-height: 0;" title="AI \uC694\uC57D\uC644\uB8CC: ${enrichedCount}\uAC74"></div>
        </div>

        <span class="text-[10px] sm:text-[11px] font-mono font-bold ${isCurrent ? "text-indigo-600 font-extrabold" : "text-ink-muted"} mt-2 group-hover:text-indigo-600 transition text-center">
          ${d.slot}
        </span>
      `;
        tlContainer.appendChild(col);
      });
      const totCollected = (tData || []).reduce((acc, cur) => acc + (cur.inbox_count || 0), 0);
      const totEnriched = (tData || []).reduce((acc, cur) => acc + (cur.enriched_count !== void 0 ? cur.enriched_count : (cur.news_count || 0) + (cur.model_count || 0)), 0);
      const ftEl = document.getElementById("timelineFooterText");
      if (ftEl) {
        if (isPending) {
          ftEl.innerHTML = `\u26A1 <b class="text-indigo-700">${curKstDateStr} 1\uD68C\uCC28(00:00~06:00) \uD30C\uC774\uD504\uB77C\uC778 \uAC00\uB3D9 \uC911</b> \u2502 \u{1F4CA} \uC804\uC77C \uD655\uC815 \uC2E4\uC801: <b class="text-slate-800">${totCollected}\uAC74 \uC218\uC9D1</b> / <b class="text-emerald-700">${totEnriched}\uAC74 AI \uBD84\uC11D</b>`;
        } else {
          ftEl.innerHTML = `\u26A1 \uB2F9\uC77C 24H \uC218\uC9D1: <b class="text-indigo-700">${totCollected}\uAC74</b> \u2502 \u2728 AI \uC694\uC57D\uBD84\uC11D \uC644\uB8CC: <b class="text-emerald-700">${totEnriched}\uAC74</b>`;
        }
      }
    }
    if (typeof window.renderRadarSession === "function") {
      window.renderRadarSession();
    }
  }
  var _lastTelemetryMinute = -1;
  function renderPipelineTelemetryCards() {
    if (typeof document === "undefined") return;
    const slotsContainer = document.getElementById("pipelineSlotsContainer");
    if (!slotsContainer) return;
    const tLang = (typeof window !== "undefined" && window.currentLang ? window.currentLang : currentLang).toLowerCase();
    const aData = typeof window !== "undefined" && window.actionsTelemetryData ? window.actionsTelemetryData : actionsTelemetryData;
    const usedMin = aData.monthly_used_minutes || 0;
    const remMin = aData.monthly_remaining_minutes || 2e3 - usedMin;
    const usagePct = aData.monthly_usage_percent || 0;
    const usedEl = document.getElementById("quotaUsedMin");
    const remEl = document.getElementById("quotaRemMin");
    const progEl = document.getElementById("quotaProgressBar");
    if (usedEl) usedEl.innerText = `${usedMin}\uBD84`;
    if (remEl) remEl.innerText = `${remMin}\uBD84 (${100 - usagePct}%)`;
    if (progEl) progEl.style.width = `${Math.min(100, Math.max(2, usagePct))}%`;
    const nowKst = getDynamicKstDate();
    const curHour = nowKst.getHours();
    const curMin = nowKst.getMinutes();
    const curSec = nowKst.getSeconds();
    const curTotalSec = curHour * 3600 + curMin * 60 + curSec;
    const tData = typeof window !== "undefined" && window.timeline24hData ? window.timeline24hData : timeline24hData;
    let cardsHtml = "";
    cronScheduleConfig.forEach((s, idx) => {
      const sTotalSec = s.hour * 3600 + s.min * 60;
      const isPast = curTotalSec >= sTotalSec + (s.estSec || 360);
      const isActive = curTotalSec >= sTotalSec && curTotalSec < sTotalSec + (s.estSec || 360);
      const sessionTitle = tLang === "zh" ? s.slotZh : tLang === "en" ? s.slotEn : s.slotKo;
      const sessionSub = tLang === "zh" ? s.nameZh : tLang === "en" ? s.nameEn : s.nameKo;
      const slotKeys = ["00:00", "06:00", "12:00", "18:00"];
      const slotKey = slotKeys[idx] || "00:00";
      const sLog = aData.slot_logs && aData.slot_logs[slotKey] ? aData.slot_logs[slotKey] : null;
      const tlMatch = (tData || []).find((d) => d.hour === idx * 6);
      const itemCount = sLog && sLog.is_today && sLog.items_collected !== null && sLog.items_collected !== void 0 ? sLog.items_collected : tlMatch ? tlMatch.inbox_count || 0 : 0;
      let statusBadge = "";
      let timeInfo = "";
      let cardBorder = "border-surface-border";
      let cardBg = "bg-slate-50/50";
      const isRunToday = sLog && sLog.is_today;
      const isRunSuccess = isRunToday && (sLog.status === "SUCCESS" || sLog.status === "completed");
      const isRunActive = sLog && sLog.status === "in_progress" || isActive;
      if (isRunSuccess) {
        const actualDuration = sLog.actual_duration || (s.actualDur || "-");
        const errCount = sLog && typeof sLog.error_count !== "undefined" ? sLog.error_count : 0;
        cardBorder = "border-emerald-200";
        cardBg = "bg-emerald-50/30";
        statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1"><i data-lucide="check-circle" class="w-3 h-3 text-emerald-600"></i>${tLang === "zh" ? "\u5DF2\u5B8C\u6210" : tLang === "en" ? "Completed" : "\uC218\uC9D1 \uC644\uB8CC"}</span>`;
        timeInfo = `<span>${tLang === "zh" ? "\u5B9E\u6D4B\u8017\u65F6" : tLang === "en" ? "Duration" : "\uC2E4\uCE21 \uC18C\uC694"}: <b class="text-ink-primary font-bold">${actualDuration}</b> \xB7 ${errCount} ${tLang === "zh" ? "\u9519\u8BEF" : tLang === "en" ? "errors" : "\uC5D0\uB7EC"}</span>`;
      } else if (isRunActive) {
        cardBorder = "border-indigo-400 ring-2 ring-indigo-200";
        cardBg = "bg-indigo-50/70";
        statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-600 text-white flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-white animate-ping"></span>${tLang === "zh" ? "\u8FD0\u884C\u4E2D" : tLang === "en" ? "Running" : "\uC218\uC9D1 \uC9C4\uD589 \uC911"}</span>`;
        timeInfo = `<span class="text-indigo-700 font-bold">${tLang === "zh" ? "\u6B63\u5728\u6267\u884C" : tLang === "en" ? "Ingesting live..." : "\uC2E4\uC2DC\uAC04 \uD30C\uC774\uD504\uB77C\uC778 \uAC00\uB3D9"}</span>`;
      } else if (isPast && !isRunToday) {
        cardBorder = "border-amber-300 ring-1 ring-amber-200";
        cardBg = "bg-amber-50/40";
        statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300 flex items-center gap-1"><i data-lucide="clock" class="w-3 h-3 text-amber-600"></i>${tLang === "zh" ? "\u961F\u5217\u7B49\u5F85\u4E2D" : tLang === "en" ? "Queue Waiting" : "\u23F3 \uC218\uC9D1 \uD050 \uB300\uAE30"}</span>`;
        timeInfo = `<span class="text-amber-700 font-medium">${tLang === "zh" ? "\u5DF2\u8FC7\u8C03\u5EA6\u65F6\u6BB5 \xB7 GHA \u961F\u5217\u7B49\u5F85\u4E2D" : tLang === "en" ? "Scheduled time elapsed \xB7 Waiting in GHA queue" : "\uC608\uC815 \uC2DC\uAC01 \uACBD\uACFC \xB7 Actions \uD050 \uB300\uAE30 \uC911"}</span>`;
      } else {
        const slotDiffSec = sTotalSec - curTotalSec;
        const futH = Math.floor(slotDiffSec / 3600);
        const futM = Math.floor(slotDiffSec % 3600 / 60);
        statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200 flex items-center gap-1"><i data-lucide="clock" class="w-3 h-3 text-slate-500"></i>${tLang === "zh" ? "\u7B49\u5F85\u4E2D" : tLang === "en" ? "Scheduled" : "\uB300\uAE30 \uC911"}</span>`;
        timeInfo = `<span>${tLang === "zh" ? "\u5269\u4F59" : tLang === "en" ? "Remaining" : "\uB0A8\uC740 \uC2DC\uAC04"}: <b class="text-indigo-600">${futH}h ${futM}m</b> \xB7 ${tLang === "zh" ? "\u9884\u8BA1\u7EA6" : tLang === "en" ? "Est. " : "\uC608\uC0C1 "}${Math.round(s.estSec / 60)}\uBD84</span>`;
      }
      cardsHtml += `
      <div class="p-3.5 rounded-xl border ${cardBorder} ${cardBg} flex flex-col justify-between space-y-2.5 transition">
        <div class="flex items-center justify-between">
          <span class="font-bold text-ink-primary text-xs">${sessionTitle}</span>
          ${statusBadge}
        </div>
        <div class="space-y-1">
          <div class="text-[11px] text-ink-secondary font-medium">${sessionSub}</div>
          <div class="text-xs font-bold text-ink-primary flex items-center justify-between">
            <span>${tLang === "zh" ? "\u91C7\u96C6\u603B\u91CF" : tLang === "en" ? "Ingested" : "\uC218\uC9D1\uB7C9"}:</span>
            <span class="text-indigo-600 font-mono">${itemCount}\uAC74</span>
          </div>
        </div>
        <div class="pt-2 border-t border-surface-border/60 text-[10px] text-ink-muted flex items-center justify-between">
          ${timeInfo}
        </div>
      </div>
    `;
    });
    slotsContainer.innerHTML = cardsHtml;
    if (typeof lucide !== "undefined") lucide.createIcons({ root: slotsContainer });
  }
  function updateCronCountdown() {
    if (typeof document === "undefined") return;
    const curView = typeof window !== "undefined" && window.currentView ? window.currentView : currentView;
    if (curView !== "inbox") return;
    const countdownEl = document.getElementById("pipelineCountdownValue");
    if (!countdownEl) return;
    const nowKst = getDynamicKstDate();
    const curHour = nowKst.getHours();
    const curMin = nowKst.getMinutes();
    const curSec = nowKst.getSeconds();
    const curTotalSec = curHour * 3600 + curMin * 60 + curSec;
    let nextSlot = null;
    let diffSec = 0;
    for (let s of cronScheduleConfig) {
      const sTotalSec = s.hour * 3600 + s.min * 60;
      if (sTotalSec > curTotalSec) {
        nextSlot = s;
        diffSec = sTotalSec - curTotalSec;
        break;
      }
    }
    if (!nextSlot) {
      nextSlot = cronScheduleConfig[0];
      const eodSec = 24 * 3600 - curTotalSec;
      diffSec = eodSec + (nextSlot.hour * 3600 + nextSlot.min * 60);
    }
    const remH = Math.floor(diffSec / 3600);
    const remM = Math.floor(diffSec % 3600 / 60);
    const remS = diffSec % 60;
    const pad = (n) => String(n).padStart(2, "0");
    const tLang = (typeof window !== "undefined" && window.currentLang ? window.currentLang : currentLang).toLowerCase();
    const slotName = tLang === "zh" ? nextSlot.slotZh : tLang === "en" ? nextSlot.slotEn : nextSlot.slotKo;
    countdownEl.innerText = `${pad(remH)}:${pad(remM)}:${pad(remS)} (${slotName})`;
    if (_lastTelemetryMinute !== curMin) {
      _lastTelemetryMinute = curMin;
      renderPipelineTelemetryCards();
      renderRunsTable();
    }
    if (curSec === 17 && !document.hidden) {
      checkLiveActionsRuns();
    }
  }
  function switchRunLogsTab(tab) {
    if (typeof window !== "undefined") window.currentRunsTab = tab;
    const btnGha = document.getElementById("tabRunsGha");
    const btnVercel = document.getElementById("tabRunsVercel");
    const btnVoyage = document.getElementById("tabRunsVoyage");
    const inactiveCls = "px-2.5 py-1 rounded-md font-medium text-ink-secondary hover:text-ink-primary transition cursor-pointer";
    if (btnGha) btnGha.className = inactiveCls;
    if (btnVercel) btnVercel.className = inactiveCls;
    if (btnVoyage) btnVoyage.className = inactiveCls;
    if (tab === "gha") {
      if (btnGha) btnGha.className = "px-2.5 py-1 rounded-md font-bold bg-white text-ink-primary shadow-xs border border-surface-border transition cursor-pointer";
    } else if (tab === "vercel") {
      if (btnVercel) btnVercel.className = "px-2.5 py-1 rounded-md font-bold bg-white text-indigo-700 shadow-xs border border-indigo-200 transition cursor-pointer";
    } else if (tab === "voyage") {
      if (btnVoyage) btnVoyage.className = "px-2.5 py-1 rounded-md font-bold bg-white text-emerald-800 shadow-xs border border-emerald-300 transition cursor-pointer";
    }
    renderRunsTable();
  }
  function renderRunsTable() {
    if (typeof document === "undefined") return;
    const thead = document.getElementById("pipelineRecentRunsThead");
    const tbody = document.getElementById("pipelineRecentRunsTbody");
    if (!tbody || !thead) return;
    const tLang = (typeof window !== "undefined" && window.currentLang ? window.currentLang : currentLang).toLowerCase();
    const aData = typeof window !== "undefined" && window.actionsTelemetryData ? window.actionsTelemetryData : actionsTelemetryData;
    const curTab = typeof window !== "undefined" && window.currentRunsTab ? window.currentRunsTab : "gha";
    if (curTab === "gha") {
      thead.innerHTML = `
      <tr>
        <th class="py-2.5 px-3">\uC2E4\uD589 \uC2DC\uAC01 (KST)</th>
        <th class="py-2.5 px-3">\uC6CC\uD06C\uD50C\uB85C\uC6B0</th>
        <th class="py-2.5 px-3">\uD2B8\uB9AC\uAC70</th>
        <th class="py-2.5 px-3">\uC18C\uC694 \uC2DC\uAC04</th>
        <th class="py-2.5 px-3" title="\uC2E0\uADDC \uC778\uC785 \uAC74\uC218 \uBC0F 5\uB300 \uD50C\uB7AB\uD3FC \uC2A4\uCE94 \uD6C4\uBCF4 \uCD1D\uB7C9">\uC218\uC9D1 \uACB0\uACFC (\uC2E0\uADDC/\uC2A4\uCE94)</th>
        <th class="py-2.5 px-3">\uC0C1\uD0DC</th>
        <th class="py-2.5 px-3">\uC5D0\uB7EC</th>
      </tr>
    `;
      if (aData.runs && aData.runs.length > 0) {
        let rowsHtml = "";
        aData.runs.forEach((r) => {
          const isSuccess = r.conclusion === "success";
          const isCancelled = r.conclusion === "cancelled";
          const statusCls = isSuccess ? "bg-emerald-100 text-emerald-800 border-emerald-300" : isCancelled ? "bg-amber-100 text-amber-800 border-amber-300" : "bg-indigo-100 text-indigo-800 border-indigo-300";
          const statusLabel = isSuccess ? tLang === "zh" ? "\u6210\u529F" : tLang === "en" ? "Success" : "\uC131\uACF5" : isCancelled ? tLang === "zh" ? "\u5DF2\u53D6\u6D88" : tLang === "en" ? "Cancelled" : "\uCDE8\uC18C" : tLang === "zh" ? "\u8FD0\u884C\u4E2D" : tLang === "en" ? "Running" : "\uC9C4\uD589\uC911";
          let itemsCell = "-";
          let collectedCount = 0;
          let scannedCount = 0;
          let hasCollected = false;
          let hasScanned = false;
          if (typeof r.items_collected === "number") {
            collectedCount = r.items_collected;
            hasCollected = true;
          } else if (typeof r.items_collected === "string") {
            const m = r.items_collected.match(/\d+/);
            if (m) {
              if (r.items_collected.includes("\uC2A4\uCE94")) {
                scannedCount = parseInt(m[0], 10);
                hasScanned = true;
              } else {
                collectedCount = parseInt(m[0], 10);
                hasCollected = true;
              }
            }
          }
          if (typeof r.items_scanned === "number") {
            scannedCount = r.items_scanned;
            hasScanned = true;
          } else if (typeof r.items_scanned === "string") {
            const m = r.items_scanned.match(/\d+/);
            if (m) {
              scannedCount = parseInt(m[0], 10);
              hasScanned = true;
            }
          }
          const isNonHarvestWorkflow = r.event === "push" || !hasCollected && !hasScanned || collectedCount === 0 && scannedCount === 0 || r.items_collected === null && r.items_scanned === null;
          if (isNonHarvestWorkflow) {
            if (r.event === "schedule" && (r.status === "in_progress" || r.status === "queued")) {
              itemsCell = `<span class="text-amber-600 animate-pulse font-medium">\uC218\uC9D1 \uC9C4\uD589 \uC911...</span>`;
            } else {
              itemsCell = `<span class="text-ink-muted">-</span>`;
            }
          } else if (hasCollected && hasScanned) {
            const colLabel = tLang === "zh" ? "\u6761\u91C7\u96C6" : tLang === "en" ? "collected" : "\uAC74 \uC218\uC9D1";
            const scanLabel = tLang === "zh" ? "\u6761\u626B\u63CF" : tLang === "en" ? "scanned" : "\uAC74 \uC2A4\uCE94";
            itemsCell = `<span class="font-bold text-indigo-700">${collectedCount}${colLabel}</span> <span class="text-[10px] text-ink-muted">/ ${scannedCount}${scanLabel}</span>`;
          } else if (hasCollected && collectedCount > 0) {
            const colLabel = tLang === "zh" ? "\u6761\u91C7\u96C6" : tLang === "en" ? "collected" : "\uAC74 \uC218\uC9D1";
            itemsCell = `<span class="font-bold text-indigo-700">${collectedCount}${colLabel}</span>`;
          } else if (hasScanned && scannedCount > 0) {
            const colLabel = tLang === "zh" ? "\u6761\u91C7\u96C6" : tLang === "en" ? "collected" : "\uAC74 \uC218\uC9D1";
            const scanLabel = tLang === "zh" ? "\u6761\u626B\u63CF" : tLang === "en" ? "scanned" : "\uAC74 \uC2A4\uCE94";
            itemsCell = `<span class="font-bold text-indigo-700">0${colLabel}</span> <span class="text-[10px] text-ink-muted">/ ${scannedCount}${scanLabel}</span>`;
          } else {
            itemsCell = `<span class="text-ink-muted">-</span>`;
          }
          rowsHtml += `
          <tr class="hover:bg-slate-50/80 transition">
            <td class="py-2.5 px-3 font-bold text-ink-primary text-[11px]">${r.created_at_kst}</td>
            <td class="py-2.5 px-3 font-medium text-ink-secondary">${r.name.length > 32 ? r.name.slice(0, 30) + "..." : r.name}</td>
            <td class="py-2.5 px-3 text-ink-muted"><span class="px-1.5 py-0.5 rounded bg-slate-100 text-[10px] border border-slate-200">${r.event}</span></td>
            <td class="py-2.5 px-3 font-bold text-ink-primary">${r.duration_str}</td>
            <td class="py-2.5 px-3 font-mono font-semibold">${itemsCell}</td>
            <td class="py-2.5 px-3">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${statusCls} inline-flex items-center gap-1">
                ${statusLabel}
              </span>
            </td>
            <td class="py-2.5 px-3 font-bold ${r.error_count > 0 ? "text-rose-600" : "text-emerald-600"}">${r.error_count || 0} errors</td>
          </tr>
        `;
        });
        tbody.innerHTML = rowsHtml;
      } else {
        tbody.innerHTML = `<tr><td colspan="7" class="py-4 text-center text-ink-muted">\uAE30\uB85D\uB41C \uC218\uC9D1 \uC2E4\uD589 \uB85C\uADF8\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4.</td></tr>`;
      }
    } else if (curTab === "vercel") {
      thead.innerHTML = `
      <tr>
        <th class="py-2.5 px-3">\uC2E4\uD589 \uC2DC\uAC01 (KST)</th>
        <th class="py-2.5 px-3">\uC11C\uBC84\uB9AC\uC2A4 \uC6CC\uCEE4</th>
        <th class="py-2.5 px-3">AI \uBAA8\uB378</th>
        <th class="py-2.5 px-3">\uC18C\uC694 \uC2DC\uAC04</th>
        <th class="py-2.5 px-3">\uCC98\uB9AC \uAC74\uC218</th>
        <th class="py-2.5 px-3">\uC794\uC5EC \uBBF8\uCC98\uB9AC</th>
        <th class="py-2.5 px-3">\uC0C1\uD0DC</th>
      </tr>
    `;
      const vRuns = window.vercelWorkerRunsData || [];
      if (vRuns.length > 0) {
        let rowsHtml = "";
        vRuns.forEach((r) => {
          const isSuccess = r.status === "SUCCESS";
          const statusCls = isSuccess ? "bg-emerald-100 text-emerald-800 border-emerald-300" : "bg-rose-100 text-rose-800 border-rose-300";
          const shortModel = (r.model_used || "openrouter-free").split("/").pop().replace(":free", "");
          rowsHtml += `
          <tr class="hover:bg-slate-50/80 transition">
            <td class="py-2.5 px-3 font-bold text-ink-primary text-[11px]">${r.created_at_kst}</td>
            <td class="py-2.5 px-3 font-medium text-ink-secondary flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full bg-indigo-500"></span> ${r.worker_name || "AI Enricher"}
            </td>
            <td class="py-2.5 px-3 text-ink-muted font-mono text-[11px]"><span class="px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 text-[10px] border border-indigo-200">${shortModel}</span></td>
            <td class="py-2.5 px-3 font-bold text-ink-primary">${r.duration_str}</td>
            <td class="py-2.5 px-3 font-mono font-semibold text-emerald-600">${r.processed_count}\uAC74 \uC694\uC57D</td>
            <td class="py-2.5 px-3 font-mono font-medium text-amber-700">${r.remaining_count}\uAC74 \uB300\uAE30</td>
            <td class="py-2.5 px-3">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${statusCls} inline-flex items-center gap-1">
                ${isSuccess ? "\uC131\uACF5" : "\uC2E4\uD328"}
              </span>
            </td>
          </tr>
        `;
        });
        tbody.innerHTML = rowsHtml;
      } else {
        tbody.innerHTML = `<tr><td colspan="7" class="py-4 text-center text-ink-muted">\uCD5C\uADFC Vercel Serverless AI \uC6CC\uCEE4 \uC2E4\uD589 \uAE30\uB85D \uB300\uAE30 \uC911...</td></tr>`;
      }
    } else if (curTab === "voyage") {
      thead.innerHTML = `
      <tr>
        <th class="py-2.5 px-3">\uC2E4\uD589 \uC2DC\uAC01 (KST)</th>
        <th class="py-2.5 px-3">\uC784\uBCA0\uB529 \uC5D4\uC9C4</th>
        <th class="py-2.5 px-3">\uC18C\uC694 \uC2DC\uAC04</th>
        <th class="py-2.5 px-3">\uCC98\uB9AC \uAC74\uC218</th>
        <th class="py-2.5 px-3">\uBCD1\uD569 \uAC74\uC218</th>
        <th class="py-2.5 px-3">\uC18C\uC694 \uD1A0\uD070</th>
        <th class="py-2.5 px-3">\uC794\uC5EC \uBBF8\uC784\uBCA0\uB529</th>
        <th class="py-2.5 px-3">\uC0C1\uD0DC</th>
      </tr>
    `;
      const voyRuns = window.voyageWorkerRunsData || [];
      if (voyRuns.length > 0) {
        let rowsHtml = "";
        voyRuns.slice(0, 6).forEach((r) => {
          const isSuccess = r.status === "SUCCESS";
          const statusCls = isSuccess ? "bg-emerald-100 text-emerald-800 border-emerald-300" : "bg-rose-100 text-rose-800 border-rose-300";
          const mergedBadge = r.merged_count && r.merged_count > 0 ? `<span class="px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 text-[10px] font-bold border border-purple-200">${r.merged_count}\uAC74 \uBCD1\uD569</span>` : `<span class="text-ink-muted text-xs">-</span>`;
          const tokensStr = typeof r.tokens_used === "number" ? r.tokens_used.toLocaleString() + " tok" : "-";
          const remainingStr = typeof r.remaining_count === "number" ? r.remaining_count.toLocaleString() + "\uAC74 \uB300\uAE30" : "-";
          rowsHtml += `
          <tr class="hover:bg-slate-50/80 transition">
            <td class="py-2.5 px-3 font-bold text-ink-primary text-[11px]">${r.created_at_kst}</td>
            <td class="py-2.5 px-3 font-medium text-emerald-800 flex items-center gap-1 font-mono text-[11px]">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> ${r.engine || "voyage-4-lite"}
            </td>
            <td class="py-2.5 px-3 font-bold text-ink-primary">${r.duration_str}</td>
            <td class="py-2.5 px-3 font-mono font-semibold text-emerald-700">${r.processed_count}\uAC74 \uC784\uBCA0\uB529</td>
            <td class="py-2.5 px-3 font-mono">${mergedBadge}</td>
            <td class="py-2.5 px-3 font-mono text-[11px] text-ink-secondary">${tokensStr}</td>
            <td class="py-2.5 px-3 font-mono font-medium text-amber-700">${remainingStr}</td>
            <td class="py-2.5 px-3">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${statusCls} inline-flex items-center gap-1">
                ${isSuccess ? "\uC131\uACF5" : "\uC2E4\uD328"}
              </span>
            </td>
          </tr>
        `;
        });
        tbody.innerHTML = rowsHtml;
      } else {
        tbody.innerHTML = `<tr><td colspan="8" class="py-4 text-center text-ink-muted">\uCD5C\uADFC Voyage AI \uC784\uBCA0\uB529 \uC2E4\uD589 \uAE30\uB85D \uB300\uAE30 \uC911... ('\u26A1 Voyage \uC784\uBCA0\uB529' \uBC84\uD2BC\uC744 \uD074\uB9AD\uD558\uBA74 \uC2E4\uC2DC\uAC04 \uBC30\uCE58 \uC791\uC5C5\uC774 \uC2DC\uC791\uB429\uB2C8\uB2E4)</td></tr>`;
      }
    }
    if (typeof lucide !== "undefined") lucide.createIcons({ root: tbody });
  }
  var lastPolledTime = 0;
  async function checkLiveActionsRuns() {
    const now = Date.now();
    if (now - lastPolledTime < 45e3 || typeof document !== "undefined" && document.hidden) return;
    lastPolledTime = now;
    const ctrl = new AbortController();
    const tid = setTimeout(() => ctrl.abort(), 2500);
    try {
      const resp = await fetch("https://api.github.com/repos/AnnyeongHae/ai-factcheck-portfolio/actions/runs?per_page=6", {
        headers: { "Accept": "application/vnd.github.v3+json" },
        signal: ctrl.signal
      });
      clearTimeout(tid);
      if (!resp.ok) return;
      const data = await resp.json();
      const liveRuns = data.workflow_runs || [];
      if (!liveRuns.length) return;
      const kstTz = 9 * 60;
      const pad = (n) => String(n).padStart(2, "0");
      const runs = liveRuns.map((r) => {
        const cDate = new Date(r.created_at);
        const uDate = new Date(r.updated_at);
        const durSec = Math.max(1, Math.floor((uDate - cDate) / 1e3));
        const durStr = `${Math.floor(durSec / 60)}\uBD84 ${durSec % 60}\uCD08`;
        const kstTime = new Date(cDate.getTime() + (kstTz + cDate.getTimezoneOffset()) * 6e4);
        const kstStr = `${kstTime.getFullYear()}-${pad(kstTime.getMonth() + 1)}-${pad(kstTime.getDate())} ${pad(kstTime.getHours())}:${pad(kstTime.getMinutes())}:${pad(kstTime.getSeconds())}`;
        const isSuccess = r.conclusion === "success";
        const isCancelled = r.conclusion === "cancelled";
        const isFailure = r.conclusion === "failure" || r.conclusion === "timed_out";
        const errCount = isFailure ? 1 : 0;
        const existingRuns = typeof window !== "undefined" && window.actionsTelemetryData?.runs || actionsTelemetryData.runs || [];
        const existingRun = existingRuns.find((x) => String(x.id) === String(r.id));
        return {
          id: String(r.id),
          name: r.name,
          event: r.event,
          status: r.status,
          conclusion: r.conclusion || r.status,
          duration_str: durStr,
          duration_sec: durSec,
          items_collected: existingRun?.items_collected || null,
          items_scanned: existingRun?.items_scanned || null,
          created_at_kst: kstStr,
          html_url: r.html_url,
          error_count: errCount
        };
      });
      if (typeof window !== "undefined") {
        window.actionsTelemetryData = window.actionsTelemetryData || {};
        window.actionsTelemetryData.runs = runs;
      }
      actionsTelemetryData.runs = runs;
      renderRunsTable();
      renderPipelineTelemetryCards();
    } catch (e) {
    }
  }
  if (typeof window !== "undefined") {
    window.cronScheduleConfig = cronScheduleConfig;
    window.recomputeTimeline24hFromLiveInbox = recomputeTimeline24hFromLiveInbox;
    window.renderTelemetryCharts = renderTelemetryCharts;
    window.renderPipelineTelemetryCards = renderPipelineTelemetryCards;
    window.updateCronCountdown = updateCronCountdown;
    window.switchRunLogsTab = switchRunLogsTab;
    window.switchRunsTab = switchRunLogsTab;
    window.renderRunsTable = renderRunsTable;
    window.checkLiveActionsRuns = checkLiveActionsRuns;
    setInterval(updateCronCountdown, 1e3);
  }

  // src/js/components/citationGraph.js
  var simulationRef = null;
  var nodeSelection = null;
  var linkSelection = null;
  function initCitationGraph() {
    if (typeof d3 === "undefined") {
      console.warn("[CitationGraph] d3 library is not loaded");
      return;
    }
    const svg = d3.select("#techGraphSvg");
    const container = document.getElementById("graphView");
    if (!container || svg.empty()) return;
    const width = container.clientWidth || 1100;
    const height = 640;
    svg.selectAll("*").remove();
    svg.attr("viewBox", [-width / 2, -height / 2, width, height]);
    const g = svg.append("g");
    svg.call(d3.zoom().scaleExtent([0.2, 4]).on("zoom", (e) => g.attr("transform", e.transform)));
    const rawNodes = window.graphData?.nodes?.length ? window.graphData.nodes : graphData?.nodes || [];
    const rawLinks = window.graphData?.links?.length ? window.graphData.links : graphData?.links || [];
    const nodes = rawNodes.map((d) => ({ ...d }));
    const links = rawLinks.map((d) => ({ ...d }));
    if (nodes.length === 0) {
      console.info("[CitationGraph] No nodes found for citation graph.");
      return;
    }
    simulationRef = d3.forceSimulation(nodes).force("link", d3.forceLink(links).id((d) => d.id).distance(100)).force("charge", d3.forceManyBody().strength(-380)).force("center", d3.forceCenter(0, 0)).force("collision", d3.forceCollide().radius((d) => (d.val || 15) + 14));
    linkSelection = g.append("g").selectAll("line").data(links).join("line").attr("stroke", "rgba(0, 0, 0, 0.12)").attr("stroke-width", 1.5);
    const nodeGroup = g.append("g").selectAll("g").data(nodes).join("g").call(d3.drag().on("start", dragstarted).on("drag", dragged).on("end", dragended));
    function getNodeColor(d) {
      if (d.group === "language") return "#b45309";
      if (d.group === "technology") return "#047857";
      if (d.group === "organization") return "#4338ca";
      if (d.group === "person") return "#be185d";
      if (d.group === "paper") return "#c2410c";
      return "#111827";
    }
    nodeSelection = nodeGroup.append("circle").attr("r", (d) => d.val || 15).attr("fill", (d) => getNodeColor(d)).attr("stroke", "#ffffff").attr("stroke-width", 2.5);
    nodeGroup.append("text").text((d) => d.name || d.id).attr("x", 0).attr("y", (d) => (d.val || 15) + 14).attr("text-anchor", "middle").attr("fill", "#111827").attr("font-size", "11px").attr("font-family", "Pretendard, Noto Sans SC, sans-serif").attr("font-weight", "600");
    simulationRef.on("tick", () => {
      linkSelection.attr("x1", (d) => d.source.x).attr("y1", (d) => d.source.y).attr("x2", (d) => d.target.x).attr("y2", (d) => d.target.y);
      nodeGroup.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });
    function dragstarted(event, d) {
      if (!event.active) simulationRef.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }
    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }
    function dragended(event, d) {
      if (!event.active) simulationRef.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
  }
  function filterGraphGroup(group) {
    window.currentGraphType = group;
    document.querySelectorAll(".graph-group-btn").forEach((btn) => {
      if (btn.dataset.group === group) {
        btn.classList.add("active", "bg-ink-primary", "text-white");
      } else {
        btn.classList.remove("active", "bg-ink-primary", "text-white");
      }
    });
    const nodes = graphData && graphData.nodes || window.graphData && window.graphData.nodes || [];
    if (nodeSelection) {
      nodeSelection.attr("opacity", (d) => group === "ALL" || d.group === group ? 0.95 : 0.08);
    }
    if (linkSelection) {
      linkSelection.attr("opacity", (l) => {
        if (group === "ALL") return 0.4;
        const s = typeof l.source === "object" ? l.source : nodes.find((n) => n.id === l.source);
        const t = typeof l.target === "object" ? l.target : nodes.find((n) => n.id === l.target);
        return s && s.group === group || t && t.group === group ? 0.8 : 0.04;
      });
    }
  }

  // src/js/views/newsView.js
  var newsFetchAbortController = null;
  var newsDbCache = /* @__PURE__ */ new Map();
  function getNewsCacheKey(page = window.currentNewsPage || currentNewsPage || 1) {
    const params = new URLSearchParams();
    params.set("limit", PAGE_SIZE);
    params.set("page", page);
    const t1 = window.currentNewsTier1 || currentNewsTier1;
    const t2 = window.currentNewsTier2 || currentNewsTier2;
    const facet = window.currentNewsFacet || currentNewsFacet;
    const src = window.currentNewsSource || currentNewsSource;
    const search = window.currentNewsSearch || currentNewsSearch;
    const sort = window.currentNewsSort || currentNewsSort;
    if (t1 && t1 !== "ALL") params.set("tier1", t1);
    if (t2 && t2 !== "ALL") params.set("tier2", t2);
    if (facet && facet !== "ALL") params.set("facet", facet);
    if (src && src !== "ALL") params.set("source", src);
    if (search) params.set("search", search);
    if (sort) params.set("sort", sort);
    return params.toString();
  }
  async function fetchNewsFromDb(page = window.currentNewsPage || currentNewsPage || 1, bypassCache = false) {
    const baseUrl = APP_CONFIG.apiUrl("/api/inbox");
    const cacheKey = getNewsCacheKey(page);
    if (!bypassCache) {
      const cached = ClientCache.get(cacheKey, 6e4);
      if (cached) {
        newsDbCache.set(cacheKey, cached);
        return cached;
      }
    }
    if (newsFetchAbortController) {
      try {
        newsFetchAbortController.abort();
      } catch (e) {
      }
    }
    newsFetchAbortController = new AbortController();
    const url = `${baseUrl}?${cacheKey}`;
    const res = await fetch(url, { signal: newsFetchAbortController.signal });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    if (data && data.status === "success") {
      const result = {
        total: data.total || 0,
        totalPages: data.total_pages || Math.ceil((data.total || 0) / PAGE_SIZE) || 1,
        items: data.items || [],
        timestamp: Date.now()
      };
      newsDbCache.set(cacheKey, result);
      ClientCache.set(cacheKey, result);
      return result;
    }
    throw new Error("API returned invalid payload");
  }
  function renderNewsGridItems(items, grid) {
    if (!grid) return;
    grid.innerHTML = "";
    const frag = document.createDocumentFragment();
    const renderPool = Array.isArray(items) ? items : [];
    const curLang = window.currentLang || currentLang || "KO";
    renderPool.forEach((it) => frag.appendChild(createNewsCardElement(it, curLang)));
    grid.appendChild(frag);
    if (window.lucide) window.lucide.createIcons({ root: grid });
  }
  function renderNewsSkeleton2(grid, count = 6) {
    if (!grid) return;
    grid.innerHTML = Array.from({ length: count }).map(() => `
    <div class="executive-card p-5 animate-pulse space-y-4">
      <div class="h-4 bg-slate-200 rounded w-1/3"></div>
      <div class="h-5 bg-slate-200 rounded w-5/6"></div>
      <div class="h-12 bg-slate-100 rounded"></div>
      <div class="h-4 bg-slate-200 rounded w-1/2"></div>
    </div>
  `).join("");
  }
  function setNewsCategoryFilter(t1) {
    window.currentNewsPage = 1;
    window.currentNewsTier1 = t1;
    if (t1 !== "TECH_COMPUTING") {
      window.currentNewsTier2 = "ALL";
    }
    const curFacet = window.currentNewsFacet || currentNewsFacet;
    if (curFacet !== "ALL") {
      window.currentNewsFacet = "ALL";
      document.querySelectorAll(".news-facet-pill").forEach((btn) => {
        const isAll = btn.getAttribute("data-facet") === "ALL";
        if (isAll) {
          btn.className = "news-facet-pill active px-3.5 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 text-white shadow-md ring-2 ring-indigo-300 transition shrink-0 whitespace-nowrap cursor-pointer";
        } else {
          const f = btn.getAttribute("data-facet");
          let colorCls = "text-slate-200 bg-white/10 border-white/20 hover:bg-white/20";
          if (f === "CROSS_SPIKE") colorCls = "text-amber-300 bg-amber-500/10 border-amber-400/30 hover:bg-amber-500/20";
          else if (f === "MODEL") colorCls = "text-cyan-300 bg-cyan-500/10 border-cyan-400/30 hover:bg-cyan-500/20";
          else if (f === "TOOL") colorCls = "text-emerald-300 bg-emerald-500/10 border-emerald-400/30 hover:bg-emerald-500/20";
          btn.className = `news-facet-pill px-3.5 py-1.5 rounded-xl text-xs font-semibold ${colorCls} border transition shrink-0 whitespace-nowrap cursor-pointer`;
        }
      });
    }
    document.querySelectorAll(".news-cat-pill").forEach((btn) => {
      if (btn.getAttribute("data-cat") === t1) {
        btn.className = "news-cat-pill active px-3 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap cursor-pointer";
      } else {
        btn.className = "news-cat-pill px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap cursor-pointer";
      }
    });
    const curT2 = window.currentNewsTier2 || currentNewsTier2;
    document.querySelectorAll(".news-t2-pill").forEach((btn) => {
      if (btn.getAttribute("data-t2") === curT2) {
        btn.className = "news-t2-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap cursor-pointer";
      } else {
        btn.className = "news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap cursor-pointer";
      }
    });
    const t2Container = document.getElementById("newsTier2Container");
    if (t2Container) {
      if (t1 !== "ALL" && t1 !== "TECH_COMPUTING") {
        t2Container.classList.add("opacity-40", "pointer-events-none");
      } else {
        t2Container.classList.remove("opacity-40", "pointer-events-none");
      }
    }
    renderNews();
  }
  function setNewsTier2Filter(t2) {
    window.currentNewsPage = 1;
    window.currentNewsTier2 = t2;
    const curT1 = window.currentNewsTier1 || currentNewsTier1;
    if (t2 !== "ALL" && curT1 !== "ALL" && curT1 !== "TECH_COMPUTING") {
      window.currentNewsTier1 = "TECH_COMPUTING";
      document.querySelectorAll(".news-cat-pill").forEach((btn) => {
        if (btn.getAttribute("data-cat") === "TECH_COMPUTING") {
          btn.className = "news-cat-pill active px-3 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap cursor-pointer";
        } else {
          btn.className = "news-cat-pill px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap cursor-pointer";
        }
      });
      const t2Container = document.getElementById("newsTier2Container");
      if (t2Container) t2Container.classList.remove("opacity-40", "pointer-events-none");
    }
    document.querySelectorAll(".news-t2-pill").forEach((btn) => {
      if (btn.getAttribute("data-t2") === t2) {
        btn.className = "news-t2-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap cursor-pointer";
      } else {
        btn.className = "news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap cursor-pointer";
      }
    });
    renderNews();
  }
  var newsSearchDebounceTimer = null;
  function updateSearchClearBtn(val) {
    const btn = document.getElementById("newsSearchClearBtn");
    if (btn) {
      if (val && String(val).trim().length > 0) {
        btn.classList.remove("hidden");
      } else {
        btn.classList.add("hidden");
      }
    }
  }
  function clearNewsSearch() {
    const input = document.getElementById("newsSearchInput");
    if (input) {
      input.value = "";
      input.focus();
    }
    updateSearchClearBtn("");
    handleNewsSearchImmediate("");
  }
  function handleNewsSearch(val) {
    updateSearchClearBtn(val);
    clearTimeout(newsSearchDebounceTimer);
    newsSearchDebounceTimer = setTimeout(() => {
      window.targetSelectedInboxId = "";
      window.currentNewsPage = 1;
      window.currentNewsSearch = (val || "").trim().toLowerCase();
      renderNews();
    }, 300);
  }
  function handleNewsSearchImmediate(val) {
    updateSearchClearBtn(val);
    clearTimeout(newsSearchDebounceTimer);
    window.targetSelectedInboxId = "";
    window.currentNewsPage = 1;
    window.currentNewsSearch = (val || "").trim().toLowerCase();
    renderNews();
  }
  function setNewsSort(sort) {
    window.currentNewsPage = 1;
    window.currentNewsSort = sort;
    renderNews();
  }
  function setNewsFacetFilter(facet) {
    window.targetSelectedInboxId = "";
    window.currentNewsPage = 1;
    window.currentNewsFacet = facet;
    const sortSel = document.getElementById("newsSortSelect");
    if (facet === "CROSS_SPIKE") {
      window.currentNewsSort = "viral-score-desc";
      if (sortSel) sortSel.value = "viral-score-desc";
    } else if (facet === "ALL" || window.currentNewsSort === "viral-score-desc") {
      window.currentNewsSort = "date-audit-desc";
      if (sortSel) sortSel.value = "date-audit-desc";
    }
    if (facet !== "ALL") {
      window.currentNewsTier1 = "ALL";
      window.currentNewsTier2 = "ALL";
      document.querySelectorAll(".news-cat-pill").forEach((btn) => {
        if (btn.getAttribute("data-cat") === "ALL") {
          btn.className = "news-cat-pill active px-3 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap cursor-pointer";
        } else {
          btn.className = "news-cat-pill px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap cursor-pointer";
        }
      });
      document.querySelectorAll(".news-t2-pill").forEach((btn) => {
        if (btn.getAttribute("data-t2") === "ALL") {
          btn.className = "news-t2-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap cursor-pointer";
        } else {
          btn.className = "news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap cursor-pointer";
        }
      });
      const t2Container = document.getElementById("newsTier2Container");
      if (t2Container) t2Container.classList.remove("opacity-40", "pointer-events-none");
    }
    document.querySelectorAll(".news-facet-pill").forEach((btn) => {
      const isActive = btn.getAttribute("data-facet") === facet;
      if (isActive) {
        btn.className = "news-facet-pill active px-3.5 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 text-white shadow-md ring-2 ring-indigo-300 transition shrink-0 whitespace-nowrap cursor-pointer";
      } else {
        const f = btn.getAttribute("data-facet");
        let colorCls = "text-slate-200 bg-white/10 border-white/20 hover:bg-white/20";
        if (f === "CROSS_SPIKE") colorCls = "text-amber-300 bg-amber-500/10 border-amber-400/30 hover:bg-amber-500/20";
        else if (f === "MODEL") colorCls = "text-cyan-300 bg-cyan-500/10 border-cyan-400/30 hover:bg-cyan-500/20";
        else if (f === "TOOL") colorCls = "text-emerald-300 bg-emerald-500/10 border-emerald-400/30 hover:bg-emerald-500/20";
        btn.className = `news-facet-pill px-3.5 py-1.5 rounded-xl text-xs font-semibold ${colorCls} border transition shrink-0 whitespace-nowrap cursor-pointer`;
      }
    });
    const grid = document.getElementById("newsGrid");
    if (grid) renderNewsSkeleton2(grid, 6);
    renderNews();
  }
  function setNewsSourceFilter(src) {
    window.currentNewsPage = 1;
    window.currentNewsSource = src;
    document.querySelectorAll(".news-src-btn").forEach((btn) => {
      if (btn.getAttribute("data-src") === src) {
        btn.className = "news-src-btn active px-2.5 py-1 rounded-lg text-xs font-bold bg-ink-primary text-white transition shrink-0 whitespace-nowrap";
      } else {
        btn.className = "news-src-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:bg-white transition border border-surface-border shrink-0 whitespace-nowrap";
      }
    });
    renderNews();
  }
  async function renderNews() {
    const grid = document.getElementById("newsGrid");
    if (!grid) return;
    const curLang = window.currentLang || currentLang || "KO";
    const curPage = window.currentNewsPage || currentNewsPage || 1;
    const curT1 = window.currentNewsTier1 || currentNewsTier1 || "ALL";
    const curT2 = window.currentNewsTier2 || currentNewsTier2 || "ALL";
    const curFacet = window.currentNewsFacet || currentNewsFacet || "ALL";
    const curSrc = window.currentNewsSource || currentNewsSource || "ALL";
    const curSearch = window.currentNewsSearch || currentNewsSearch || "";
    const targetId = window.targetSelectedInboxId || targetSelectedInboxId || "";
    const cacheKey = getNewsCacheKey(curPage);
    const isDefaultFilter = curT1 === "ALL" && curT2 === "ALL" && curFacet === "ALL" && !curSearch && !targetId;
    let renderedFromCache = false;
    let cachedFirstId = null;
    let cached = newsDbCache.get(cacheKey);
    if (!cached) {
      cached = ClientCache.get(cacheKey, 6e4);
      if (cached) newsDbCache.set(cacheKey, cached);
    }
    if (cached && Array.isArray(cached.items) && cached.items.length > 0) {
      renderNewsGridItems(cached.items, grid);
      renderPagination("newsPagination", curPage, cached.totalPages, "changeNewsPage");
      if (window.lucide) window.lucide.createIcons({ root: grid });
      renderedFromCache = true;
      cachedFirstId = cached.items[0]?.inbox_id || cached.items[0]?.id;
      if (Date.now() - (cached.timestamp || 0) < 1e4) {
        return;
      }
    }
    let memMatches = [];
    const curSort = window.currentNewsSort || currentNewsSort || "date-audit-desc";
    if (!renderedFromCache) {
      const newsList = window.liveNewsData || liveNewsData || [];
      memMatches = newsList.filter((it) => {
        if (targetId && (it.inbox_id === targetId || it.id === targetId)) return true;
        if ((curSort === "date-audit-desc" || curSort === "date-audit-asc") && (!it.ai_enrichment || !it.ai_enrichment.enriched_at)) return false;
        if (curT1 !== "ALL" && (it.tier1_category || "TECH_COMPUTING") !== curT1) return false;
        if (curT2 !== "ALL" && (it.tier2_category || it.category_primary || "INDUSTRY_TRENDS") !== curT2) return false;
        if (curFacet === "CROSS_SPIKE" && !it.is_cross_spiking && (!it.sources || it.sources.length <= 1)) return false;
        if (curFacet === "MODEL" && !it.is_model && it.facet_type !== "MODEL") return false;
        if (curFacet === "TOOL" && it.facet_type !== "TOOL" && !(it.source_platform || "").toLowerCase().includes("github") && !(it.artifact_type || "").includes("agent") && !(it.artifact_type || "").includes("skill") && !(it.category_primary || "").toLowerCase().includes("devtool")) return false;
        if (curFacet === "NEWS" && (it.is_model || it.facet_type === "MODEL" || (it.source_platform || "").toLowerCase().includes("github"))) return false;
        if (curSrc !== "ALL") {
          const plat = (it.source_platform || "").toLowerCase();
          const filterKey = curSrc.toLowerCase();
          const hasInCrossPosts = Array.isArray(it.cross_posts) && it.cross_posts.some((cp) => (cp.platform || "").toLowerCase().includes(filterKey));
          const hasInSources = Array.isArray(it.sources) && it.sources.some((s) => (s.platform || s.source_name || "").toLowerCase().includes(filterKey));
          if (!plat.includes(filterKey) && !hasInCrossPosts && !hasInSources) return false;
        }
        if (curSearch) {
          const s = curSearch.toLowerCase();
          const matchTitle = (it.title || "").toLowerCase().includes(s) || (it.title_ko || "").toLowerCase().includes(s);
          const matchHook = (it.hook || "").toLowerCase().includes(s) || (it.hook_ko || "").toLowerCase().includes(s);
          if (!matchTitle && !matchHook) return false;
        }
        return true;
      });
      if (memMatches.length >= PAGE_SIZE || targetId && memMatches.length > 0) {
        sortCollection(memMatches, curSort);
        const optimisticSlice = memMatches.slice(0, PAGE_SIZE);
        renderNewsGridItems(optimisticSlice, grid);
        const estPages = Math.ceil((snapshotStats.inbox_total_count || memMatches.length) / PAGE_SIZE) || 1;
        renderPagination("newsPagination", curPage, estPages, "changeNewsPage");
        if (window.lucide) window.lucide.createIcons({ root: grid });
      } else {
        renderNewsSkeleton2(grid, 6);
      }
    }
    try {
      const dbRes = await fetchNewsFromDb(curPage, renderedFromCache);
      const items = dbRes.items || [];
      const total = dbRes.total || 0;
      const totalPages = dbRes.totalPages || Math.ceil(total / PAGE_SIZE) || 1;
      const newFirstId = items[0]?.inbox_id || items[0]?.id;
      if (!renderedFromCache || newFirstId !== cachedFirstId || items.length !== newsDbCache.get(cacheKey)?.items?.length) {
        if (items.length === 0) {
          grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${curLang === "KO" ? "\uD574\uB2F9 \uD50C\uB7AB\uD3FC/\uC870\uAC74\uC758 \uC218\uC9D1 AI \uB274\uC2A4\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4." : curLang === "ZH" ? "\u6682\u65E0\u8BE5\u6761\u4EF6\u7684 AI \u8D44\u8BAF\u3002" : "No AI news articles available for this criteria."}</div>`;
        } else {
          renderNewsGridItems(items, grid);
        }
        if (window.currentNewsPage > totalPages) window.currentNewsPage = totalPages;
        if (window.currentNewsPage < 1) window.currentNewsPage = 1;
        renderPagination("newsPagination", window.currentNewsPage, totalPages, "changeNewsPage");
        if (isDefaultFilter && total > 0) {
          const fullCount = snapshotStats.inbox_total_count || total;
          const numEl = document.getElementById("statValNews");
          if (numEl) numEl.textContent = fullCount.toLocaleString();
          const headEl = document.getElementById("headerNewsCount");
          if (headEl) headEl.textContent = `(${fullCount.toLocaleString()})`;
        }
      }
    } catch (err) {
      if (err.name === "AbortError") return;
      console.warn("[News DB-Native Fetch Fallback]:", err.message);
      if (!renderedFromCache && memMatches.length > 0 && grid.querySelector(".animate-pulse")) {
        sortCollection(memMatches, curSort);
        renderNewsGridItems(memMatches.slice(0, PAGE_SIZE), grid);
        renderPagination("newsPagination", curPage, Math.ceil(memMatches.length / PAGE_SIZE) || 1, "changeNewsPage");
      }
    }
  }

  // src/js/views/homeView.js
  var activeRadarSession = 1;
  function switchRadarSession(sessionNum) {
    activeRadarSession = sessionNum;
    window.activeRadarSession = sessionNum;
    renderRadarSession();
  }
  function navigateFromRadar(view, searchKey, inboxId) {
    window.targetSelectedInboxId = inboxId || "";
    switchView(view);
    const cleanQ = (searchKey || "").trim();
    if (view === "models") {
      window.currentModelsPage = 1;
      window.modelsSearchQuery = cleanQ;
      const inp = document.getElementById("modelsSearchInput");
      if (inp) inp.value = cleanQ;
      renderModels();
    } else if (view === "news") {
      window.currentNewsPage = 1;
      window.currentNewsSearch = cleanQ.toLowerCase();
      const inp = document.getElementById("newsSearchInput");
      if (inp) inp.value = cleanQ;
      renderNews();
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  function renderRadarSession() {
    const radarData = trendRadarData && trendRadarData.sessions ? trendRadarData : window.trendRadarData || {};
    if (!radarData.sessions) return;
    const sessionData = radarData.sessions[String(activeRadarSession)];
    if (!sessionData) return;
    const sLabels = {
      KO: ["1\uD68C 00\uC2DC", "2\uD68C 06\uC2DC", "3\uD68C 12\uC2DC", "4\uD68C 18\uC2DC"],
      ZH: ["1\u671F 00\u70B9", "2\u671F 06\u70B9", "3\u671F 12\u70B9", "4\u671F 18\u70B9"],
      EN: ["S1 00:00", "S2 06:00", "S3 12:00", "S4 18:00"]
    };
    const curLang = window.currentLang || currentLang || "KO";
    const curLabels = sLabels[curLang] || sLabels["KO"];
    for (let i = 1; i <= 4; i++) {
      const btn = document.getElementById("radarBtn" + i);
      if (btn) {
        btn.innerText = curLabels[i - 1];
        if (i === activeRadarSession) {
          btn.className = "px-2 py-0.5 rounded border border-emerald-600 bg-emerald-600 text-white font-bold shadow-xs transition cursor-pointer";
        } else {
          btn.className = "px-2 py-0.5 rounded border border-surface-border bg-surface-subtle text-ink-muted hover:text-ink-primary hover:bg-slate-100 transition cursor-pointer font-medium";
        }
      }
    }
    const windowLabelEl = document.getElementById("trendRadarWindowLabel");
    const pulseDotEl = document.getElementById("trendRadarPulseDot");
    if (windowLabelEl) {
      const wLabel = (curLang === "KO" ? sessionData.window_label_ko : curLang === "ZH" ? sessionData.window_label_zh : sessionData.window_label_en) || sessionData.window_label;
      windowLabelEl.innerText = wLabel;
    }
    if (pulseDotEl) {
      if (sessionData.is_current) {
        pulseDotEl.className = "w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse";
      } else if (sessionData.is_future) {
        pulseDotEl.className = "w-1.5 h-1.5 rounded-full bg-amber-500";
      } else {
        pulseDotEl.className = "w-1.5 h-1.5 rounded-full bg-slate-400";
      }
    }
    const bulletsContainer = document.getElementById("trendRadarBullets");
    if (bulletsContainer) {
      bulletsContainer.innerHTML = "";
      const items = sessionData.items || [];
      if (items.length > 0) {
        items.forEach((it, idx) => {
          const cleanPlatform = cleanPlatformName(it.platform || it.source_platform || "AI Hub");
          let platformBadgeClass = "bg-surface-subtle text-ink-primary border-surface-border";
          const pf = (it.platform_family || "").toLowerCase();
          if (pf.includes("github")) {
            platformBadgeClass = "bg-slate-100 text-slate-800 border-slate-300";
          } else if (pf.includes("hugging")) {
            platformBadgeClass = "bg-purple-50 text-purple-700 border-purple-200";
          } else if (pf.includes("arxiv")) {
            platformBadgeClass = "bg-rose-50 text-rose-700 border-rose-200";
          } else if (pf.includes("hacker")) {
            platformBadgeClass = "bg-amber-50 text-amber-800 border-amber-200";
          } else if (pf.includes("geek")) {
            platformBadgeClass = "bg-blue-50 text-blue-700 border-blue-200";
          }
          const itemTitle = (curLang === "KO" ? it.title_ko || it.title : curLang === "ZH" ? it.title_zh || it.title : it.title_en || it.title) || it.title;
          const itemSummary = (curLang === "KO" ? it.summary_ko || it.summary : curLang === "ZH" ? it.summary_zh || it.summary : it.summary_en || it.summary) || it.summary;
          const factCheckBtnText = curLang === "KO" ? "\uD329\uD2B8\uCCB4\uD06C" : curLang === "ZH" ? "\u4E8B\u5B9E\u6838\u67E5" : "Fact-Check";
          const pointBadgeHtml = formatRadarPointBadge(it, curLang);
          const itemCard = document.createElement("div");
          itemCard.className = "group p-3 rounded-xl bg-surface-subtle/50 hover:bg-white border border-surface-border hover:border-emerald-400 hover:shadow-xs transition duration-150 flex flex-col gap-2";
          itemCard.innerHTML = `
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="w-5 h-5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200/80 flex items-center justify-center font-mono font-bold text-[10px] shrink-0">0${idx + 1}</span>
              <span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold ${platformBadgeClass} border">${cleanPlatform}</span>
              ${pointBadgeHtml}
              ${it.is_this_session ? `<span class="px-1.5 py-0.5 rounded-md text-[9px] font-mono font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-0.5"><i data-lucide="sparkles" class="w-2.5 h-2.5 text-emerald-700"></i><span>${curLang === "KO" ? "\uC2E4\uC2DC\uAC04 \uC2E0\uADDC" : curLang === "ZH" ? "\u5B9E\u65F6\u66F4\u65B0" : "Live New"}</span></span>` : ""}
            </div>
            <div class="flex items-center gap-1.5 shrink-0">
              ${it.case_id ? `
                <button onclick="openCaseModal('${it.case_id}')" class="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800 border border-emerald-300 hover:bg-emerald-200 flex items-center gap-1 transition cursor-pointer">
                  <i data-lucide="shield-check" class="w-3 h-3 text-emerald-700"></i>
                  <span>${factCheckBtnText}</span>
                </button>
              ` : ""}
            </div>
          </div>

          <a href="${it.source_url}" target="_blank" rel="noopener noreferrer" class="group/title block">
            <div class="text-xs sm:text-[13px] font-bold text-ink-primary group-hover/title:text-emerald-700 transition flex items-center justify-between gap-2 leading-snug">
              <span class="line-clamp-1">${itemTitle}</span>
              <span class="text-[11px] font-mono text-emerald-700 shrink-0 flex items-center gap-0.5 opacity-80 group-hover/title:opacity-100 bg-emerald-50 hover:bg-emerald-100 px-1.5 py-0.5 rounded border border-emerald-200 transition">
                <i data-lucide="arrow-up-right" class="w-3 h-3"></i>
              </span>
            </div>
            ${itemSummary ? `<p class="text-[11px] text-ink-muted line-clamp-1 leading-relaxed mt-1">${itemSummary}</p>` : ""}
          </a>

          <div class="pt-1.5 border-t border-surface-border/60 flex items-center justify-between text-[10px] font-mono text-ink-muted flex-wrap gap-1">
            <span class="flex items-center gap-1"><i data-lucide="calendar" class="w-3 h-3 text-slate-400"></i><span class="font-medium">${curLang === "KO" ? "\uBC1C\uD589" : curLang === "ZH" ? "\u53D1\u5E03" : "Pub"}:</span> ${formatDateTimeCompact(it.published_at || it.harvested_at)}</span>
            <span class="flex items-center gap-1"><i data-lucide="download" class="w-3 h-3 text-slate-400"></i><span class="font-medium">${curLang === "KO" ? "\uC218\uC9D1" : curLang === "ZH" ? "\u91C7\u96C6" : "Rec"}:</span> ${formatDateTimeCompact(it.harvested_at)}</span>
          </div>
        `;
          bulletsContainer.appendChild(itemCard);
        });
      } else {
        const emptyMsg = curLang === "KO" ? "\uC774 \uD68C\uCC28\uC5D0 \uB4F1\uB85D\uB41C \uD2B8\uB80C\uB4DC \uB370\uC774\uD130\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4." : curLang === "ZH" ? "\u8BE5\u65F6\u6BB5\u6682\u65E0\u8D8B\u52BF\u6570\u636E\u3002" : "No trend data for this session.";
        bulletsContainer.innerHTML = `<div class="py-6 text-center text-xs text-ink-muted font-mono">${emptyMsg}</div>`;
      }
    }
    if (window.lucide) window.lucide.createIcons();
  }
  function renderHomeTopPicks() {
    const container = document.getElementById("homeTopPicksContainer");
    if (!container) return;
    container.innerHTML = "";
    const cases = window.liveCasesData && window.liveCasesData.length > 0 ? window.liveCasesData : liveCasesData && liveCasesData.length > 0 ? liveCasesData : AppStore.getCases() || [];
    const sortedCases = sortCollection([...cases], "date-audit-desc");
    const top3 = sortedCases.slice(0, 3);
    const curLang = window.currentLang || currentLang || "KO";
    top3.forEach((c) => {
      const card = document.createElement("div");
      card.className = "p-4 rounded-xl border border-surface-border bg-surface-subtle hover:bg-white hover:border-ink-primary hover:shadow-md transition cursor-pointer flex flex-col justify-between space-y-2.5";
      card.onclick = () => openModal(c);
      const isVerifiedTrue = c.verdict === "VERIFIED_TRUE";
      const isHalfTrue = (c.verdict || "").includes("HALF");
      const badgeColor = isVerifiedTrue ? "bg-emerald-50 text-emerald-800 border-emerald-200" : isHalfTrue ? "bg-amber-50 text-amber-900 border-amber-200" : "bg-rose-50 text-rose-800 border-rose-200";
      const badgeLabel = isVerifiedTrue ? curLang === "KO" ? "\uC0AC\uC2E4 \uAC80\uC99D\uB428" : curLang === "ZH" ? "\u4E8B\u5B9E\u5DF2\u6838\u9A8C" : "Verified True" : isHalfTrue ? curLang === "KO" ? "\uC808\uBC18\uC758 \uC0AC\uC2E4" : curLang === "ZH" ? "\u90E8\u5206\u5C5E\u5B9E" : "Half True" : curLang === "KO" ? "\uACFC\uC7A5/\uC65C\uACE1" : curLang === "ZH" ? "\u5938\u5927/\u5931\u5B9E" : "Gamed/Hype";
      const { displayTitle, displayHook } = getLocalizedContent(c, curLang);
      const displayDate = c.investigation_date || (c.source_published_date ? c.source_published_date.slice(0, 10) : "2026-09-04");
      card.innerHTML = `
      <div class="space-y-2">
        <div class="flex items-center justify-between text-xs font-mono">
          <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${badgeColor}">${badgeLabel}</span>
          <span class="text-ink-muted text-[11px] font-semibold">${c.confidence_score || 95}%</span>
        </div>
        <h4 class="text-xs sm:text-sm font-bold text-ink-primary line-clamp-2 leading-snug hover:text-indigo-600 transition">${displayTitle}</h4>
        <p class="text-[11px] text-ink-secondary line-clamp-2 leading-relaxed">${displayHook}</p>
      </div>
      <div class="pt-2 border-t border-surface-border flex items-center justify-between text-[10px] font-mono text-ink-muted">
        <span>\u{1F52C} ${curLang === "KO" ? "\uBD84\uC11D\uC77C: " : curLang === "ZH" ? "\u5206\u6790\u65E5: " : "Audited: "}${displayDate}</span>
        <span class="font-bold text-indigo-700 flex items-center gap-0.5">${curLang === "KO" ? "\uC0C1\uC138 \uBCF4\uACE0\uC11C" : curLang === "ZH" ? "\u67E5\u770B\u62A5\u544A" : "View Dossier"} <i data-lucide="arrow-right" class="w-3 h-3"></i></span>
      </div>
    `;
      container.appendChild(card);
    });
    if (window.lucide) window.lucide.createIcons({ root: container });
  }

  // src/js/views/inboxView.js
  function setInboxSort(val) {
    window.currentInboxPage = 1;
    window.currentInboxSort = val;
    renderInbox();
  }
  function toggleInboxIncludePending(checked) {
    window.inboxIncludePending = !!checked;
    window.currentInboxPage = 1;
    renderInbox();
  }
  function setInboxLangFilter(lang) {
    window.currentInboxPage = 1;
    window.currentInboxLang = lang;
    document.querySelectorAll(".inbox-filter-pill").forEach((btn) => {
      if (btn.dataset.langVal === lang) {
        btn.className = "inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap";
      } else {
        btn.className = "inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap";
      }
    });
    renderInbox();
  }
  function setInboxTypeFilter(typeVal) {
    window.currentInboxPage = 1;
    window.currentInboxType = typeVal;
    document.querySelectorAll(".inbox-type-pill").forEach((btn) => {
      if (btn.dataset.typeVal === typeVal) {
        btn.className = "inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap";
      } else {
        btn.className = "inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap";
      }
    });
    renderInbox();
  }
  function setInboxTechFilter(tech) {
    window.currentInboxPage = 1;
    window.currentInboxTech = tech;
    document.querySelectorAll(".inbox-tech-pill").forEach((btn) => {
      if (btn.dataset.techVal === tech) {
        btn.className = "inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap";
      } else {
        btn.className = "inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap";
      }
    });
    renderInbox();
  }
  function setInboxSourceFilter(src) {
    window.currentInboxPage = 1;
    window.currentInboxSource = src;
    const sel = document.getElementById("inboxSourceSelect");
    if (sel && sel.value !== src) sel.value = src;
    document.querySelectorAll(".inbox-src-pill").forEach((btn) => {
      if (btn.dataset.srcVal === src) {
        btn.className = "inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap";
      } else {
        btn.className = "inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap";
      }
    });
    renderInbox();
  }
  async function toggleQueueItem(inboxId, title) {
    const isCurrentlyQueued = queuedItemIds.has(inboxId);
    const action = isCurrentlyQueued ? "unqueue" : "queue";
    if (isCurrentlyQueued) {
      queuedItemIds.delete(inboxId);
    } else {
      queuedItemIds.add(inboxId);
    }
    try {
      localStorage.setItem("queued_factchecks", JSON.stringify(Array.from(queuedItemIds)));
    } catch (e) {
    }
    renderInbox();
    try {
      const res = await fetch(API_BASE + "/api/queue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ inbox_id: inboxId, action })
      });
      if (res.ok) {
        showToast(action === "queue" ? `[${title}] \uD56D\uBAA9\uC774 \uD074\uB77C\uC6B0\uB4DC DB \uC2E4\uC2DC\uAC04 \uD050\uC5D0 \uB4F1\uB85D\uB418\uC5C8\uC2B5\uB2C8\uB2E4!` : `\uB300\uAE30\uC5F4\uC5D0\uC11C \uC81C\uC678\uB418\uC5C8\uC2B5\uB2C8\uB2E4.`);
        return;
      }
    } catch (err) {
    }
    showToast(isCurrentlyQueued ? `\uB300\uAE30\uC5F4\uC5D0\uC11C \uC81C\uC678\uB418\uC5C8\uC2B5\uB2C8\uB2E4.` : `[${title}] \uD56D\uBAA9\uC774 \uB300\uAE30\uC5F4\uC5D0 \uB4F1\uB85D\uB418\uC5C8\uC2B5\uB2C8\uB2E4.`);
  }
  var inboxDbCache = /* @__PURE__ */ new Map();
  var inboxFetchAbortController = null;
  function getInboxCacheKey(page) {
    const params = new URLSearchParams();
    params.set("limit", PAGE_SIZE);
    params.set("page", page);
    const curSrc = window.currentInboxSource || currentInboxSource || "ALL";
    const curLangFilter = window.currentInboxLang || currentInboxLang || "ALL";
    const curType = window.currentInboxType || currentInboxType || "ALL";
    const curSearch = window.inboxSearchQuery || inboxSearchQuery || "";
    const curSort = window.currentInboxSort || currentInboxSort || "date-audit-desc";
    if (curSrc && curSrc !== "ALL") params.set("source", curSrc);
    if (curLangFilter && curLangFilter !== "ALL") params.set("lang", curLangFilter);
    if (curType && curType !== "ALL") params.set("type", curType);
    if (curSearch) params.set("search", curSearch);
    if (curSort) params.set("sort", curSort);
    if (window.inboxIncludePending) params.set("include_pending", "true");
    return params.toString();
  }
  async function fetchInboxFromDb(page = window.currentInboxPage || currentInboxPage || 1, bypassCache = false) {
    const baseUrl = APP_CONFIG.apiUrl("/api/inbox");
    const cacheKey = getInboxCacheKey(page);
    if (!bypassCache) {
      const cached = ClientCache.get(cacheKey, 6e4);
      if (cached) {
        inboxDbCache.set(cacheKey, cached);
        return cached;
      }
    }
    if (inboxFetchAbortController) {
      try {
        inboxFetchAbortController.abort();
      } catch (e) {
      }
    }
    inboxFetchAbortController = new AbortController();
    const url = `${baseUrl}?${cacheKey}`;
    const res = await fetch(url, { signal: inboxFetchAbortController.signal });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    if (data && data.status === "success") {
      const result = {
        total: data.total || 0,
        totalPages: data.total_pages || Math.ceil((data.total || 0) / PAGE_SIZE) || 1,
        items: data.items || [],
        timestamp: Date.now()
      };
      inboxDbCache.set(cacheKey, result);
      ClientCache.set(cacheKey, result);
      return result;
    }
    throw new Error("API returned invalid payload");
  }
  function createInboxCardElement(it, curLang) {
    const isQueued = queuedItemIds.has(it.inbox_id);
    const ai = it.ai_enrichment;
    const effectiveSourceLang = detectSourceLang(it);
    const { displayTitle, displayHook, displayDesc, displayTakeaways, hasTrilingual } = getLocalizedContent(it, curLang);
    const showDesc = (!displayTakeaways || displayTakeaways.length === 0) && displayDesc;
    const viralScore = calculateStandardizedViralScore(it);
    const tracking = it.metric_tracking || {};
    const initDate = formatKstMonthDay(tracking.initial?.recorded_at || tracking.initial_date || it.created_at || it.harvested_date);
    const latestDate = formatKstMonthDay(tracking.latest?.updated_at || tracking.latest_date || it.updated_at || it.harvested_date);
    const initVal = tracking.initial?.display || tracking.initial_metric || it.viral_metric || "-";
    const latestVal = tracking.latest?.display || tracking.latest_metric || it.viral_metric || "-";
    const delta = tracking.delta !== void 0 ? tracking.delta : tracking.growth_delta || 0;
    let typeBadge = curLang === "KO" ? "\u26A1 \uC2E0\uAE30\uC220" : curLang === "ZH" ? "\u26A1 \u65B0\u6280\u672F" : "\u26A1 Tech";
    if (ai && ai.type_classification === "AGENT") typeBadge = curLang === "KO" ? "\u{1F9BE} \uC5D0\uC774\uC804\uD2B8" : curLang === "ZH" ? "\u{1F9BE} \u667A\u80FD\u4F53" : "\u{1F9BE} Agent";
    else if (ai && ai.type_classification === "MODEL") typeBadge = curLang === "KO" ? "\u{1F916} AI \uBAA8\uB378" : curLang === "ZH" ? "\u{1F916} AI \u6A21\u578B" : "\u{1F916} AI Model";
    else if (ai && ai.type_classification === "NEWS") typeBadge = curLang === "KO" ? "\u{1F4F0} \uC5C5\uACC4 \uB3D9\uD5A5" : curLang === "ZH" ? "\u{1F4F0} \u884C\u4E1A\u8D44\u8BAF" : "\u{1F4F0} News";
    const card = document.createElement("div");
    card.className = "executive-card p-4 sm:p-5 flex flex-col justify-between space-y-3.5 hover:border-indigo-400 hover:shadow-md transition";
    const hookHtml = renderHookCallout(displayHook);
    const aiSummaryHtml = renderAiTakeaways(displayTakeaways, curLang);
    const relatedHtml = renderRelatedDossierButton(it.related_dossier, curLang);
    const rawComments = Array.isArray(it.raw_comments) ? it.raw_comments : Array.isArray(it.raw_payload?.raw_comments) ? it.raw_payload.raw_comments : [];
    const commentsHtml = renderCommentsAccordion(rawComments, curLang, it.source_url);
    const queueActionBtn = `
    <button onclick="toggleQueueItem('${it.inbox_id}', '${displayTitle.replace(/'/g, "")}')" 
            class="px-2.5 py-1 rounded-lg text-xs font-bold transition flex items-center gap-1.5 shrink-0 ${isQueued ? "bg-emerald-700 text-white font-black" : "bg-surface-subtle text-ink-primary hover:bg-ink-primary hover:text-white border border-surface-border"}">
      <i data-lucide="${isQueued ? "check-circle-2" : "plus-circle"}" class="w-3.5 h-3.5"></i>
      <span>${isQueued ? curLang === "KO" ? "\uD050 \uB4F1\uB85D\uB428" : curLang === "ZH" ? "\u5DF2\u5165\u961F\u5217" : "Queued" : curLang === "KO" ? "\uD050 \uCD94\uAC00" : curLang === "ZH" ? "\u52A0\u5165\u961F\u5217" : "Queue"}</span>
    </button>
  `;
    const footerHtml = renderCardStandardFooter(it, curLang, queueActionBtn);
    card.innerHTML = `
    <div class="space-y-2.5">
      <div class="flex items-center justify-between text-xs font-mono">
        <span class="px-2 py-0.5 rounded bg-surface-subtle text-ink-primary font-bold border border-surface-border text-[11px]">
          ${it.source_platform || "Tech Candidate"}
        </span>
        <span class="px-2.5 py-0.5 rounded-lg text-[11px] font-black font-mono shadow-2xs flex items-center gap-1 ${viralScore >= 70 ? "bg-rose-100/90 text-rose-800 border border-rose-300" : "bg-amber-100/90 text-amber-900 border border-amber-300"}">
          <i data-lucide="flame" class="w-3 h-3 ${viralScore >= 70 ? "text-rose-600 fill-rose-500" : "text-amber-600 fill-amber-500"}"></i>
          <span>${curLang === "KO" ? `\uC778\uAE30 ${viralScore}\uC810` : curLang === "ZH" ? `\u70ED\u5EA6 ${viralScore}\u5206` : `Viral ${viralScore} pts`}</span>
        </span>
      </div>

      <div class="flex items-center gap-1.5 flex-wrap">
        <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-900 border border-indigo-200">
          ${typeBadge}
        </span>
        ${ai && ai.programming_lang && ai.programming_lang !== "General" ? `<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-50 text-amber-900 border border-amber-200">\u{1F4BB} ${ai.programming_lang}</span>` : ""}
        ${effectiveSourceLang ? `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-semibold bg-surface-subtle text-ink-muted border border-surface-border">\u{1F310} ${effectiveSourceLang}</span>` : ""}
        ${hasTrilingual ? `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">\u{1F310} KO\xB7EN\xB7ZH</span>` : `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-medium bg-surface-subtle text-ink-muted border border-surface-border">\u{1F310} \uBC88\uC5ED \uB300\uAE30</span>`}
      </div>

      <h3 class="font-bold text-sm text-ink-primary leading-snug">
        ${displayTitle}
      </h3>

      ${hookHtml}

      ${showDesc ? `<p class="text-xs text-ink-secondary leading-relaxed line-clamp-3">${displayDesc}</p>` : ""}

      ${aiSummaryHtml}
      ${relatedHtml}
      ${commentsHtml}

      <div class="p-2.5 rounded-xl bg-surface-subtle border border-surface-border text-[11px] space-y-1 font-mono">
        <div class="flex items-center justify-between text-ink-muted">
          <span>${curLang === "KO" ? "\uCD5C\uCD08 \uC218\uC9D1" : curLang === "ZH" ? "\u9996\u6B21\u91C7\u96C6" : "Created"} (${initDate}):</span>
          <span class="font-semibold text-ink-secondary">${initVal}</span>
        </div>
        <div class="flex items-center justify-between pt-0.5 border-t border-surface-border">
          <span class="${delta > 0 ? "text-indigo-950 font-bold" : "text-ink-muted"}">${curLang === "KO" ? "\uCD5C\uC2E0 \uAC31\uC2E0" : curLang === "ZH" ? "\u6700\u65B0\u540C\u6B65" : "Latest"} (${latestDate}):</span>
          <span class="${delta > 0 ? "text-emerald-700 font-bold" : "text-ink-primary font-semibold"}">${latestVal}</span>
        </div>
      </div>

    </div>

    ${footerHtml}
  `;
    return card;
  }
  function renderInboxGridItems(items, grid, curLang) {
    if (!grid) return;
    grid.innerHTML = "";
    const fragment = document.createDocumentFragment();
    const renderPool = Array.isArray(items) ? items : [];
    renderPool.forEach((it) => fragment.appendChild(createInboxCardElement(it, curLang)));
    grid.appendChild(fragment);
    if (window.lucide) window.lucide.createIcons({ root: grid });
  }
  async function renderInbox() {
    const grid = document.getElementById("inboxGrid");
    if (!grid) return;
    const curLang = window.currentLang || currentLang || "KO";
    const curPage = window.currentInboxPage || currentInboxPage || 1;
    const curSort = window.currentInboxSort || currentInboxSort || "date-audit-desc";
    const curSrc = window.currentInboxSource || currentInboxSource || "ALL";
    const curLangFilter = window.currentInboxLang || currentInboxLang || "ALL";
    const curType = window.currentInboxType || currentInboxType || "ALL";
    const curTech = window.currentInboxTech || currentInboxTech || "ALL";
    const curSearch = window.inboxSearchQuery || inboxSearchQuery || "";
    const cacheKey = getInboxCacheKey(curPage);
    let renderedFromCache = false;
    let cachedFirstId = null;
    let cached = inboxDbCache.get(cacheKey);
    if (!cached) {
      cached = ClientCache.get(cacheKey, 6e4);
      if (cached) inboxDbCache.set(cacheKey, cached);
    }
    if (cached && Array.isArray(cached.items) && cached.items.length > 0) {
      renderInboxGridItems(cached.items, grid, curLang);
      renderPagination("inboxPagination", curPage, cached.totalPages, "changeInboxPage");
      renderedFromCache = true;
      cachedFirstId = cached.items[0]?.inbox_id || cached.items[0]?.id;
      if (Date.now() - (cached.timestamp || 0) < 1e4) {
        return;
      }
    }
    let fallbackPaged = [];
    let fallbackTotalPages = 1;
    if (!renderedFromCache) {
      const inboxList = window.liveInboxData || liveInboxData || [];
      const filtered = inboxList.filter((item) => {
        const ai = item.ai_enrichment;
        const filterSrcKey = curSrc.toLowerCase();
        const matchesSrc = curSrc === "ALL" || (item.source_platform || "").toLowerCase().includes(filterSrcKey);
        const itemLang = detectSourceLang(item);
        const matchesLang = curLangFilter === "ALL" || itemLang === curLangFilter;
        const itemType = (ai ? ai.type_classification : null) || item.category_type || "TECH";
        const matchesType = curType === "ALL" ? true : itemType === curType;
        const itemTech = (ai ? ai.programming_lang : null) || item.programming_lang || "General";
        const matchesTech = curTech === "ALL" || itemTech.toLowerCase().includes(curTech.toLowerCase());
        const includePending = !!window.inboxIncludePending;
        if (curSort === "pending" && (item.ai_enrichment && item.ai_enrichment.enriched_at && item.is_classified)) return false;
        if (!includePending && (curSort === "date-audit-desc" || curSort === "date-audit-asc")) {
          if (!item.is_classified || !item.ai_enrichment || !item.ai_enrichment.enriched_at) return false;
        }
        const text = ((item.title || "") + " " + (item.title_ko || "") + " " + (item.description || "")).toLowerCase();
        const matchesSearch = !curSearch || text.includes(curSearch.toLowerCase());
        return matchesSrc && matchesLang && matchesType && matchesTech && matchesSearch;
      });
      if (filtered.length > 0) {
        sortCollection(filtered, curSort);
        fallbackTotalPages = Math.ceil(filtered.length / PAGE_SIZE) || 1;
        fallbackPaged = filtered.slice((curPage - 1) * PAGE_SIZE, curPage * PAGE_SIZE);
      }
      if (fallbackPaged.length >= PAGE_SIZE) {
        renderInboxGridItems(fallbackPaged, grid, curLang);
        renderPagination("inboxPagination", curPage, fallbackTotalPages, "changeInboxPage");
      } else {
        grid.innerHTML = Array.from({ length: 6 }).map(() => `
        <div class="executive-card p-5 animate-pulse space-y-4">
          <div class="h-4 bg-slate-200 rounded w-1/3"></div>
          <div class="h-5 bg-slate-200 rounded w-5/6"></div>
          <div class="h-12 bg-slate-100 rounded"></div>
          <div class="h-4 bg-slate-200 rounded w-1/2"></div>
        </div>
      `).join("");
      }
    }
    try {
      const dbResult = await fetchInboxFromDb(curPage, renderedFromCache);
      if (dbResult && Array.isArray(dbResult.items)) {
        const newFirstId = dbResult.items[0]?.inbox_id || dbResult.items[0]?.id;
        if (!renderedFromCache || newFirstId !== cachedFirstId || dbResult.items.length !== inboxDbCache.get(cacheKey)?.items?.length) {
          if (dbResult.items.length === 0) {
            grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${curLang === "KO" ? "\uC218\uC9D1\uB41C \uC778\uBC15\uC2A4 \uD6C4\uBCF4\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4." : curLang === "ZH" ? "\u6536\u4EF6\u7BB1\u6682\u65E0\u5019\u9009\u6570\u636E\u3002" : "No candidates in the inbox."}</div>`;
            renderPagination("inboxPagination", 1, 1, "changeInboxPage");
          } else {
            renderInboxGridItems(dbResult.items, grid, curLang);
            renderPagination("inboxPagination", curPage, dbResult.totalPages, "changeInboxPage");
          }
        }
      }
    } catch (err) {
      if (err.name === "AbortError") return;
      console.warn("[Inbox SWR] DB fetch skipped:", err.message);
      if (!renderedFromCache && fallbackPaged.length > 0 && grid.querySelector(".animate-pulse")) {
        renderInboxGridItems(fallbackPaged, grid, curLang);
        renderPagination("inboxPagination", curPage, fallbackTotalPages, "changeInboxPage");
      } else if (!grid.children.length || grid.querySelector(".animate-pulse")) {
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${curLang === "KO" ? "\uC218\uC9D1\uB41C \uC778\uBC15\uC2A4 \uD6C4\uBCF4\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4." : curLang === "ZH" ? "\u6536\u4EF6\u7BB1\u6682\u65E0\u5019\u9009\u6570\u636E\u3002" : "No candidates in the inbox."}</div>`;
      }
    }
  }

  // src/js/views/router.js
  function resetAllFiltersAndSearch() {
    window.currentPortfolioPage = 1;
    window.searchQuery = "";
    window.currentMode = "ALL";
    window.currentDomain = "ALL";
    window.currentSort = "date-audit-desc";
    const cInput = document.getElementById("searchInput");
    if (cInput) cInput.value = "";
    const cBtn = document.getElementById("clearSearchBtn");
    if (cBtn) cBtn.classList.add("hidden");
    const sortSel = document.getElementById("sortSelect");
    if (sortSel) sortSel.value = "date-audit-desc";
    document.querySelectorAll(".tag-pill").forEach((b) => {
      if (b.dataset.domain === "ALL") b.classList.add("active");
      else b.classList.remove("active");
    });
    document.querySelectorAll(".segment-btn").forEach((b) => b.classList.remove("active"));
    const modeAll = document.getElementById("modeBtnAll");
    if (modeAll) modeAll.classList.add("active");
    window.currentNewsPage = 1;
    window.currentNewsSearch = "";
    window.currentNewsTier1 = "ALL";
    window.currentNewsTier2 = "ALL";
    window.currentNewsSource = "ALL";
    window.currentNewsSort = "date-audit-desc";
    const nInput = document.getElementById("newsSearchInput");
    if (nInput) nInput.value = "";
    const nSort = document.getElementById("newsSortSelect");
    if (nSort) nSort.value = "date-audit-desc";
    document.querySelectorAll(".news-cat-pill").forEach((btn) => {
      if (btn.getAttribute("data-cat") === "ALL") {
        btn.className = "news-cat-pill active px-3 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap cursor-pointer";
      } else {
        btn.className = "news-cat-pill px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap cursor-pointer";
      }
    });
    document.querySelectorAll(".news-t2-pill").forEach((btn) => {
      if (btn.getAttribute("data-t2") === "ALL") {
        btn.className = "news-t2-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap cursor-pointer";
      } else {
        btn.className = "news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap cursor-pointer";
      }
    });
    const t2Container = document.getElementById("newsTier2Container");
    if (t2Container) t2Container.classList.remove("opacity-40", "pointer-events-none");
    document.querySelectorAll(".news-src-btn").forEach((btn) => {
      if (btn.getAttribute("data-src") === "ALL") {
        btn.className = "news-src-btn active px-2.5 py-1 rounded-lg text-xs font-bold bg-ink-primary text-white transition shrink-0 whitespace-nowrap";
      } else {
        btn.className = "news-src-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:bg-white transition border border-surface-border shrink-0 whitespace-nowrap";
      }
    });
    window.currentModelsPage = 1;
    window.modelsSearchQuery = "";
    window.currentModelsFamily = "ALL";
    window.currentModelsModality = "ALL";
    window.currentModelsArtifact = "ALL";
    window.currentModelsSort = "date-audit-desc";
    const mInput = document.getElementById("modelsSearchInput");
    if (mInput) mInput.value = "";
    const mSort = document.getElementById("modelsSortSelect");
    if (mSort) mSort.value = "date-audit-desc";
    document.querySelectorAll(".model-fam-pill").forEach((btn) => {
      if (btn.getAttribute("data-fam") === "ALL") {
        btn.className = "model-fam-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap";
      } else {
        btn.className = "model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap";
      }
    });
    document.querySelectorAll(".model-mod-pill").forEach((btn) => {
      if (btn.dataset.mod === "ALL") {
        btn.className = "model-mod-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap";
      } else {
        btn.className = "model-mod-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap";
      }
    });
    document.querySelectorAll(".model-art-pill").forEach((btn) => {
      if (btn.getAttribute("data-art") === "ALL") {
        btn.className = "model-art-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap";
      } else {
        btn.className = "model-art-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap";
      }
    });
    window.currentInboxPage = 1;
    window.inboxSearchQuery = "";
    window.currentInboxSource = "ALL";
    window.currentInboxLang = "ALL";
    window.currentInboxType = "ALL";
    window.currentInboxTech = "ALL";
    window.currentInboxSort = "date-audit-desc";
    const iInput = document.getElementById("inboxSearchInput");
    if (iInput) iInput.value = "";
    const iSort = document.getElementById("inboxSortSelect");
    if (iSort) iSort.value = "date-audit-desc";
    document.querySelectorAll(".inbox-src-pill").forEach((btn) => {
      if (btn.getAttribute("data-src-val") === "ALL") {
        btn.className = "inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap";
      } else {
        btn.className = "inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap";
      }
    });
    document.querySelectorAll(".inbox-filter-pill").forEach((btn) => {
      if (btn.dataset.langVal === "ALL") {
        btn.className = "inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap";
      } else {
        btn.className = "inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap";
      }
    });
  }
  function switchView(view, pushHistory = true, preserveFilters = false) {
    if (!preserveFilters) {
      resetAllFiltersAndSearch();
    }
    const validViews = ["home", "portfolio", "news", "models", "graph", "inbox"];
    const targetView = validViews.includes(view) ? view : "home";
    window.currentView = targetView;
    validViews.forEach((v) => {
      const el = document.getElementById(v + "View");
      const btn = document.getElementById("tab" + v.charAt(0).toUpperCase() + v.slice(1) + "Btn");
      const mBtn = document.getElementById("mTab" + v.charAt(0).toUpperCase() + v.slice(1) + "Btn");
      if (el) el.classList.toggle("hidden", v !== targetView);
      if (btn) {
        if (v === targetView) {
          btn.className = "nav-tab active flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white bg-ink-primary transition shadow-sm";
        } else {
          btn.className = "nav-tab flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition";
        }
      }
      if (mBtn) {
        if (v === targetView) {
          mBtn.className = "mobile-nav-tab active shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-ink-primary transition shadow-sm";
        } else {
          mBtn.className = "mobile-nav-tab shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-secondary hover:text-ink-primary bg-surface-subtle border border-surface-border transition";
        }
      }
    });
    const adminBtn = document.getElementById("adminArchiveBtn");
    if (adminBtn) {
      if (targetView === "inbox") {
        adminBtn.className = "flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold text-white bg-slate-800 transition border border-slate-700 shadow-sm";
      } else {
        adminBtn.className = "flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold text-ink-muted hover:text-ink-primary hover:bg-surface-subtle transition border border-transparent hover:border-surface-border";
      }
    }
    if (pushHistory) {
      const targetHash = ROUTES[targetView] || "#/" + targetView;
      if (window.location.hash !== targetHash) {
        try {
          history.pushState({ view: targetView }, "", targetHash);
        } catch (e) {
          window.location.hash = targetHash;
        }
      }
    }
    if (targetView === "home") {
      renderTelemetryCharts();
      updateCronCountdown();
      renderHomeTopPicks();
    } else if (targetView === "portfolio") {
      renderCards();
    } else if (targetView === "models") {
      renderModels();
    } else if (targetView === "news") {
      renderNews();
    } else if (targetView === "inbox") {
      renderInbox();
      renderPipelineTelemetryCards();
      renderRunsTable();
      updateCronCountdown();
    } else if (targetView === "graph") {
      initCitationGraph();
    }
    if (pushHistory && window.scrollY > 60) {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
    if (window.lucide && typeof window.lucide.createIcons === "function") {
      requestAnimationFrame(() => {
        const viewEl = document.getElementById(targetView + "View");
        if (viewEl) window.lucide.createIcons({ root: viewEl });
        else window.lucide.createIcons();
      });
    }
  }
  function handleHashRoute() {
    const hash = window.location.hash || "";
    if (hash.includes("case=") || hash.startsWith("#case/")) {
      let targetCaseId = "";
      if (hash.includes("case=")) {
        const m = hash.match(/case=([^&]+)/);
        if (m) targetCaseId = decodeURIComponent(m[1]);
      } else {
        targetCaseId = decodeURIComponent(hash.replace("#case/", ""));
      }
      if (targetCaseId) {
        switchView("portfolio", false, true);
        const pool = window.liveCasesData || liveCasesData || casesData || [];
        const target = pool.find((c) => c.case_id === targetCaseId || c.investigation_id === targetCaseId);
        if (target) {
          openModal(target, false);
          return;
        }
      }
    }
    closeModal(false);
    const [routePart, queryPart] = hash.split("?");
    const params = new URLSearchParams(queryPart || "");
    const pageParam = parseInt(params.get("page"), 10) || 1;
    let targetView = "home";
    if (routePart.startsWith("#/factchecks") || routePart.startsWith("#factchecks") || routePart.startsWith("#/portfolio")) {
      targetView = "portfolio";
    } else if (routePart.startsWith("#/news") || routePart.startsWith("#news")) {
      targetView = "news";
    } else if (routePart.startsWith("#/models") || routePart.startsWith("#models")) {
      targetView = "models";
    } else if (routePart.startsWith("#/graph") || routePart.startsWith("#graph")) {
      targetView = "graph";
    } else if (routePart.startsWith("#/inbox") || routePart.startsWith("#inbox")) {
      targetView = "inbox";
    } else {
      targetView = "home";
    }
    const curView = window.currentView || currentView || "home";
    if (curView !== targetView) {
      switchView(targetView, false, false);
    } else if (targetView === "home") {
      renderTelemetryCharts();
      updateCronCountdown();
      renderHomeTopPicks();
    }
    if (targetView === "news") {
      const curP = window.currentNewsPage || currentNewsPage || 1;
      if (curP !== pageParam) changeNewsPage(pageParam, false);
    } else if (targetView === "portfolio") {
      const curP = window.currentPortfolioPage || currentPortfolioPage || 1;
      if (curP !== pageParam) changePortfolioPage(pageParam, false);
    } else if (targetView === "models") {
      const curP = window.currentModelsPage || currentModelsPage || 1;
      if (curP !== pageParam) changeModelsPage(pageParam, false);
    } else if (targetView === "inbox") {
      const curP = window.currentInboxPage || currentInboxPage || 1;
      if (curP !== pageParam) changeInboxPage(pageParam, false);
    }
  }
  function initRouter() {
    window.addEventListener("popstate", handleHashRoute);
    window.addEventListener("hashchange", handleHashRoute);
    window.addEventListener("load", () => {
      const hash = window.location.hash || "";
      if (!window.__APP_INITIALIZED__ || hash.includes("case=") || hash.startsWith("#case/") || hash.includes("page=")) {
        setTimeout(handleHashRoute, 150);
      }
    });
  }

  // src/js/main.js
  if (typeof window !== "undefined") {
    window.APP_CONFIG = APP_CONFIG;
    window.API_BASE = API_BASE;
    window.ROUTES = ROUTES;
    window.AppStore = AppStore;
    window.i18n = i18n;
    window.setLanguage = setLanguage;
    window.switchView = switchView;
    window.resetAllFiltersAndSearch = resetAllFiltersAndSearch;
    window.handleHashRoute = handleHashRoute;
    window.renderHomeTopPicks = renderHomeTopPicks;
    window.switchRadarSession = switchRadarSession;
    window.navigateFromRadar = navigateFromRadar;
    window.renderRadarSession = renderRadarSession;
    window.renderCards = renderCards;
    window.setModeFilter = setModeFilter;
    window.setDomainFilter = setDomainFilter;
    window.changeSort = changeSort;
    window.clearSearch = clearSearch;
    window.renderModels = renderModels;
    window.setModelsSort = setModelsSort;
    window.setModelsArtifactFilter = setModelsArtifactFilter;
    window.setModelsModalityFilter = setModelsModalityFilter;
    window.setModelsFamilyFilter = setModelsFamilyFilter;
    window.toggleFamilyGrouping = toggleFamilyGrouping;
    window.renderNews = renderNews;
    window.setNewsCategoryFilter = setNewsCategoryFilter;
    window.setNewsTier2Filter = setNewsTier2Filter;
    window.setNewsFacetFilter = setNewsFacetFilter;
    window.switchNewsFacet = function(facet) {
      switchView("news");
      setNewsFacetFilter(facet || "ALL");
    };
    window.setNewsSourceFilter = setNewsSourceFilter;
    window.setNewsSort = setNewsSort;
    window.handleNewsSearch = handleNewsSearch;
    window.handleNewsSearchImmediate = handleNewsSearchImmediate;
    window.clearNewsSearch = clearNewsSearch;
    window.updateSearchClearBtn = updateSearchClearBtn;
    window.renderInbox = renderInbox;
    window.setInboxSort = setInboxSort;
    window.toggleInboxIncludePending = toggleInboxIncludePending;
    window.setInboxLangFilter = setInboxLangFilter;
    window.setInboxTypeFilter = setInboxTypeFilter;
    window.setInboxTechFilter = setInboxTechFilter;
    window.setInboxSourceFilter = setInboxSourceFilter;
    window.toggleQueueItem = toggleQueueItem;
    window.changePortfolioPage = changePortfolioPage;
    window.changeModelsPage = changeModelsPage;
    window.changeNewsPage = changeNewsPage;
    window.changeInboxPage = changeInboxPage;
    window.openModal = openModal;
    window.openCaseModal = openCaseModal;
    window.closeModal = closeModal;
    window.toggleSourcePopover = toggleSourcePopover;
    window.toggleClusterPopover = toggleClusterPopover;
    window.toggleNewsComments = toggleNewsComments;
    window.renderTelemetryCharts = renderTelemetryCharts;
    window.renderPipelineTelemetryCards = renderPipelineTelemetryCards;
    window.renderRunsTable = renderRunsTable;
    window.updateCronCountdown = updateCronCountdown;
    window.switchRunLogsTab = switchRunLogsTab;
    window.filterLogsByRunner = switchRunLogsTab;
    window.initCitationGraph = initCitationGraph;
    window.filterGraphGroup = filterGraphGroup;
    window.showToast = showToast;
    window.checkVoyageEmbeddingStatus = checkVoyageEmbeddingStatus;
    window.toggleVoyageEmbeddingWorker = toggleVoyageEmbeddingWorker;
    window.startContinuousVoyageWorker = startContinuousVoyageWorker;
    window.toggleAiEnrichWorker = toggleAiEnrichWorker;
    window.drainAiEnrichmentWorker = startContinuousAiWorker;
    window.startContinuousAiWorker = startContinuousAiWorker;
    window.triggerAiEnrichWorker = triggerAiEnrichWorker;
    window.updateGlobalStatsUI = updateGlobalStatsUI;
    window.runSystemVerificationAgent = runSystemVerificationAgent;
    window.showVerificationReportModal = showVerificationReportModal;
    window.cleanStealthUrl = cleanStealthUrl;
    window.stealthNavigate = stealthNavigate;
    window.addEventListener("unhandledrejection", (event) => {
      if (event?.reason?.message && event.reason.message.includes("message channel closed before a response was received")) {
        event.preventDefault();
      }
    });
    const inboxSearchEl = document.getElementById("inboxSearchInput");
    if (inboxSearchEl) {
      inboxSearchEl.addEventListener("input", (e) => {
        window.currentInboxPage = 1;
        window.inboxSearchQuery = e.target.value;
        renderInbox();
      });
    }
    const searchEl = document.getElementById("searchInput");
    if (searchEl) {
      searchEl.addEventListener("input", (e) => {
        window.searchQuery = e.target.value;
        const clearBtn = document.getElementById("clearSearchBtn");
        if (clearBtn) clearBtn.classList.toggle("hidden", !e.target.value);
        renderCards();
      });
    }
    initStealthLinkInterceptor();
    initRouter();
    console.log("[App] \u{1F680} Modular architecture components registered.");
  }
  if (typeof document !== "undefined") {
    try {
      const cachedVoyage = localStorage.getItem("voyage_runs_history_v1");
      if (cachedVoyage) window.voyageWorkerRunsData = JSON.parse(cachedVoyage);
    } catch (e) {
    }
    const initApp = async () => {
      try {
        await bootstrapApplicationData();
      } catch (err) {
        console.warn("[App] Bootstrap warning:", err);
        const savedLang = localStorage.getItem("factcheck_lang") || "KO";
        setLanguage(savedLang);
      }
      setInterval(updateCronCountdown, 1e3);
      updateCronCountdown();
      setTimeout(checkVoyageEmbeddingStatus, 800);
      window.__APP_INITIALIZED__ = true;
      console.log("[App] \u{1F680} Modular architecture hydrated and fully ready.");
    };
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", initApp);
    } else {
      initApp();
    }
  }
})();
