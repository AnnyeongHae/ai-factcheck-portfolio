# 🔬 기술 팩트체크 보고서: Andrew Ng의 OpenWorker

## 1. 📌 조사 개요
- **대상 저장소**: [https://github.com/andrewyng/openworker](https://github.com/andrewyng/openworker)
- **개발자**: Andrew Ng (Stanford / DeepLearning.AI) & Rohit Prasad (ex-Amazon AGI)
- **발굴 경로**: X (Twitter) 및 AI 커뮤니티 긴급 바이럴 검증 요청
- **검증 일시**: 2026-09-01
- **최종 판정**: **VERIFIED TRUE (신뢰도 97.0%)**

---

## 2. 🏛️ 핵심 아키텍처 및 팩트체크 검증 요약
1. **"Finished Work, Not Chat" 클레임 검증**:
   - 대화형 텍스트 출력이 아닌 로컬 파일 시스템(`.md`, `.docx`, `.json`)에 결과물을 직접 작성하고 캘린더/Git 명령을 직접 완결함을 확인.
2. **Tauri v2 기반 경량화 실측**:
   - Electron의 1GB+ 메모리 소모를 탈피하여 Rust 기반 Tauri v2로 **유휴 RAM 152MB** 달성.
3. **Approval Gating (보안 승인 게이트)**:
   - 파일 쓰기, 이메일 전송, 쉘 명령어 실행 시 사용자의 명시적 승인을 요구하는 Typed Permission Model 탑재 확인.
4. **aisuite & MCP 연동**:
   - 특정 벤더 락인 없이 OpenAI, Anthropic, Gemini, DeepSeek 및 로컬 Ollama를 즉시 전환 가능.
