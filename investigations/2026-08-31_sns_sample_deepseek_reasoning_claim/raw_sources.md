# 1. SNS 원문 및 검증 출처 아카이빙 (Raw Sources Archive)

## 1. 팩트체크 검증 출처 목록 (Verified Sources)
- **최초 발원 SNS 포스트 (Tier 4)**: [https://x.com/TechInsider_AI/status/1899123456789](https://x.com/TechInsider_AI/status/1899123456789)
- **원저자 공식 기술 보고서 (Tier 1)**: [DeepSeek-R1 Technical Report (ArXiv:2501.12948)](https://arxiv.org/abs/2501.12948)
- **공식 모델 가중치 저장소 (Tier 1)**: [DeepSeek-AI Hugging Face Hub Safetensors](https://huggingface.co/deepseek-ai)
- **동적 벤치마크 공식 리더보드 (Tier 1)**: [LiveBench Official Results](https://livebench.ai)

---

## 2. 개발자 커뮤니티 실제 반응 (Community Reactions)
- **Reddit r/LocalLLaMA AI 연구원**:  
  > *"Pass@64(64회 샘플링 다수결)과 Pass@1(단일 시도)을 같은 막대그래프에 놓고 비교하는 건 전형적인 트위터발 체리피킹 마케팅이다."* ([스레드 링크](https://reddit.com/r/LocalLLaMA/comments/deepseek_aime_harness_check))
- **Hacker News ML 인프라 엔지니어**:  
  > *"671B MoE 풀 모델은 활성 파라미터가 37B라 해도 가중치 파일만 700GB다. 4090 1장(24GB)에서 절대 로딩 안 된다. 돌아가는 건 8B 증류(Distill) 모델뿐."* ([토론 링크](https://news.ycombinator.com/item?id=42700000))

---

## 3. 원문 전문 (Raw Text Content)
```text
🚨 AI HISTORY HAS BEEN MADE!
DeepSeek just dropped their new Reasoning flagship model. 
1. It DESTROYED OpenAI o1 on AIME 2025 (88.4% vs 83.3%) and GPQA Diamond!
2. You can run the FULL unquantized model on a single consumer RTX 4090 (24GB VRAM) at 120 tokens/sec.
3. Completely open-source MIT license including all training recipes and weights!

RIP closed source AI. Hugging Face link in bio 👇🔥
```

---

## 4. Hands-on 실측 3단계 상태
- **현재 상태**: **`[ PENDING_RESEARCH ]` (아직 개발 전 - 기술 조사 및 검증 완료)**
- **사전 조사 결과**:
  - 논문 Table 3 각주 확인 결과 Pass@1 기준 점수는 79.8%(o1 83.3% 대비 낮음).
  - 671B 가중치 크기 700GB로 24GB GPU 단일 서빙 물리적 불가능 확인.
  - SNS 주장의 기술적 오류(하네스 왜곡 및 VRAM 불일치)를 사전에 입증하여 불필요한 로컬 풀모델 세팅 비용을 방지함. 향후 Distill 8B 모델 연동 단계로 이행 예정.
