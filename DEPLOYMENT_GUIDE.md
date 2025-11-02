# 배포 가이드: GitHub + Netlify + Railway + Supabase

이 가이드는 22명의 학생들이 접속할 수 있도록 프롬프톤 플랫폼을 배포하는 방법을 설명합니다.

## 📋 아키텍처 개요

```
┌─────────────────┐
│   Netlify       │ → 프론트엔드 배포 (HTML/CSS/JS)
│  (프론트엔드)    │
└─────────────────┘
        │
        ├─ API 요청 → ┌─────────────────┐
        │            │   Railway       │ → FastAPI 백엔드
        │            │   (백엔드)       │   (Solar API, 평가, WebSocket)
        │            └─────────────────┘
        │
        └─ 데이터 저장 → ┌─────────────────┐
                       │  Supabase       │ → PostgreSQL DB
                       │  (Database)     │   (리더보드, 히스토리)
                       └─────────────────┘
```

## 🚀 배포 순서

### 1단계: Supabase 프로젝트 설정 (5분)

**상세 가이드**: `SUPABASE_SETUP.md` 참고

1. **Supabase 콘솔 접속**
   - https://supabase.com 접속
   - GitHub 계정으로 로그인

2. **새 프로젝트 생성**
   - "New Project" 클릭
   - 프로젝트 이름: `prompthon-leaderboard`
   - 데이터베이스 비밀번호 설정
   - 지역: `Northeast Asia (Seoul)` 선택
   - "Create new project" 클릭

3. **테이블 생성**
   - SQL Editor에서 `SUPABASE_SETUP.md`의 SQL 실행
   - `leaderboard` 테이블 생성
   - `prompt_history` 테이블 생성

4. **API 키 확인**
   - Settings → API에서 다음 정보 복사:
     - `Project URL`
     - `anon/public key`

### 2단계: Railway 백엔드 배포 (3분)

1. **Railway 계정 생성**
   - https://railway.app 접속
   - GitHub 계정으로 로그인

2. **새 프로젝트 생성**
   - "New Project" 클릭
   - "Deploy from GitHub repo" 선택
   - 리포지토리: `sw_supporters_prompthon` 선택
   - **브랜치: `deployment`** 선택 ⚠️

3. **환경변수 설정**
   Railway 대시보드 → Variables 탭에서 다음 환경변수 설정:

   ```
   USE_SUPABASE=true
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   
   SOLAR_API_KEY_1=실제_키_1
   SOLAR_API_KEY_2=실제_키_2
   SOLAR_API_KEY_3=실제_키_3
   SOLAR_API_KEY_4=실제_키_4
   SOLAR_API_KEY_5=실제_키_5
   SOLAR_API_KEY_6=실제_키_6
   ```

4. **배포 확인**
   - Railway 대시보드에서 배포 진행 상황 확인
   - 배포 완료 후 생성된 URL 확인 (예: `https://xxxxx.up.railway.app`)
   - `https://xxxxx.up.railway.app/api/health` 접속하여 서버 상태 확인
   - 로그에서 다음 메시지 확인:
     ```
     ✅ Supabase 클라이언트 초기화 완료
     ✅ Supabase를 사용합니다.
     ```

5. **도메인 설정** (선택사항)
   - Railway → Settings → Domains
   - 커스텀 도메인 추가 가능

### 3단계: Netlify 프론트엔드 배포 (2분)

1. **Netlify 계정 생성**
   - https://www.netlify.com 접속
   - GitHub 계정으로 로그인

2. **새 사이트 생성**
   - "Add new site" → "Import an existing project"
   - GitHub 리포지토리 선택
   - **브랜치: `deployment`** 선택 ⚠️
   - 빌드 설정:
     - **Base directory**: (비워두기)
     - **Build command**: `echo 'No build needed'`
     - **Publish directory**: `frontend`

3. **환경변수 설정**
   Netlify → Site settings → Environment variables:

   ```
   BACKEND_URL=https://your-railway-app.up.railway.app
   NETLIFY_ENV=production
   ```

4. **netlify.toml 수정**
   `netlify.toml` 파일에서 `your-railway-app`을 실제 Railway URL로 변경:
   
   ```toml
   [[redirects]]
     from = "/api/*"
     to = "https://your-actual-railway-url.up.railway.app/api/:splat"
   ```

5. **배포 확인**
   - Netlify에서 자동으로 배포 시작
   - 배포 완료 후 생성된 URL 확인 (예: `https://xxxxx.netlify.app`)
   - 접속하여 테스트

### 4단계: WebSocket 설정

Netlify는 WebSocket을 직접 프록시할 수 없으므로, 프론트엔드 코드에서 백엔드 URL을 직접 사용해야 합니다.

`frontend/config.js` 파일이 자동으로 `BACKEND_URL` 환경변수를 읽어 WebSocket URL을 설정합니다.

확인사항:
- Netlify 환경변수에 `BACKEND_URL`이 설정되어 있는지 확인
- 브라우저 콘솔에서 WebSocket 연결 URL 확인

## 🔧 환경변수 체크리스트

### Railway (백엔드)
- [ ] `USE_SUPABASE=true`
- [ ] `SUPABASE_URL` (Supabase 프로젝트 URL)
- [ ] `SUPABASE_ANON_KEY` (Supabase anon key)
- [ ] `SOLAR_API_KEY_1` ~ `SOLAR_API_KEY_6`
- [ ] `PORT` (자동 설정)

### Netlify (프론트엔드)
- [ ] `BACKEND_URL` (Railway URL)
- [ ] `NETLIFY_ENV=production`

## 📝 Supabase 데이터 구조

### leaderboard 테이블
```sql
nickname (TEXT, PRIMARY KEY)
best_score (REAL)
submission_count (INTEGER)
last_submission (TIMESTAMPTZ)
created_at (TIMESTAMPTZ)
```

### prompt_history 테이블
```sql
nickname (TEXT, PRIMARY KEY)
submissions (JSONB)  -- 배열 형태로 저장
last_updated (TIMESTAMPTZ)
```

## 🔍 문제 해결

### Supabase 연결 실패
- `SUPABASE_URL`이 올바른지 확인 (https:// 포함)
- `SUPABASE_ANON_KEY`가 올바른지 확인
- Railway 로그 확인

### WebSocket 연결 실패
- `BACKEND_URL` 환경변수 확인
- Railway URL이 올바른지 확인
- 브라우저 콘솔 오류 확인

### CORS 오류
- `backend/main.py`의 CORS 설정 확인
- Netlify URL을 `allow_origins`에 추가

### 데이터가 저장되지 않음
- Supabase RLS 정책 확인
- Railway 로그 확인
- Supabase 대시보드에서 데이터 확인

## 🎉 배포 완료 후

1. **테스트**
   - 로그인 테스트
   - 프롬프트 제출 테스트
   - 리더보드 확인
   - 히스토리 확인

2. **학생들에게 공유**
   - Netlify URL 공유 (예: `https://prompthon.netlify.app`)
   - 사용 방법 안내

3. **모니터링**
   - Railway 대시보드에서 로그 확인
   - Supabase 대시보드에서 데이터 확인
   - Netlify 대시보드에서 트래픽 확인

## 💰 예상 비용

- **Railway**: 무료 티어 (월 $5 크레딧) - 충분함
- **Netlify**: 무료 티어 (충분함)
- **Supabase**: 무료 티어 (500MB DB, 일일 50,000 요청) - 충분함

총 비용: **$0** (22명 학생 기준)

## 📚 추가 리소스

- [Railway 문서](https://docs.railway.app/)
- [Netlify 문서](https://docs.netlify.com/)
- [Supabase 문서](https://supabase.com/docs)
- [Supabase 설정 가이드](./SUPABASE_SETUP.md)
