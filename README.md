# 🌐 2026 SOTA Web & SNS 최신 기술 Fact-Check & 포트폴리오 시스템

본 저장소는 **웹(WEB) 및 SNS(X, Reddit, Hacker News, Hugging Face 등)에서 유입되는 최신 AI 모델 및 신기술 주장을 2026년 SOTA(State-of-the-Art) 기준으로 검증하고, 실제 실무 적용 가능성을 체계적으로 기록하는 엔지니어링 포트폴리오 시스템**입니다.

---

## 📁 디렉토리 구조

```
2026-08-31_WEB_Factcheck/
├── dashboard/                             # 🎨 실시간 인터랙티브 포트폴리오 대시보드
│   ├── index.html                         # 단일 파일 포트폴리오 UI (다크모드, 필터, 모달)
│   └── data.json                          # 구조화된 포트폴리오 메타데이터
│
├── inbox/                                 # 📥 자동 수집된 트렌드 후보 대기 큐 (미승인 상태)
│   ├── _promoted/                         # 공식 포트폴리오로 승격 완료된 아카이브
│   └── _rejected/                         # 사용자가 반려한 아카이브 (재수집 영구 차단)
│
├── investigations/                        # 🏆 [공식 포트폴리오] 검증 완료된 심층 프로젝트들
│   ├── 2026-08-31_repo_firecrawl_anydoc/  # 🟢 [실제 개발 완료] 4.4ms 오피스 to 마크다운 파서
│   ├── 2026-08-31_sns_angeldot_claim/     # 🟡 [성능/과금 중단] AI 비디오 파이프라인 원가 분석
│   └── 2026-08-31_sns_deepseek_claim/     # ⚪ [아직 개발 전] 벤치마크 하네스 왜곡 감사
│
├── configs/                               # 검증 기준 및 사용자 맞춤 설정
│   ├── user_persona_alignment.json        # 👤 사용자 커리어 및 5대 실무 도메인 매핑 설정
│   ├── source_credibility_matrix.json     # 소스별 신뢰도 가중치 매트릭스 (Tier 1 ~ 4)
│   ├── pipeline_cost_benchmark.json       # 2026 AI 모델별 단위 원가 레지스트리
│   └── local_reference_bridge.json        # D:\2026-08-04_CODEX\collection-foundation 연동
│
├── tools/                                 # CLI 자동화 및 감사 도구 모음
│   ├── harvest_trends.py                  # 1단계: 비로그인 트렌드 자동 수집기 (중복 차단)
│   ├── triage.py                          # 2단계: 승인/반려 게이트웨이 (Human-in-the-Loop)
│   ├── init_case.py                       # 3단계: 신규 케이스 폴더 생성기
│   ├── estimate_pipeline_cost.py          # 4단계: 파이프라인 실질 제작 원가 계산기
│   └── build_dashboard.py                 # 5단계: 대시보드 원클릭 빌더
│
└── .github/workflows/
    └── deploy_pages.yml                   # GitHub Pages 자동 배포 및 매일 자정 자동 수집 Cron
```

---

## 🚀 워크플로우 3단계 가이드

### 1단계: 최신 트렌드 자동 수집 (비로그인 무료 수집)
```bash
python tools/harvest_trends.py
```
- Hacker News, Hugging Face, Reddit에서 핫한 최신 기술을 중복 없이 `inbox/`에 수집합니다.

### 2단계: 수집 후보 검토 및 승인 게이트 (Human-in-the-Loop)
```bash
# 승인 대기 목록 확인
python tools/triage.py --list

# 맘에 드는 기술을 공식 포트폴리오로 승격 (사용자 승인)
python tools/triage.py --promote <case_id>

# 맘에 들지 않는 기술 반려 (이후 재수집 영구 차단)
python tools/triage.py --reject <case_id>
```

### 3단계: 대시보드 확인 및 GitHub Pages 배포
```bash
python tools/build_dashboard.py
```
- [dashboard/index.html](file:///d:/2026.06.21_Antigravity/2026-08-31_WEB_Factcheck/dashboard/index.html)을 열어 실시간 갱신된 포트폴리오를 확인합니다.
- 저장소를 GitHub에 푸시하면 `.github/workflows/deploy_pages.yml`에 의해 **GitHub Pages로 실시간 전 세계 배포**됩니다.

---

## 🎯 사용자 맞춤형 5대 실무 도메인 연계 (User Persona Alignment)
1. **DX & Python 업무 프로세스 자동화**: 사내 반복 업무의 Python/LLM 오케스트레이션.
2. **엔터프라이즈 RAG & 문서 파싱 인프라**: 오피스/PDF 문서의 로컬 경량 임베딩 파이프라인.
3. **생성형 마케팅 & GEO/SEO 최적화**: 생성형 검색(ChatGPT/Gemini) 최적화 및 콘텐츠 파이프라인.
4. **이커머스 & 커머스 데이터 수집**: 쿠팡, 스마트스토어, 특가 수집, `collection-foundation` 연동.
5. **정량 데이터 분석 & 벤치마크 감사**: 단위 경제학(Unit Economics) 원가 계산 및 벤치마크 오염 감사.
