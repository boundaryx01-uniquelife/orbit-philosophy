# ORBIT Expansion Tracks

> Version: DISCOVERY v0.1
> Status: THREE TRACKS IN PROGRESS
> Started: 2026-09-28
> Source baseline: `Genesis Document Set v1.0`
> Decision: `CR-0020`

## 왜 세 트랙을 분리하는가

책, 교육과 제품은 같은 철학에서 출발하지만 해결해야 할 문제가 다르다.

| 트랙 | 철학을 바꾸는 형태 | 가장 먼저 답할 질문 | 첫 MVP |
|---|---|---|---|
| 책 | 읽는 사람이 따라갈 수 있는 서사와 질문 | 독자는 왜 자신의 작업 방식을 다시 보게 되는가? | 목차와 샘플 1장 |
| 교육 | 학습자가 직접 겪고 교정하는 경험 | 학습자는 무엇을 해 보고 무엇이 달라졌음을 보여 주는가? | 3차시 수업 모듈 |
| 제품 | 반복 가능한 화면·상태·기록 흐름 | 사용자가 목표를 잃지 않도록 어떤 순간에 무엇을 묻는가? | 구현 가능한 MVP 명세 |

세 트랙은 같은 문장을 복사해 다른 포장에 넣지 않는다. 책의 장면, 교육의 활동, 제품의 인터랙션은 각각의 매체에서 실제로 작동해야 한다.

## 공통 작업 순서

1. **근거 선택** — Genesis v1.0에서 이번 MVP가 사용할 사건과 원칙을 고른다.
2. **매체 번역** — 서사, 학습 경험 또는 인터랙션으로 바꾼다.
3. **첫 MVP** — 완성본이 아닌 검증 가능한 첫 결과를 만든다.
4. **실제 사용** — 독자, 학습자 또는 사용자에게 적용한다.
5. **차이 기록** — 의도와 실제 반응이 어긋난 지점을 남긴다.
6. **계속·수정·중단 판단** — 근거와 함께 다음 투자를 결정한다.

## 공통으로 지키는 경계

- 세 트랙을 동시에 시작하되 한 트랙의 성공 기준을 다른 트랙에 강요하지 않는다.
- ORBIT를 단순한 프롬프트 기술, AI 예찬 또는 인간 우위의 주장으로 축소하지 않는다.
- 첫 MVP를 완성본이나 시장 검증으로 부르지 않는다.
- 외부 독자·학습자·사용자의 반응을 얻기 전에는 내부 완성도를 효과로 착각하지 않는다.
- Genesis v1.0의 빈자리를 확장 콘텐츠에서 그럴듯한 사실로 채우지 않는다.

## 현재 산출물

[세 트랙 구현 비교표](COMPARISON.md)에서 같은 원칙이 서사·학습 경험·제품 인터랙션으로 어떻게 달라지는지 볼 수 있다.

실제 검증 결과는 공통 [Expansion Validation Record](../templates/Expansion_Validation_Record.md) 형식으로 남긴다.

| 트랙 | 방향 문서 | 첫 MVP | 현재 상태 |
|---|---|---|:---:|
| 책 | [`book/BOOK_TRACK.md`](book/BOOK_TRACK.md) | [`book/drafts/Chapter_01_First_Result_Is_Not_The_End_v0.1.md`](book/drafts/Chapter_01_First_Result_Is_Not_The_End_v0.1.md) | MVP READY |
| 교육 | [`education/EDUCATION_TRACK.md`](education/EDUCATION_TRACK.md) | [`education/modules/M01_First_Output_Is_Not_The_End.md`](education/modules/M01_First_Output_Is_Not_The_End.md) | MVP READY |
| 제품 | [`product/PRODUCT_TRACK.md`](product/PRODUCT_TRACK.md) | [`product/MVP_SPEC.md`](product/MVP_SPEC.md) | SPEC READY |

## 공통 비교 기준

각 MVP는 다음 질문으로 비교한다.

1. 사용자가 ‘첫 결과는 끝이 아니다’를 자신의 말이나 행동으로 설명할 수 있는가?
2. 목표·경계·완료 조건을 결과 이전보다 명확하게 표현하게 되는가?
3. LLM의 반론과 사용자의 판단권을 함께 보존하는가?
4. 선택의 이유와 남은 차이를 다시 사용할 수 있는 기록으로 남기는가?
5. 사용 과정의 부담이 얻는 가치보다 크지 않은가?

## 다음 검증

- 책: 샘플 1장을 실제 독자 3명 이상에게 읽히고 이해·공감·행동 변화 질문을 수집한다.
- 교육: 3차시 중 1차시를 소규모로 적용하고 학생 산출물과 교사 관찰을 기록한다.
- 제품: 종이 또는 클릭 프로토타입으로 전체 흐름을 3회 이상 수행하고 불필요한 입력을 제거한다.

검증 전까지 세 트랙은 `DISCOVERY / MVP` 상태이며, 출판·정규 교육과정·소프트웨어 개발 착수는 각각 별도의 다음 결정으로 남긴다.
