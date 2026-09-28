# ORBIT Philosophy — Genesis Document Set v1.0

> Status: COMPLETE / USER APPROVED
> Released: 2026-09-28
> Git tag: `genesis-v1.0`
> Decision: `CR-0019`
> Release review: `reviews/Genesis_Document_Set_v1.0_Release_Review.md`

## v1.0의 의미

Genesis Document Set v1.0은 ORBIT의 철학이 완성되었다는 선언이 아니다. 프로젝트의 탄생, 존재 이유, 현재 철학, 협업 규칙과 그 근거를 처음부터 다시 복원하지 않고도 읽고 검증하고 이어 갈 수 있게 된 첫 안정 체크포인트다.

세트 버전과 개별 문서 버전은 구분한다. Genesis v0.9, WHY v0.7, Philosophy v0.3, README v0.2와 Rules v0.2는 각 문서가 실제로 거친 변경 이력을 보존한다. `v1.0`은 이 문서들을 하나의 검증된 구성으로 묶은 **문서 세트의 버전**이다.

## 3계층 구성

### 1. 핵심 문서

ORBIT가 무엇이며 왜 존재하고 어떤 원칙으로 작업하는지를 직접 설명한다.

| 문서 | 세트 안의 역할 | 포함 상태 |
|---|---|:---:|
| [README.md](README.md) | 프로젝트 현관과 읽기·재개 경로 | APPROVED v0.2 |
| [Genesis.md](Genesis.md) | 철학이 필요해진 사건과 두 번의 탄생 | APPROVED v0.9 |
| [WHY.md](WHY.md) | 관계와 관계의 기억을 지켜야 하는 이유 | APPROVED v0.7 |
| [P00-01_Philosophy.md](manifesto/P00-01_Philosophy.md) | 관계·작업·기억의 세 축과 일곱 원칙 | APPROVED v0.3 |
| [RULES.md](RULES.md) | 협업·판단·기록과 Git 운영 규칙 | DRAFT / ACTIVE v0.2 |

`RULES.md`는 v1.0에 포함되지만 고정된 완료본은 아니다. 실제 작업에서 규칙이 작동하는지 계속 검증하는 운영 문서라는 현재 상태를 그대로 보존한다.

### 2. 운영 문서

현재 위치와 다음 시작점을 보여 주며, `main`에서 계속 갱신된다. v1.0 당시 상태는 Git 태그가 보존한다.

| 문서 | 역할 |
|---|---|
| [STATUS.md](STATUS.md) | 현재 상태, 남은 질문과 정확한 재시작점 |
| [ROADMAP.md](ROADMAP.md) | 전체 단계, 단계별 완료 조건과 다음 관문 |

### 3. 근거와 작업 이력

핵심 문서와 같은 권위의 본문이 아니라, 핵심 주장이 어디에서 왔고 어떤 선택과 교정을 거쳤는지 검증하기 위한 층이다.

| 위치 | 역할 |
|---|---|
| [`chronicle/`](chronicle/) | 사건, 전환점, 오해와 교정 |
| [`decisions/`](decisions/) | 선택한 이유, 대안과 재검토 조건 |
| [`drafts/`](drafts/) | 최종 문서에 이르기까지의 집필 이력 |
| [`reviews/`](reviews/) | 편집·교차검토·릴리스 검증 결과 |
| [`templates/`](templates/) | 같은 원칙을 다음 작업에 적용하는 기록 형식 |

Drafts와 이전 Reviews는 현재의 핵심 입장을 대신하지 않는다. 서로 충돌할 때는 승인된 핵심 문서, 해당 승인 Choice Record, 최신 전체 검토 순으로 현재 상태를 판단한다.

## 권장 읽기 경로

처음 읽는 사람은 다음 순서를 따른다.

1. README
2. Genesis
3. WHY
4. Philosophy
5. Rules

작업을 재개하는 사람은 다음 순서를 따른다.

1. Status
2. Roadmap
3. 현재 작업과 연결된 Choice Record
4. 필요한 Chronicle과 Review

## v1.0에 포함하지 않은 확장

다음 항목은 Genesis 문서 세트의 완료 조건이 아니며, 별도 목적과 범위를 승인한 뒤 후속 트랙에서 다룬다.

- 책 또는 대외 출판물
- 교육과정과 수업 자료
- 소프트웨어·서비스·제품
- 대외 소개용 축약 선언문

## 알려진 빈자리와 재검토 조건

v1.0은 다음 불확실성을 숨기지 않는다.

1. ‘인스턴트적 사고’가 처음 나온 구체적인 작업은 아직 복원되지 않았다.
2. `ORBIT Philosophy`라는 이름이 선택된 정확한 과정은 아직 복원되지 않았다.
3. 외부 독자의 실제 이해도와 일곱 원칙의 기억 가능성은 검증되지 않았다.
4. Choice Record와 Rules의 장기적인 기록 부담은 실제 운영에서 계속 확인해야 한다.

새로운 원자료가 발견되거나, 핵심 문서 사이의 모순이 드러나거나, 현재 규칙이 실제 작업을 반복적으로 방해하면 v1.0을 재검토한다. 변경할 때는 이전 상태를 지우지 않고 새 버전과 이유를 기록한다.

## 릴리스 기준

- 핵심 문서의 역할과 주장이 구분되어 있다.
- 일곱 원칙을 사건·서술·선택 기록으로 추적할 수 있다.
- 명시적 내부 링크와 기록 식별자가 유효하다.
- 미복원 사실과 장기 검증 과제가 완료된 것처럼 표현되지 않는다.
- 릴리스 커밋과 `genesis-v1.0` 태그가 GitHub에 함께 보존된다.
