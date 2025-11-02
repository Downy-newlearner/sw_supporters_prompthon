# 배포 가이드: GitHub + Netlify + Railway + Firebase

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
                       │  Firebase       │ → Firestore DB
                       │  Firestore      │   (리더보드, 히스토리)
                       └─────────────────┘
```

## 🚀 배포 순서

### 1단계: Firebase 프로젝트 설정

1. **Firebase 콘솔 접속**
   - https://console.firebase.google.com/
   - "프로젝트 추가" 클릭

2. **프로젝트 생성**
   - 프로젝트 이름 입력 (예: "prompthon-leaderboard")
   - Google Analytics 설정 (선택사항)

3. **Firestore Database 생성**
   - 좌측 메뉴에서 "Firestore Database" 클릭
   - "데이터베이스 만들기" 클릭
   - "테스트 모드에서 시작" 선택 (나중에 보안 규칙 설정)
   - 위치 선택 (asia-northeast3 권장 - 서울)

4. **서비스 계정 키 발급**
   - 좌측 메뉴 → 프로젝트 설정 → 서비스 계정
   - "새 비공개 키 생성" 클릭
   - JSON 파일 다운로드 → `firebase-key.json`으로 저장
   - ⚠️ 이 파일은 절대 Git에 커밋하지 마세요!

5. **보안 규칙 설정** (프로덕션 전에 필수)
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       // 리더보드는 읽기만 허용, 쓰기는 인증된 서버만
       match /leaderboard/{nickname} {
         allow read: if true;
         allow write: if false;  // 서버에서만 쓰기
       }
       
       // 히스토리는 사용자 본인만 읽기, 쓰기는 서버만
       match /prompt_history/{nickname} {
         allow read: if request.auth != null && request.auth.uid == nickname;
         allow write: if false;  // 서버에서만 쓰기
       }
     }
   }
   ```

### 2단계: Railway 백엔드 배포

1. **Railway 계정 생성**
   - https://railway.app 접속
   - GitHub 계정으로 로그인

2. **새 프로젝트 생성**
   - "New Project" 클릭
   - "Deploy from GitHub repo" 선택
   - GitHub 리포지토리 선택

3. **환경변수 설정**
   Railway 대시보드 → Variables 탭에서 다음 환경변수 설정:

   ```
   USE_FIREBASE=true
   
   SOLAR_API_KEY_1=실제_키_1
   SOLAR_API_KEY_2=실제_키_2
   SOLAR_API_KEY_3=실제_키_3
   SOLAR_API_KEY_4=실제_키_4
   SOLAR_API_KEY_5=실제_키_5
   SOLAR_API_KEY_6=실제_키_6
   
   # Firebase 설정 (방법 1: JSON 문자열)
   FIREBASE_CONFIG_JSON={"type":"service_account",...}
   
   # 또는 방법 2: Firebase 키 파일 업로드
   # Railway에서 파일 업로드 기능 사용하여 firebase-key.json 업로드
   ```

4. **Firebase 키 파일 업로드** (방법 1 - JSON 문자열 권장)
   - 다운로드한 `firebase-key.json` 파일 열기
   - 전체 내용을 한 줄로 만들기 (줄바꿈 제거)
   - `FIREBASE_CONFIG_JSON` 환경변수에 붙여넣기

5. **배포 확인**
   - Railway 대시보드에서 배포 진행 상황 확인
   - 배포 완료 후 생성된 URL 확인 (예: `https://xxxxx.up.railway.app`)
   - `https://xxxxx.up.railway.app/api/health` 접속하여 서버 상태 확인

6. **도메인 설정** (선택사항)
   - Railway → Settings → Domains
   - 커스텀 도메인 추가 가능

### 3단계: Netlify 프론트엔드 배포

1. **Netlify 계정 생성**
   - https://www.netlify.com 접속
   - GitHub 계정으로 로그인

2. **새 사이트 생성**
   - "Add new site" → "Import an existing project"
   - GitHub 리포지토리 선택
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
- [ ] `USE_FIREBASE=true`
- [ ] `SOLAR_API_KEY_1` ~ `SOLAR_API_KEY_6`
- [ ] `FIREBASE_CONFIG_JSON` (또는 `FIREBASE_KEY_FILE`)
- [ ] `PORT` (자동 설정)

### Netlify (프론트엔드)
- [ ] `BACKEND_URL` (Railway URL)
- [ ] `NETLIFY_ENV=production`

## 📝 Firebase Firestore 데이터 구조

### leaderboard 컬렉션
```json
{
  "nickname": "학생1",
  "best_score": 95.5,
  "submission_count": 3,
  "last_submission": "2025-11-02T15:30:00",
  "created_at": "2025-11-02T14:00:00"
}
```

### prompt_history 컬렉션
```json
{
  "nickname": "학생1",
  "submissions": [
    {
      "prompt": "프롬프트 내용...",
      "score": 95.5,
      "timestamp": "2025-11-02T15:30:00",
      "submission_number": 1
    }
  ],
  "last_updated": "2025-11-02T15:30:00"
}
```

## 🔍 문제 해결

### Firebase 연결 실패
- Firebase 키 파일이 올바른지 확인
- `USE_FIREBASE=true` 설정 확인
- Railway 로그 확인

### WebSocket 연결 실패
- `BACKEND_URL` 환경변수 확인
- Railway URL이 올바른지 확인
- 브라우저 콘솔 오류 확인

### CORS 오류
- `backend/main.py`의 CORS 설정 확인
- Netlify URL을 `allow_origins`에 추가

### 데이터가 저장되지 않음
- Firebase 보안 규칙 확인
- Railway 로그 확인
- Firestore 콘솔에서 데이터 확인

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
   - Firebase 콘솔에서 데이터 확인
   - Netlify 대시보드에서 트래픽 확인

## 💰 예상 비용

- **Railway**: 무료 티어 (월 $5 크레딧) - 충분함
- **Netlify**: 무료 티어 (충분함)
- **Firebase**: 무료 티어 (일일 읽기 50,000 / 쓰기 20,000) - 충분함

총 비용: **$0** (22명 학생 기준)

## 📚 추가 리소스

- [Railway 문서](https://docs.railway.app/)
- [Netlify 문서](https://docs.netlify.com/)
- [Firebase Firestore 문서](https://firebase.google.com/docs/firestore)

