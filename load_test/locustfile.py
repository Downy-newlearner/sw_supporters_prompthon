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
        self.next_submit_time = 0  # 다음 제출 가능 시간 (제출 완료 후 3-5분 랜덤)
        self.pending_submit = False  # 제출이 진행 중인지 여부
        self.submit_start_time = 0  # 제출 시작 시간 (타임아웃 체크용)
        self.submit_lock = threading.Lock()  # 제출 상태 동기화용
        
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
                        progress = data.get("progress", 0)
                        stage = data.get("stage", "")
                        if progress % 25 == 0:  # 25% 단위로만 로깅
                            logger.debug(f"📊 진행: {self.nickname} - {stage} {progress}%")
                    elif data.get("type") == "complete":
                        # 제출 완료 시 다음 제출 시간 설정 (3-5분 후 랜덤)
                        with self.submit_lock:
                            complete_time = time.time()
                            processing_time = complete_time - self.submit_start_time if self.submit_start_time > 0 else 0
                            
                            if not self.pending_submit:
                                logger.warning(
                                    f"⚠️ 완료 메시지 수신했지만 pending_submit이 False: {self.nickname} - "
                                    f"이미 해제된 상태일 수 있음"
                                )
                            
                            # 3-5분(180-300초) 사이의 랜덤 간격 추가
                            next_interval = random.uniform(180, 300)
                            self.next_submit_time = complete_time + next_interval
                            self.pending_submit = False
                            self.submit_start_time = 0
                            
                            logger.info(f"🔓 제출 잠금 해제: {self.nickname} - pending_submit=False")
                        
                        wait_minutes = next_interval / 60
                        logger.info(
                            f"✅ 제출 완료: {self.nickname} - 점수: {data.get('score', 0)} - "
                            f"처리 시간: {processing_time:.1f}초 - 다음 제출 {wait_minutes:.1f}분 후 가능"
                        )
                    elif data.get("type") == "error":
                        # 오류 발생 시에도 제출 상태 해제
                        with self.submit_lock:
                            self.pending_submit = False
                            self.submit_start_time = 0
                            logger.info(f"🔓 제출 잠금 해제 (오류): {self.nickname} - pending_submit=False")
                        logger.error(f"❌ WebSocket 오류: {self.nickname} - {data.get('message')}")
                except Exception as e:
                    logger.error(f"❌ WebSocket 메시지 파싱 오류: {e} - {message}")
            
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
        프롬프트 제출 (무거운 작업)
        조건:
        1. 제출 완료 후에만 다시 제출 가능
        2. 마지막 제출 완료 후 3-5분(180-300초) 사이에 제출
        3. 동시에 여러 제출 방지
        """
        current_time = time.time()
        
        # 제출 상태 확인 및 업데이트 (스레드 안전)
        with self.submit_lock:
            # 타임아웃 체크: 10분(600초) 이상 pending 상태면 자동 해제
            if self.pending_submit and self.submit_start_time > 0:
                elapsed = current_time - self.submit_start_time
                if elapsed >= 600:  # 10분 이상
                    logger.warning(
                        f"⚠️ 제출 타임아웃 자동 해제: {self.nickname} - "
                        f"{elapsed/60:.1f}분 경과, 완료 메시지 없음"
                    )
                    self.pending_submit = False
                    self.submit_start_time = 0
            
            # 이미 제출이 진행 중이면 skip
            if self.pending_submit:
                elapsed = current_time - self.submit_start_time if self.submit_start_time > 0 else 0
                logger.info(
                    f"⏸️ 제출 차단: {self.nickname} - "
                    f"진행 중인 제출이 있어 건너뜀 (경과: {elapsed:.0f}초)"
                )
                return
            
            # 다음 제출 시간 확인
            # 첫 제출이거나 다음 제출 시간이 지났으면 제출 가능
            if self.next_submit_time > 0 and current_time < self.next_submit_time:
                wait_time = self.next_submit_time - current_time
                logger.info(
                    f"⏳ 제출 대기: {self.nickname} - "
                    f"다음 제출까지 {wait_time/60:.1f}분 남음"
                )
                return
            
            # 제출 시작 표시
            self.pending_submit = True
            self.submit_start_time = current_time
            logger.info(f"🔒 제출 잠금 설정: {self.nickname} - pending_submit=True")
        
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
        
        # 제출 시작 로그
        logger.info(f"📤 제출 시작: {self.nickname} (#{self.submit_count})")
        
        try:
            with self.client.post(
                "/api/submit",
                json={
                    "nickname": self.nickname,
                    "prompt": prompt
                },
                name="/api/submit",
                catch_response=True,
                timeout=10  # API 응답 타임아웃 (백그라운드 처리 시작 확인용)
            ) as response:
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get("success"):
                            response.success()
                            logger.info(
                                f"✅ 제출 요청 성공: {self.nickname} (#{self.submit_count}) - "
                                f"처리 중... (WebSocket으로 완료 알림 대기)"
                            )
                            # pending_submit은 WebSocket 완료 메시지에서 해제됨
                        else:
                            # 실패 시 상태 해제
                            with self.submit_lock:
                                self.pending_submit = False
                                self.submit_start_time = 0
                                logger.info(f"🔓 제출 잠금 해제 (실패): {self.nickname} - pending_submit=False")
                            response.failure(f"제출 실패: {data.get('message')}")
                    except:
                        # 실패 시 상태 해제
                        with self.submit_lock:
                            self.pending_submit = False
                            self.submit_start_time = 0
                            logger.info(f"🔓 제출 잠금 해제 (파싱 오류): {self.nickname} - pending_submit=False")
                        response.failure("JSON 파싱 실패")
                else:
                    # 실패 시 상태 해제
                    with self.submit_lock:
                        self.pending_submit = False
                        self.submit_start_time = 0
                        logger.info(f"🔓 제출 잠금 해제 (HTTP 오류): {self.nickname} - pending_submit=False")
                    response.failure(f"HTTP {response.status_code}")
        except Exception as e:
            # 예외 발생 시 상태 해제
            with self.submit_lock:
                self.pending_submit = False
                self.submit_start_time = 0
                logger.info(f"🔓 제출 잠금 해제 (예외): {self.nickname} - pending_submit=False")
            logger.error(f"❌ 제출 요청 오류: {e}")
            raise
    
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

