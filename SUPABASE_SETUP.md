# Supabase 설정 가이드

## 1. Supabase 프로젝트 생성

1. **Supabase 콘솔 접속**
   - https://supabase.com 접속
   - GitHub 계정으로 로그인

2. **새 프로젝트 생성**
   - "New Project" 클릭
   - 프로젝트 이름: `prompthon-leaderboard` (또는 원하는 이름)
   - 데이터베이스 비밀번호 설정 (기억해야 함!)
   - 지역: `Northeast Asia (Seoul)` 선택
   - "Create new project" 클릭

3. **프로젝트 생성 대기** (약 2분 소요)

## 2. 데이터베이스 테이블 생성

### 2.1 SQL Editor 접속
1. 좌측 메뉴 → "SQL Editor" 클릭
2. "New query" 클릭

### 2.2 리더보드 테이블 생성
다음 SQL을 실행:

```sql
-- 리더보드 테이블 생성
CREATE TABLE IF NOT EXISTS leaderboard (
  nickname TEXT PRIMARY KEY,
  best_score REAL NOT NULL DEFAULT 0,
  submission_count INTEGER NOT NULL DEFAULT 0,
  last_submission TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 인덱스 생성 (성능 향상)
CREATE INDEX IF NOT EXISTS idx_leaderboard_best_score ON leaderboard(best_score DESC);
```

### 2.3 프롬프트 히스토리 테이블 생성
다음 SQL을 실행:

```sql
-- 프롬프트 히스토리 테이블 생성
CREATE TABLE IF NOT EXISTS prompt_history (
  nickname TEXT PRIMARY KEY,
  submissions JSONB NOT NULL DEFAULT '[]'::jsonb,
  last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 인덱스 생성 (JSON 쿼리 성능 향상)
CREATE INDEX IF NOT EXISTS idx_prompt_history_last_updated ON prompt_history(last_updated DESC);
```

### 2.4 Row Level Security (RLS) 설정

보안을 위해 RLS를 활성화하고 정책을 설정:

```sql
-- 리더보드 테이블 RLS 활성화
ALTER TABLE leaderboard ENABLE ROW LEVEL SECURITY;

-- 모든 사용자가 읽기 가능 (리더보드 조회)
CREATE POLICY "Allow public read access" ON leaderboard
  FOR SELECT
  USING (true);

-- 서버(service_role)만 쓰기 가능
-- 이 정책은 Railway에서 service_role 키를 사용할 때만 작동
CREATE POLICY "Allow service role write access" ON leaderboard
  FOR ALL
  USING (auth.role() = 'service_role');

-- 프롬프트 히스토리 테이블 RLS 활성화
ALTER TABLE prompt_history ENABLE ROW LEVEL SECURITY;

-- 모든 사용자가 읽기 가능 (자신의 히스토리 조회)
CREATE POLICY "Allow public read access" ON prompt_history
  FOR SELECT
  USING (true);

-- 서버(service_role)만 쓰기 가능
CREATE POLICY "Allow service role write access" ON prompt_history
  FOR ALL
  USING (auth.role() = 'service_role');
```

## 3. API 키 확인

1. 좌측 메뉴 → "Settings" → "API"
2. 다음 정보 확인 및 복사:
   - **Project URL**: 예) `https://xxxxx.supabase.co`
   - **anon/public key**: Railway에서 사용할 키
   - **service_role key**: ⚠️ 절대 공개하지 마세요! (서버에서만 사용)

## 4. Railway 환경변수 설정

Railway 대시보드 → Variables 탭에서 다음 환경변수 추가:

```
USE_SUPABASE=true
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

⚠️ **주의사항:**
- `SUPABASE_ANON_KEY`는 `anon/public key`를 사용하세요
- `service_role key`는 더 강력한 권한이지만, 현재 구조에서는 `anon key`로 충분합니다
- RLS 정책이 `service_role`을 요구하면 `SUPABASE_KEY`에 `service_role key`를 설정하세요

## 5. 데이터 구조 확인

### leaderboard 테이블
```sql
-- 데이터 예시
nickname    | best_score | submission_count | last_submission        | created_at
------------|------------|------------------|------------------------|------------------------
학생1       | 95.5       | 3                | 2025-11-02T15:30:00Z   | 2025-11-02T14:00:00Z
학생2       | 92.3       | 2                | 2025-11-02T16:00:00Z   | 2025-11-02T15:00:00Z
```

### prompt_history 테이블
```sql
-- 데이터 예시
nickname | submissions (JSONB)                                                                   | last_updated
---------|---------------------------------------------------------------------------------------|------------------------
학생1    | [{"prompt": "...", "score": 95.5, "timestamp": "...", "submission_number": 1}, ...] | 2025-11-02T15:30:00Z
```

## 6. 테스트

1. Railway 로그에서 다음 메시지 확인:
   ```
   ✅ Supabase 클라이언트 초기화 완료
   ✅ Supabase를 사용합니다.
   ```

2. Supabase 대시보드 → "Table Editor"에서 데이터 확인:
   - `leaderboard` 테이블
   - `prompt_history` 테이블

## 7. 문제 해결

### Supabase 연결 실패
- `SUPABASE_URL`이 올바른지 확인 (https:// 포함)
- `SUPABASE_ANON_KEY`가 올바른지 확인
- Railway 로그에서 오류 메시지 확인

### 데이터가 저장되지 않음
- RLS 정책 확인
- `service_role key` 필요 시 `SUPABASE_KEY` 환경변수 사용
- Supabase 로그 확인 (Settings → Logs)

### 권한 오류
- RLS 정책 재확인
- `anon key` 대신 `service_role key` 사용 고려 (보안 주의)

## 8. 추가 리소스

- [Supabase 문서](https://supabase.com/docs)
- [PostgreSQL 튜토리얼](https://supabase.com/docs/guides/database)
- [Row Level Security 가이드](https://supabase.com/docs/guides/auth/row-level-security)

