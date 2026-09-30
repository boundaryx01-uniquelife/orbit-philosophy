# PDF Prototype

> Status: `PAUSED UNTIL MANUSCRIPT COMPLETION`

`output/pdf/First_Output_Is_Not_Completion_v0.3.pdf`은 화면 읽기와 소량 인쇄를 함께 고려한 A5 고정 지면 시제품이다.

현재 v0.3은 PDF 제작 파이프라인을 검증한 참고용 체크포인트다. 원고를 교정하는 동안에는 반응이 빠르고 직접 수정할 수 있는 웹판을 사용하며, PDF를 다시 생성하지 않는다.

## 다시 만드는 시점

전체 원고의 구조와 문장이 완성 단계에 들어가고, 고정 지면·인쇄·최종 조판 검토가 필요해질 때 이 빌드를 재개한다.

```bash
./tracks/book/pdf/build.sh
```

표지, 속표지, 전체 구성, 시각적 도입과 1부의 세 장을 담는다. Noto Sans KR 부분 글꼴을 PDF 안에 포함하며, 책갈피와 페이지 번호를 제공한다.

최종 출간용 PDF에서는 재단 여백, 도련, 인쇄소 색상 규격과 최종 저자 크레디트를 별도로 확정해야 한다.
