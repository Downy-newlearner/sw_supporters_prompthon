-- ============================================
-- Supabase RLS 정책 설정 (안전한 버전)
-- ============================================
-- 이 SQL은 데이터를 변경하지 않고 정책만 설정합니다.
-- 경고 없이 안전하게 실행할 수 있습니다.
-- ============================================

-- 1단계: 기존 정책 확인 (선택사항)
-- 실행 후 결과를 확인하여 정책이 이미 있는지 확인하세요
SELECT schemaname, tablename, policyname 
FROM pg_policies 
WHERE tablename IN ('leaderboard', 'prompt_history');

-- 2단계: 리더보드 테이블 RLS 설정
-- RLS 활성화 (이미 활성화되어 있어도 오류 없음)
ALTER TABLE leaderboard ENABLE ROW LEVEL SECURITY;

-- 읽기 정책 생성 (기존 정책이 있으면 오류 발생하지만 무시 가능)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'leaderboard' 
        AND policyname = 'Allow public read access'
    ) THEN
        CREATE POLICY "Allow public read access" ON leaderboard
            FOR SELECT
            USING (true);
    END IF;
END $$;

-- 쓰기 정책 생성 (기존 정책이 있으면 오류 발생하지만 무시 가능)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'leaderboard' 
        AND policyname = 'Allow anon insert and update'
    ) THEN
        CREATE POLICY "Allow anon insert and update" ON leaderboard
            FOR ALL
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;

-- 3단계: 프롬프트 히스토리 테이블 RLS 설정
-- RLS 활성화 (이미 활성화되어 있어도 오류 없음)
ALTER TABLE prompt_history ENABLE ROW LEVEL SECURITY;

-- 읽기 정책 생성
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'prompt_history' 
        AND policyname = 'Allow public read access'
    ) THEN
        CREATE POLICY "Allow public read access" ON prompt_history
            FOR SELECT
            USING (true);
    END IF;
END $$;

-- 쓰기 정책 생성
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'prompt_history' 
        AND policyname = 'Allow anon insert and update'
    ) THEN
        CREATE POLICY "Allow anon insert and update" ON prompt_history
            FOR ALL
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;

-- 4단계: 정책 확인
-- 설정이 완료되었는지 확인
SELECT schemaname, tablename, policyname, cmd, qual, with_check
FROM pg_policies 
WHERE tablename IN ('leaderboard', 'prompt_history')
ORDER BY tablename, policyname;

