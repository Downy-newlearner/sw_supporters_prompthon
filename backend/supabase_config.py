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
    supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "Supabase 설정이 없습니다.\n"
            "환경변수에 다음을 설정하세요:\n"
            "  - SUPABASE_URL: Supabase 프로젝트 URL\n"
            "  - SUPABASE_ANON_KEY: Supabase anon key (또는 SUPABASE_KEY)"
        )
    
    try:
        _supabase_client = create_client(supabase_url, supabase_key)
        print("✅ Supabase 클라이언트 초기화 완료")
        return _supabase_client
    except Exception as e:
        print(f"❌ Supabase 초기화 오류: {e}")
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

