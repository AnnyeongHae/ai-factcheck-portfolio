# [제17호 팩트체크] Taste-Skill: AI 슬롭(Slop) 디자인 탈피를 위한 3대 다이얼 프론트엔드 취향 프레임워크

## 1. 큐레이션 동기 및 문제의식 (Discovery Motivation)
- **Curator**: Anyong Cheong (직접 큐레이션)
- **문제의식**: 요즘 AI 코딩 에이전트(Cursor, Claude Code, Windsurf 등)가 만든 웹사이트들은 묘하게 기시감이 듭니다. **어두침침한 사이버펑크 네온 다크모드, 획일적인 3열 카드 박스(Three-Equal-Cards), 뻔한 그라데이션, 그리고 천편일률적인 폰트와 이모지 남발**이 그것입니다.
- **해결 방안**: Leon Lin(`Leonxlnx`)이 오픈소스로 공개한 `taste-skill`은 AI에게 전문 프로덕트 디자이너의 ‘디자인 취향(Taste)’을 주입하여 **AI 슬롭을 사전에 강제 차단하고 스위스 에디토리얼 스타일의 웜 미니멀리즘**을 구현해냅니다.

## 2. 3대 핵심 디자인 다이얼 (The 3 Design Dials)
1. **`DESIGN_VARIANCE` (기본값: 8)**: 레이아웃의 비대칭성과 실험성을 제어하여 획일적인 3열 카드 복붙을 방지.
2. **`MOTION_INTENSITY` (기본값: 6)**: 과도한 네온 블러 대신 부드럽고 절제된 마이크로 인터랙션과 트랜지션 적용.
3. **`VISUAL_DENSITY` (기본값: 4)**: 텍스트가 빽빽하게 뭉치지 않도록 넉넉한 네거티브 스페이스(여백)와 명확한 시각적 위계 확보.

## 3. 원문 주장 검증 (Claims Assessment)
- **주장 1: AI 특유의 3-Card 및 네온 다크모드 슬롭 차단?** ➔ **VERIFIED TRUE (사실)**. SKILL.md 내의 Anti-Pattern Ban 체크리스트를 통해 통계적 평균 디자인으로의 회귀를 원천 차단함.
- **주장 2: 프레임워크 무관 npx 설치 지원?** ➔ **VERIFIED TRUE (사실)**. React, Svelte, Tailwind, Pure HTML 어디서든 100% 동일하게 작동함.
