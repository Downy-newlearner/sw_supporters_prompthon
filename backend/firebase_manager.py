"""Firebase Firestore를 사용한 리더보드 및 히스토리 관리"""
from typing import List, Optional
from datetime import datetime
from firebase_admin import firestore
from firebase_config import get_db, is_firebase_available
from models import LeaderboardEntry, PromptHistoryEntry

class FirebaseLeaderboardManager:
    """Firebase Firestore를 사용한 리더보드 관리"""
    
    COLLECTION_NAME = "leaderboard"
    
    def __init__(self):
        self.db = None
        if is_firebase_available():
            self.db = get_db()
        else:
            print("⚠️ Firebase를 사용할 수 없습니다. 로컬 JSON 파일을 사용합니다.")
            self.db = None
    
    def update_score(self, nickname: str, score: float):
        """점수 업데이트"""
        if not self.db:
            raise ValueError("Firebase가 초기화되지 않았습니다.")
        
        doc_ref = self.db.collection(self.COLLECTION_NAME).document(nickname)
        doc = doc_ref.get()
        
        now = datetime.now().isoformat()
        
        if doc.exists:
            data = doc.to_dict()
            submission_count = data.get("submission_count", 0) + 1
            best_score = max(data.get("best_score", 0), score)
            
            doc_ref.update({
                "best_score": best_score,
                "submission_count": submission_count,
                "last_submission": now
            })
        else:
            doc_ref.set({
                "nickname": nickname,
                "best_score": score,
                "submission_count": 1,
                "last_submission": now,
                "created_at": now
            })
    
    def get_leaderboard(self) -> List[LeaderboardEntry]:
        """리더보드 반환 (점수 높은 순)"""
        if not self.db:
            return []
        
        try:
            # 점수 내림차순으로 정렬하여 가져오기
            docs = self.db.collection(self.COLLECTION_NAME)\
                .order_by("best_score", direction=firestore.Query.DESCENDING)\
                .limit(100)\
                .stream()
            
            entries = []
            for doc in docs:
                data = doc.to_dict()
                entries.append(LeaderboardEntry(
                    nickname=data.get("nickname", doc.id),
                    score=data.get("best_score", 0),
                    timestamp=data.get("last_submission", ""),
                    submission_count=data.get("submission_count", 0)
                ))
            
            return entries
        except Exception as e:
            print(f"리더보드 조회 오류: {e}")
            return []


class FirebasePromptHistoryManager:
    """Firebase Firestore를 사용한 프롬프트 히스토리 관리"""
    
    COLLECTION_NAME = "prompt_history"
    
    def __init__(self):
        self.db = None
        if is_firebase_available():
            self.db = get_db()
        else:
            print("⚠️ Firebase를 사용할 수 없습니다. 로컬 JSON 파일을 사용합니다.")
            self.db = None
    
    def add_submission(self, nickname: str, prompt: str, score: float):
        """프롬프트 제출 기록 추가"""
        if not self.db:
            raise ValueError("Firebase가 초기화되지 않았습니다.")
        
        # 해당 사용자의 제출 횟수 확인
        user_ref = self.db.collection(self.COLLECTION_NAME).document(nickname)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            submissions = user_doc.to_dict().get("submissions", [])
            submission_number = len(submissions) + 1
        else:
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
        
        # Firestore에 저장
        user_ref.set({
            "nickname": nickname,
            "submissions": submissions,
            "last_updated": datetime.now().isoformat()
        }, merge=False)
    
    def get_history(self, nickname: str) -> List[PromptHistoryEntry]:
        """사용자의 프롬프트 히스토리 반환 (최신순)"""
        if not self.db:
            return []
        
        try:
            doc = self.db.collection(self.COLLECTION_NAME).document(nickname).get()
            
            if not doc.exists:
                return []
            
            data = doc.to_dict()
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

