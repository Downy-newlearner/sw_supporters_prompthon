import pandas as pd
import os
from typing import Dict, List, Tuple
import difflib

class Evaluator:
    def __init__(self, test_csv_path: str, answer_csv_path: str):
        """평가 시스템 초기화"""
        self.test_csv_path = test_csv_path
        self.answer_csv_path = answer_csv_path
        self.test_set = None
        self.answer_set = None
        self._load_test_data()
    
    def _load_test_data(self):
        """테스트 데이터와 정답 데이터 로드"""
        # 테스트 데이터 (err_sentence)
        df_test = pd.read_csv(self.test_csv_path)
        df_test = df_test.dropna(subset=['err_sentence'])
        self.test_set = df_test
        
        # 정답 데이터 (cor_sentence)
        df_answer = pd.read_csv(self.answer_csv_path)
        df_answer = df_answer.dropna(subset=['cor_sentence'])
        self.answer_set = df_answer
        
        print(f"Test set 크기: {len(self.test_set)} 샘플")
        print(f"Answer set 크기: {len(self.answer_set)} 샘플")
    
    def _get_edit_operations(self, source: str, target: str) -> List[Tuple[str, int, int, str, str]]:
        """두 문자열 간의 편집 연산 추출
        Returns: List of (operation, i1, i2, source_text, target_text)
        """
        matcher = difflib.SequenceMatcher(None, source, target)
        operations = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            operations.append((tag, i1, i2, source[i1:i2], target[j1:j2]))
        
        return operations
    
    def calculate_correction_score(self, err_sentence: str, predicted: str, cor_sentence: str) -> Dict:
        """
        TP / (TP + FP + FM) 기준으로 점수 계산
        단순화된 문자 일치 기반 방식 사용
        
        Args:
            err_sentence: 원본 오류 문장
            predicted: 모델이 교정한 문장
            cor_sentence: 정답 교정 문장
        
        Returns:
            Dict with TP, FP, FM counts and score
        """
        # 정답과 일치하는지 먼저 확인
        if predicted == cor_sentence:
            # 완벽하게 일치하는 경우
            return {
                'tp': 100,
                'fp': 0,
                'fm': 0,
                'score': 1.0
            }
        
        # 원본 → 정답의 차이점 추출
        required_edits = self._get_edit_operations(err_sentence, cor_sentence)
        
        # 원본 → 예측의 차이점 추출
        predicted_edits = self._get_edit_operations(err_sentence, predicted)
        
        # 교정 사항 추출 (문자열 변환 내용)
        required_changes = set()
        for tag, i1, i2, src, tgt in required_edits:
            if tag != 'equal':
                required_changes.add((src, tgt))
        
        predicted_changes = set()
        for tag, i1, i2, src, tgt in predicted_edits:
            if tag != 'equal':
                predicted_changes.add((src, tgt))
        
        # TP: 올바른 교정 (일치하는 교정)
        tp = len(required_changes & predicted_changes)
        
        # FP: 잘못된/불필요한 교정
        fp = len(predicted_changes - required_changes)
        
        # FM: 놓친 교정
        fm = len(required_changes - predicted_changes)
        
        # 점수 계산
        denominator = tp + fp + fm
        score = tp / denominator if denominator > 0 else 0.0
        
        return {
            'tp': tp,
            'fp': fp,
            'fm': fm,
            'score': score
        }
    
    def evaluate_submission(self, predictions: List[Tuple[str, str]]) -> Dict:
        """
        제출물 평가 (TP / (TP + FP + FM) 기준)
        predictions: [(id, corrected_sentence), ...]
        """
        if self.test_set is None or self.answer_set is None:
            return {
                "error": "Test set 또는 Answer set이 준비되지 않았습니다.",
                "score": 0.0
            }
        
        # predictions를 딕셔너리로 변환
        pred_dict = {id_val: cor_sent for id_val, cor_sent in predictions}
        
        # test_set과 answer_set을 ID로 매칭
        total_tp = 0
        total_fp = 0
        total_fm = 0
        evaluated_count = 0
        individual_scores = []
        
        # test_set과 answer_set 병합
        merged = self.test_set.merge(self.answer_set, on='id', how='inner')
        
        for idx, row in merged.iterrows():
            row_id = row['id']
            err_sentence = row['err_sentence']
            cor_sentence = row['cor_sentence']
            
            if row_id in pred_dict:
                predicted = pred_dict[row_id]
                
                # TP, FP, FM 계산
                result = self.calculate_correction_score(err_sentence, predicted, cor_sentence)
                
                total_tp += result['tp']
                total_fp += result['fp']
                total_fm += result['fm']
                individual_scores.append(result['score'])
                evaluated_count += 1
        
        if evaluated_count == 0:
            return {
                "error": "평가할 수 있는 데이터가 없습니다.",
                "score": 0.0
            }
        
        # 전체 점수 계산
        denominator = total_tp + total_fp + total_fm
        final_score = (total_tp / denominator * 100) if denominator > 0 else 0.0
        
        # 평균 개별 점수
        avg_individual_score = (sum(individual_scores) / len(individual_scores) * 100) if individual_scores else 0.0
        
        return {
            "score": round(final_score, 2),
            "avg_individual_score": round(avg_individual_score, 2),
            "total_tp": total_tp,
            "total_fp": total_fp,
            "total_fm": total_fm,
            "evaluated_samples": evaluated_count,
            "total_test_samples": len(merged)
        }
    
    def get_test_ids(self) -> List[str]:
        """Test set의 ID 리스트 반환"""
        if self.test_set is None:
            return []
        return self.test_set['id'].tolist()

