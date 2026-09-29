# GitHub Pages Book Site

이 디렉터리는 EPUB·웹·PDF 시제품을 하나의 공개 진입점으로 묶는다.

## 로컬 빌드

저장소 루트에서 실행한다.

```bash
./tracks/book/site/build.sh
```

`dist/`에는 다음이 생성된다.

- `/index.html` — 세 판본 선택 화면
- `/book/index.html` — 반응형 웹북
- `/downloads/*.pdf` — A5 PDF
- `/downloads/*.epub` — EPUB 3

`main`에 관련 파일이 반영되면 `.github/workflows/deploy-pages.yml`이 같은 빌드를 실행하고 GitHub Pages에 배포한다.

