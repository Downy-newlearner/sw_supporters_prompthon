# 🚀 배포 실행 단계 (순서대로 진행)

## ⚡ 현재 상태
✅ GitHub 푸시 완료 (deployment 브랜치)
✅ 모든 배포 파일 준비 완료
✅ Supabase 연동 코드 준비 완료

---

## 1단계: Supabase 프로젝트 생성 (5분)

### 1.1 프로젝트 생성
1. **접속**: https://supabase.com/
2. **GitHub로 로그인**
3. **"New Project"** 클릭
4. 프로젝트 이름: `prompthon-leaderboard`
5. 데이터베이스 비밀번호 설정 (기억해야 함!)
6. 지역: **Northeast Asia (Seoul)** 선택
7. **"Create new project"** 클릭
8. 프로젝트 생성 대기 (약 2분)

### 1.2 테이블 생성
1. 좌측 메뉴 → **SQL Editor**
2. **"New query"** 클릭
3. `SUPABASE_SETUP.md` 파일의 SQL 코드 복사하여 실행:
   - 리더보드 테이블 생성 SQL
   - 프롬프트 히스토리 테이블 생성 SQL
   - RLS 정책 설정 SQL

### 1.3 API 키 확인
1. 좌측 메뉴 → **Settings** → **API**
2. 다음 정보 **복사** (다음 단계에서 사용):
   - **Project URL**: 예) `https://xxxxx.supabase.co`
   - **anon/public key**: 예) `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

**⚠️ 중요**: 이 정보를 Railway 환경변수에 설정할 예정입니다.

---

## 2단계: Railway 백엔드 배포 (3분)

### 2.1 Railway 프로젝트 생성
1. **접속**: https://railway.app/
2. **GitHub로 로그인**
3. **"New Project"** 클릭
4. **"Deploy from GitHub repo"** 선택
5. 리포지토리: `sw_supporters_prompthon` 선택
6. ⚠️ **브랜치: `deployment`** 선택 (중요!)
7. **Deploy** 클릭

### 2.2 환경변수 설정
Railway 대시보드 → **Variables** 탭 → **+ New Variable** 클릭하여 추가:

#### 필수 환경변수:

1. **USE_SUPABASE**
   ```
   Name: USE_SUPABASE
   Value: true
   ```

2. **SUPABASE_URL**
   ```
   Name: SUPABASE_URL
   Value: https://xxxxx.supabase.co
   ```
   ⚠️ 1단계에서 복사한 Project URL 사용

3. **SUPABASE_ANON_KEY**
   ```
   Name: SUPABASE_ANON_KEY
   Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
   ⚠️ 1단계에서 복사한 anon key 사용

4. **SOLAR_API_KEY_1** ~ **SOLAR_API_KEY_6**
   ```
   Name: SOLAR_API_KEY_1
   Value: 실제_API_키_1
   ```
   (나머지 2~6도 동일하게 추가)

### 2.3 배포 확인
1. Railway 대시보드에서 배포 진행 상황 확인
2. 배포 완료 후 **Settings** → **Domains**에서 URL 확인
   - 예: `https://xxxxx.up.railway.app`
3. **URL 복사** (다음 단계에서 사용)
4. 브라우저에서 `https://xxxxx.up.railway.app/api/health` 접속
   - `{"status":"healthy",...}` 응답이 오면 성공!
5. Railway 로그에서 다음 메시지 확인:
   ```
   ✅ Supabase 클라이언트 초기화 완료
   ✅ Supabase를 사용합니다.
   ```

---

## 3단계: Netlify 프론트엔드 배포 (2분)

### 3.1 Netlify 프로젝트 생성
1. **접속**: https://www.netlify.com/
2. **GitHub로 로그인**
3. **"Add new site"** → **"Import an existing project"**
4. **GitHub** 선택
5. 리포지토리: `sw_supporters_prompthon` 선택
6. ⚠️ **브랜치: `deployment`** 선택 (중요!)
7. **Show advanced** 클릭하여 빌드 설정:
   - **Base directory**: (비워두기)
   - **Build command**: `echo 'No build needed'`
   - **Publish directory**: `frontend`
8. **Deploy site** 클릭

### 3.2 환경변수 설정
Netlify → **Site settings** → **Environment variables** → **Add variable**:

1. **BACKEND_URL**
   ```
   Key: BACKEND_URL
   Value: https://your-railway-url.up.railway.app
   ```
   ⚠️ `your-railway-url`을 2단계에서 복사한 Railway URL로 변경!

2. **NETLIFY_ENV**
   ```
   Key: NETLIFY_ENV
   Value: production
   ```

### 3.3 netlify.toml 수정 (Railway URL 반영)
1. GitHub에서 `netlify.toml` 파일 열기
2. `your-railway-app`을 실제 Railway URL로 변경:
   ```
   to = "https://your-actual-railway-url.up.railway.app/api/:splat"
   ```
3. 변경사항 커밋 및 푸시:
   ```bash
   git add netlify.toml
   git commit -m "Update Railway URL in netlify.toml"
   git push origin deployment
   ```
4. Netlify가 자동으로 재배포됨

### 3.4 배포 확인
1. Netlify 대시보드에서 배포 완료 확인
2. **Site settings** → **Domain management**에서 URL 확인
   - 예: `https://xxxxx.netlify.app`
3. **URL 복사** (학생들에게 공유할 URL)
4. 브라우저에서 접속하여 테스트:
   - 로그인 테스트
   - 프롬프트 제출 테스트
   - 리더보드 확인

---

## ✅ 최종 체크리스트

배포가 성공적으로 완료되었는지 확인:

- [ ] Supabase 테이블 생성 완료 (leaderboard, prompt_history)
- [ ] Railway 배포 완료 및 `/api/health` 응답 확인
- [ ] Railway 로그에서 Supabase 초기화 메시지 확인
- [ ] Netlify 배포 완료 및 접속 확인
- [ ] Supabase 대시보드에서 데이터 저장되는지 확인
- [ ] 로그인 기능 테스트
- [ ] 프롬프트 제출 기능 테스트
- [ ] 리더보드 표시 확인
- [ ] WebSocket 연결 확인 (콘솔 로그 확인)

---

## 🎉 배포 완료!

**학생들에게 공유할 URL**: Netlify URL
- 예: `https://prompthon.netlify.app`

---

## 🔧 문제 해결

### Railway 배포 실패
- **로그 확인**: Railway → Deployments → 로그
- **환경변수 확인**: 모든 변수가 올바른지
- **Supabase 연결**: URL과 키가 올바른지

### Netlify 연결 실패
- **BACKEND_URL**: Railway URL이 올바른지
- **브라우저 콘솔**: 오류 메시지 확인
- **CORS 오류**: Railway에서 NETLIFY_URL 환경변수 설정

### Supabase 연결 실패
- **USE_SUPABASE**: `true`로 설정되었는지
- **SUPABASE_URL**: 올바른 URL인지 (https:// 포함)
- **SUPABASE_ANON_KEY**: 올바른 키인지
- **Railway 로그**: Supabase 초기화 메시지 확인

### 데이터가 저장되지 않음
- **RLS 정책**: Supabase에서 RLS 정책 확인
- **Railway 로그**: 오류 메시지 확인
- **Supabase 대시보드**: Table Editor에서 데이터 확인

---

## 📞 다음 단계

1. **Supabase RLS 정책 확인** (프로덕션 안전을 위해)
   - `SUPABASE_SETUP.md` 참고

2. **커스텀 도메인 설정** (선택사항)
   - Netlify와 Railway 모두 커스텀 도메인 지원

3. **모니터링 설정**
   - Railway와 Netlify 대시보드에서 트래픽 모니터링
