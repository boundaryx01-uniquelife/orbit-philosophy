# GitHub Pages Book Site

이 디렉터리는 웹판을 기본으로, EPUB 판본을 함께 제공하는 공개 진입점이다. PDF는 2단계 용어 체계화를 마치고 고정 지면 검토를 시작할 때까지 공개 빌드와 배포에서 제외한다.

## 로컬 빌드

저장소 루트에서 실행한다.

```bash
./tracks/book/site/build.sh
```

`dist/`에는 다음이 생성된다.

- `/index.html` — 웹 우선 읽기 화면
- `/book/index.html` — 반응형 웹북
- `/downloads/*.epub` — EPUB 3

`main`에 관련 파일이 반영되면 `.github/workflows/deploy-pages.yml`이 같은 빌드를 실행하고 GitHub Pages에 배포한다.
