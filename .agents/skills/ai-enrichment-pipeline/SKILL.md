---
name: ai-enrichment-pipeline
description: In-Session Subagent AI Enrichment Pipeline for AI FactCheck Hub. Strict SSOT policy prohibiting external Gemini REST API and OpenRouter fallbacks.
---

# In-Session Subagent AI Enrichment Pipeline (SSOT)

## 1. 불변 원칙: 외부 LLM API 및 폴백 체인 영구 금지
- **Google AI Studio REST API (`GEMINI_API_KEY`)**: 호출 영구 금지 (404/누수 차단).
- **OpenRouter API (`OPENROUTER_API_KEY`)**: 호출 및 폴백 체인 영구 금지 (429/비용 차단).
- **외부 LLM Fallback 금지**: 모든 코드 및 파이프라인에서 외부 LLM 폴백은 원천 배제됩니다.

---

## 2. 정규 실행 체제: Antigravity In-Session Subagents ($0.00)
AI 요약·번역·분류는 오직 **Antigravity 내부 대화 세션의 `invoke_subagent` (Model: Flash)**로만 실행합니다.

1. **큐 배치 분할**:
   - `python tools/export_subagent_waves.py <시작번호> <배치수> 25` 실행하여 `data/subagent_queue/batch_XXX.json` 생성.
2. **병렬 서브에이전트 스폰 (`invoke_subagent`)**:
   - Model: `flash`
   - Role: `Wave Worker N`
   - 각 워커가 25건 청크를 고품질 KO/EN/ZH 3개 국어 제목 및 2줄 심층 Hook(제목 반복 금지)으로 가공 후 `batch_XXX_done.json` 저장 및 `tools/subagent_queue_manager.py --apply`로 DB 커밋.
3. **정기 자동화 (`schedule`, task-1551)**:
   - 매일 11:00 / 23:00 KST에 Antigravity 네이티브 Cron이 메인 세션 내부에서 단독 발화하여 서브 대화창 없이 조용히 완수.

---

## 3. 후속 필수 파이프라인 (Strict Order SSOT)
1. **Voyage pgvector 임베딩**:
   - AI 요약이 100% 완료된 후 정제된 **영문(`title_en` + `hook_en`)만** 추출하여 `tools/drain_voyage_embeddings.py`로 1024차원 벡터 일괄 적재.
2. **H-V-D Tripod 스파이크 및 Daily Hot 10**:
   - `tools/recompute_spike_scores.py --commit`으로 다중 출처 중복 기사 자동 병합 및 랭킹 최신화.
