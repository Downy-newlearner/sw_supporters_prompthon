# 🚀 빠른 배포 가이드 (즉시 시작)

## ⚡ 10분 안에 배포하기

### 1단계: Supabase 설정 (5분)

#### 1.1 Supabase 프로젝트 생성
1. https://supabase.com/ 접속
2. "New Project" 클릭
3. 프로젝트 이름: `prompthon-leaderboard`
4. 데이터베이스 비밀번호 설정
5. 지역: **Northeast Asia (Seoul)** 선택
6. "Create new project" 클릭

#### 1.2 테이블 생성
1. 좌측 메뉴 → "SQL Editor"
2. "New query" 클릭
3. `SUPABASE_SETUP.md` 파일의 SQL 복사하여 실행:
   - 리더보드 테이블 생성
   - 프롬프트 히스토리 테이블 생성
   - RLS 정책 설정

#### 1.3 API 키 확인
1. 좌측 메뉴 → Settings → API
2. 다음 정보 복사:
   - `Project URL` (예: `https://xxxxx.supabase.co`)
   - `anon/public key` (예: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`)

### 2단계: Railway 배포 (3분)

#### 2.1 Railway 프로젝트 생성
1. https://railway.app/ 접속
2. GitHub로 로그인
3. "New Project" 클릭
4. "Deploy from GitHub repo" 선택
5. 리포지토리: `sw_supporters_prompthon` 선택
6. **브랜치**: `deployment` 선택 ⚠️

#### 2.2 환경변수 설정
Railway → Variables 탭에서 추가:

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

#### 2.3 배포 확인
- Railway 대시보드에서 배포 진행 확인
- 배포 완료 후 URL 복사 (예: `https://xxxxx.up.railway.app`)
- `https://xxxxx.up.railway.app/api/health` 접속하여 확인
- 로그에서 `✅ Supabase를 사용합니다.` 메시지 확인

### 3단계: Netlify 배포 (2분)

#### 3.1 Netlify 프로젝트 생성
1. https://www.netlify.com/ 접속
2. GitHub로 로그인
3. "Add new site" → "Import an existing project"
4. 리포지토리: `sw_supporters_prompthon` 선택
5. **브랜치**: `deployment` 선택 ⚠️
6. 빌드 설정:
   - Base directory: (비워두기)
   - Build command: `echo 'No build needed'`
   - Publish directory: `frontend`
7. "Deploy site" 클릭

#### 3.2 환경변수 설정
Netlify → Site settings → Environment variables:

```
BACKEND_URL=https://your-railway-url.up.railway.app
NETLIFY_ENV=production
```

⚠️ `your-railway-url`을 실제 Railway URL로 변경!

#### 3.3 netlify.toml 수정
1. GitHub에서 `netlify.toml` 파일 열기
2. `your-railway-app`을 실제 Railway URL로 변경
3. 커밋 및 푸시 (또는 Netlify에서 다시 배포)

#### 3.4 배포 확인
- Netlify URL 복사 (예: `https://xxxxx.netlify.app`)
- 접속하여 테스트

## ✅ 완료 체크리스트

- [ ] Supabase 프로젝트 생성 완료
- [ ] Supabase 테이블 생성 완료
- [ ] Railway 프로젝트 생성 및 배포 완료
- [ ] Railway 환경변수 설정 완료
- [ ] Railway URL 확인 (`/api/health` 접속 테스트)
- [ ] Railway 로그에서 Supabase 초기화 확인
- [ ] Netlify 프로젝트 생성 및 배포 완료
- [ ] Netlify 환경변수 설정 완료
- [ ] Netlify URL 확인 및 테스트

## 🎉 배포 완료!

Netlify URL을 학생들에게 공유하세요!

## 🔧 문제 해결

### Railway 배포 실패
- 로그 확인: Railway → Deployments → 로그 보기
- 환경변수 확인: 모든 변수가 올바르게 설정되었는지
- Supabase 설정 확인: URL과 키가 올바른지

### Netlify에서 백엔드 연결 실패
- `BACKEND_URL` 환경변수 확인
- `netlify.toml`의 URL이 올바른지 확인
- 브라우저 콘솔에서 오류 확인

### Supabase 연결 실패
- `USE_SUPABASE=true` 확인
- `SUPABASE_URL`과 `SUPABASE_ANON_KEY`가 올바른지 확인
- Railway 로그에서 Supabase 초기화 메시지 확인

## 📞 지원

문제가 발생하면:
1. Railway 로그 확인
2. Netlify 로그 확인
3. 브라우저 콘솔 확인
4. Supabase 대시보드 확인
