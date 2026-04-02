# Clickary

> 딸깍 한 번에, 프로젝트는 기억된다.

단축키 한 번으로 화면/파일/텍스트를 프로젝트별로 자동 저장하고, AI가 바로 이해할 수 있는 Markdown 인수인계 문서를 자동 생성하는 데스크톱 도구.

---

## 왜 만들었나?

- 프로젝트 데이터가 이메일, 슬랙, 로컬 폴더에 산재
- 담당자 바뀌면 "이거 어디 있어요?" 반복
- AI 활용하려면 자료 찾기 → 복붙 → 맥락 설명에 시간 낭비
- **AI 쓰는 시간보다 AI한테 줄 자료 정리하는 시간이 더 길다**

## 핵심 기능

| 기능 | 설명 |
|------|------|
| 원클릭 캡처 | `Win+Shift+A` → 프로젝트 선택 → 2초 만에 저장 |
| 프로젝트별 자동 분류 | 토글 하나로 프로젝트 선택, 폴더 자동 정리 |
| AI 최적화 문서 생성 | LLM이 바로 이해하는 MD 포맷 자동 생성 |
| 100% 로컬 저장 | 데이터가 외부로 나가지 않음 |

## 사용 흐름

```
작업 중 중요한 화면 발견
  → Win+Shift+A
  → 프로젝트 선택
  → 캡처/파일/텍스트 선택
  → 자동 저장 + context.md 업데이트
  → AI에게 바로 전달 가능!
```

## 설치

```bash
# 1. 클론
git clone https://github.com/your-username/clickary.git
cd clickary

# 2. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 실행
python src/main.py
```

## 프로젝트 구조

```
clickary/
├── src/
│   ├── main.py              # 앱 엔트리포인트
│   ├── capture.py           # 스크린샷/파일/텍스트 캡처
│   ├── project_manager.py   # 프로젝트 CRUD
│   ├── md_generator.py      # AI용 Markdown 문서 생성
│   ├── hotkey.py            # 글로벌 단축키
│   ├── tray.py              # 시스템 트레이
│   └── ui/
│       ├── capture_dialog.py    # 캡처 다이얼로그
│       └── project_list.py      # 프로젝트 관리 윈도우
├── data/                    # 프로젝트 데이터 (자동 생성)
│   └── {프로젝트명}/
│       ├── captures/        # 스크린샷, 파일
│       ├── notes/           # 텍스트 메모
│       └── context.md       # AI용 자동 생성 문서
└── tests/
```

## AI용 문서 (context.md) 예시

Clickary가 자동 생성하는 `context.md`는 이런 형태:

```markdown
# 프로젝트: 삼성SDI VBScript 마이그레이션

## 개요
- 생성일: 2026-04-01
- 마지막 업데이트: 2026-04-02
- 캡처 수: 12건

## 타임라인
- [2026-04-01 14:30] 스크린샷: 기존 VBS 코드 구조
- [2026-04-01 15:00] 텍스트: 고객 요구사항 메모
- [2026-04-02 09:15] 파일: migration_plan.xlsx 추가

## 텍스트 노트
### 고객 요구사항 메모 (2026-04-01 15:00)
VBScript에서 Python으로 전환 시 ...

## 파일 목록
- captures/20260401_143022.png
- captures/migration_plan.xlsx
```

이 파일을 Claude/ChatGPT에 그대로 전달하면 프로젝트 맥락을 즉시 이해.

## 개발 (Ralph Loop)

에이전트 자율 개발 루프로 개발:

```bash
# Ralph Loop 실행 (에이전트가 알아서 개발 → 테스트 → 커밋)
chmod +x ralph.sh
./ralph.sh 20
```

## 기술 스택

- Python 3.11+
- PyQt6 (GUI)
- Pillow + mss (스크린샷)
- pynput (글로벌 단축키)

## 차별점

| | 노션/Confluence | 클립보드 매니저 | Clickary |
|---|---|---|---|
| 프로젝트 분류 | 수동 정리 | ❌ 없음 | 자동 분류 |
| AI용 문서 | ❌ 없음 | ❌ 없음 | 자동 생성 |
| 데이터 저장 | 클라우드 | 로컬 | 로컬 |
| 보안 민감 기업 | ⚠️ 제한적 | ✅ 가능 | ✅ 가능 |

## 라이선스

MIT
