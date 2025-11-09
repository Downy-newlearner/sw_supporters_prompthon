"""
Locust 부하테스트 스크립트
프롬프톤 플랫폼 부하테스트
"""
from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser
import websocket
import json
import time
import random
import threading
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrompthonUser(FastHttpUser):
    """프롬프톤 사용자 시뮬레이션"""
    wait_time = between(2, 8)  # 요청 간 대기 시간 (2-8초, 더 현실적으로)
    
    def on_start(self):
        """사용자 세션 시작"""
        self.nickname = f"loadtest_user_{random.randint(10000, 99999)}"
        self.ws = None
        self.ws_thread = None
        self.ws_connected = False
        self.submit_count = 0
        self.last_submit_time = 0  # submit 빈도 제한용
        
        # 로그인
        try:
            response = self.client.post(
                "/api/login",
                json={"nickname": self.nickname},
                name="/api/login"
            )
            
            if response.status_code == 200:
                logger.info(f"✅ 로그인 성공: {self.nickname}")
                # WebSocket 연결
                self.connect_websocket()
            else:
                logger.error(f"❌ 로그인 실패: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"❌ 로그인 오류: {e}")
    
    def connect_websocket(self):
        """WebSocket 연결"""
        try:
            # URL 변환 (http -> ws, https -> wss)
            ws_host = self.host.replace("http://", "ws://").replace("https://", "wss://")
            ws_path = f"/api/ws/{self.nickname}"
            ws_url = f"{ws_host}{ws_path}"
            
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    if data.get("type") == "connected":
                        self.ws_connected = True
                        logger.info(f"✅ WebSocket 연결됨: {self.nickname}")
                    elif data.get("type") == "progress":
                        # 진행 상황 로깅 (선택적)
                        pass
                    elif data.get("type") == "complete":
                        logger.info(f"✅ 제출 완료: {self.nickname} - 점수: {data.get('score', 0)}")
                    elif data.get("type") == "error":
                        logger.error(f"❌ WebSocket 오류: {data.get('message')}")
                except Exception as e:
                    logger.error(f"❌ WebSocket 메시지 파싱 오류: {e}")
            
            def on_error(ws, error):
                logger.error(f"❌ WebSocket 오류 ({self.nickname}): {error}")
                self.ws_connected = False
            
            def on_close(ws, close_status_code, close_msg):
                logger.info(f"WebSocket 연결 종료: {self.nickname}")
                self.ws_connected = False
            
            def on_open(ws):
                logger.info(f"WebSocket 연결 시도: {self.nickname}")
            
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            # WebSocket을 별도 스레드에서 실행
            self.ws_thread = threading.Thread(target=self.ws.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
            # 연결 대기 (최대 5초)
            for _ in range(50):
                if self.ws_connected:
                    break
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"❌ WebSocket 연결 오류: {e}")
    
    def on_stop(self):
        """사용자 세션 종료"""
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
    
    @task(15)
    def get_leaderboard(self):
        """리더보드 조회 (가벼운 작업, 자주 호출)"""
        with self.client.get(
            "/api/leaderboard",
            name="/api/leaderboard",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "leaderboard" in data:
                        response.success()
                    else:
                        response.failure("리더보드 데이터 없음")
                except:
                    response.failure("JSON 파싱 실패")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(5)
    def get_history(self):
        """히스토리 조회"""
        with self.client.get(
            f"/api/history/{self.nickname}",
            name="/api/history",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def submit_prompt(self):
        """
        프롬프트 제출 (무거운 작업, 매우 가끔 호출)
        실제 사용 시나리오: 5-10분마다 1번 정도
        """
        # submit 빈도 제한: 이전 submit 후 최소 5분 경과해야 함
        current_time = time.time()
        time_since_last_submit = current_time - self.last_submit_time
        
        # 최소 5분(300초) 대기 - 실제 사용 시나리오
        min_interval = 300  # 5분
        
        if time_since_last_submit < min_interval:
            # 아직 대기 시간이 안 지났으면 skip (가중치를 낮춰서 선택 확률 감소)
            # 하지만 task는 실행되므로 짧은 대기만 하고 종료
            return
        
        # 샘플 프롬프트 (실제 사용 시나리오 시뮬레이션)
        prompts = [
            "다음 문장의 오류를 수정하세요. 문법과 맞춤법을 확인하세요.",
            "문장을 자연스럽고 정확하게 수정해주세요.",
            "맞춤법과 띄어쓰기를 확인하고 수정하세요.",
            "문법 오류를 찾아서 수정하세요.",
            "문장을 올바르게 교정해주세요.",
        ]
        
        prompt = random.choice(prompts)
        self.submit_count += 1
        self.last_submit_time = current_time
        
        logger.info(f"📤 제출 시작: {self.nickname} (#{self.submit_count}) - 마지막 제출 후 {time_since_last_submit:.0f}초 경과")
        
        with self.client.post(
            "/api/submit",
            json={
                "nickname": self.nickname,
                "prompt": prompt
            },
            name="/api/submit",
            catch_response=True,
            timeout=60  # 타임아웃 60초 (AI 교정 시간 고려)
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("success"):
                        response.success()
                        logger.info(f"✅ 제출 성공: {self.nickname} (#{self.submit_count})")
                    else:
                        response.failure(f"제출 실패: {data.get('message')}")
                except:
                    response.failure("JSON 파싱 실패")
            else:
                response.failure(f"HTTP {response.status_code}")
        
        # submit 후 추가 대기 (AI 교정 시간 고려)
        # wait_time과 별도로 추가 대기하지 않음 (이미 wait_time이 적용됨)
    
    @task(3)
    def get_pdfs(self):
        """PDF 목록 조회"""
        with self.client.get(
            "/api/pdfs",
            name="/api/pdfs",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(2)
    def health_check(self):
        """헬스 체크"""
        with self.client.get(
            "/api/health",
            name="/api/health",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


# 커스텀 이벤트 핸들러
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """테스트 시작"""
    logger.info("=" * 60)
    logger.info("부하테스트 시작")
    logger.info(f"대상 서버: {environment.host}")
    logger.info("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """테스트 종료"""
    logger.info("=" * 60)
    logger.info("부하테스트 종료")
    logger.info("=" * 60)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """요청 이벤트 로깅 (느린 요청만)"""
    if response_time > 5000:  # 5초 이상
        logger.warning(
            f"⚠️ 느린 요청: {name} - {response_time:.0f}ms"
        )

