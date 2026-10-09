# Life OS 첫 흐름 데이터 모델 — 2단계

> 이슈 #1의 데이터 모델과 공개 가능한 합성 사례. 작동 화면, 인증, DB 스키마 또는 배포 설정은 아직 아니다.

`first_flow.schema.json`은 한 Case의 공개 검증 자료 형식을 정의한다. `../fixtures/first_flow.synthetic.json`에는 InBody 없이 질문으로 시작하는 사례와, 조건이 다른 두 신체 구성 기록·불완전한 운동 메모를 비교하는 사례가 있다. 모든 이름, 계정, 날짜, 수치는 합성이다.

| 개념 | 첫 흐름에서 맡는 역할 |
|---|---|
| Case | 사용자의 질문과 계정 소유자 |
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

검증기는 JSON Schema 형식과 사례 내부 참조, Case 경계, 합성 소유자 ID를 확인한다. 실제 저장 구현에서는 서버가 인증된 계정 ID를 부여하고 DB가 모든 읽기·쓰기·삭제에서 소유자를 검사해야 한다. JSON Schema 자체는 접근 제어를 제공하지 않는다. Case 삭제 시 관련 자료와 Chronicle도 삭제하고, 개별 삭제 사건에는 삭제된 본문을 남기지 않는 정책을 다음 단계에서 구현·검증한다.
