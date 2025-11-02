"""Supabase를 사용한 리더보드 및 히스토리 관리"""
from typing import List
from datetime import datetime
from supabase_config import get_supabase, is_supabase_available
from models import LeaderboardEntry, PromptHistoryEntry


class SupabaseLeaderboardManager:
    """Supabase를 사용한 리더보드 관리"""
    
    TABLE_NAME = "leaderboard"
    
    def __init__(self):
        self.supabase = None
        if is_supabase_available():
            self.supabase = get_supabase()
        else:
            print("⚠️ Supabase를 사용할 수 없습니다. 로컬 JSON 파일을 사용합니다.")
            self.supabase = None
    
    def update_score(self, nickname: str, score: float):
        """점수 업데이트"""
        if not self.supabase:
            raise ValueError("Supabase가 초기화되지 않았습니다.")
        
        now = datetime.now().isoformat()
        
        try:
            # 기존 레코드 확인
            existing = self.supabase.table(self.TABLE_NAME)\
                .select("*")\
                .eq("nickname", nickname)\
                .execute()
            
            if existing.data:
                # 업데이트
                current_data = existing.data[0]
                submission_count = current_data.get("submission_count", 0) + 1
                best_score = max(current_data.get("best_score", 0), score)
                
                self.supabase.table(self.TABLE_NAME)\
                    .update({
                        "best_score": best_score,
                        "submission_count": submission_count,
                        "last_submission": now
                    })\
                    .eq("nickname", nickname)\
                    .execute()
            else:
                # 새로 생성
                self.supabase.table(self.TABLE_NAME)\
                    .insert({
                        "nickname": nickname,
                        "best_score": score,
                        "submission_count": 1,
                        "last_submission": now,
                        "created_at": now
                    })\
                    .execute()
        except Exception as e:
            print(f"리더보드 업데이트 오류: {e}")
            raise
    
    def get_leaderboard(self) -> List[LeaderboardEntry]:
        """리더보드 반환 (점수 높은 순)"""
        if not self.supabase:
            return []
        
        try:
            # 점수 내림차순으로 정렬하여 가져오기
            response = self.supabase.table(self.TABLE_NAME)\
                .select("*")\
                .order("best_score", desc=True)\
                .limit(100)\
                .execute()
            
            entries = []
            for row in response.data:
                entries.append(LeaderboardEntry(
                    nickname=row.get("nickname", ""),
                    score=row.get("best_score", 0),
                    timestamp=row.get("last_submission", ""),
                    submission_count=row.get("submission_count", 0)
                ))
            
            return entries
        except Exception as e:
            print(f"리더보드 조회 오류: {e}")
            return []


class SupabasePromptHistoryManager:
    """Supabase를 사용한 프롬프트 히스토리 관리"""
    
    TABLE_NAME = "prompt_history"
    
    def __init__(self):
        self.supabase = None
        if is_supabase_available():
            self.supabase = get_supabase()
        else:
            print("⚠️ Supabase를 사용할 수 없습니다. 로컬 JSON 파일을 사용합니다.")
            self.supabase = None
    
    def add_submission(self, nickname: str, prompt: str, score: float):
        """프롬프트 제출 기록 추가"""
        if not self.supabase:
            raise ValueError("Supabase가 초기화되지 않았습니다.")
        
        try:
            # 해당 사용자의 기존 제출 횟수 확인
            existing = self.supabase.table(self.TABLE_NAME)\
                .select("*")\
                .eq("nickname", nickname)\
                .execute()
            
            if existing.data:
                # 기존 레코드 업데이트
                current_data = existing.data[0]
                submissions = current_data.get("submissions", [])
                submission_number = len(submissions) + 1
            else:
                # 새 레코드 생성
                submissions = []
                submission_number = 1
            
            # 새 제출 추가
            new_submission = {
                "prompt": prompt,
                "score": score,
                "timestamp": datetime.now().isoformat(),
                "submission_number": submission_number
            }
            
            submissions.append(new_submission)
            
            # Supabase에 저장 (upsert)
            self.supabase.table(self.TABLE_NAME)\
                .upsert({
                    "nickname": nickname,
                    "submissions": submissions,
                    "last_updated": datetime.now().isoformat()
                })\
                .execute()
                
        except Exception as e:
            print(f"히스토리 저장 오류: {e}")
            raise
    
    def get_history(self, nickname: str) -> List[PromptHistoryEntry]:
        """사용자의 프롬프트 히스토리 반환 (최신순)"""
        if not self.supabase:
            return []
        
        try:
            response = self.supabase.table(self.TABLE_NAME)\
                .select("*")\
                .eq("nickname", nickname)\
                .execute()
            
            if not response.data:
                return []
            
            data = response.data[0]
            submissions = data.get("submissions", [])
            
            entries = []
            for sub in submissions:
                entries.append(PromptHistoryEntry(
                    prompt=sub.get("prompt", ""),
                    score=sub.get("score", 0),
                    timestamp=sub.get("timestamp", ""),
                    submission_number=sub.get("submission_number", 0)
                ))
            
            # 최신 제출부터 표시 (역순 정렬)
            entries.reverse()
            return entries
        except Exception as e:
            print(f"히스토리 조회 오류: {e}")
            return []

