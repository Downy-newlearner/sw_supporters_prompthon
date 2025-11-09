import os
import asyncio
from openai import OpenAI
from typing import List, Tuple, Optional
import time
from dotenv import load_dotenv
from pathlib import Path
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
        
        # 각 API 키별 세마포어: API 키당 동시 처리 가능한 문장 수 제한
        # 키당 최대 5개 동시 처리
        # 라운드로빈으로 모든 키를 공유하므로 총 20개 키 × 5개 = 100개 동시 처리 가능
        self.concurrent_per_key = 5
        # Semaphore는 이벤트 루프 없이도 생성 가능하지만, 일관성을 위해 지연 초기화
        self.key_semaphores = None
        
        # 라운드로빈 방식으로 클라이언트 선택
        self.client_cycle = None
        
        # 클라이언트 선택 시 사용할 락 (동기화용)
        self.allocation_lock = None
        
        self.model = "solar-pro2"
        self.max_retries = 3
        
        total_concurrent = len(self.clients) * self.concurrent_per_key
        print(f"📊 라운드로빈 방식으로 모든 API 키 공유 사용")
        print(f"   키당 최대 {self.concurrent_per_key}개 동시 처리, 총 {total_concurrent}개 문장 동시 처리 가능")
    
    def _ensure_async_objects(self):
        """비동기 객체들 초기화 (첫 번째 비동기 메서드 호출 시)"""
        if self.client_cycle is None:
            self.client_cycle = itertools.cycle(enumerate(self.clients))
        if self.key_semaphores is None:
            self.key_semaphores = [asyncio.Semaphore(self.concurrent_per_key) for _ in self.clients]
        if self.allocation_lock is None:
            self.allocation_lock = asyncio.Lock()
    
    async def correct_sentence(
        self, 
        prompt: str, 
        err_sentence: str
    ) -> str:
        """
        단일 문장 교정 (라운드로빈 방식으로 API 키 선택)
        모든 API 키를 공유하여 사용
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
                # 라운드로빈으로 클라이언트 선택
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
        라운드로빈으로 모든 API 키 공유 사용
        sentences: [(id, err_sentence), ...]
        returns: [(id, corrected_sentence), ...]
        """
        total = len(sentences)
        
        print(f"📊 배치 처리 시작: {nickname} - {total}개 문장, 라운드로빈 방식")
        
        # 완료된 작업 수 추적 (스레드 안전)
        completed = 0
        completed_lock = asyncio.Lock()
        start_time = time.time()
        
        async def process_sentence(idx, item):
            nonlocal completed
            
            # 라운드로빈 방식으로 모든 API 키 공유 사용
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
        
        # 모든 문장을 비동기로 처리
        # 라운드로빈으로 모든 API 키를 공유하여 사용
        tasks = [
            process_sentence(idx, item) 
            for idx, item in enumerate(sentences)
        ]
        
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        print(f"✅ 배치 처리 완료: {nickname} - {total}개 문장 ({total_time:.2f}초, 평균 {total/total_time:.2f}개/초)")
        
        return results

