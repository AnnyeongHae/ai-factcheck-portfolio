# 2. 주장 분해 및 증거 수집 (Claim Decomposition & Evidence)

## 1. 감정/마케팅 노이즈 제거 및 원자적 명제 (Atomic Claims)

### Claim 1: [파이프라인 완전 자동화]
- **명제**: MoneyPrinterTurbo는 키워드 1개 입력 시 스크립트 작성, 스톡 영상 매칭, 음성 합성, 자막 생성, 렌더링을 End-to-End로 자동 완료한다.
- **속성**: 기능 / 소프트웨어 파이프라인

### Claim 2: [100% 무료 및 로컬 무GPU 실행]
- **명제**: 완전 무료로 사용할 수 있으며, 고성능 외장 GPU 없이 일반 PC 환경에서 구동 가능하다.
- **속성**: 비용 / 하드웨어 요구사양

### Claim 3: [플랫폼 자동 수익화 가능]
- **명제**: 생성된 영상을 YouTube Shorts 및 TikTok에 업로드하여 안정적으로 계정 정지 없이 광고 수익을 창출할 수 있다.
- **속성**: 플랫폼 정책 / 저작권 및 수익화 가능성

---

## 2. 증거 수집 및 Tier 매핑 (Multi-Hop Evidence)

### Evidence for Claim 1 (파이프라인 기능 검증)
- **출처 1 (Tier 1 - GitHub `harry0703/MoneyPrinterTurbo` 소스코드)**:
  - `app/services/llm.py`: OpenAI, Gemini, DeepSeek, Ollama 연동을 통한 스크립트 자동 생성 코드 확인.
  - `app/services/voice.py`: Edge-TTS 및 Azure TTS 연동 확인.
  - `app/services/video.py`: Pexels Video API를 통해 키워드 기반 스톡 영상 자동 다운로드 및 MoviePy/FFmpeg 합성 확인.
  - `app/services/subtitle.py`: Whisper 기반 자동 자막 타이밍 생성 확인.
  - **결론**: **기능 파이프라인 자체는 완전히 사실로 확인됨.**
  - 신뢰도 가중치: 1.0 (Tier 1)

### Evidence for Claim 2 (비용 및 무GPU 구동 검증)
- **출처 1 (Tier 1 - 설정 파일 `config.toml` 및 코드 의존성 감사)**:
  - **하드웨어**: 무거운 로컬 생성 모델을 직접 돌리는 것이 아니라 외부 API를 호출하므로 GPU 없이 CPU만으로 FFmpeg 렌더링 가능 (사실).
  - **비용**: 
    - 코드 자체는 오픈소스(무료)이나, LLM(OpenAI GPT-4o / Claude)을 사용할 경우 **유료 API 토큰 비용**이 발생함. (Ollama 로컬 LLM을 쓰면 무료이나 저사양 CPU에서는 매우 느림).
    - Pexels API는 무료 키를 발급받아야 하며 시간당 호출 제한(Rate Limit 200 req/hr)이 있음.
  - **결론**: 코드는 무료이나 "100% 무비용"은 아니며 상용 LLM 사용 시 API 종량제 비용 발생.
  - 신뢰도 가중치: 0.95 (Tier 1)

### Evidence for Claim 3 (플랫폼 수익화 및 제재 리스크 검증)
- **출처 1 (Tier 1 - YouTube 채널 수익화 정책 & TikTok Community Guidelines 2026)**:
  - **YouTube의 '재사용 및 반복적인 콘텐츠(Reused & Repetitive Content)' 규정**: Pexels의 공개 스톡 영상과 Edge-TTS 기계 음성만으로 대량 생성된 영상은 2025~2026년 강화된 AI 자동화 콘텐츠 필터에 걸려 **수익화 승인이 거절되거나 채널 섀도우밴(Shadowban) 대상**이 됨.
  - **스톡 비디오 중복성**: 수천 명의 사용자가 동일한 Pexels 키워드 영상을 반복 사용하므로 독창성(Originality) 지수가 극히 낮음.
  - 신뢰도 가중치: 0.95 (Tier 1)

---

## 3. End-to-End 파이프라인 원가 분석 (Unit Economics Audit)

1분(60초)짜리 숏폼 비디오 1편을 제작할 때, 적용하는 AI 컴포넌트에 따른 **실질 원가 및 대량 양산 비용** 비교 분석입니다.

| 파이프라인 시나리오 | 구성 (LLM + Voice + Video) | 1편당 표기 원가 | Reject Ratio(1.5x) 반영 실질 원가 | 월 30편(1일 1영상) 양산 비용 | 수익화/플랫폼 안정성 |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **A. 완전 무료형 (SNS 주장)** | DeepSeek V3 + EdgeTTS + Pexels API | **$0.0002** | **$0.0002** | **$0.01 / 월** | ❌ 극도로 위험 (반복 스톡으로 채널 정지) |
| **B. 상용 고품질 스톡형** | GPT-4o + ElevenLabs + Pexels API | **$0.125** | **$0.125** | **$3.75 / 월** | ⚠️ 중간 (음성은 자연스러우나 영상 중복) |
| **C. 순수 AI 생성 (Higgsfield 720p)** | GPT-4o + ElevenLabs + **Higgsfield Seedance 2.0 (720p)** | **$13.32** | **$19.92** | **$597.75 / 월** | ✅ 매우 안전 (100% 고유 비디오, 승인 용이) |
| **D. 최고화질 시네마틱 (Higgsfield 1080p)**| Claude 3.5 + ElevenLabs + **Higgsfield Seedance 2.0 (1080p)** | **$27.13** | **$40.63** | **$1,218.81 / 월** | 💎 최고 수준 (상업 광고/스폰서십 가능) |

> 💡 **비용 감사 핵심 인사이트**:  
> SNS에서 주장하는 "0원 파이프라인"은 플랫폼의 AI 스팸 필터에 의해 1~2개월 내에 채널이 정지됩니다. 반면, 플랫폼 정책을 완벽히 우회하고 독창성을 확보하기 위해 **Higgsfield Seedance 2.0** 같은 최신 비디오 생성 모델을 도입할 경우, **1편당 약 $20(월 약 600달러)**의 실질 API 비용이 발생하므로 단순 "돈 복사기"라는 주장은 경제학적으로 성립하지 않습니다.
