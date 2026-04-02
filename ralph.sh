#!/bin/bash
# ============================================
# Clickary Ralph Loop
# 사용법: ./ralph.sh [최대 반복 횟수]
# 예시:   ./ralph.sh 20
# ============================================

MAX_ITERATIONS=${1:-30}  # 기본 30회
ITERATION=0

echo "🚀 Clickary Ralph Loop 시작"
echo "   최대 반복: $MAX_ITERATIONS"
echo "   시작 시간: $(date)"
echo "==========================================="

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
    ITERATION=$((ITERATION + 1))
    echo ""
    echo "--- 🔄 반복 #$ITERATION ($(date '+%H:%M:%S')) ---"

    # DONE 파일 있으면 종료
    if [ -f "DONE" ]; then
        echo "✅ DONE 파일 발견! 모든 태스크 완료!"
        break
    fi

    # 새 Claude 세션으로 다음 태스크 실행
    claude -p "
너는 Clickary 프로젝트의 개발 에이전트야.

1. CLAUDE.md를 읽고 프로젝트 규칙을 파악해.
2. prd.json에서 status가 'pending'인 첫 번째 태스크를 찾아.
3. 기존 코드가 있으면 먼저 파악하고, 해당 태스크를 구현해.
4. 테스트를 작성하고 pytest로 통과시켜.
5. prd.json에서 해당 태스크 status를 'done'으로 변경해.
6. progress.txt에 '[$(date)] Task N 완료: 설명' 형식으로 기록해.
7. git add . && git commit 해.
8. 모든 태스크가 done이면 DONE 파일을 생성해.

중요:
- 테스트가 실패하면 코드를 수정하고 다시 테스트 (통과할 때까지)
- 기존 코드의 스타일과 구조를 존중해
- 한 세션에서 태스크 1개만 처리하고 끝내
"

    EXIT_CODE=$?
    echo "   세션 종료 (exit code: $EXIT_CODE)"

    # 잠깐 대기 (API rate limit 방지)
    sleep 3
done

echo ""
echo "==========================================="
echo "🏁 Ralph Loop 종료"
echo "   총 반복: $ITERATION"
echo "   종료 시간: $(date)"
echo "==========================================="

# 최종 상태 출력
if [ -f "progress.txt" ]; then
    echo ""
    echo "📋 진행 상황:"
    cat progress.txt
fi
