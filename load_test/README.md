# 부하테스트 가이드

## 개요

프롬프톤 플랫폼의 부하테스트를 위한 Locust 스크립트입니다.

## 설치

```bash
cd load_test
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 사용법

### 웹 UI 모드 (권장)

모니터링 대시보드를 웹 브라우저에서 확인할 수 있습니다.

```bash
./run_test.sh web
```

또는 직접 실행:

```bash
locust -f locustfile.py --host=https://dku-prompthon.up.railway.app
```

브라우저에서 `http://localhost:8089` 접속하여:
1. 사용자 수 설정
2. 스폰 레이트 설정 (초당 생성 사용자 수)
3. "Start swarming" 클릭하여 테스트 시작

### 헤드리스 모드

자동으로 테스트를 실행하고 결과를 저장합니다.

```bash
./run_test.sh headless 30 2h
```

파라미터:
- `30`: 동시 사용자 수
- `2h`: 테스트 지속 시간 (2시간)

### 커스텀 실행

```bash
# 웹 UI 모드 (커스텀 호스트)
./run_test.sh web 30 2h https://custom-host.com

# 헤드리스 모드
locust -f locustfile.py \
  --host=https://dku-prompthon.up.railway.app \
  --users 30 \
  --spawn-rate 2 \
  --run-time 2h \
  --headless \
  --html=report.html \
  --csv=results
```

## 테스트 시나리오

### 일반 사용자 (80% 트래픽)
- 리더보드 조회: 매우 자주 (가중치 15)
- 히스토리 조회: 자주 (가중치 5)
- PDF 목록 조회: 가끔 (가중치 3)
- 헬스 체크: 가끔 (가중치 2)
- 프롬프트 제출: 가끔 (가중치 1)

### 적극적 사용자 (20% 트래픽)
- 프롬프트 제출 비율이 높음
- 리더보드 조회가 더 빈번함

## 모니터링

### Locust 웹 UI
- 실시간 통계
- 응답 시간 분포
- 요청 처리량 (RPS)
- 에러율

### Railway 메트릭
- CPU 사용률
- 메모리 사용률
- 네트워크 I/O
- 로그 확인

### 주요 지표
- **응답 시간**: 평균, 95%ile, 99%ile
- **요청 처리량**: 초당 요청 수 (RPS)
- **에러율**: 4xx, 5xx 오류 비율
- **타임아웃**: 요청 타임아웃 발생률

## 예상 부하

- **동시 사용자**: 30명
- **지속 시간**: 2시간
- **예상 RPS**: 10-50 요청/초
- **프롬프트 제출**: 평균 5-10분마다 1회

## 문제 해결

### WebSocket 연결 실패
- 서버 URL 확인
- 방화벽 설정 확인
- Railway 로그 확인

### 높은 에러율
- 서버 리소스 확인
- Solar API rate limit 확인
- Supabase 연결 확인

### 느린 응답 시간
- 서버 CPU/메모리 확인
- 네트워크 지연 확인
- 데이터베이스 쿼리 최적화

## 결과 분석

헤드리스 모드 실행 후:
- `report_*.html`: HTML 리포트
- `results_*.csv`: 상세 CSV 데이터

## 참고

- Locust 문서: https://docs.locust.io/
- Railway 메트릭: Railway 대시보드 → Metrics

