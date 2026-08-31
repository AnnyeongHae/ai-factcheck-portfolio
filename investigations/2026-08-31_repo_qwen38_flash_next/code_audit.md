# 2. 코드 및 가중치 기술 감사 (Code & Architecture Audit)

## 1. 아키텍처 및 SafeTensors 헤더 감사
- **메인 모델 크기**: 125B (MoE 구조)
- **N-gram 임베딩**: 51B
- **MTP (Multi-Token Prediction) 모듈**: 4B
- **토큰당 활성 파라미터 (Active Params per Token)**: **6B**
- **가중치 포맷**: SafeTensors (정상 해시 확인)

---

## 2. 서빙 하드웨어 요구사양 (VRAM & Serving Matrix)

| 양자화 포맷 (Format) | 전체 가중치 VRAM 점유량 | 초당 처리 속도 (Throughput) | 권장 서빙 하드웨어 |
| :--- | :---: | :---: | :--- |
| **FP16 (원본 가중치)** | ~250 GB | ~160 tokens/s | 4x A100 (80GB) 또는 4x H100 |
| **FP8 (vLLM / SGLang)** | ~130 GB | ~210 tokens/s | 2x A100 (80GB) / H100 |
| **NVFP4 / W4A16** | ~68 GB | ~280 tokens/s | **단일 80GB GPU (A100/H100) 서빙 가능** |
| **GGUF Q4_K_M (Ollama)** | ~72 GB | ~85 tokens/s | 3x RTX 3090/4090 로컬 클러스터 |

---

## 3. End-to-End 파이프라인 단위 경제학 (Unit Economics)
- 자체 GPU 서버(H100 1장 시간당 약 $2.50 임대 기준)에서 초당 200토큰으로 서빙할 경우:
  - **1백만 토큰당 인퍼런스 원가**: **약 $0.05 ~ $0.08** (상용 GPT-4o 대비 95% 이상 저렴).
- 사내 RAG 문서 분석이나 고속 에이전트 라우터로 적용 시 극도의 비용 효율성 달성 가능.
