# Life OS 첫 작동 흐름

질문 하나로 시작하는 로컬 실험이다. InBody 없이 시작하고, 출처와 시점을 둔 근거, 관찰·추론, 제약, 조심스러운 질문/제안 하나, 반응·실행·체감을 별도로 기록한다. 이전 이야기는 같은 계정의 다른 세션에서 다시 읽고 수정·삭제할 수 있다. 구현 선택은 [ADR-0001](../../../decisions/ADR-0001_Life_OS_First_Vertical_Slice.md)에 적었다. 철회된 입력 깔때기 MVP는 사용하지 않는다.

## 로컬 실행

Python 3.12 이상만 필요하다. 저장소 루트에서:

```bash
python3 tracks/product/life_os/server.py
```

브라우저에서 `http://127.0.0.1:8765`를 연다. 새 계정을 만들고 질문을 적는다. 기본 DB는 `tracks/product/life_os/data/life_os.sqlite3`이며 Git에서 무시한다. 계정과 자료는 서버 재시작 뒤에도 남는다. 처음 실행 전에 DB 위치를 바꾸려면 다음 환경 변수를 지정할 수 있다.

| 변수 | 기본값 | 용도 |
|---|---|---|
| `LIFE_OS_DB` | `tracks/product/life_os/data/life_os.sqlite3` | SQLite 파일의 절대 또는 상대 경로 |
| `LIFE_OS_HOST` | `127.0.0.1` | 수신 주소 |
| `LIFE_OS_PORT` | `8765` | 수신 포트 |
| `LIFE_OS_ORIGIN` | `http://127.0.0.1:8765` | 변경 요청에 허용할 정확한 브라우저 Origin. HTTPS면 Secure 쿠키 사용 |

공개 서비스 배포는 현재 범위 밖이다. 여러 기기에서 쓰려면 모두 **같은 서버**에 접속해야 하며, 실제 네트워크 운영 전 HTTPS와 운영 인증·백업·삭제 정책을 갖춰야 한다. 로컬 서버를 인터넷에 직접 노출하지 않는다. `LIFE_OS_ORIGIN`을 설정한 HTTPS 역방향 프록시 뒤에 두는 방식은 설계 경계일 뿐 아직 운영 검증을 하지 않았다.

## 검증

```bash
python3 -m unittest tracks.product.life_os.test_flow -v
node --check tracks/product/life_os/static/app.js
node tracks/product/life_os/test_ui.cjs
```

통합 검사는 [합성 사례](fixtures/synthetic_scenarios.json)만 사용한다. 두 세션의 반응 수정·삭제 전파, 다른 계정의 접근 차단, 서버 재시작 뒤 복구, 첨부 접근 분리, 자료 재분류, 두 시점 측정의 불확실성을 확인한다. UI 검사는 설치된 Node.js·Playwright·Chromium을 사용해 휴대폰 390px·태블릿 768px·PC 1280px를 확인한다. 브라우저 도구가 없는 환경에서는 API 검사를 별도로 실행할 수 있다.

## 자료 취급과 현재 경계

- 공개 코드·fixture·테스트에는 합성 자료만 둔다. 실제 건강 자료, 스크린샷, 식별 정보, 비밀번호와 운영 비밀 값은 Git·이슈·PR에 넣지 않는다.
- 질문·근거·첨부·반응은 선택한 서버의 SQLite DB에 저장된다. 첨부는 PNG·JPEG·PDF·텍스트, 최대 2MB이며 자동 분석하지 않는다. 사례 삭제는 그 사례의 자료와 반응을 함께 삭제한다. 계정과 전체 계정 삭제 기능은 아직 없다.
- 제안은 외부 AI가 아니라 코드의 제한된 규칙으로 생성된다. 의료 진단, 원인 추정, 연속 운동 루틴, 행동 자동 실행은 제공하지 않는다. `고려해 볼게`는 실행 여부 `아직 모름`, 체감 결과 빈 값과 별도로 남는다.
- 현지 개발용 계정·세션 구현이며 비밀번호 재설정, 계정 삭제, 이메일 확인, 로그인 속도 제한, 운영 감사, 백업·복구, 실자료 사용에 대한 동의·보존 정책은 구현되지 않았다. 따라서 실자료 업로드와 실제 서비스 배포는 별도 검토가 필요하다.

## 검토 단위

1. Genesis·Life OS 원안과 철회 기록 확인, 기술 선택 ADR
2. 계정별 Case·Evidence·Claim·Preference/Constraint·Proposal·Feedback·Chronicle 모델과 합성 사례
3. 질문 시작과 자료 부족 시 이유를 설명하는 추가 질문
4. 제안 카드와 분리된 반응·실행·체감 상태
5. 이전 이야기, 질문·반응 수정 및 사례·자료·반응 삭제
6. 계정 분리, 저장·재접속, 두 세션 동기화
7. 세 화면 폭 검증과 통합 검사

각 단위의 실행 결과와 남은 제약은 PR 설명에 요약한다.
