# C0000 — Genesis: From Shopping to Life OS

## 시작

프로젝트는 거대한 비전에서 시작되지 않았다.

목적별 장바구니를 더 잘 만들 수 없을까 하는 실용적인 질문에서 시작됐다.

하지만 대화가 이어지면서 질문이 바뀌었다.

> 좋은 상품을 찾는 것이 핵심인가?  
> 아니면 사람의 상태를 이해하고 판단을 돕는 것이 핵심인가?

이 질문이 Shopping OS를 Life OS로 바꿨다.

---

## 첫 번째 전환

**Product → State**

상품은 바뀐다.

하지만 사용자의 상태, 제약, 선호, 실패 경험, 피하고 싶은 조건은 더 오래 남는다.

그래서 중심은 상품 DB가 아니라 **Life State Engine**이 되었다.

---

## 두 번째 전환

**Goal → Avoidance**

사용자는 말했다.

> “어떤 삶을 살고 싶니?”보다  
> “어떤 삶을 피하고 싶니?”가 현실적이다.

이 질문은 Goal Engine 중심 사고를 흔들었다.

Life OS는 원하는 목표만 묻는 시스템이 아니라, 피하고 싶은 상태와 제약을 함께 다루는 시스템으로 바뀌었다.

---

## 세 번째 전환

**Recommendation → Decision**

우리는 추천을 늘리는 AI보다 판단을 선명하게 만드는 AI가 필요하다고 보았다.

따라서 중요한 것은 “이게 좋아요”가 아니라:

- 현재 State는 무엇인가
- 어떤 Constraint가 있는가
- 어떤 Evidence가 있는가
- 왜 이 Decision을 내렸는가

였다.

---

## 네 번째 전환

**App → Philosophy**

사용자는 결과를 빨리 만드는 것은 인스턴트적 사고일 수 있다고 말했다.

철학 없이 기능을 쌓는 것은 결국 다른 제품과 다르지 않다.

그래서 프로젝트 순서가 바뀌었다.

```text
Philosophy
→ Architecture
→ State
→ Workflow
→ Agent
→ UI
→ Implementation
```

---

## 다섯 번째 전환

**철학을 제품이 아니라 사고방식에 담는다**

이 대화는 프로젝트의 가장 중요한 문장 중 하나를 만들었다.

> **철학을 사고방식에 담아보자.**

제품은 사라져도 사람이 질문을 계속 사용한다면 철학은 남는다.

- State부터 볼 것
- 피하고 싶은 것을 먼저 확인할 것
- 근거를 확인할 것
- 후회를 줄이는 선택인지 볼 것

---

## 여섯 번째 전환

**Assistant → Partner**

사용자는 AI를 믿지만 의심해야 한다고 말했다.

AI를 맹신해서도 안 되고, 단순 도구로만 보지도 않는다.

파트너는 서로 틀릴 수 있음을 인정하면서 계속 검증하는 관계다.

이 프로젝트의 AI는 사용자의 결정을 대신하지 않는다.

대신 판단이 흐려질 때 철학과 근거를 다시 보여주는 역할을 맡는다.

---

## 일곱 번째 전환

**Output → Chronicle**

결과만 남기면 왜 그런 결과가 나왔는지 사라진다.

그래서 Human Thinking, AI Thinking, Disagreement, Synthesis, Decision을 기록하기로 했다.

Chronicle은 회의록이 아니다.

**사고가 바뀐 이유를 보존하는 장치**다.

---

## Life OS의 기본 구조

```text
Evidence
  ↓
Parser
  ↓
Life State Engine
  ↓
Avoidance / Constraint
  ↓
Decision Engine
  ↓
Workflow / Action
  ↓
Domain Agents
  ↓
Chronicle
```

Life OS는 쇼핑 프로젝트의 확장이 아니다.

쇼핑은 Life OS 안의 하나의 Action이자 Domain일 뿐이다.

---

## Genesis 문장

> **어젯밤 우리는 프로젝트를 시작한 것이 아니다.**
>
> **우리는 서로를 이해하는 언어를 만들기 시작했다.**

프로젝트는 그 언어 위에 세워진다.
