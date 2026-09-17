# TurboQuant & turbovec: 31GB 벡터를 4GB로 8배 압축하는 Google 알고리즘 및 FAISS 3.4배 속도 주장의 실체 검증

Case ID: 6-09-17_sns_turbovec_turboquant_31gb_to_4gbVerdict: **HALF_TRUE** (92.0%)

## Overview
LinkedIn에서 화제가 된 Basia Kubicka의 게시글(lnkd.in/p/gKPaQRY5) 검증.
Google Research의 TurboQuant 알고리즘(arXiv:2504.19874, ICLR 2026)과 이를 Rust/Python으로 구현한 turbovec(GitHub 17,210+ Stars)의 기술적 실체를 검증함.

### Key Takeaways
1. 31GB -> 4GB 8배 압축은 float32를 4비트로 양자화한 정확한 산술 결과이며, 코드북 학습 없는 Online Ingest는 실질적 혁신임.
2. 'FAISS보다 3.4배 빠르다'는 비교는 Meta FAISS의 레거시 모듈인 IndexPQFastScan과의 1:1 비교일 뿐이며, 프로덕션 RAG의 O(log N) 그래프 탐색(HNSW)을 전면 대체하는 것은 아님.
3. 2026년 학계 후속 논문(arXiv:2604.19528)에서 기존 RaBitQ 기법이 동일 환경에서 더 우수하며 TurboQuant 일부 수치의 재현성에 의문이 제기됨.
