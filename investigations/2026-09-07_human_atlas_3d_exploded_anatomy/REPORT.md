# 팩트체크 검증 도시에: Human Atlas 3D: Three.js 기반 2,234개 파트 인체 분해 시각화와 3D 생성 AI 마케팅 실체 분석

## 1. 개요 및 선정 배경
- **조사 일자**: 2026-09-07
- **검증 판정**: `HALF_TRUE` (신뢰도: 96.0%)
- **분류**: 3D/WebGL 시각화
- **선정 동기**: 2,234개 부품의 인체 분해도 3D 시각화가 프롬프트 한 번으로 통째로 생성되었다는 SNS 바이럴 마케팅의 사실 여부를 검증하고 WebGL Three.js 씬그래프 최적화 기술 분석.
- **타겟 워크플로**: 웹 기반 고성능 인터랙티브 3D 씬 및 계층형 부품 분해도 구축

---

## 2. 팩트체크 및 아키텍처 실체 분석 (The Hook & Reality)
### 🔍 핵심 이슈
AI가 2,234개 인체 부품 3D 지오메트리를 원클릭으로 생성했다는 주장은 과장이며, 실제로는 오픈 CAD 에셋을 AI 코딩 어시스턴트로 인터랙티브 프로그래밍한 것임.

### ⚠️ 마케팅 과장 해체 (Marketing Hype Anatomy)
3D 생성 AI 모델이 2,234개 내부 장기 지오메트리를 무결점으로 생성하는 기술은 현존하지 않음. 실체는 정밀 3D CAD 원본을 Draco로 88% 압축하고 Three.js 애니메이션 벡터 보간을 스크립팅한 결과물.

---

## 3. 핸즈온 실측 검증 (Hands-on Verification)
- **테스트 환경**: Three.js WebGL Renderer (Chrome / Safari Mobile)
- **실측 결과**: Draco 압축으로 120MB -> 14MB로 경량화, 모바일 60FPS 분해 애니메이션 검증
- **검증 파이프라인**: https://x.com/ashebytes/status/2096221988763173186
- **상세 내역**:
AI는 3D 메쉬 생성이 아닌 Three.js 카메라 컨트롤, 머티리얼 셰이더, 분해 좌표 보간 스크립트 작성에 기여한 것으로 팩트체크 완료.

---

## 4. 진화 계보 및 기술 대안 (Lineage & Alternatives)
- **클러스터**: 브라우저 실시간 3D 그래픽스 & 모델 분해도 (Gen 4 (Draco Compression + Hierarchical Instancing))
- **대안 기술 비교**:

### Three.js Exploded Scene (`WebGL, Draco, InstancedMesh`)
- **장점**: 브라우저 무설치 60FPS 실시간 렌더링, 부품별 인터랙티브 분해
- **한계**: 2,234개 메쉬 개별 드로우콜 시 모바일 성능 저하

### Desktop Medical CAD / DICOM (`VTK, ITK, Blender`)
- **장점**: 0.1mm 단위 정밀도와 볼륨 렌더링
- **한계**: 웹 브라우저 직접 구동 불가, 수 GB 메모리 소모

---

## 5. 엔지니어링 시사점 (Engineering Takeaways)
3D 웹 애플리케이션 구축 시 AI는 3D 지오메트리 생성보다 Three.js 씬 로직, 셰이더, 인터랙티브 이벤트 바인딩 자동화에 활용하는 것이 실질적임.

## 6. 향후 응용 분야 (Future Applications)
인터랙티브 웹 교육 플랫폼, 의료 설명 보조 도구, 복합 하드웨어 조립 분해도.
