# 부하테스트 시작 가이드

## ✅ Locust 웹 UI가 실행되었습니다!

### 접속 방법

1. **웹 브라우저 열기**
   - Chrome, Firefox, Safari 등 사용 가능

2. **다음 URL 접속**
   ```
   http://localhost:8089
   ```

3. **테스트 설정**
   - **Number of users**: `30` (동시 사용자 수)
   - **Spawn rate**: `2` (초당 생성 사용자 수)
   - **Host**: `https://dku-prompthon.up.railway.app` (자동 설정됨)

4. **테스트 시작**
   - "Start swarming" 버튼 클릭

### 모니터링 대시보드

Locust 웹 UI에서 다음을 확인할 수 있습니다:

#### 📊 Statistics 탭
- 각 엔드포인트별 통계
- 요청 수, 실패 수
- 평균 응답 시간
- 최소/최대 응답 시간
- 95%ile, 99%ile 응답 시간
- RPS (Requests Per Second)

#### 📈 Charts 탭
- 실시간 차트
- Total Requests per Second
- Response Times (ms)
- Number of Users

#### ⚠️ Failures 탭
- 실패한 요청 목록
- 오류 메시지
- 발생 시간

#### 📋 Exceptions 탭
- 예외 발생 목록
- 스택 트레이스

#### 📥 Download Data 탭
- 통계 데이터 다운로드
- CSV 형식

### 테스트 시나리오

현재 테스트는 다음 시나리오를 시뮬레이션합니다:

1. **로그인** (사용자 시작 시 1회)
2. **WebSocket 연결** (사용자 시작 시 1회)
3. **리더보드 조회** (매우 자주, 가중치 15)
4. **히스토리 조회** (자주, 가중치 5)
5. **PDF 목록 조회** (가끔, 가중치 3)
6. **헬스 체크** (가끔, 가중치 2)
7. **프롬프트 제출** (가끔, 가중치 1)

### 예상 지표

- **목표 응답 시간**: 95%ile < 2초
- **목표 에러율**: < 1%
- **예상 RPS**: 10-50 요청/초

### 테스트 중 확인 사항

1. **Railway 메트릭**
   - Railway 대시보드 → Metrics 탭
   - CPU 사용률 (목표: < 80%)
   - 메모리 사용률 (목표: < 80%)

2. **Railway 로그**
   - Railway 대시보드 → Logs 탭
   - 오류 메시지 확인
   - 느린 요청 확인

3. **Supabase 대시보드**
   - Supabase 프로젝트 → Table Editor
   - 데이터 저장 확인
   - 쿼리 성능 확인

### 테스트 종료

1. Locust 웹 UI에서 "Stop" 버튼 클릭
2. 또는 터미널에서 `Ctrl+C` 입력

### 문제 해결

#### 웹 UI에 접속할 수 없음
```bash
# 포트 확인
lsof -i :8089

# Locust 프로세스 확인
ps aux | grep locust
```

#### 테스트가 시작되지 않음
- 호스트 URL 확인
- 서버 연결 확인
- 방화벽 설정 확인

#### 높은 에러율
- Railway 로그 확인
- Solar API rate limit 확인
- Supabase 연결 확인

### 추가 명령어

```bash
# 헤드리스 모드로 실행 (자동 테스트)
./run_test.sh headless 30 2h

# 커스텀 설정으로 실행
locust -f locustfile.py \
  --host=https://dku-prompthon.up.railway.app \
  --users 30 \
  --spawn-rate 2 \
  --run-time 2h \
  --headless \
  --html=report.html
```

### 참고

- Locust 문서: https://docs.locust.io/
- Railway 메트릭: Railway 대시보드 → Metrics
- 부하테스트 가이드: `README.md`

