---
name: factcheck-content-writer
description: >-
  Use this skill whenever writing, rewriting, or evaluating any public-facing
  content for the AI factcheck project — including hooks, card news captions,
  Threads/Instagram posts, newsletter blurbs, or dossier summaries.
  The skill enforces a strict TENSION-FIRST pipeline that produces content
  people actually want to read and share, rather than dry fact-report prose.
  Activate when the user asks to write a post, rewrite a hook,
  make content shareable, write a Threads caption, draft a newsletter, or
  any similar content-creation request for this project.
---

# AI Factcheck Content Writer Skill

이 스킬은 **"사람들이 읽고 싶은 글"** 을 일관되게 만들기 위한 파이프라인이다.
모든 공개 콘텐츠(훅, 카드뉴스 캡션, Threads 포스트, 뉴스레터 등)는
아래 파이프라인을 **순서대로** 따른다. 단 하나의 스텝도 건너뛰지 않는다.

상세 이론 및 예시 → [references/theory.md](./references/theory.md)

---

## 핵심 원칙

> 결론을 먼저 말하면 독자가 멈춘다.
> 긴장을 먼저 주면 독자가 계속 읽는다.

---

## THE PIPELINE

`
[STEP 1] 소재 자격 검사 (Gate)       ← 3가지 조건 미충족시 소재 교체
         ↓ PASS
[STEP 2] 독자 정의                   ← 한 사람을 구체적으로 상상
         ↓
[STEP 3] 반전 한 줄 추출 (The Twist) ← "A라 했는데 → 실은 B"
         ↓
[STEP 4] TENSION-FIRST 초안 작성     ← A: 긴장 / B: 반전 / C: 증거 / D: 열린 질문
         ↓
[STEP 5] 5-Point 체크리스트          ← 전부 YES가 아니면 수정 후 재시도
         ↓ ALL YES
[STEP 6] 포맷별 출력                 ← Threads / 카드훅 / 뉴스레터 / 퀴즈
`

---

## STEP 1 — 소재 자격 검사

세 조건 모두 YES여야 한다. 하나라도 NO면 다른 소재를 고르거나 추가 리서치.

| 조건 | 확인 방법 |
|:---|:---|
| G1. 클레임과 현실 사이에 갭이 있는가? | verdict가 HALF_TRUE / GAMED / MISLEADING 이거나, VERIFIED_TRUE라도 대중이 잘못 알고 있는 경우 |
| G2. 실제로 사람들이 이 주제로 이야기했는가? | viral_metric에 RT수, HN Points, 조회수 등 수치가 있는가 |
| G3. 독자의 내일 행동이 달라지는가? | 돈/시간 절약 OR 나쁜 결정 방지 OR 사회적 화폐 중 하나 이상 |

---

## STEP 2 — 독자 정의

글을 쓰기 전에 한 사람을 구체적으로 상상한다.

- 이 사람은 지금 어떤 문제를 겪고 있는가?
- 이 주제에 대해 무엇을 이미 믿고 있는가?
- 이 글을 읽고 "맞아, 나도 그랬어" 할 수 있는가?

독자가 명확해지면 STEP 3로 간다.

---

## STEP 3 — 반전 한 줄 추출 (The Twist)

소재에서 반전의 핵심 한 줄을 먼저 추출한다.

형식:
  [대부분이 믿는 것] → 실제론 [다른 것]이었다.

예시:
  "AI 에이전트는 생각하는 데 토큰을 쓴다"
  → 실제론 터미널 로그를 읽는 데 85%를 썼다.

  "중국이 CUDA를 오픈소스로 박살냈다"
  → 실제론 모델 가중치는 비공개였다.

  "ChatGPT 죽으면 Claude 쓰면 되지"
  → 실제론 Claude도 연쇄로 5배 느려졌다.

이 한 줄이 완성되면 STEP 4로 간다.

---

## STEP 4 — TENSION-FIRST 구조로 초안 작성

4파트를 반드시 순서대로 채운다.

### PART A | TENSION (긴장)
독자가 공감하는 상황 또는 질문으로 시작.
결론은 절대 말하지 않는다. 1~2문장.
예: "Claude Code 쓰는데 왜 이렇게 토큰이 빨리 닳지?"

### PART B | TWIST (반전)
Step 3에서 추출한 반전을 투입. 숫자는 딱 하나만.
예: "Spotify가 뜯어봤더니, 코딩에 쓰이는 건 15%뿐이었다."

### PART C | EVIDENCE (증거)
반전을 뒷받침하는 가장 구체적인 사실 하나.
"우리가 직접 확인했다"는 느낌.
예: "나머지 85%? 터미널이 뱉는 에러 로그 쓰레기."

### PART D | IMPLICATION (열린 질문)
결론을 주거나 행동을 제안한다. 또는 더 큰 질문으로 끝낸다.
결론형보다 질문형이 공유율이 높다.
예: "필터 하나 끼웠더니 45,000 토큰 → 4,200 토큰. 
     그럼 지금 당신 에이전트는 어디서 낭비 중인가?"

---

## STEP 5 — 5-Point 체크리스트

초안이 완성되면 아래 5개에 전부 YES가 나올 때까지 다듬는다.
하나라도 NO이면 해당 파트를 수정하고 다시 확인.

  C1. PART A에 독자가 "나 얘기네" 할 수 있는 문장이 있는가?
  C2. PART A만 읽었을 때 결론이 보이지 않는가?
  C3. 전체 글에서 숫자가 최대 2개 이하인가?
  C4. PART A+B 합쳐서 140자 이내인가?
  C5. PART D가 "따라서 ~해야 한다"로 끝나지 않는가?

---

## STEP 6 — 포맷별 최종 출력

### Threads / 인스타그램 캡션
  [PART A — 1~2문장]
  (한 줄 공백)
  [PART B — 반전]
  (한 줄 공백)
  [PART C — 증거]
  (한 줄 공백)
  [PART D — 질문형 엔딩]
  (한 줄 공백)
  #AI팩트체크 #[관련태그]

### 카드뉴스 훅 (이미지 위 텍스트)
  PART A만 사용. 최대 4줄, 줄당 20자 이내.
  결론 없음, 반전 없음 — 긴장만.

### 뉴스레터 / 블로그 첫 문단
  PART A (1문장) → PART B (1~2문장) → PART C (2~3문장, 수치+출처) → PART D (브릿지)

### 퀴즈 JSON
  claim 필드       = PART A (긴장/질문)
  explanation_ko   = PART B + C (반전 + 증거)
  정답 선택지 레이블 = PART D 한 줄 요약

---

## 절대 하지 말아야 할 것

1. 수동태, 명사 종결 사용 ("~이 발생함", "~이 확인됨")
2. 훅에서 verdict 먼저 말하기 ("판정: HALF_TRUE"로 시작)
3. 한 문단에 숫자 3개 이상
4. "따라서", "결론적으로"로 끝내기
5. 훅에 "팩트체크 결과"라는 말 쓰기

---

## 반전 패턴 빠른 참고

  A라 했는데 B였다
    예: "오픈소스라 했는데 가중치는 비공개였다"

  A가 원인이라 했는데 실제 원인은 C
    예: "토큰이 추론에 쓰인다 했는데, 85%는 로그였다"

  A가 해결한다 했는데 오히려 B가 심해졌다
    예: "CUDA 킬러라 했는데 엔비디아 종속이 심해졌다"

  A가 죽었다 했는데 B도 죽었다
    예: "ChatGPT 죽으면 Claude 쓰면 되지 → Claude도 죽었다"

  전문가가 OK 했는데 아니었다
    예: "OpenAI·Anthropic이 이상 없다 했는데 CVE 6개 나왔다"
