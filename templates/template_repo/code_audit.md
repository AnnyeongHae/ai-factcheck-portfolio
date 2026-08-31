# 2. 코드 및 가중치 기술 감사 (Code & Weights Audit)

## 1. 정적 코드 분석 및 무결성 검사
- **더미/페이퍼웨어(Paperware) 여부**: [ PASS / FAIL ]
  - 핵심 모델 정의 (`model.py`, `modeling_xxx.py`) 및 레이어 구현 확인
  - 실제 추론/학습 파이프라인 존재 여부
- **의존성(Dependencies) 및 빌드 환경**:
  - `requirements.txt` / `pyproject.toml` 호환성
  - 비표준/비공개 의존성 라이브러리 사용 여부

---

## 2. 모델 가중치(Model Weights) 감사
- **가중치 호스팅 위치**: Hugging Face / ModelScope / 직접 다운로드
- **가중치 포맷**: SafeTensors (권장) / PyTorch .bin / GGUF
- **SHA256 해시 검증**:
  ```text
  safetensors file hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  ```
- **파라미터 수 실측 (Architecture Inspector)**:
  - 주장한 파라미터(예: 7B)와 실제 텐서 크기 일치 여부

---

## 3. End-to-End 파이프라인 원가 분석 (Unit Economics & Compute Cost)
- **외부 유료 API 의존성 유무**: [ YES / NO ]
  - LLM API, TTS API, Video Gen API 등
- **1회 파이프라인 가동 시 예상 원가**:
  - `python tools/estimate_pipeline_cost.py` 산출 결과 기재
  - 1편/1회 기준 실질 원가: **$XX.XX**

---

## 4. 라이선스 및 거버넌스 감사
- **GitHub 저장소 라이선스**: (예: Apache-2.0, MIT)
- **가중치(Weights) 라이선스**: (예: Custom Research-only, OpenRAIL)
- **불일치(Discrepancy) 확인**: 코드는 오픈소스이나 가중치는 상업적 사용 불가인지 여부

---

## 5. 로컬/샌드박스 재현 테스트 로그
```bash
# 재현 실행 명령어 기록
python -m eval.run_benchmark --model-path ./weights --dataset swe_bench_verified
```
- **재현 성공 여부**: [ REPRODUCED / PARTIALLY REPRODUCED / FAILED ]
- **실측 지표 (Measured Metrics)**:
  - Throughput (tokens/s): 
  - Peak VRAM (GB): 
  - Benchmark Score: 
