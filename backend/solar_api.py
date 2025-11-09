import os
import asyncio
from openai import OpenAI
from typing import List, Tuple, Optional
import time
from dotenv import load_dotenv
from pathlib import Path
import heapq
import itertools
import httpx

# .env 파일 로드 (상위 디렉토리의 .env 파일)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class SolarAPIClient:
    def __init__(self):
        """Solar API 클라이언트 초기화 - 여러 API 키 지원 (최대 20개)"""
        # 여러 API 키 로드 (SOLAR_API_KEY_1 ~ SOLAR_API_KEY_20)
        self.api_keys = []
        self.clients = []
        
        for i in range(1, 21):  # 1부터 20까지
            key = os.getenv(f"SOLAR_API_KEY_{i}", "")
            # 유효한 키만 추가 (비어있지 않고, "your_api_key"로 시작하지 않음)
            if key and not key.startswith("your_api_key"):
                self.api_keys.append(key)
                # httpx 클라이언트를 직접 생성하여 proxies 문제 회피
                http_client = httpx.Client(timeout=60.0)
                client = OpenAI(
                    api_key=key,
                    base_url="https://api.upstage.ai/v1/solar",
                    http_client=http_client
                )
                self.clients.append(client)
        
        # 호환성을 위해 단일 SOLAR_API_KEY도 확인
        single_key = os.getenv("SOLAR_API_KEY", "")
        if single_key and not single_key.startswith("your_api_key") and single_key not in self.api_keys:
            self.api_keys.append(single_key)
            # httpx 클라이언트를 직접 생성하여 proxies 문제 회피
            http_client = httpx.Client(timeout=60.0)
            client = OpenAI(
                api_key=single_key,
                base_url="https://api.upstage.ai/v1/solar",
                http_client=http_client
            )
            self.clients.append(client)
        
        if not self.api_keys:
            raise ValueError(
                "Solar API 키가 설정되지 않았습니다.\n"
                ".env 파일에 SOLAR_API_KEY_1 ~ SOLAR_API_KEY_20을 설정하거나\n"
                "환경변수로 SOLAR_API_KEY를 설정해주세요."
            )
        
        print(f"✅ {len(self.api_keys)}개의 Solar API 키를 로드했습니다.")
        
        # API 키당 최대 제출 수 (3개)
        self.max_submissions_per_key = 3
        
        # 각 API 키가 현재 담당 중인 제출 수를 추적
        # {api_key_index: submission_count}
        self.api_key_submission_count = {i: 0 for i in range(len(self.clients))}
        
        # 각 API 키별 세마포어: API 키당 동시 처리 가능한 문장 수 제한
        # 키당 최대 5개 동시 처리 (30명 사용자, 24개 제출 동시 처리 최적화)
        # 라운드로빈으로 모든 키를 공유하므로 총 20개 키 × 5개 = 100개 동시 처리 가능
        self.concurrent_per_key = 5
        # Semaphore는 이벤트 루프 없이도 생성 가능하지만, 일관성을 위해 지연 초기화
        self.key_semaphores = None
        
        # 라운드로빈 방식으로 클라이언트 선택 (이전 방식)
        # 동기 초기화이므로 즉시 초기화 가능
        self.client_cycle = None
        
        # 우선순위 큐: (submission_count, api_key_index) 튜플의 리스트
        # submission_count가 적을수록 우선순위가 높음
        self.priority_queue = [(0, i) for i in range(len(self.clients))]
        heapq.heapify(self.priority_queue)
        
        # 우선순위 큐와 submission_count 딕셔너리를 보호하는 락
        # 동기 초기화이므로 지연 초기화
        self.allocation_lock = None
        
        # 대기 중인 제출을 위한 큐: (event, nickname)
        # event는 제출이 할당될 때까지 대기하는 이벤트
        # 동기 초기화이므로 지연 초기화
        self.waiting_submissions = None
        
        # 대기 중인 제출 처리 태스크 (지연 초기화)
        # __init__는 동기 함수이므로 이벤트 루프가 없을 수 있음
        # 첫 번째 비동기 메서드 호출 시 초기화
        self.processing_waiting = None
        self._task_initialized = False
        
        self.model = "solar-pro2"
        self.max_retries = 3
        
        max_total_submissions = len(self.clients) * self.max_submissions_per_key
        total_concurrent = len(self.clients) * self.concurrent_per_key
        print(f"📊 제출 할당 설정: 키당 최대 {self.max_submissions_per_key}개 제출, 총 {max_total_submissions}개 제출 동시 처리 가능")
        print(f"   라운드로빈 방식으로 모든 API 키 공유 사용")
        print(f"   키당 최대 {self.concurrent_per_key}개 동시 처리, 총 {total_concurrent}개 문장 동시 처리 가능")
    
    def _ensure_async_objects(self):
        """비동기 객체들 초기화 (첫 번째 비동기 메서드 호출 시)"""
        if self.client_cycle is None:
            self.client_cycle = itertools.cycle(enumerate(self.clients))
        if self.key_semaphores is None:
            self.key_semaphores = [asyncio.Semaphore(self.concurrent_per_key) for _ in self.clients]
        if self.allocation_lock is None:
            self.allocation_lock = asyncio.Lock()
        if self.waiting_submissions is None:
            self.waiting_submissions = asyncio.Queue()
    
    async def _assign_api_key(self) -> Optional[int]:
        """
        우선순위 큐를 사용하여 가장 적은 제출을 담당 중인 API 키 할당
        할당 가능한 API 키가 없으면 None 반환 (큐에서 대기해야 함)
        """
        self._ensure_async_objects()
        async with self.allocation_lock:
            if not self.priority_queue:
                return None
            
            # 우선순위 큐의 front 확인 (가장 적은 제출을 담당 중인 API 키)
            submission_count, api_key_index = self.priority_queue[0]
            
            # 해당 API 키가 이미 최대 제출 수에 도달했는지 확인
            if submission_count >= self.max_submissions_per_key:
                return None  # 할당 불가, 큐에서 대기 필요
            
            # API 키 할당
            # 힙에서 제거하고 submission_count 증가 후 다시 추가
            heapq.heappop(self.priority_queue)
            self.api_key_submission_count[api_key_index] += 1
            heapq.heappush(self.priority_queue, (self.api_key_submission_count[api_key_index], api_key_index))
            
            print(f"🔑 API 키 #{api_key_index + 1} 할당 (현재 제출 수: {self.api_key_submission_count[api_key_index]}/{self.max_submissions_per_key})")
            return api_key_index
    
    async def _release_api_key(self, api_key_index: int):
        """
        제출 완료 시 API 키 해제
        해제 후 대기 중인 제출이 있으면 즉시 할당 시도
        """
        self._ensure_async_objects()
        async with self.allocation_lock:
            # submission_count 감소
            self.api_key_submission_count[api_key_index] -= 1
            
            # 우선순위 큐 재구성 (더 효율적인 방법: 모든 항목을 재추가)
            # 간단하게 하기 위해 현재 상태를 반영하여 큐 재구성
            self.priority_queue = [
                (self.api_key_submission_count[i], i) 
                for i in range(len(self.clients))
            ]
            heapq.heapify(self.priority_queue)
            
            print(f"🔓 API 키 #{api_key_index + 1} 해제 (현재 제출 수: {self.api_key_submission_count[api_key_index]}/{self.max_submissions_per_key})")
            
            # 대기 중인 제출이 있으면 즉시 할당 시도
            if not self.waiting_submissions.empty():
                if self.priority_queue:
                    submission_count, available_api_key_index = self.priority_queue[0]
                    
                    # 할당 가능한 API 키가 있는지 확인
                    if submission_count < self.max_submissions_per_key:
                        try:
                            event, nickname = self.waiting_submissions.get_nowait()
                            
                            # API 키 할당
                            heapq.heappop(self.priority_queue)
                            self.api_key_submission_count[available_api_key_index] += 1
                            heapq.heappush(self.priority_queue, (self.api_key_submission_count[available_api_key_index], available_api_key_index))
                            
                            print(f"🔑 대기 중인 제출 즉시 할당: {nickname} → API 키 #{available_api_key_index + 1}")
                            
                            # 이벤트를 통해 할당된 API 키 인덱스 전달
                            event.api_key_index = available_api_key_index
                            event.set()
                        except asyncio.QueueEmpty:
                            pass
    
    async def _process_waiting_submissions(self):
        """
        대기 중인 제출을 처리하는 백그라운드 태스크
        API 키가 해제될 때마다 대기 중인 제출에 할당 시도
        """
        # 비동기 객체들 초기화 (백그라운드 태스크 시작 시)
        self._ensure_async_objects()
        
        while True:
            try:
                # 짧은 간격으로 대기 큐 확인
                await asyncio.sleep(0.1)
                
                # 대기 중인 제출이 있고, 할당 가능한 API 키가 있는지 확인
                if not self.waiting_submissions.empty():
                    async with self.allocation_lock:
                        if not self.priority_queue:
                            continue
                        
                        submission_count, api_key_index = self.priority_queue[0]
                        
                        # 할당 가능한 API 키가 있는지 확인
                        if submission_count < self.max_submissions_per_key:
                            # 대기 큐에서 제출 가져오기
                            try:
                                event, nickname = self.waiting_submissions.get_nowait()
                                
                                # API 키 할당
                                heapq.heappop(self.priority_queue)
                                self.api_key_submission_count[api_key_index] += 1
                                heapq.heappush(self.priority_queue, (self.api_key_submission_count[api_key_index], api_key_index))
                                
                                print(f"🔑 대기 중인 제출 할당: {nickname} → API 키 #{api_key_index + 1}")
                                
                                # 이벤트를 통해 할당된 API 키 인덱스 전달
                                event.api_key_index = api_key_index
                                event.set()
                                    
                            except asyncio.QueueEmpty:
                                pass
                                
            except Exception as e:
                print(f"❌ 대기 중인 제출 처리 오류: {e}")
                import traceback
                traceback.print_exc()
    
    async def request_submission_allocation(self, nickname: str) -> int:
        """
        제출에 API 키 할당 요청
        할당 가능하면 즉시 반환, 아니면 큐에서 대기 후 반환
        """
        # 비동기 객체들 초기화
        self._ensure_async_objects()
        
        # 백그라운드 태스크 초기화 (첫 번째 비동기 호출 시)
        if not self._task_initialized:
            self.processing_waiting = asyncio.create_task(self._process_waiting_submissions())
            self._task_initialized = True
        
        # 먼저 즉시 할당 시도
        api_key_index = await self._assign_api_key()
        
        if api_key_index is not None:
            return api_key_index
        
        # 할당 불가능하면 큐에서 대기
        print(f"⏳ 제출 대기: {nickname} (모든 API 키가 최대 제출 수에 도달)")
        
        event = asyncio.Event()
        # 대기 큐에 추가 (이벤트와 nickname만 저장)
        await self.waiting_submissions.put((event, nickname))
        
        # 할당 가능해질 때까지 대기 (백그라운드 태스크가 할당하고 event.set() 호출)
        await event.wait()
        
        # 할당된 API 키 인덱스 반환 (백그라운드 태스크가 event.api_key_index에 설정)
        return event.api_key_index
    
    async def correct_sentence(
        self, 
        prompt: str, 
        err_sentence: str
    ) -> str:
        """
        단일 문장 교정 (라운드로빈 방식으로 API 키 선택)
        이전 방식처럼 모든 API 키를 공유하여 사용
        """
        # 비동기 객체들 초기화
        self._ensure_async_objects()
        
        system_prompt = prompt
        user_message = f"다음 문장을 교정해주세요: {err_sentence}"
        
        last_error = None
        last_client_idx = None
        
        # 최대 재시도 횟수만큼 시도
        for attempt in range(self.max_retries):
            try:
                # 라운드로빈으로 클라이언트 선택 (이전 방식)
                async with self.allocation_lock:
                    client_idx, client = next(self.client_cycle)
                    last_client_idx = client_idx
                
                # 해당 키의 세마포어 획득 (동시 처리 수 제한)
                async with self.key_semaphores[client_idx]:
                    # 동기 함수를 비동기로 실행
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,
                        lambda c=client, sp=system_prompt, um=user_message: c.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": sp},
                                {"role": "user", "content": um}
                            ],
                            temperature=0.1,
                            max_tokens=500
                        )
                    )
                    
                    corrected = response.choices[0].message.content.strip()
                    return corrected
            
            except Exception as e:
                last_error = e
                # 재시도 전 대기 (지수 백오프)
                if attempt < self.max_retries - 1:
                    wait_time = 1 * (attempt + 1)
                    await asyncio.sleep(wait_time)
        
        # 모든 재시도 실패
        key_info = f"API key #{last_client_idx + 1}" if last_client_idx is not None else "모든 API key"
        print(f"Error correcting sentence ({key_info}, {self.max_retries}회 시도 실패): {last_error}")
        return err_sentence  # 실패 시 원본 반환
    
    async def correct_batch(
        self, 
        prompt: str, 
        sentences: List[Tuple[str, str]], 
        callback=None,
        nickname: str = "unknown"
    ) -> List[Tuple[str, str]]:
        """
        배치로 문장 교정 (진행 상황 실시간 콜백)
        하이브리드 방식: 제출 단위 제한은 유지하지만, 라운드로빈으로 모든 API 키 공유 사용
        sentences: [(id, err_sentence), ...]
        returns: [(id, corrected_sentence), ...]
        """
        total = len(sentences)
        
        # 1. API 키 할당 요청 (제출 단위 제한 유지)
        api_key_index = await self.request_submission_allocation(nickname)
        
        try:
            print(f"📊 배치 처리 시작: {nickname} - {total}개 문장, 모든 API 키 공유 사용 (라운드로빈)")
            
            # 완료된 작업 수 추적 (스레드 안전)
            completed = 0
            completed_lock = asyncio.Lock()
            start_time = time.time()
            
            async def process_sentence(idx, item):
                nonlocal completed
                
                # 라운드로빈 방식으로 모든 API 키 공유 사용 (이전 방식)
                id_val, err_sentence = item
                corrected = await self.correct_sentence(prompt, err_sentence)
                
                # 진행 상황 업데이트 (스레드 안전)
                async with completed_lock:
                    completed += 1
                    current = completed
                    elapsed = time.time() - start_time
                
                # 콜백 호출 (완료될 때마다)
                if callback:
                    await callback(current, total, id_val)
                
                return (id_val, corrected)
            
            # 모든 문장을 비동기로 처리 (이전 방식과 동일)
            # 라운드로빈으로 모든 API 키를 공유하여 사용
            tasks = [
                process_sentence(idx, item) 
                for idx, item in enumerate(sentences)
            ]
            
            results = await asyncio.gather(*tasks)
            
            total_time = time.time() - start_time
            print(f"✅ 배치 처리 완료: {nickname} - {total}개 문장 ({total_time:.2f}초, 평균 {total/total_time:.2f}개/초)")
            
            return results
            
        finally:
            # 제출 완료 후 API 키 해제
            await self._release_api_key(api_key_index)
            print(f"🏁 제출 완료: {nickname} - API 키 할당 해제")

