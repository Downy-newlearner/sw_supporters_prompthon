#!/bin/bash

echo "🚀 프롬프톤 플랫폼 시작"
echo "=========================="

# 현재 디렉토리 확인
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Solar API 키 확인
if [ -z "$SOLAR_API_KEY" ]; then
    echo "⚠️  경고: SOLAR_API_KEY 환경변수가 설정되지 않았습니다."
    echo "다음 명령어로 API 키를 설정해주세요:"
    echo "export SOLAR_API_KEY='your_api_key_here'"
    echo ""
    read -p "계속 진행하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Python 가상환경 확인 및 생성
if [ ! -d "venv" ]; then
    echo "📦 Python 가상환경 생성 중..."
    python3 -m venv venv
fi

# 가상환경 활성화
echo "🔧 가상환경 활성화..."
source venv/bin/activate

# 의존성 설치
echo "📚 의존성 설치 중..."
cd backend
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 서버 실행
echo ""
echo "✅ 준비 완료!"
echo "=========================="
echo "🌐 서버를 시작합니다..."
echo "📍 URL: http://localhost:8000"
echo "종료하려면 Ctrl+C를 누르세요"
echo "=========================="
echo ""

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

