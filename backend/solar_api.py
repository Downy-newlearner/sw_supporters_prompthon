import os
import asyncio
from openai import OpenAI
from typing import List, Tuple
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
        """Solar API 클라이언트 초기화 - 여러 API 키 지원"""
        # 여러 API 키 로드 (SOLAR_API_KEY_1 ~ SOLAR_API_KEY_6)
        self.api_keys = []
        self.clients = []
        
        for i in range(1, 7):  # 1부터 6까지
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
                ".env 파일에 SOLAR_API_KEY_1 ~ SOLAR_API_KEY_6을 설정하거나\n"
                "환경변수로 SOLAR_API_KEY를 설정해주세요."
            )
        
        print(f"✅ {len(self.api_keys)}개의 Solar API 키를 로드했습니다.")
        
        # 라운드로빈 방식으로 클라이언트 선택
        self.client_cycle = itertools.cycle(enumerate(self.clients))
        self.current_client_lock = asyncio.Lock()
        
        self.model = "solar-pro2"
        self.max_retries = 3
        self.batch_delay = 0.5  # 배치 간 대기 시간 (초)
    
    async def _get_next_client(self):
        """라운드로빈 방식으로 다음 클라이언트 선택"""
        async with self.current_client_lock:
            client_idx, client = next(self.client_cycle)
            return client_idx, client
    
    async def correct_sentence(self, prompt: str, err_sentence: str) -> str:
        """단일 문장 교정"""
        system_prompt = prompt
        user_message = f"다음 문장을 교정해주세요: {err_sentence}"
        
        for attempt in range(self.max_retries):
            try:
                # 라운드로빈으로 클라이언트 선택
                client_idx, client = await self._get_next_client()
                
                # 동기 함수를 비동기로 실행
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        temperature=0.1,
                        max_tokens=500
                    )
                )
                
                corrected = response.choices[0].message.content.strip()
                return corrected
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))  # 지수 백오프
                else:
                    print(f"Error correcting sentence (API key #{client_idx + 1}): {e}")
                    return err_sentence  # 실패 시 원본 반환
    
    async def correct_batch(
        self, 
        prompt: str, 
        sentences: List[Tuple[str, str]], 
        callback=None
    ) -> List[Tuple[str, str]]:
        """
        배치로 문장 교정 (진행 상황 실시간 콜백)
        sentences: [(id, err_sentence), ...]
        returns: [(id, corrected_sentence), ...]
        """
        results = []
        total = len(sentences)
        
        # 동시 처리 수 제한 (rate limit 고려)
        # API 키 개수에 따라 동시 처리 수 조정 (키당 최대 5개)
        max_concurrent = len(self.clients) * 5
        semaphore = asyncio.Semaphore(max_concurrent)
        
        print(f"📊 배치 처리 시작: {total}개 문장, {len(self.clients)}개 API 키 사용 (최대 동시 처리: {max_concurrent})")
        
        # 완료된 작업 수 추적 (스레드 안전)
        completed = 0
        completed_lock = asyncio.Lock()
        start_time = time.time()
        
        async def process_with_semaphore(idx, item):
            nonlocal completed
            
            async with semaphore:
                id_val, err_sentence = item
                corrected = await self.correct_sentence(prompt, err_sentence)
                
                # 진행 상황 업데이트 (스레드 안전)
                async with completed_lock:
                    completed += 1
                    current = completed
                    elapsed = time.time() - start_time
                    speed = current / elapsed if elapsed > 0 else 0
                
                # 콜백 호출 (완료될 때마다)
                if callback:
                    await callback(current, total, id_val)
                
                return (id_val, corrected)
        
        # 모든 문장을 비동기로 처리
        tasks = [
            process_with_semaphore(idx, item) 
            for idx, item in enumerate(sentences)
        ]
        
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        print(f"✅ 배치 처리 완료: {total}개 문장 ({total_time:.2f}초, 평균 {total/total_time:.2f}개/초)")
        
        return results

