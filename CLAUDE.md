# Clickary - 프로젝트 컨텍스트

## 프로젝트 개요
Clickary는 단축키 한 번으로 화면/파일/텍스트를 프로젝트별로 자동 저장하고,
AI가 바로 이해할 수 있는 Markdown 인수인계 문서를 자동 생성하는 데스크톱 도구.

## 기술 스택
- Python 3.11+
- PyQt6 (GUI, 시스템 트레이, 글로벌 단축키)
- Pillow (스크린샷 캡처)
- 100% 로컬 저장 (클라우드 전송 없음)

## 디렉토리 구조
```
clickary/
├── CLAUDE.md              ← 이 파일 (매 세션마다 읽기)
├── prd.json               ← 태스크 목록 (진행 상태 추적)
├── progress.txt           ← 완료된 태스크 로그
├── ralph.sh               ← 랄프 루프 스크립트
├── src/
│   ├── main.py            ← 앱 엔트리포인트
│   ├── capture.py         ← 스크린샷/파일/텍스트 캡처 로직
│   ├── project_manager.py ← 프로젝트 CRUD, 분류
│   ├── md_generator.py    ← AI용 Markdown 문서 자동 생성
│   ├── hotkey.py          ← 글로벌 단축키 (Win+Shift+A)
│   ├── tray.py            ← 시스템 트레이 아이콘/메뉴
│   └── ui/
│       ├── capture_dialog.py   ← 캡처 시 프로젝트 선택 다이얼로그
│       └── project_list.py     ← 프로젝트 목록/관리 윈도우
├── data/                  ← 프로젝트 데이터 저장 루트
│   └── {project_name}/
│       ├── captures/      ← 스크린샷, 파일 복사본
│       ├── notes/         ← 텍스트 메모
│       └── context.md     ← AI용 자동 생성 문서
├── tests/
│   ├── test_capture.py
│   ├── test_project_manager.py
│   └── test_md_generator.py
└── requirements.txt
```

## 에이전트 규칙 (중요!)

### 작업 흐름
1. 이 파일(CLAUDE.md)을 먼저 읽는다
2. prd.json에서 status가 "pending"인 첫 번째 태스크를 찾는다
3. 해당 태스크를 구현한다
4. 테스트를 작성하고 `pytest`로 통과시킨다
5. prd.json에서 해당 태스크 status를 "done"으로 변경한다
6. progress.txt에 완료 내역을 기록한다
7. `git add . && git commit -m "feat: {태스크 설명}"` 커밋한다
8. 모든 태스크가 done이면 DONE 파일을 생성한다

### 코딩 규칙
- 파일당 200줄 이하로 유지
- 함수에 docstring 필수
- 타입 힌트 사용
- 에러 핸들링 빠짐없이
- print 대신 logging 사용
- 기존 코드가 있으면 그 스타일을 따른다

### 테스트 규칙
- 각 모듈에 대응하는 test 파일 작성
- GUI 테스트는 불필요 (로직만 테스트)
- `pytest tests/` 로 전체 테스트 실행
- 테스트 실패 시 코드를 수정하고 다시 실행 (통과할 때까지)

### 커밋 컨벤션
- feat: 새 기능
- fix: 버그 수정
- test: 테스트 추가/수정
- refactor: 리팩토링
- docs: 문서 수정
