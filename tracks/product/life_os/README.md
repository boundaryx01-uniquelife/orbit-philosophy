# Life OS 첫 작동 흐름

이슈 #1의 첫 세로 흐름을 합성 사례로 실행하는 로컬 웹 앱이다. 질문만으로 시작하고, 출처·시점이 붙은 근거, 관찰·추론, 제약, 이유가 있는 질문/제안 하나, 의사 표현·실행·체감을 별도로 기록한다. 같은 서버에 로그인한 다른 세션에서 이전 이야기를 다시 읽고 수정·삭제할 수 있다. 철회된 입력 깔때기 MVP는 사용하지 않는다.

## 로컬 실행

Python 3.12 이상만 필요하다. 저장소 루트에서:

```sh
python3 tracks/product/life_os/server.py
```

브라우저에서 `http://127.0.0.1:8765`를 열어 합성 계정을 만들고 질문을 적는다. 기본 DB는 `tracks/product/life_os/data/life_os.sqlite3`이며 Git에서 무시한다. 계정과 자료는 서버 재시작 뒤에도 남는다. 실제 개인 자료는 이 실험에 입력하지 않는다.

| 변수 | 기본값 | 용도 |
|---|---|---|
| `LIFE_OS_DB` | `tracks/product/life_os/data/life_os.sqlite3` | SQLite 파일 경로 |
| `LIFE_OS_HOST` | `127.0.0.1` | 수신 주소 |
| `LIFE_OS_PORT` | `8765` | 수신 포트 |
| `LIFE_OS_ORIGIN` | `http://127.0.0.1:8765` | 변경 요청을 허용할 정확한 브라우저 Origin. HTTPS면 Secure 쿠키 사용 |

같은 계정의 여러 브라우저 세션은 같은 서버의 SQLite DB를 읽는다. 화면은 5초마다 재조회하며, 저장이 완료된 응답을 받은 뒤 현재 화면을 갱신한다. 서버 접속 또는 저장 오류가 나면 입력을 지우지 않고 오류를 보인다. 휴대폰과 PC에서 실제로 접속하려면 두 기기가 **같은 서버**에 닿아야 한다. 로컬 서버를 인터넷에 직접 노출하지 않는다. 공개 운영에는 HTTPS, 계정 운영, 백업·복구, 보존·삭제 정책을 별도로 검토해야 한다.

## 합성 검증

```sh
python -m pip install jsonschema==4.26.0
python tracks/product/life_os/model/validate_first_flow.py
python3 -m unittest discover -s tracks/product/life_os -p 'test_flow.py' -v
node --check tracks/product/life_os/static/app.js
node tracks/product/life_os/test_ui.cjs
```

API 테스트는 임시 DB와 무작위 합성 계정만 사용한다. 다른 계정의 사례·첨부 접근 거부, 한 계정의 두 세션에서 반응 수정·삭제 전파, 서버 재시작 뒤 복구, 시점이 다른 합성 신체 자료의 불확실성을 검사한다. UI 테스트는 Playwright와 Chromium이 설치된 환경에서 휴대폰 390px·태블릿 768px·PC 1280px를 검사한다. 저장 요청이 실패할 때 질문 입력을 보존하는지도 확인한다. UI 도구가 없으면 API 테스트를 별도로 실행할 수 있다.

`model/first_flow.schema.json`은 공개 합성 사례의 개념 모델이다. 현재 로컬 API는 일부 이름을 단순화한다(`observation`↔`observed`, `considering`↔`consider`, `execution_status`↔`did_act`). 두 형식의 의미는 같지만 파일을 그대로 DB에 가져오는 기능은 없다. 실제 저장소를 바꿀 때는 이 매핑을 명시적으로 구현하고 검증해야 한다.

## 자료와 기능 경계

- 코드·fixture·테스트와 PR에는 합성 자료만 둔다. 실제 건강 자료, 스크린샷, 식별 정보, 비밀번호 또는 운영 비밀 값을 Git·이슈·PR에 넣지 않는다.
- 질문·근거·첨부·반응은 선택한 서버의 SQLite DB에 저장된다. 첨부는 PNG·JPEG·PDF·텍스트, 최대 2MB이며 자동 분석하지 않는다. 사례를 삭제하면 관련 자료와 반응도 함께 삭제된다. 계정 자체 삭제 기능은 아직 없다.
- 제안은 외부 AI가 아닌 제한된 규칙으로 생성된다. 의료 진단, 수치 변화의 원인 추정, 고정 운동 루틴, 행동 자동 실행은 제공하지 않는다. “고려해 볼게”를 선택해도 실행과 체감은 `unknown`으로 남는다.
- 현재 계정·세션 구현은 로컬 검증용이다. 비밀번호 재설정, 이메일 확인, 로그인 속도 제한, 운영 감사, 백업·복구, 실자료 사용의 동의·보존 정책은 구현되지 않았다. 따라서 실자료 업로드와 서비스 배포는 별도 검토 대상이다.

첫 구현의 기술 선택과 이후 운영 조건은 [ADR-0001](../../../decisions/ADR-0001_Life_OS_First_Vertical_Slice.md)에 기록한다.
