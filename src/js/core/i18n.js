/**
 * ==============================================================================
 * Internationalization (i18n) Engine & High-Fidelity CJK Font Switching
 * Complete Tri-Lingual Support: KO (Korean), ZH (Simplified Chinese), EN (English)
 * ==============================================================================
 */

import { currentLang, setGlobalLang, liveModelsData, liveNewsData, liveInboxData } from './store.js';
import { getDynamicKstDate } from '../utils/dateTime.js';

export const i18n = {
  KO: {
    brandTitle: "FactCheck Hub",
    brandSubtitle: "AI 팩트체크 & 글로벌 테크 최신 동향",
    navHome: "대시보드",
    navPortfolio: "공식 검증",
    navModels: "AI 모델 트렌드",
    navNews: "실시간 트렌드 레이더",
    navGraph: "인용 계보망",
    navInbox: "수집 인박스",
    adminArchiveBtn: "아카이브 (Admin)",
    statArchiveLabel: "원천 아카이브 (Admin)",
    pipelineScheduleDesc: "1일 4회(00:17, 06:17, 12:17, 18:17 KST) 전략 수집",
    pipelineWidgetTitle: "자율 크론 파이프라인 텔레메트리 & 차기 수집 카운트다운",
    pipelineNextTargetLabel: "다음 자동 수집 예정",
    pipelineFooterAudit: "1일 4회(00, 06, 12, 18시 KST) 정기 전략 수집 & Vercel 실시간 동기화",
    pipelineFooterNote: "* GitHub Actions 큐 상태에 따라 ±2~5분의 스케줄 지연이 발생할 수 있습니다.",
    heroBadge: "ZERO-HALLUCINATION ARCHITECTURE & COST AUDIT",
    heroMainTitle: "바이럴된 AI 기술의 실체 분석",
    heroMainDesc: "SNS 바이럴 마케팅의 환각을 걷어내고, 1차 공식 출처 감사와 기저 표준 vs 서드파티 실측 벤치마크를 통해 도출한 100% 실증 보고서입니다.",
    heroUpdateLabel: "최종 검증일",
    heroAuditCount: "49개 기술 검증 완료",
    promoBannerTitle: "기술 검증 포트폴리오 최신 상태 알림",
    promoCountBadge: "49건 검증 완료",
    promoBannerDesc: "바이럴 임계치를 초과하여 유입된 주요 오픈소스 및 모델 후보군 총 49건에 대한 심층 실측 벤치마크와 팩트체크가 모두 완료되었습니다.",
    promoBtnText: "수집 인박스 후보군 보기",
    timelineTitle: "당일 24시간 수집 타임라인",
    timelineSub: "1일 4회(00, 06, 12, 18시 KST) 6시간 주기 전략 수집 & AI 실시간 분류",
    timelineBadge: "1일 4회 6h 펄스",
    timelineLegend: "세션별 수집 건수",
    timelineFooterPrefix: "⚡ 당일 총 수집량:",
    trendRadarTitle: "1일 4회 AI 트렌드 레이더",
    trendRadarSub: "글로벌 오픈소스 & AI 신규 가중치 6시간 주기 자동 감지",
    homeTopPicksTitle: "최신 심층 기술 검증 하이라이트",
    homeTopPicksViewAll: "전체 49개 검증 도시에 보러가기",
    btnAll: "전체 검증",
    btnUser: "직접 큐레이션",
    btnAuto: "자동 트렌드",
    sortLabel: "정렬:",
    sortOptions: [
      { val: "date-audit-desc", text: "🔬 분석일자 최신순 (기본)" },
      { val: "date-audit-asc", text: "🔬 분석일자 오래된순" },
      { val: "date-source-desc", text: "📅 원출처 발행 최신순" },
      { val: "date-source-asc", text: "📅 원출처 발행 오래된순" }
    ],
    searchPlaceholder: "기술명, 아키텍처, 큐레이션 동기 검색...",
    domainLabel: "도메인:",
    tagAll: "전체",
    tagFrontend: "프론트엔드",
    tagAgent: "AI 에이전트",
    tagScraping: "웹 스크래핑",
    tagDoc: "문서 파싱",
    tag3d: "3D/컴포넌트",
    tagRust: "Rust/시스템",
    tagOther: "기타/코어 인프라",
    cardMotivationLabel: "💡 발굴 의도 / 문제의식:",
    cardVerdictLabel: "⚡ 검증 팩트 / 결론:",
    cardConfidenceLabel: "신뢰도",
    cardSourcesLabel: "개 1차 출처",
    cardViewBtn: "심층 보고서 열람",
    newsHeaderBadge: "GLOBAL TECH & AI INTELLIGENCE FEED",
    newsHeaderTitle: "커뮤니티, 해커뉴스, 사설에서 수집된 테크 & AI 최신 담론",
    newsHeaderDesc: "소프트웨어·AI 저장소뿐만 아니라 신소재·우주, 거시경제, 인프라 보안 등 글로벌 기술 동향을 선별합니다.",
    newsOriginalLink: "기사 원문",
    newsCatFilterLabel: "🏷️ 기술·글로벌 분류:",
    newsCats: {
      'ALL': "전체",
      'TECH_COMPUTING': "💻 IT·컴퓨팅",
      'SCIENCE_RESEARCH': "🚀 과학·우주",
      'ECONOMY_FINANCE': "🏦 경제·금융",
      'LAW_CRIME_JUSTICE': "⚖️ 사회·법률",
      'POLITICS_POLICY': "🏛️ 정치·정책",
      'CULTURE_HUMANITIES': "🌿 문화·인문"
    },
    newsTier2FilterLabel: "↳ 💻 IT 세부 분야:",
    newsT2: {
      'ALL': "전체 IT 분야",
      'INFERENCE_OPT': "⚡ 추론·서빙",
      'AGENTS_DEVTOOLS': "🛠️ 에이전트·도구",
      'MULTIMODAL_AI': "🎨 멀티모달",
      'FOUNDATION_MODELS': "🤖 파운데이션",
      'INFRA_RAG_SECURITY': "🛡️ 인프라·보안",
      'INDUSTRY_TRENDS': "🌐 일반 SW·웹"
    },
    newsSourceLabel: "출처:",
    newsSrcAll: "전체 출처",
    newsSearchPlaceholder: "기술명, 키워드 검색...",
    newsSortLabel: "정렬:",
    newsSortOptions: [
      { val: "date-audit-desc", text: "🔬 AI 분석일 최신순 (기본)" },
      { val: "date-audit-asc", text: "🔬 AI 분석일 오래된순" },
      { val: "date-source-desc", text: "📅 수집/발표 최신순" },
      { val: "date-source-asc", text: "📅 수집/발표 오래된순" }
    ],
    modelsFamilyLabel: "🤖 모델 패밀리:",
    modelFams: {
      'ALL': "전체 패밀리",
      'Qwen': "Qwen",
      'Wan': "Wan 비디오",
      'MiniMax': "MiniMax",
      'FLUX': "FLUX 이미지",
      'GLM': "GLM",
      'DeepSeek': "DeepSeek",
      'Hunyuan': "Hunyuan",
      'Audio': "음성/TTS",
      'Standalone': "독립/신규 모델"
    },
    modelsArtifactLabel: "🧩 허브 유형:",
    modelArts: {
      'ALL': "전체",
      'WEIGHTS': "🤖 가중치·체크포인트",
      'WEB_SERVICE': "🌐 인터랙티브 데모·Spaces",
      'FINETUNE': "🎯 특화 파인튜닝"
    },
    modelsSearchPlaceholder: "모델명, 아키텍처, 포맷 검색...",
    modelsSortLabel: "정렬:",
    modelsSortOptions: [
      { val: "date-source-desc", text: "📅 발행일 최신순 (기본)" },
      { val: "date-source-asc", text: "📅 발행일 오래된순" },
      { val: "date-audit-desc", text: "🔬 분석일 최신순" },
      { val: "title-asc", text: "🔤 모델명 가나다순" }
    ],
    graphHeaderBadge: "MULTI-ENTITY CITATION NETWORK",
    graphHeaderTitle: "인물과 논문 인용 계보를 통한 기술 탄생의 뿌리 지도",
    graphHeaderSub: "기술 • 연구자 • 연구소 • 1차 논문",
    graphBtnAll: "전체 보기",
    graphBtnLang: "언어",
    graphBtnTech: "기술/엔진",
    graphBtnOrg: "연구소",
    graphBtnPerson: "인물",
    graphBtnPaper: "논문",
    criteriaTitle: "자율 크론 4대 자동 승격(Promotion) 기준 가이드",
    criteriaDesc: "수집된 수많은 오픈소스 및 논문 중 아래의 4대 바이럴/기술 임계치를 돌파한 항목은 자동으로 [자동 승격 트렌드 후보]로 격상되어 최우선 기술 검증 대기열에 등록됩니다.",
    critGithub: "최근 14일 이내 생성 & ★ > 500 Stars 돌파",
    critHn: "Top/Best 스토리 중 추천 점수 🔥 > 150 Points",
    critHf: "Trending 점수 상위권 & ❤️ > 100 Likes 모델/데모",
    critArxiv: "MoE, Reasoning, VLM 등 혁신 아키텍처 1차 논문",
    inboxHeaderBadge: "AUTONOMOUS HARVEST INBOX",
    inboxHeaderTitle: "원천 데이터 아카이브 & 관리자 파이프라인",
    inboxHeaderDesc: "크롤러가 24시간 실시간 수집한 원천 로우 데이터를 영구 보존하며, 관리자가 심층 팩트체크(공식 검증)로 승격할 후보를 검토하는 내부 저장소입니다.",
    inboxFamilyOn: "패밀리 묶음 (ON)",
    inboxFamilyOff: "패밀리 묶음 (OFF)",
    inboxSearchPlaceholder: "후보 기술 또는 모델명 검색...",
    inboxQueueBtn: "분석 큐 담기",
    inboxQueuedBtn: "대기열 등록됨",
    modalSecCurationTitle: "Discovery Motivation & Target Workflow",
    modalSecViralPostTitle: "1차 마케팅 원문 & 바이럴 클레임 발췌 (Raw Viral Claim)",
    modalSecClaimsTitle: "Marketing Claims vs Empirical Reality",
    modalSecHookTitle: "The Hook & Marketing Hype",
    modalSecHandsOnTitle: "Hands-on Measured Results",
    modalSecAltsTitle: "Comparative Alternatives Matrix",
    modalSecSourcesTitle: "Audited Primary Sources",
    modalWorkflowLabel: "🎯 연계 워크플로우:",
    modalViralLinkText: "원문 포스트 바로가기",
    thTool: "도구 / 기술명",
    thStack: "기술 스택",
    thPros: "장점",
    thCons: "단점",
    thBestFor: "적합한 환경"
  },
  ZH: {
    brandTitle: "FactCheck Hub",
    brandSubtitle: "AI 事实核查与全球科技前沿动态",
    navHome: "仪表盘",
    navPortfolio: "官方核查",
    navModels: "AI 模型趋势",
    navNews: "实时趋势雷达",
    navGraph: "引用系谱图",
    navInbox: "采集收件箱",
    adminArchiveBtn: "归档 (Admin)",
    statArchiveLabel: "原始归档 (Admin)",
    pipelineScheduleDesc: "每日 4 次（00:17、06:17、12:17、18:17 KST）周期策略采集",
    pipelineWidgetTitle: "自主定时流水线遥测与下次采集倒计时",
    pipelineNextTargetLabel: "下次自动采集计划",
    pipelineFooterAudit: "每日4次(00, 06, 12, 18时 KST) 定向策略采集 & Vercel 实时同步",
    pipelineFooterNote: "* 受 GitHub Actions 队列负载影响，可能存在 ±2~5 分钟调度延迟.",
    heroBadge: "ZERO-HALLUCINATION ARCHITECTURE & COST AUDIT",
    heroMainTitle: "热门 AI 技术的工程真相与实体验证",
    heroMainDesc: "摒弃社交媒体营销炒作与幻觉，基于第一手官方源码审计以及基础标准 vs 第三方工具的实测基准，输出 100% 真实客观的工程报告。",
    heroUpdateLabel: "最新审计",
    heroAuditCount: "已完成 49 项技术审计",
    promoBannerTitle: "技术审计档案库最新状态",
    promoCountBadge: "49 项核验完毕",
    promoBannerDesc: "已对突破热度阈值自动晋升的 49 项重点开源项目与前沿模型完成全流程深度实测基准与事实核查。",
    promoBtnText: "查看采集收件箱候选",
    timelineTitle: "当日 24 小时采集时间线",
    timelineSub: "每日 4 次 (00, 06, 12, 18时 KST) 6小时周期定向采集 & AI 实时分类",
    timelineBadge: "每日4次 6h脉冲",
    timelineLegend: "各时段采集数",
    timelineFooterPrefix: "⚡ 当日总采集量:",
    trendRadarTitle: "每日 4 次 AI 趋势雷达",
    trendRadarSub: "全球开源与 AI 前沿权重 6 小时周期自动感应",
    homeTopPicksTitle: "最新深度技术核查精选",
    homeTopPicksViewAll: "查看全部 49 份核查档案",
    btnAll: "全部审计",
    btnUser: "人工精选",
    btnAuto: "自动趋势",
    sortLabel: "排序:",
    sortOptions: [
      { val: "date-audit-desc", text: "🔬 审核日期最新 (默认)" },
      { val: "date-audit-asc", text: "🔬 审核日期最早" },
      { val: "date-source-desc", text: "📅 原文发布最新" },
      { val: "date-source-asc", text: "📅 原文发布最早" }
    ],
    searchPlaceholder: "搜索技术名、架构或策展动机...",
    domainLabel: "领域:",
    tagAll: "全部",
    tagFrontend: "前端/UI",
    tagAgent: "AI Agent",
    tagScraping: "网页爬虫",
    tagDoc: "文档解析",
    tag3d: "3D/组件",
    tagRust: "Rust系统",
    tagOther: "核心基建",
    cardMotivationLabel: "💡 挖掘动机 / 痛点问题:",
    cardVerdictLabel: "⚡ 审计结论 / 事实核验:",
    cardConfidenceLabel: "可信度",
    cardSourcesLabel: "个一手来源",
    cardViewBtn: "查阅完整报告",
    newsHeaderBadge: "GLOBAL TECH & AI INTELLIGENCE FEED",
    newsHeaderTitle: "源自社区、HackerNews 与专栏的全球科技与 AI 讨论",
    newsHeaderDesc: "不仅追踪开源代码与模型，还精选深科技、航空航天、宏观经济与基础设施安全动态。",
    newsOriginalLink: "阅读原文",
    newsCatFilterLabel: "🏷️ 技术与全球领域:",
    newsCats: {
      'ALL': "全部",
      'TECH_COMPUTING': "💻 IT与计算",
      'SCIENCE_RESEARCH': "🚀 科学与航天",
      'ECONOMY_FINANCE': "🏦 经济与金融",
      'LAW_CRIME_JUSTICE': "⚖️ 社会与法治",
      'POLITICS_POLICY': "🏛️ 政治与政策",
      'CULTURE_HUMANITIES': "🌿 文化与人文"
    },
    newsTier2FilterLabel: "↳ 💻 IT 细分领域:",
    newsT2: {
      'ALL': "全部 IT 领域",
      'INFERENCE_OPT': "⚡ 推理与服务",
      'AGENTS_DEVTOOLS': "🛠️ 智能体与工具",
      'MULTIMODAL_AI': "🎨 多模态",
      'FOUNDATION_MODELS': "🤖 基础模型",
      'INFRA_RAG_SECURITY': "🛡️ 基础架构与安全",
      'INDUSTRY_TRENDS': "🌐 软件与行业动态"
    },
    newsSourceLabel: "来源:",
    newsSrcAll: "全部来源",
    newsSearchPlaceholder: "搜索技术名、关键词...",
    newsSortLabel: "排序:",
    newsSortOptions: [
      { val: "date-audit-desc", text: "🔬 AI 审核时间最新 (默认)" },
      { val: "date-audit-asc", text: "🔬 AI 审核时间最早" },
      { val: "date-source-desc", text: "📅 采集发布时间最新" },
      { val: "date-source-asc", text: "📅 采集发布时间最早" }
    ],
    modelsFamilyLabel: "🤖 模型系列:",
    modelFams: {
      'ALL': "全部系列",
      'Qwen': "Qwen",
      'Wan': "Wan 视频",
      'MiniMax': "MiniMax",
      'FLUX': "FLUX 图像",
      'GLM': "GLM",
      'DeepSeek': "DeepSeek",
      'Hunyuan': "Hunyuan",
      'Audio': "语音/TTS",
      'Standalone': "独立/新模型"
    },
    modelsArtifactLabel: "🧩 资源类型:",
    modelArts: {
      'ALL': "全部",
      'WEIGHTS': "🤖 模型权重·检查点",
      'WEB_SERVICE': "🌐 在线演示·Spaces",
      'FINETUNE': "🎯 定制微调"
    },
    modelsSearchPlaceholder: "搜索模型名、架构、格式...",
    modelsSortLabel: "排序:",
    modelsSortOptions: [
      { val: "date-source-desc", text: "📅 发布时间最新 (默认)" },
      { val: "date-source-asc", text: "📅 发布时间最早" },
      { val: "date-audit-desc", text: "🔬 AI 审核最新" },
      { val: "title-asc", text: "🔤 模型名 A-Z" }
    ],
    graphHeaderBadge: "MULTI-ENTITY CITATION NETWORK",
    graphHeaderTitle: "人物与论文引用系谱技术溯源全景图",
    graphHeaderSub: "技术 • 研究员 • 实验室 • 一手论文",
    graphBtnAll: "查看全部",
    graphBtnLang: "编程语言",
    graphBtnTech: "核心技术/引擎",
    graphBtnOrg: "科研机构",
    graphBtnPerson: "代表人物",
    graphBtnPaper: "经典论文",
    criteriaTitle: "全自动巡检 4 大自动晋升 (Promotion) 判定准则",
    criteriaDesc: "在海量采集的开源项目与前沿论文中，突破以下 4 项热度与技术指标的候选项目将自动晋升至优先核查队列。",
    critGithub: "14 天内新建仓库且 ★ > 500 Stars 突破",
    critHn: "Top/Best 讨论中点赞热度 🔥 > 150 Points",
    critHf: "Trending 趋势榜前列且 ❤️ > 100 Likes 模型/Demo",
    critArxiv: "涵盖 MoE、推理强化、VLM 的第一手经典架构论文",
    inboxHeaderBadge: "AUTONOMOUS HARVEST INBOX",
    inboxHeaderTitle: "原始数据归档与管理员流水线",
    inboxHeaderDesc: "全天候实时采集的原始数据永久存储库，供管理员审查并晋升至深度事实核查（官方审计）候选。",
    inboxFamilyOn: "系列聚合 (开)",
    inboxFamilyOff: "系列聚合 (关)",
    inboxSearchPlaceholder: "搜索候选技术或模型名称...",
    inboxQueueBtn: "加入待审队列",
    inboxQueuedBtn: "已在队列中",
    modalSecCurationTitle: "Discovery Motivation & Target Workflow",
    modalSecViralPostTitle: "营销宣传原文摘录与主张证据 (Raw Viral Claim)",
    modalSecClaimsTitle: "Marketing Claims vs Empirical Reality",
    modalSecHookTitle: "The Hook & Marketing Hype",
    modalSecHandsOnTitle: "Hands-on Measured Results",
    modalSecAltsTitle: "Comparative Alternatives Matrix",
    modalSecSourcesTitle: "Audited Primary Sources",
    modalWorkflowLabel: "🎯 协同工作流:",
    modalViralLinkText: "直达原文帖子",
    thTool: "工具 / 技术",
    thStack: "技术栈",
    thPros: "核心优势",
    thCons: "劣势与局限",
    thBestFor: "最适用场景"
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
    pipelineFooterNote: "* ±2~5 min schedule variance may occur based on GitHub Actions runner queue load.",
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
    timelineFooterPrefix: "⚡ Today Total Collected:",
    trendRadarTitle: "4x Daily AI Trend Radar",
    trendRadarSub: "Autonomous 6-hour radar for trending open weights & code",
    homeTopPicksTitle: "Latest Deep Technical Verification Highlights",
    homeTopPicksViewAll: "View All 49 Empirical Dossiers",
    btnAll: "All Dossiers",
    btnUser: "User Curated",
    btnAuto: "Auto Trends",
    sortLabel: "Sort:",
    sortOptions: [
      { val: "date-audit-desc", text: "🔬 Audit Date (Newest first)" },
      { val: "date-audit-asc", text: "🔬 Audit Date (Oldest first)" },
      { val: "date-source-desc", text: "📅 Source Published (Newest first)" },
      { val: "date-source-asc", text: "📅 Source Published (Oldest first)" }
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
    cardMotivationLabel: "💡 Intent & Problem:",
    cardVerdictLabel: "⚡ Empirical Truth & Verdict:",
    cardConfidenceLabel: "Confidence",
    cardSourcesLabel: "Sources",
    cardViewBtn: "View Full Dossier",
    newsHeaderBadge: "GLOBAL AI INTELLIGENCE FEED",
    newsHeaderTitle: "AI Trends & Engineering Discourse from HackerNews & Communities",
    newsHeaderDesc: "Curated engineering analyses, security vulnerabilities, and architectural tutorials.",
    newsOriginalLink: "Read Source",
    newsCatFilterLabel: "🏷️ Global Domain:",
    newsCats: {
      'ALL': "All",
      'TECH_COMPUTING': "💻 IT & Computing",
      'SCIENCE_RESEARCH': "🚀 Science & Space",
      'ECONOMY_FINANCE': "🏦 Economy & Finance",
      'LAW_CRIME_JUSTICE': "⚖️ Society & Law",
      'POLITICS_POLICY': "🏛️ Policy & Politics",
      'CULTURE_HUMANITIES': "🌿 Culture & Arts"
    },
    newsTier2FilterLabel: "↳ 💻 IT Sub-tracks:",
    newsT2: {
      'ALL': "All IT Tracks",
      'INFERENCE_OPT': "⚡ Inference & Serving",
      'AGENTS_DEVTOOLS': "🛠️ Agents & DevTools",
      'MULTIMODAL_AI': "🎨 Multimodal AI",
      'FOUNDATION_MODELS': "🤖 Foundation Models",
      'INFRA_RAG_SECURITY': "🛡️ Infra & Security",
      'INDUSTRY_TRENDS': "🌐 General SW & Web"
    },
    newsSourceLabel: "Source:",
    newsSrcAll: "All Sources",
    newsSearchPlaceholder: "Search tech, keywords...",
    newsSortLabel: "Sort:",
    newsSortOptions: [
      { val: "date-audit-desc", text: "🔬 AI Audit Date (Newest first, default)" },
      { val: "date-audit-asc", text: "🔬 AI Audit Date (Oldest first)" },
      { val: "date-source-desc", text: "📅 Source Published (Newest first)" },
      { val: "date-source-asc", text: "📅 Source Published (Oldest first)" }
    ],
    modelsFamilyLabel: "🤖 Model Family:",
    modelFams: {
      'ALL': "All Families",
      'Qwen': "Qwen",
      'Wan': "Wan Video",
      'MiniMax': "MiniMax",
      'FLUX': "FLUX Image",
      'GLM': "GLM",
      'DeepSeek': "DeepSeek",
      'Hunyuan': "Hunyuan",
      'Audio': "Audio/TTS",
      'Standalone': "Standalone Models"
    },
    modelsArtifactLabel: "🧩 Hub Resource:",
    modelArts: {
      'ALL': "All",
      'WEIGHTS': "🤖 Weights & Checkpoints",
      'WEB_SERVICE': "🌐 Interactive Demos / Spaces",
      'FINETUNE': "🎯 Specialized Finetunes"
    },
    modelsSearchPlaceholder: "Search model name, architecture, format...",
    modelsSortLabel: "Sort:",
    modelsSortOptions: [
      { val: "date-source-desc", text: "📅 Source Published (Newest first)" },
      { val: "date-source-asc", text: "📅 Source Published (Oldest first)" },
      { val: "date-audit-desc", text: "🔬 Audit Date (Newest first)" },
      { val: "title-asc", text: "🔤 Model Name (A-Z)" }
    ],
    graphHeaderBadge: "MULTI-ENTITY CITATION NETWORK",
    graphHeaderTitle: "Genealogy Map of AI Innovations via Citations",
    graphHeaderSub: "Tech • Researchers • Labs • Primary Papers",
    graphBtnAll: "Show All",
    graphBtnLang: "Language",
    graphBtnTech: "Tech / Engine",
    graphBtnOrg: "Laboratories",
    graphBtnPerson: "People",
    graphBtnPaper: "Papers",
    criteriaTitle: "Autonomous Cron Promotion Criteria Guide",
    criteriaDesc: "Repositories and papers exceeding these 4 viral thresholds are auto-promoted into the priority technical verification queue.",
    critGithub: "Created in last 14 days & > 500 Stars",
    critHn: "Top/Best stories with Score 🔥 > 150 Points",
    critHf: "Top Trending with ❤️ > 100 Likes",
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
    modalWorkflowLabel: "🎯 Target Workflow:",
    modalViralLinkText: "Go to Viral Post",
    thTool: "Tool / Repository",
    thStack: "Tech Stack",
    thPros: "Empirical Strengths",
    thCons: "Weaknesses & Bottlenecks",
    thBestFor: "Best For"
  }
};

export function setLanguage(lang) {
  setGlobalLang(lang);
  if (typeof localStorage !== 'undefined') {
    try { localStorage.setItem('factcheck_lang', lang); } catch (e) {}
  }

  if (typeof document !== 'undefined') {
    // Dynamic Native Font Stack Switching
    if (lang === 'ZH') {
      document.documentElement.lang = 'zh-CN';
      document.body.style.fontFamily = "'Noto Sans SC', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'SimHei', sans-serif";
    } else if (lang === 'EN') {
      document.documentElement.lang = 'en';
      document.body.style.fontFamily = "'Geist', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
    } else {
      document.documentElement.lang = 'ko';
      document.body.style.fontFamily = "'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif";
    }

    // Language Switcher Button Highlighting
    ['KO', 'ZH', 'EN'].forEach(l => {
      const btn = document.getElementById('lang' + l.charAt(0) + l.slice(1).toLowerCase() + 'Btn');
      if (btn) {
        btn.className = l === lang 
          ? 'px-2 py-0.5 rounded bg-ink-primary text-white font-bold transition text-[10px] sm:text-[11px] shadow-sm' 
          : 'px-2 py-0.5 rounded text-ink-secondary hover:text-ink-primary transition text-[10px] sm:text-[11px]';
      }
    });

    const t = i18n[lang] || i18n['KO'];
    const safeSetText = (id, txt) => {
      const el = document.getElementById(id);
      if (el && txt !== undefined) el.innerText = txt;
    };
    const safeSetHtml = (id, html) => {
      const el = document.getElementById(id);
      if (el && html !== undefined) el.innerHTML = html;
    };
    const safeSetAttr = (id, attr, val) => {
      const el = document.getElementById(id);
      if (el && val !== undefined) el.setAttribute(attr, val);
    };

    // Brand & Navigation
    safeSetText('headerBrandTitle', t.brandTitle);
    safeSetText('headerBrandSubtitle', t.brandSubtitle);
    safeSetText('navTabHome', t.navHome || '대시보드');
    safeSetText('mNavTabHome', t.navHome || '대시보드');
    safeSetText('navTabPortfolio', t.navPortfolio);
    safeSetText('mNavTabPortfolio', t.navPortfolio);
    safeSetText('navTabModels', t.navModels);
    safeSetText('mNavTabModels', t.navModels + ' (' + (typeof liveModelsData !== 'undefined' ? liveModelsData.length : 242) + ')');
    safeSetText('navTabNews', t.navNews);
    safeSetText('mNavTabNews', t.navNews + ' (' + (typeof liveNewsData !== 'undefined' ? liveNewsData.length : 1535) + ')');
    safeSetText('navTabGraph', t.navGraph);
    safeSetText('mNavTabGraph', t.navGraph);
    safeSetText('adminArchiveLabel', t.adminArchiveBtn);
    safeSetText('mNavTabInbox', (t.adminArchiveBtn || '아카이브') + ' (' + (typeof liveInboxData !== 'undefined' ? liveInboxData.length : 1777) + ')');

    // Hero Elements
    safeSetText('heroBadge', t.heroBadge);
    safeSetText('heroMainTitle', t.heroMainTitle);
    safeSetHtml('heroMainDesc', t.heroMainDesc);
    const liveCasesCount = (window.liveCasesData && window.liveCasesData.length) || (window.casesData && window.casesData.length) || 63;
    const heroAuditText = lang === 'KO' ? `● ${liveCasesCount}개 기술 검증 완료` : (lang === 'ZH' ? `已完成 ${liveCasesCount} 项技术审计` : `${liveCasesCount} Audits Completed`);
    safeSetText('heroAuditCount', heroAuditText);

    // Dashboard KPI Telemetry
    safeSetText('statLabelVerified', lang === 'KO' ? '공식 기술 검증' : (lang === 'ZH' ? '官方技术核查' : 'Verified Fact-Checks'));
    safeSetText('statLabelInbox', lang === 'KO' ? '수집 인박스' : (lang === 'ZH' ? '采集收件箱' : 'Harvested Inbox'));
    safeSetText('statLabelModels', lang === 'KO' ? 'AI 모델 트렌드' : (lang === 'ZH' ? 'AI 模型趋势' : 'AI Model Trends'));
    safeSetText('statLabelNews', lang === 'KO' ? 'AI 테크 동향' : (lang === 'ZH' ? 'AI 科技动态' : 'Tech Intelligence'));
    safeSetText('statLabelArchive', t.statArchiveLabel);
    safeSetText('statDescInbox', lang === 'KO' ? 'HN · GeekNews · GitHub · HF 24/7 수집' : (lang === 'ZH' ? 'HN · GeekNews · GitHub · HF 全天候采集' : 'HN · GeekNews · GitHub · HF 24/7 Ingestion'));
    safeSetText('statDescModels', lang === 'KO' ? 'MoE, VLM, 추론 특화 오픈 가중치' : (lang === 'ZH' ? 'MoE、VLM与推理优化开源权重' : 'MoE, VLM & Reasoning Open Weights'));
    safeSetText('statDescNews', lang === 'KO' ? 'CVE 취약점, 인프라 장애, 아키텍처 토론' : (lang === 'ZH' ? 'CVE 漏洞、基础设施故障与架构实践' : 'CVEs, Infra Outages & Architecture Posts'));

    const nowKstForTitle = getDynamicKstDate();
    const pad0 = (n) => String(n).padStart(2, '0');
    const curKstDateStrForTitle = `${nowKstForTitle.getFullYear()}-${pad0(nowKstForTitle.getMonth() + 1)}-${pad0(nowKstForTitle.getDate())}`;
    safeSetText('timelineTitleText', (t.timelineTitle || '당일 24시간 수집 타임라인') + ' (' + curKstDateStrForTitle + ')');
    safeSetText('timelineSub', t.timelineSub);
    safeSetText('timelineBadgeText', t.timelineBadge);
    safeSetText('timelineLegendText', t.timelineLegend);
    safeSetHtml('timelineFooterText', t.timelineFooterPrefix + ' <b class="text-indigo-700">0' + (lang === 'KO' ? '건' : (lang === 'ZH' ? '条' : ' items')) + '</b>');
    safeSetText('trendRadarTitleText', t.trendRadarTitle);
    safeSetText('trendRadarSub', t.trendRadarSub);
    safeSetHtml('trendRadarFooter', `<span class="flex items-center gap-1.5"><i data-lucide="zap" class="w-3.5 h-3.5 text-amber-500"></i> ` + (lang === 'KO' ? 'LLM 자동 트렌드 추출 (OpenRouter 0원 라우팅)' : (lang === 'ZH' ? 'LLM 自动化趋势提取 (OpenRouter 0元路由)' : 'Automated LLM Trend Extraction (OpenRouter Free Tier)')) + `</span>`);
    safeSetText('homeTopPicksTitle', t.homeTopPicksTitle);
    const viewAllDynamicText = lang === 'KO' ? `전체 ${liveCasesCount}개 검증 도시에 보러가기` : (lang === 'ZH' ? `查看全部 ${liveCasesCount} 份核查档案` : `View All ${liveCasesCount} Empirical Dossiers`);
    safeSetText('homeTopPicksViewAll', viewAllDynamicText);

    // News View Labels & Pills
    safeSetText('newsHeaderBadge', t.newsHeaderBadge);
    safeSetText('newsHeaderTitle', t.newsHeaderTitle);
    safeSetText('newsHeaderDesc', t.newsHeaderDesc);
    safeSetText('newsCatFilterLabel', t.newsCatFilterLabel);
    safeSetText('newsTier2FilterLabel', t.newsTier2FilterLabel);
    safeSetText('newsSourceLabel', t.newsSourceLabel);
    safeSetText('newsSrcBtnAll', t.newsSrcAll);
    safeSetAttr('newsSearchInput', 'placeholder', t.newsSearchPlaceholder);
    safeSetText('newsSortLabel', t.newsSortLabel);

    if (typeof window.updateNewsCategoryPillCounts === 'function') {
      window.updateNewsCategoryPillCounts();
    }

    const newsSortSel = document.getElementById('newsSortSelect');
    if (newsSortSel && t.newsSortOptions) {
      const cur = newsSortSel.value;
      newsSortSel.innerHTML = t.newsSortOptions.map(opt => `<option value="${opt.val}" ${opt.val === cur ? 'selected' : ''}>${opt.text}</option>`).join('');
    }

    // Models View Labels & Pills
    safeSetText('modelsFamilyLabel', t.modelsFamilyLabel);
    safeSetText('modelsArtifactLabel', t.modelsArtifactLabel);
    safeSetAttr('modelsSearchInput', 'placeholder', t.modelsSearchPlaceholder);
    safeSetText('modelsSortLabel', t.modelsSortLabel);

    if (typeof window.updateModelCategoryPillCounts === 'function') {
      window.updateModelCategoryPillCounts();
    } else {
      document.querySelectorAll('.model-fam-pill').forEach(pill => {
        const fam = pill.dataset.fam;
        if (t.modelFams && t.modelFams[fam]) pill.innerText = t.modelFams[fam];
      });
      document.querySelectorAll('.model-art-pill').forEach(pill => {
        const art = pill.dataset.art;
        if (t.modelArts && t.modelArts[art]) pill.innerText = t.modelArts[art];
      });
    }

    const modelsSortSel = document.getElementById('modelsSortSelect');
    if (modelsSortSel && t.modelsSortOptions) {
      const cur = modelsSortSel.value;
      modelsSortSel.innerHTML = t.modelsSortOptions.map(opt => `<option value="${opt.val}" ${opt.val === cur ? 'selected' : ''}>${opt.text}</option>`).join('');
    }

    // Graph View
    safeSetText('graphHeaderBadge', t.graphHeaderBadge);
    safeSetText('graphHeaderTitle', t.graphHeaderTitle);
    safeSetText('graphHeaderSub', t.graphHeaderSub);
    safeSetText('graphBtnAll', t.graphBtnAll);
    safeSetText('graphBtnLang', t.graphBtnLang);
    safeSetText('graphBtnTech', t.graphBtnTech);
    safeSetText('graphBtnOrg', t.graphBtnOrg);
    safeSetText('graphBtnPerson', t.graphBtnPerson);
    safeSetText('graphBtnPaper', t.graphBtnPaper);

    // Archive & Inbox View
    safeSetText('inboxHeaderBadge', t.inboxHeaderBadge);
    safeSetText('inboxHeaderTitle', t.inboxHeaderTitle);
    safeSetText('pipelineScheduleDesc', t.pipelineScheduleDesc);
    safeSetText('pipelineWidgetTitle', t.pipelineWidgetTitle);
    safeSetText('pipelineNextTargetLabel', t.pipelineNextTargetLabel);
    safeSetText('pipelineFooterAudit', t.pipelineFooterAudit);
    if (typeof window.renderPipelineTelemetryCards === 'function') window.renderPipelineTelemetryCards();
    if (typeof window.renderRunsTable === 'function') window.renderRunsTable();
    if (typeof window.updateCronCountdown === 'function') window.updateCronCountdown();
    safeSetText('inboxHeaderDesc', t.inboxHeaderDesc);
    safeSetText('inboxHeaderCount', lang === 'KO' ? ('총 ' + (typeof liveInboxData !== 'undefined' ? liveInboxData.length : '') + '건') : (lang === 'ZH' ? ('共 ' + (typeof liveInboxData !== 'undefined' ? liveInboxData.length : '') + ' 项') : ('Total: ' + (typeof liveInboxData !== 'undefined' ? liveInboxData.length : '') + ' items')));
    safeSetText('criteriaTitle', t.criteriaTitle);
    safeSetText('criteriaDesc', t.criteriaDesc);
    safeSetText('critGithub', t.critGithub);
    safeSetText('critHn', t.critHn);
    safeSetText('critHf', t.critHf);
    safeSetText('critArxiv', t.critArxiv);
    safeSetAttr('inboxSearchInput', 'placeholder', t.inboxSearchPlaceholder);

    // Portfolio Controls
    safeSetText('btnLabelAll', t.btnAll);
    safeSetText('btnLabelUser', t.btnUser);
    safeSetText('btnLabelAuto', t.btnAuto);
    safeSetText('sortLabel', t.sortLabel);
    safeSetAttr('searchInput', 'placeholder', t.searchPlaceholder);
    safeSetText('domainFilterLabel', t.domainLabel);
    safeSetText('tagAll', t.tagAll);
    safeSetText('tagFrontend', t.tagFrontend);
    safeSetText('tagAgent', t.tagAgent);
    safeSetText('tagScraping', t.tagScraping);
    safeSetText('tagDoc', t.tagDoc);
    safeSetText('tag3d', t.tag3d);
    safeSetText('tagRust', t.tagRust);
    safeSetText('tagOther', t.tagOther);

    const sortSel = document.getElementById('sortSelect');
    if (sortSel && t.sortOptions) {
      const curVal = sortSel.value;
      sortSel.innerHTML = t.sortOptions.map(opt => `<option value="${opt.val}" ${opt.val === curVal ? 'selected' : ''}>${opt.text}</option>`).join('');
    }

    // 🌟 Instant Full Re-render on Active Views
    try { if (typeof window.renderCards === 'function') window.renderCards(); } catch (e) {}
    try { if (typeof window.renderHomeTopPicks === 'function') window.renderHomeTopPicks(); } catch (e) {}
    try { if (typeof window.renderRadarSession === 'function') window.renderRadarSession(); } catch (e) {}
    try { if (typeof window.renderTelemetryCharts === 'function') window.renderTelemetryCharts(); } catch (e) {}
    try { if (typeof window.updateCronCountdown === 'function') window.updateCronCountdown(); } catch (e) {}
    try { if (typeof window.renderModels === 'function') window.renderModels(); } catch (e) {}
    try { if (typeof window.renderNews === 'function') window.renderNews(); } catch (e) {}
    try { if (typeof window.renderInbox === 'function') window.renderInbox(); } catch (e) {}
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      try { window.lucide.createIcons(); } catch (e) {}
    }
  }
}

if (typeof window !== 'undefined') {
  window.i18n = i18n;
  window.setLanguage = setLanguage;
}
