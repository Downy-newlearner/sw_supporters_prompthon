# 👤 사용자가 해야 할 작업 (순서대로 진행)

## 📋 현재 상태
✅ 코드 변경 완료 (Firebase → Supabase)
✅ 문서 업데이트 완료
⚠️ **이제 GitHub에 푸시하고 배포를 진행하세요!**

---

## 1단계: 변경사항 커밋 및 푸시

```bash
git add -A
git commit -m "Firebase → Supabase 전환: Railway + Supabase DB 구성"
git push origin deployment
```

---

## 2단계: Supabase 프로젝트 생성 및 설정 (5분)

### 2.1 Supabase 프로젝트 생성
1. https://supabase.com/ 접속
2. GitHub로 로그인
3. **"New Project"** 클릭
4. 프로젝트 이름: `prompthon-leaderboard`
5. 데이터베이스 비밀번호 설정 (기억해야 함!)
6. 지역: **Northeast Asia (Seoul)** 선택
7. **"Create new project"** 클릭
8. 프로젝트 생성 대기 (약 2분)

### 2.2 테이블 생성
1. 좌측 메뉴 → **"SQL Editor"** 클릭
2. **"New query"** 클릭
3. **`SUPABASE_SETUP.md`** 파일 열기
4. 다음 SQL 코드를 복사하여 실행:

#### 리더보드 테이블 생성
```sql
CREATE TABLE IF NOT EXISTS leaderboard (
  nickname TEXT PRIMARY KEY,
  best_score REAL NOT NULL DEFAULT 0,
  submission_count INTEGER NOT NULL DEFAULT 0,
  last_submission TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leaderboard_best_score ON leaderboard(best_score DESC);
```

#### 프롬프트 히스토리 테이블 생성
```sql
CREATE TABLE IF NOT EXISTS prompt_history (
  nickname TEXT PRIMARY KEY,
  submissions JSONB NOT NULL DEFAULT '[]'::jsonb,
  last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prompt_history_last_updated ON prompt_history(last_updated DESC);
```

#### RLS 정책 설정
```sql
ALTER TABLE leaderboard ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public read access" ON leaderboard FOR SELECT USING (true);
CREATE POLICY "Allow service role write access" ON leaderboard FOR ALL USING (auth.role() = 'service_role');

ALTER TABLE prompt_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public read access" ON prompt_history FOR SELECT USING (true);
CREATE POLICY "Allow service role write access" ON prompt_history FOR ALL USING (auth.role() = 'service_role');
```

### 2.3 API 키 확인
1. 좌측 메뉴 → **Settings** → **API**
2. 다음 정보 **복사** (다음 단계에서 사용):
   - **Project URL**: 예) `https://xxxxx.supabase.co`
   - **anon/public key**: 예) `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

---

## 3단계: Railway 환경변수 업데이트 (2분)

1. https://railway.app/ 접속
2. 배포한 프로젝트 선택
3. **Variables** 탭 클릭
4. 다음 환경변수 **수정/추가**:

### 삭제할 환경변수:
- ❌ `USE_FIREBASE`
- ❌ `FIREBASE_CONFIG_JSON`

### 추가할 환경변수:
- ✅ `USE_SUPABASE` = `true`
- ✅ `SUPABASE_URL` = `https://xxxxx.supabase.co` (2단계에서 복사한 URL)
- ✅ `SUPABASE_ANON_KEY` = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (2단계에서 복사한 키)

### 기존 환경변수 (유지):
- `SOLAR_API_KEY_1` ~ `SOLAR_API_KEY_6` (그대로 유지)

5. **재배포 트리거** (환경변수 저장 후 자동 재배포 또는 수동 재배포)
6. Railway 로그에서 다음 메시지 확인:
   ```
   ✅ Supabase 클라이언트 초기화 완료
   ✅ Supabase를 사용합니다.
   ```

---

## 4단계: 배포 확인 및 테스트 (5분)

### 4.1 Railway 확인
1. Railway → Deployments → 로그 확인
2. `https://xxxxx.up.railway.app/api/health` 접속
   - `{"status":"healthy",...}` 응답 확인

### 4.2 Netlify 확인
1. Netlify URL 접속 (예: `https://xxxxx.netlify.app`)
2. 로그인 테스트
3. 프롬프트 제출 테스트
4. 리더보드 표시 확인

### 4.3 Supabase 확인
1. Supabase 대시보드 → **Table Editor**
2. `leaderboard` 테이블에서 데이터 확인
3. `prompt_history` 테이블에서 데이터 확인

---

## ✅ 완료 체크리스트

- [ ] GitHub에 변경사항 푸시 완료
- [ ] Supabase 프로젝트 생성 완료
- [ ] Supabase 테이블 생성 완료 (leaderboard, prompt_history)
- [ ] Railway 환경변수 업데이트 완료
- [ ] Railway 재배포 완료 및 로그 확인
- [ ] Supabase 초기화 메시지 확인
- [ ] Netlify 접속 및 기능 테스트
- [ ] Supabase 대시보드에서 데이터 저장 확인

---

## 🎉 완료!

모든 작업이 완료되면 학생들에게 Netlify URL을 공유하세요!

---

## 🔧 문제 해결

### Supabase 연결 실패
- Railway 로그에서 오류 메시지 확인
- `SUPABASE_URL`과 `SUPABASE_ANON_KEY` 재확인
- Supabase 프로젝트가 활성화되어 있는지 확인

### 데이터가 저장되지 않음
- Supabase RLS 정책 확인
- Railway 로그에서 오류 확인
- Supabase Table Editor에서 직접 데이터 추가 테스트

### 기타 문제
- `DEPLOYMENT_GUIDE.md` 또는 `SUPABASE_SETUP.md` 참고
- Railway와 Supabase 로그 확인

