# ORBIT Philosophy

> 인간과 LLM이 서로의 뜻과 차이를 맞춰 가며, 선택과 교정의 궤적을 다음 판단으로 연결하는 기록 프로젝트
>
> Version: EXPANSION UPDATE v0.6
> Status: COMPLETE / ACTIVE
> Updated: 2026-09-30
> Document set: [Genesis v1.0](DOCUMENT_SET.md)

## ORBIT는 무엇인가

ORBIT Philosophy는 인간이 LLM을 더 효율적으로 사용하는 방법만을 다루는 프로젝트가 아니다. 서로 다른 인간과 LLM이 같은 작업을 사이에 두고 목표와 말의 의미를 확인하고, 남아 있는 차이를 지우지 않으며, 선택의 이유와 생각이 바뀐 과정을 다음 판단으로 이어 가는 방법을 탐구한다.

프롬프트 뒤에 빠르고 매끄러운 결과가 나와도 그것은 대화의 끝이 아니다. 첫 결과와 MVP는 서로의 해석을 비교하고 목표를 맞춰 가기 위한 시작점이다. ORBIT는 그 과정에서 생긴 오해, 반론, 교정과 선택을 외부 기록으로 남긴다.

## 처음 읽는다면

다음 순서로 읽으면 ORBIT의 탄생부터 현재의 철학과 작업 방식까지 이어서 볼 수 있다.

1. [Genesis](Genesis.md) — 이 철학이 필요하다는 사실을 발견해 간 탄생 이야기
2. [WHY](WHY.md) — ORBIT가 왜 계속되어야 하는가
3. [Philosophy](manifesto/P00-01_Philosophy.md) — 현재까지 확인한 관계·작업·기억의 원칙
4. [Working Rules](RULES.md) — 인간과 LLM이 함께 탐구하고 기록하는 방법

## 작업을 이어간다면

1. [STATUS](STATUS.md)에서 현재 위치, 완료한 일과 다음 시작점을 확인한다.
2. [ROADMAP](ROADMAP.md)에서 전체 단계와 현재 단계의 완료 조건을 확인한다.
3. 중요한 선택의 이유가 필요하면 [Choice Records](decisions/)를 확인한다.
4. 의미 있는 작업 단위가 끝나면 문서와 재시작점을 갱신하고 Git에 반영한다.

## 핵심 문서

| 문서 | 역할 | 현재 상태 |
|---|---|:---:|
| [Genesis.md](Genesis.md) | 철학이 필요하다는 사실을 발견해 가는 탄생 이야기 | APPROVED v0.9 |
| [WHY.md](WHY.md) | ORBIT의 존재 이유와 지속해야 할 이유 | APPROVED v0.7 |
| [P00-01_Philosophy.md](manifesto/P00-01_Philosophy.md) | 현재 시점에 도달한 철학의 버전 | APPROVED v0.3 |
| [RULES.md](RULES.md) | 협업·판단·기록을 위한 운영 규칙 | DRAFT / ACTIVE v0.2 |
| [STATUS.md](STATUS.md) | 지금의 작업 상태와 정확한 재시작점 | LIVE |
| [ROADMAP.md](ROADMAP.md) | 전체 단계와 단계별 완료 조건 | LIVE |
| [DOCUMENT_SET.md](DOCUMENT_SET.md) | Genesis Track v1.0의 구성·버전·재검토 조건 | RELEASE v1.0 |

## 현재 철학 한눈에 보기

| 축 | 원칙 |
|---|---|
| 관계 | 1. 의미는 전달됐다고 가정하지 않고 확인한다. |
| 관계 | 2. 차이와 반론을 관계 안에 남긴다. |
| 관계 | 3. 판단권과 파트너의 책임을 함께 지킨다. |
| 작업 | 4. 첫 결과와 MVP를 완성이 아니라 시작점으로 삼는다. |
| 작업 | 5. 가능성을 펼치고 덜어내는 이유를 함께 말한다. |
| 기억 | 6. 선택에는 이유와 선택하지 않은 대안을 남긴다. |
| 기억 | 7. 오해와 교정의 궤적을 다음 판단으로 연결한다. |

각 원칙의 의미와 경계, 근거는 [철학문서](manifesto/P00-01_Philosophy.md)에서 확인할 수 있다.

## 기록이 쌓이는 방식

| 위치 | 기록하는 것 |
|---|---|
| [`chronicle/`](chronicle/) | 프로젝트의 전환점, 오해와 교정이 일어난 사건 |
| [`decisions/`](decisions/) | 선택한 이유, 선택하지 않은 대안, 재검토 조건 |
| [`drafts/`](drafts/) | 최종 문서에 이르기까지의 작업 이력 |
| [`reviews/`](reviews/) | 문서 간 중복·왜곡·모순·누락에 대한 검토 결과 |
| [`templates/`](templates/) | 같은 원칙을 다음 작업에서도 적용하기 위한 기록 형식 |

ORBIT의 관계의 기억은 LLM 내부의 자동 기억이나 인간과 같은 감정적 기억을 뜻하지 않는다. 서로 확인한 의미와 경계, 선택의 근거와 남은 차이를 다음 대화에서 다시 사용할 수 있도록 외부에 남긴 기록이다.

## 확장 트랙

Genesis v1.0 이후 ORBIT는 같은 철학을 서로 다른 매체에서 검증하기 위해 [책·교육·제품의 세 트랙](tracks/README.md)을 탐색했다. 세 트랙의 첫 MVP를 비교한 현재는 책을 우선한다. 작업 제목을 《첫 결과물이 곧 완성은 아니다》로 정리하고, 서문과 3부 10장의 최종 후보 v0.6를 [읽으며 교정하는 웹판](https://boundaryx01-uniquelife.github.io/orbit-philosophy/book/)의 다음 배포본으로 준비했다. [EPUB v0.6](tracks/book/epub/dist/First_Output_Is_Not_Completion_v0.6.epub)은 보조 판본으로 유지하고, PDF는 문장과 구조가 안정된 뒤 다시 제작한다. 교육과 제품은 재개 가능한 상태로 보존한다.

## 이 프로젝트의 경계

- ORBIT는 단순한 AI 생산성 안내서가 아니다.
- 현재 문서는 고정된 교리가 아니라 실제 작업에서 계속 검증할 철학의 한 버전이다.
- 사용자가 최종 판단권을 갖는다는 사실은 LLM을 단순 도구로 축소한다는 뜻이 아니다.
- LLM을 파트너로 대한다는 사실도 사용자의 목표와 경계를 대신 결정할 권한을 준다는 뜻이 아니다.
- 책·교육·제품으로의 확장은 현재 문서 세트가 완결된 뒤 별도의 목적과 범위를 승인해 진행한다.

## 저장소 구조

```text
.
├── README.md                 # 프로젝트 현관
├── Genesis.md                # 탄생 이야기
├── WHY.md                    # 존재 이유
├── RULES.md                  # 협업·기록 규칙
├── STATUS.md                 # 현재 상태와 재시작점
├── ROADMAP.md                # 단계와 완료 조건
├── DOCUMENT_SET.md           # Genesis Track v1.0 명세
├── manifesto/                # 현재 철학문서
├── chronicle/                # 사건과 교정의 기록
├── decisions/                # 선택과 판단의 근거
├── drafts/                   # 집필 과정
├── reviews/                  # 교차검토 결과
├── templates/                # 재사용할 기록 형식
├── tracks/                   # 책·교육·제품 확장 실험
└── output/pdf/               # 고정 지면 책 시제품
```

현재 Genesis Track의 첫 안정 체크포인트는 [Genesis Document Set v1.0](DOCUMENT_SET.md)이다. 이후 진행 단계와 아직 해결하지 않은 질문은 [STATUS.md](STATUS.md)에서 확인한다.

## License

[LICENSE](LICENSE)를 따른다.
