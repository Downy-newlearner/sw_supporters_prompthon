#!/bin/bash

# 부하테스트 실행 스크립트
# 사용법: ./run_test.sh [모드] [사용자수] [시간]
# 모드: web (웹 UI), headless (헤드리스)
# 예: ./run_test.sh web 30 2h

set -e

# 기본값 설정
MODE="${1:-web}"
USERS="${2:-30}"
TIME="${3:-2h}"
HOST="${4:-https://dku-prompthon.up.railway.app}"

# 색상 코드
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}프롬프톤 플랫폼 부하테스트${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "대상 서버: ${YELLOW}${HOST}${NC}"
echo -e "모드: ${YELLOW}${MODE}${NC}"
echo -e "사용자 수: ${YELLOW}${USERS}${NC}"
echo -e "지속 시간: ${YELLOW}${TIME}${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 디렉토리 확인
if [ ! -f "locustfile.py" ]; then
    echo "❌ 오류: locustfile.py를 찾을 수 없습니다."
    echo "load_test 디렉토리에서 실행하세요."
    exit 1
fi

# 가상환경 확인 및 생성
if [ ! -d "venv" ]; then
    echo "📦 가상환경 생성 중..."
    python3 -m venv venv
fi

# 가상환경 활성화
echo "🔌 가상환경 활성화 중..."
source venv/bin/activate

# 패키지 설치
echo "📦 패키지 설치 중..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 타임스탬프 생성
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ "$MODE" = "web" ]; then
    # 웹 UI 모드
    echo ""
    echo -e "${GREEN}웹 UI 모드로 실행 중...${NC}"
    echo -e "브라우저에서 ${YELLOW}http://localhost:8089${NC} 접속하세요"
    echo ""
    
    locust -f locustfile.py \
        --host="${HOST}" \
        --web-host=0.0.0.0 \
        --web-port=8089
else
    # 헤드리스 모드
    echo ""
    echo -e "${GREEN}헤드리스 모드로 실행 중...${NC}"
    echo ""
    
    locust -f locustfile.py \
        --host="${HOST}" \
        --users "${USERS}" \
        --spawn-rate 2 \
        --run-time "${TIME}" \
        --headless \
        --html="report_${TIMESTAMP}.html" \
        --csv="results_${TIMESTAMP}" \
        --loglevel INFO
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}부하테스트 완료!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "리포트: ${YELLOW}report_${TIMESTAMP}.html${NC}"
    echo -e "CSV 결과: ${YELLOW}results_${TIMESTAMP}_*.csv${NC}"
    echo -e "${GREEN}========================================${NC}"
fi

