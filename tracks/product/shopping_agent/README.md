# 쇼핑 판단 상세 시제품

쇼핑에 한정한 로그인 없는 로컬 합성 체험이다. 메인페이지보다 먼저 한 구매 판단의 상세 화면을 검증한다. Python 3.12 이상이 필요하다.

```bash
python3 tracks/product/shopping_agent/server.py
```

브라우저에서 **http://127.0.0.1:8766**을 연다. 이 방식은 서버의 SQLite에 대화를 저장할 때만 필요하다. 설치 스크립트와 외부 패키지는 필요하지 않다.

**휴대폰 미리보기에는 Python이 필요 없다.** [단일 HTML](index.html)을 정적 웹 호스팅으로 열면 선택·대화 수정·새로고침이 브라우저 저장소에서 작동한다. 저장소의 GitHub Pages 배포에는 `/shopping-preview/` 경로를 추가했다. 변경이 기본 브랜치에 반영되고 Pages 배포가 완료되면 `https://boundaryx01-uniquelife.github.io/orbit-philosophy/shopping-preview/`에서 볼 수 있다. 배포 전 작업 브랜치의 파일은 공개 HTML 미리보기 서비스로 확인할 수 있으나, 외부 서비스에서는 **합성 내용만** 입력한다.

| 환경 변수 | 기본값 | 용도 |
|---|---|---|
| `SHOPPING_DEMO_PORT` | `8766` | 로컬 서버 포트 |
| `SHOPPING_DEMO_DB` | `tracks/product/shopping_agent/data/shopping.sqlite3` | 로컬 SQLite 파일 |

처음 실행하면 가상의 손목 기기와 보호 액세서리 두 후보가 만들어진다. **측면·모서리 보호** 또는 **얇은 착용감**을 선택하면 그 발화가 이번 구매 건의 판단 조건이 된다. 자유 입력은 대화 원문으로 저장되지만 현재 버전은 그 의미를 자동 추출하지 않는다. 발화를 수정·삭제하면 현재 조건과 비교 판단을 다시 계산한다. 수정 전 내용은 그 발화의 수정 이력에서 볼 수 있고, 발화를 삭제하면 수정 이력도 삭제된다. 제안 반응, 실제 구매, 사용 뒤 체감은 별도 필드다.

서버 모드의 저장 위치는 서버의 SQLite 파일이다. 같은 로컬 서버를 보는 브라우저 창은 한 합성 사례를 공유한다. 정적 미리보기의 저장 위치는 **그 브라우저의 localStorage**이며 다른 기기와 공유되지 않는다. 브라우저 사이트 데이터를 지우면 사라진다. **계정 분리나 기기 간 실사용 동기화는 아직 없다.** 서버는 루프백 주소에서만 수신한다. 실제 개인정보, 구매 기록, 스크린샷, 결제 정보를 입력하지 않는다. 서버 로그에는 대화 내용을 남기지 않으며 DB 파일은 Git에서 제외한다. 서버 시제품의 자료를 초기화하려면 서버를 중지하고 로컬 DB 파일을 삭제한다.

이 버전에는 판매처 수집, 실시간 가격·배송·반품 확인, 자유 문장에서 조건 추출, 외부 AI, 실제 상품 추천이 없다. 가격과 상품은 전부 합성 예시다. 실자료 업로드나 서비스 배포 전에는 인증, 사용자별 접근 제어, 백업·삭제 정책, 상품 정보 출처, HTTPS를 별도로 구현·검토해야 한다.

## 검증

```bash
python3 -m unittest tracks.product.shopping_agent.test_flow -v
node tracks/product/shopping_agent/test_ui.cjs
```

첫 검사는 대화 저장·수정·삭제, 출처 연결, 재시작 후 복구, 반응 상태 분리, 외부 Origin 쓰기 차단을 확인한다. 두 번째 검사는 설치된 Playwright와 Chromium으로 390px·768px·1280px 화면과 서버 API 없는 정적 미리보기의 새로고침 복구를 확인한다.

설계와 아직 남은 판단은 [쇼핑 에이전트 첫 상세 구조](../SHOPPING_AGENT_FIRST_DETAIL.md)에, 시제품 기술 선택은 [ADR-0002](../../../decisions/ADR-0002_Shopping_Conversation_Detail_Prototype.md)에 적었다.
