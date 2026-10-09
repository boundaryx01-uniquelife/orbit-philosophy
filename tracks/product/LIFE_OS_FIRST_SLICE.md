# Life OS 첫 세로 흐름 — 문서 확인과 화면 교정

> 상태: 로그인 없는 챗 시제품 / 사용자 경험 확인 전
> 기준: [이슈 #1](https://github.com/boundaryx01-uniquelife/orbit-philosophy/issues/1), 2026-10-09
> 사례: 모두 합성. 실제 건강 자료와 비밀 값은 사용하지 않는다.

## 확인한 문서

| 자료 | 현재 적용 |
|---|---|
| [공개 Genesis](../../genesis/GENESIS_PUBLIC_TRANSCRIPT.md), [C0000](../../genesis/C0000_GENESIS.md) | 사용자의 상태와 현실 제약을 보고, 근거와 판단 이유를 남기며 최종 판단을 사용자에게 둔다 |
| [Life OS handoff](LIFE_OS_HANDOFF.md) | 공개 Genesis는 편집본이며 구체적인 첫 사용 경험은 별도 확인이 필요하다 |
| [CR-0030](../../decisions/CR-0030_Withdraw_Input_Form_Prototype.md) | 과거 입력형 시험본은 철회됐다 |
| [CR-0031](../../decisions/CR-0031_Keep_Life_OS_Chat_First_Without_Login.md) | 이번에도 설문식 화면과 로그인을 앞당긴 오류를 교정했다 |
| [이슈 #1](https://github.com/boundaryx01-uniquelife/orbit-philosophy/issues/1) | 질문 우선, 근거 부족 설명, 제안 하나, 의사 표현·실행·체감 분리를 첫 챗에서 검증한다 |

## 철회된 가설과 이번 교정

[PRODUCT_TRACK.md](PRODUCT_TRACK.md)와 [MVP_SPEC.md](MVP_SPEC.md)의 `Brief → Mirror → Funnel → Decision → Checkpoint`는 **철회된 AI 가설**이다. 이슈의 데이터 개념을 각각의 입력 양식으로 노출했던 첫 구현도 같은 실패를 반복했다. 사용자가 다시 명시한 순서는 **챗 경험 먼저, 로그인은 완성 이후**다.

## 현재 첫 화면

[로그인 없는 챗 시제품](life_os/README.md)을 열면 바로 질문을 적을 수 있다. InBody, 계정, 설문 단계가 필요 없다. 답변은 현재 확인된 것, 아직 모르는 것, 이유가 있는 질문 또는 제안 **하나**를 대화 안에 보여 준다. 합성 기본 사례는 “퇴근하면 저녁을 챙길 여유가 없어요. 무엇부터 살펴볼까요?”다. 비교 사례는 다른 시점의 신체 구성 기록과 불완전한 운동 메모를 보여 주되 원인을 단정하지 않는다.

반응 버튼의 “고려해 볼게”는 실행이나 효과로 바꾸지 않는다. 이어 말하기와 이전 이야기는 현재 탭 안에서만 동작한다. 새로고침하면 입력이 사라지고 서버에는 기록되지 않는다. 파일 업로드, 계정 분리, 동기화, 외부 AI 해석은 아직 제공하지 않는다.

## 다음 판단

이 챗 화면이 사용자가 원한 Life OS의 시작점인지 확인한다. 그 후 근거 해석의 실제 동작과 파일·계정·저장·삭제·동기화 경계를 차례로 설계한다. [ADR-0001](../../decisions/ADR-0001_Life_OS_First_Vertical_Slice.md)에 현재 기술 선택과 재검토 조건을 기록했다.
