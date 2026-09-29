# Book Format Matrix

> Version: v0.1
> Updated: 2026-09-29
> Principle: 원고는 하나로 관리하고, 읽는 환경에 맞게 표현만 달리한다.

## 현재 세 판본

| 형식 | 가장 알맞은 사용 | 장점 | 현재 한계 | 산출물 |
|---|---|---|---|---|
| EPUB 3 | 전자책 앱·리더기에서 오래 읽기 | 글자 크기와 화면 폭에 따라 본문이 자연스럽게 흐름 | 기기별 글꼴·표지 표현 차이를 실제 앱에서 더 확인해야 함 | [`epub/dist/First_Answer_Is_Not_The_End_v0.1.epub`](epub/dist/First_Answer_Is_Not_The_End_v0.1.epub) |
| 반응형 웹 | PC·휴대전화 브라우저에서 즉시 읽고 공유하기 | 설치 없이 열 수 있고 화면 폭에 따라 목차와 본문이 재배치됨 | 아직 공개 URL로 배포하지 않은 단일 HTML 파일임 | [`web/dist/First_Answer_Is_Not_The_End_v0.1.html`](web/dist/First_Answer_Is_Not_The_End_v0.1.html) |
| A5 PDF | 인쇄, 고정된 지면 검토, 파일 배포 | 표지·여백·줄바꿈·페이지 번호가 항상 동일함 | 출판 인쇄용 도련·재단선·색상 규격은 아직 적용하지 않음 | [`../../output/pdf/First_Answer_Is_Not_The_End_v0.1.pdf`](../../output/pdf/First_Answer_Is_Not_The_End_v0.1.pdf) |

## 하나의 원고를 유지하는 이유

세 판본을 각각 수정하면 같은 문장이 서로 다른 상태로 남는다. 현재는 다음 자료를 공통 근거로 사용한다.

- 전체 구성과 안내: `tracks/book/epub/src/frontmatter.md`
- 제1장 원고: `tracks/book/drafts/Chapter_01_First_Result_Is_Not_The_End_v0.1.md`
- 메타데이터: `tracks/book/epub/src/metadata.yaml`
- 표지·삽화: `tracks/book/assets/`

각 빌드는 공통 원고를 읽되 매체별 표현만 담당한다.

- EPUB은 가변형 본문과 전자책 목차를 만든다.
- 웹은 반응형 목차, 읽기 진행 표시와 단일 HTML 패키징을 맡는다.
- PDF는 A5 고정 지면, 글꼴 임베딩, 책갈피와 쪽 번호를 맡는다.

## 현재 검증 상태

- EPUB: MIME·ZIP·XML·목차·이미지 포함 검사 통과
- 웹: UTF-8·모바일 viewport·목차·대체 텍스트·외부 의존성 없음 확인
- PDF: 8쪽 전 페이지 PNG 렌더링 검토, 한글 글꼴 임베딩·텍스트 추출·메타데이터 확인

세 형식 모두 제작 검사는 통과했지만, 실제 독자의 이해와 사용성은 아직 검증하지 않았다.

## 다시 만들기

저장소 루트에서 실행한다.

```bash
./tracks/book/epub/build.sh
./tracks/book/web/build.sh
./tracks/book/pdf/build.sh
```

