# Life OS 첫 흐름 데이터 모델 — 2단계

> 이슈 #1의 데이터 모델과 공개 가능한 합성 사례. 현재 챗 시제품은 로그인·DB 없이 탭 메모리에서만 동작한다.

`first_flow.schema.json`은 한 Case의 공개 검증 자료 형식을 정의한다. `../fixtures/first_flow.synthetic.json`에는 InBody 없이 질문으로 시작하는 사례와, 조건이 다른 두 신체 구성 기록·불완전한 운동 메모를 비교하는 사례가 있다. 모든 이름, 날짜, 수치는 합성이다.

| 개념 | 첫 흐름에서 맡는 역할 |
|---|---|
| Case | 대화의 첫 질문과 생성·변경 시점 |
| Evidence | 자료의 출처·기록 시점·관찰 시점·한계. 원본 파일을 포함하지 않음 |
| Claim | Evidence를 참조하는 관찰 또는 불확실성을 밝힌 추론 |
| Preference/Constraint | 사용자가 밝힌 선호 또는 제약과 그 출처. 영구적 성향으로 취급하지 않음 |
| Proposal | 관찰, 모르는 점, 제안 또는 추가 질문 **하나**, 판단 근거 |
| Feedback | 제안에 대한 의사 표현, 실제 실행, 뒤의 체감을 독립적으로 기록 |
| Chronicle | 생성·수정·삭제 사건의 식별자와 시점. 삭제된 본문을 복사해 보존하지 않음 |

`considering`은 의사 표현일 뿐이다. 합성 기본 사례의 `execution_status`와 `outcome_status`는 각각 `unknown`이며 실행·효과를 암시하지 않는다. 두 번째 사례는 수치 차이를 관찰하되 운동 효과나 원인을 추정하지 않는다.

검증 명령:

```sh
python -m pip install jsonschema==4.26.0
python tracks/product/life_os/model/validate_first_flow.py
```

검증기는 JSON Schema 형식과 사례 내부 참조, Case 경계를 확인한다. 현재 시제품은 로그인·동기화·서버 저장을 제공하지 않는다. 계정 기능을 나중에 추가한다면 인증된 계정별 읽기·쓰기·삭제와 자료 보존·삭제 정책을 먼저 설계하고 검증해야 한다. JSON Schema 자체는 접근 제어를 제공하지 않는다.
