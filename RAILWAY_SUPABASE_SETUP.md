# Railway Supabase 설정 가이드

## 현재 문제
- `Invalid API key` 오류 발생
- 리더보드 조회 시 401 Unauthorized 오류

## 해결 방법

### 1. Supabase 프로젝트에서 API 키 확인

1. **Supabase 대시보드 접속**
   - https://supabase.com 접속
   - 프로젝트 선택

2. **Settings → API 이동**
   - 좌측 메뉴에서 "Settings" 클릭
   - "API" 섹션 클릭

3. **필요한 정보 확인**
   - **Project URL**: `https://xxxxx.supabase.co` 형식
   - **anon public key**: `eyJhbGci...`로 시작하는 긴 문자열
   - **service_role key**: `eyJhbGci...`로 시작하는 긴 문자열 (보안 주의!)

### 2. Railway 환경 변수 설정

Railway 대시보드 → Variables 탭에서 다음을 설정:

#### 필수 환경 변수

```
USE_SUPABASE=true
SUPABASE_URL=https://xxxxx.supabase.co  (Supabase에서 복사한 Project URL)
SUPABASE_ANON_KEY=eyJhbGci...  (Supabase에서 복사한 anon public key)
```

#### 선택적 환경 변수 (RLS 정책이 service_role을 요구하는 경우)

```
SUPABASE_KEY=eyJhbGci...  (Supabase에서 복사한 service_role key)
```

⚠️ **주의사항:**
- `SUPABASE_URL`은 `https://`로 시작해야 합니다
- `SUPABASE_ANON_KEY`와 `SUPABASE_KEY`는 공백 없이 정확히 복사해야 합니다
- 키 앞뒤에 공백이 있으면 제거하세요

### 3. RLS (Row Level Security) 정책 확인

Supabase SQL Editor에서 다음 SQL 실행하여 정책 확인:

```sql
-- 리더보드 테이블 정책 확인
SELECT * FROM pg_policies WHERE tablename = 'leaderboard';

-- 프롬프트 히스토리 테이블 정책 확인
SELECT * FROM pg_policies WHERE tablename = 'prompt_history';
```

#### RLS 정책이 없는 경우

다음 SQL을 실행하여 정책 생성:

```sql
-- 리더보드 테이블 RLS 활성화
ALTER TABLE leaderboard ENABLE ROW LEVEL SECURITY;

-- 모든 사용자가 읽기 가능 (리더보드 조회)
CREATE POLICY "Allow public read access" ON leaderboard
  FOR SELECT
  USING (true);

-- anon key로도 쓰기 가능하도록 설정 (또는 service_role key 사용)
CREATE POLICY "Allow anon insert and update" ON leaderboard
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- 프롬프트 히스토리 테이블 RLS 활성화
ALTER TABLE prompt_history ENABLE ROW LEVEL SECURITY;

-- 모든 사용자가 읽기 가능
CREATE POLICY "Allow public read access" ON prompt_history
  FOR SELECT
  USING (true);

-- anon key로도 쓰기 가능하도록 설정
CREATE POLICY "Allow anon insert and update" ON prompt_history
  FOR ALL
  USING (true)
  WITH CHECK (true);
```

### 4. 테이블이 없는 경우

SQL Editor에서 다음 SQL 실행:

```sql
-- 리더보드 테이블 생성
CREATE TABLE IF NOT EXISTS leaderboard (
  nickname TEXT PRIMARY KEY,
  best_score REAL NOT NULL DEFAULT 0,
  submission_count INTEGER NOT NULL DEFAULT 0,
  last_submission TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 프롬프트 히스토리 테이블 생성
CREATE TABLE IF NOT EXISTS prompt_history (
  nickname TEXT PRIMARY KEY,
  submissions JSONB NOT NULL DEFAULT '[]'::jsonb,
  last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 5. API 키 검증

Railway 환경 변수 설정 후:

1. **Railway 재배포**
   - 환경 변수 변경 후 자동 재배포됨
   - 또는 수동으로 "Redeploy" 클릭

2. **로그 확인**
   - Railway → Logs 탭에서 다음 메시지 확인:
   ```
   ✅ Supabase 클라이언트 초기화 완료
   ✅ Supabase를 사용합니다 (API 키 검증 완료).
   ```

3. **오류가 계속 발생하는 경우**
   - `SUPABASE_URL`이 정확한지 확인 (끝에 `/` 없어야 함)
   - `SUPABASE_ANON_KEY`가 정확히 복사되었는지 확인
   - Supabase 프로젝트의 API 키가 최신인지 확인 (키가 재생성되었을 수 있음)

### 6. 문제 해결 체크리스트

- [ ] Supabase 프로젝트가 활성 상태인가?
- [ ] `SUPABASE_URL`이 정확한가? (https:// 포함, 끝에 / 없음)
- [ ] `SUPABASE_ANON_KEY`가 정확히 복사되었는가? (공백 없음)
- [ ] `USE_SUPABASE=true`로 설정되어 있는가?
- [ ] 테이블(`leaderboard`, `prompt_history`)이 생성되었는가?
- [ ] RLS 정책이 올바르게 설정되었는가?
- [ ] Railway 재배포가 완료되었는가?

### 7. service_role key 사용 (고급)

만약 `anon key`로 계속 문제가 발생한다면:

1. **Railway 환경 변수에 추가**
   ```
   SUPABASE_KEY=eyJhbGci...  (service_role key)
   ```

2. **코드 수정 필요** (현재는 SUPABASE_ANON_KEY 우선 사용)

⚠️ **보안 주의:**
- `service_role key`는 모든 RLS 정책을 우회합니다
- 절대 공개 저장소나 클라이언트 코드에 포함하지 마세요
- Railway 환경 변수에만 저장하세요

## 테스트

설정 완료 후:

1. **리더보드 조회 테스트**
   - 프론트엔드에서 리더보드 로드
   - 오류가 없어야 함

2. **제출 테스트**
   - 프롬프트 제출
   - Supabase Table Editor에서 데이터 확인

3. **로그 확인**
   - Railway 로그에서 Supabase 관련 오류가 없어야 함

