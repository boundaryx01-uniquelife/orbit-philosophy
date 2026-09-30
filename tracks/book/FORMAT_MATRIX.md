# Book Format Matrix

> Version: v0.4
> Updated: 2026-09-30
> Principle: 원고는 하나로 관리하고, 읽는 환경에 맞게 표현만 달리한다.

## 현재 운용 우선순위

| 형식 | 가장 알맞은 사용 | 장점 | 현재 한계 | 산출물 |
|---|---|---|---|---|
| 반응형 웹 | **현재 기본 검토본**. PC·휴대전화에서 읽으며 표현 교정하기 | 화면 폭에 따라 재배치되고, 교정본을 브라우저에 자동 저장해 Markdown으로 내보냄 | 기기 간 자동 동기화와 GitHub 직접 반영은 지원하지 않음 | [`web/dist/First_Output_Is_Not_Completion_v0.3.html`](web/dist/First_Output_Is_Not_Completion_v0.3.html) |
| EPUB 3 | 전자책 앱·리더기에서 오래 읽기 | 글자 크기와 화면 폭에 따라 본문이 자연스럽게 흐름 | 기기별 글꼴·표지 표현 차이를 실제 앱에서 더 확인해야 함 | [`epub/dist/First_Output_Is_Not_Completion_v0.3.epub`](epub/dist/First_Output_Is_Not_Completion_v0.3.epub) |
| A5 PDF | 원고 완성 뒤 인쇄·고정 지면 검토 | 표지·여백·줄바꿈·페이지 번호를 고정해 최종 조판을 확인할 수 있음 | **제작 일시 중단**. v0.3은 제작 검증 기록으로만 보존 | [`../../output/pdf/First_Output_Is_Not_Completion_v0.3.pdf`](../../output/pdf/First_Output_Is_Not_Completion_v0.3.pdf) |

## 하나의 원고를 유지하는 이유

세 판본을 각각 수정하면 같은 문장이 서로 다른 상태로 남는다. 현재는 다음 자료를 공통 근거로 사용한다.

- 전체 구성과 안내: `tracks/book/epub/src/frontmatter.md`
- 제1장 원고: `tracks/book/drafts/Chapter_01_First_Output_Is_Not_Completion_v0.2.md`
- 제2장 원고: `tracks/book/drafts/Chapter_02_When_Helpfulness_Loses_The_Goal_v0.1.md`
- 제3장 원고: `tracks/book/drafts/Chapter_03_Same_Words_Different_Meanings_v0.1.md`
- 메타데이터: `tracks/book/epub/src/metadata.yaml`
- 표지·삽화: `tracks/book/assets/`

각 빌드는 공통 원고를 읽되 매체별 표현만 담당한다.

- EPUB은 가변형 본문과 전자책 목차를 만든다.
- 웹은 반응형 목차, 읽기 진행 표시와 단일 HTML 패키징을 맡는다.
- PDF는 원고가 완성 단계에 들어간 뒤 A5 고정 지면, 글꼴 임베딩, 책갈피와 쪽 번호를 검증한다.

## 현재 검증 상태

- EPUB: MIME·ZIP·XML·목차·이미지 포함 검사 통과
- 웹: UTF-8·모바일 viewport·목차·대체 텍스트·외부 의존성 없음·교정 스크립트 구문 확인
- PDF: v0.3에서 전 페이지 이미지 렌더링, 한글 글꼴 임베딩·텍스트 추출·메타데이터 확인 완료. 이후 생성 일시 중단

세 형식의 제작 검사는 통과했지만, 현재 독자 교정은 웹판에 집중한다. PDF는 전체 원고의 구조와 문장이 완성 단계에 들어가고 고정 지면 검토가 실제로 필요해질 때 재개한다.

## 다시 만들기

저장소 루트에서 실행한다.

```bash
./tracks/book/epub/build.sh
./tracks/book/web/build.sh
```

`tracks/book/pdf/build.sh`는 최종 조판 단계까지 실행하지 않는다.
