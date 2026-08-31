# [Repository 팩트체크] Qwen3.8-Flash-Next 아키텍처 및 초저지연 추론 검증

- **대상 저장소**: [https://huggingface.co/Qwen/Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next)
- **조사 개시일**: 2026-08-31
- **최종 판정**: `[ VERIFIED TRUE ]` (MoE 125B 총용량 중 6B 활성화 및 MTP 가속 구조 입증)
- **Hands-on 상태**: `[ PENDING_RESEARCH ]` (기술 조사 및 SafeTensors 가중치 확인 완료)

---

## 1. 개요
2026년 8월 26일 알리바바가 공개하여 Hugging Face 트렌딩 1위(4,228점)를 기록한 **Qwen3.8-Flash-Next**의 125B MoE 아키텍처, 토큰당 6B 활성화, Multi-Token Prediction(MTP) 지원 여부 및 서빙 요구사양을 팩트체크했습니다.

## 2. 조사 파일 목차
1. [claim_analysis.md](./claim_analysis.md): 125B/6B MoE 구조, MTP 지원 여부 등 핵심 클레임 분해
2. [code_audit.md](./code_audit.md): SafeTensors 헤더 감사, vLLM/SGLang 호환성 및 양자화 VRAM 역산
3. [verdict_report.md](./verdict_report.md): 최종 팩트체크 판정서 및 실무 엔지니어링 활용 가이드
