-- ============================================
-- Supabase RLS 정책 설정 (간단한 버전)
-- ============================================
-- 이 SQL은 경고 없이 안전하게 실행할 수 있습니다.
-- 정책이 이미 있으면 오류가 발생하지만 무시해도 됩니다.
-- ============================================

-- 리더보드 테이블 RLS 활성화
ALTER TABLE leaderboard ENABLE ROW LEVEL SECURITY;

-- 리더보드 읽기 정책 (모든 사용자가 읽기 가능)
CREATE POLICY "Allow public read access" ON leaderboard
  FOR SELECT
  USING (true);

-- 리더보드 쓰기 정책 (anon key로도 쓰기 가능)
CREATE POLICY "Allow anon insert and update" ON leaderboard
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- 프롬프트 히스토리 테이블 RLS 활성화
ALTER TABLE prompt_history ENABLE ROW LEVEL SECURITY;

-- 프롬프트 히스토리 읽기 정책 (모든 사용자가 읽기 가능)
CREATE POLICY "Allow public read access" ON prompt_history
  FOR SELECT
  USING (true);

-- 프롬프트 히스토리 쓰기 정책 (anon key로도 쓰기 가능)
CREATE POLICY "Allow anon insert and update" ON prompt_history
  FOR ALL
  USING (true)
  WITH CHECK (true);

