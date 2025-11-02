from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json
import os

class LoginRequest(BaseModel):
    nickname: str

class LoginResponse(BaseModel):
    success: bool
    nickname: str
    message: str

class SubmitRequest(BaseModel):
    nickname: str
    prompt: str

class SubmitResponse(BaseModel):
    success: bool
    message: str
    score: Optional[float] = None
    total_processed: Optional[int] = None
    total_tp: Optional[int] = None
    total_fp: Optional[int] = None
    total_fm: Optional[int] = None
    
class LeaderboardEntry(BaseModel):
    nickname: str
    score: float
    timestamp: str
    submission_count: int

class LeaderboardResponse(BaseModel):
    leaderboard: List[LeaderboardEntry]

class ProgressUpdate(BaseModel):
    current: int
    total: int
    message: str

class PromptHistoryEntry(BaseModel):
    prompt: str
    score: float
    timestamp: str
    submission_number: int

class PromptHistoryResponse(BaseModel):
    history: List[PromptHistoryEntry]
    total_submissions: int

# 리더보드 관리 클래스
class LeaderboardManager:
    def __init__(self, filepath: str = "leaderboard.json"):
        self.filepath = filepath
        self.data = self._load()
    
    def _load(self):
        """리더보드 데이터 로드"""
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save(self):
        """리더보드 데이터 저장"""
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def update_score(self, nickname: str, score: float):
        """점수 업데이트"""
        if nickname not in self.data:
            self.data[nickname] = {
                "best_score": score,
                "submission_count": 1,
                "last_submission": datetime.now().isoformat()
            }
        else:
            self.data[nickname]["submission_count"] += 1
            self.data[nickname]["last_submission"] = datetime.now().isoformat()
            if score > self.data[nickname]["best_score"]:
                self.data[nickname]["best_score"] = score
        
        self._save()
    
    def get_leaderboard(self) -> List[LeaderboardEntry]:
        """리더보드 반환 (점수 높은 순)"""
        entries = []
        for nickname, data in self.data.items():
            entries.append(LeaderboardEntry(
                nickname=nickname,
                score=data["best_score"],
                timestamp=data["last_submission"],
                submission_count=data["submission_count"]
            ))
        
        # 점수 내림차순 정렬
        entries.sort(key=lambda x: x.score, reverse=True)
        return entries

# 프롬프트 히스토리 관리 클래스
class PromptHistoryManager:
    def __init__(self, filepath: str = "prompt_history.json"):
        self.filepath = filepath
        self.data = self._load()
    
    def _load(self):
        """히스토리 데이터 로드"""
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save(self):
        """히스토리 데이터 저장"""
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def add_submission(self, nickname: str, prompt: str, score: float):
        """프롬프트 제출 기록 추가"""
        if nickname not in self.data:
            self.data[nickname] = []
        
        self.data[nickname].append({
            "prompt": prompt,
            "score": score,
            "timestamp": datetime.now().isoformat(),
            "submission_number": len(self.data[nickname]) + 1
        })
        
        self._save()
    
    def get_history(self, nickname: str) -> List[PromptHistoryEntry]:
        """사용자의 프롬프트 히스토리 반환 (최신순)"""
        if nickname not in self.data:
            return []
        
        entries = []
        for entry in self.data[nickname]:
            entries.append(PromptHistoryEntry(
                prompt=entry["prompt"],
                score=entry["score"],
                timestamp=entry["timestamp"],
                submission_number=entry["submission_number"]
            ))
        
        # 최신 제출부터 표시 (역순 정렬)
        entries.reverse()
        return entries

