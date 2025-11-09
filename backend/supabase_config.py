"""Supabase 클라이언트 초기화"""
import os
from supabase import create_client, Client
from typing import Optional

# Supabase 클라이언트 인스턴스
_supabase_client: Optional[Client] = None

def init_supabase() -> Client:
    """Supabase 클라이언트 초기화"""
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    # 환경변수에서 Supabase 설정 읽기
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    supabase_service_key = os.getenv("SUPABASE_KEY")
    
    # 키 우선순위: SUPABASE_KEY (service_role) > SUPABASE_ANON_KEY (anon)
    supabase_key = supabase_service_key or supabase_anon_key
    
    # 환경 변수 검증
    if not supabase_url:
        raise ValueError(
            "SUPABASE_URL 환경 변수가 설정되지 않았습니다.\n"
            "Railway 환경 변수에서 SUPABASE_URL을 설정하세요.\n"
            "형식: https://xxxxx.supabase.co"
        )
    
    if not supabase_key:
        raise ValueError(
            "Supabase API 키가 설정되지 않았습니다.\n"
            "Railway 환경 변수에서 다음 중 하나를 설정하세요:\n"
            "  - SUPABASE_ANON_KEY: anon/public key (권장)\n"
            "  - SUPABASE_KEY: service_role key (고급, 보안 주의)"
        )
    
    # URL 검증
    if not supabase_url.startswith("https://"):
        raise ValueError(
            f"SUPABASE_URL이 올바른 형식이 아닙니다: {supabase_url}\n"
            "형식: https://xxxxx.supabase.co"
        )
    
    # 키 타입 로깅
    key_type = "service_role" if supabase_service_key else "anon"
    print(f"📝 Supabase 설정:")
    print(f"   URL: {supabase_url}")
    print(f"   Key Type: {key_type}")
    print(f"   Key Length: {len(supabase_key)} characters")
    
    try:
        _supabase_client = create_client(supabase_url, supabase_key)
        print("✅ Supabase 클라이언트 초기화 완료")
        return _supabase_client
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Supabase 초기화 오류: {error_msg}")
        
        # 더 자세한 오류 메시지 제공
        if "Invalid API key" in error_msg or "401" in error_msg:
            raise ValueError(
                f"Supabase API 키가 유효하지 않습니다.\n"
                f"해결 방법:\n"
                f"1. Supabase 대시보드 → Settings → API에서 올바른 키 확인\n"
                f"2. Railway 환경 변수에서 키가 정확히 복사되었는지 확인 (공백 없음)\n"
                f"3. 키가 최신인지 확인 (키가 재생성되었을 수 있음)\n"
                f"현재 사용 중인 키 타입: {key_type}\n"
                f"오류 상세: {error_msg}"
            )
        elif "Connection" in error_msg or "Network" in error_msg:
            raise ValueError(
                f"Supabase 연결 오류: {error_msg}\n"
                f"SUPABASE_URL을 확인하세요: {supabase_url}"
            )
        else:
        raise

def get_supabase() -> Client:
    """Supabase 클라이언트 인스턴스 반환"""
    global _supabase_client
    if _supabase_client is None:
        init_supabase()
    return _supabase_client

def is_supabase_available() -> bool:
    """Supabase가 사용 가능한지 확인"""
    try:
        init_supabase()
        return True
    except:
        return False

