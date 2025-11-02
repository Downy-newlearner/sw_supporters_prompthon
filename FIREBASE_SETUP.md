# Firebase 설정 가이드

## 1. Firebase 프로젝트 생성

1. https://console.firebase.google.com/ 접속
2. "프로젝트 추가" 클릭
3. 프로젝트 이름 입력 (예: "prompthon-leaderboard")
4. Google Analytics 설정 (선택사항)

## 2. Firestore Database 생성

1. 좌측 메뉴에서 "Firestore Database" 클릭
2. "데이터베이스 만들기" 클릭
3. **"테스트 모드에서 시작"** 선택
   - ⚠️ 나중에 보안 규칙을 반드시 설정해야 합니다!
4. 위치 선택: **asia-northeast3 (Seoul)** 권장

## 3. 서비스 계정 키 발급

1. 좌측 메뉴 → ⚙️ (프로젝트 설정)
2. "서비스 계정" 탭 클릭
3. "Firebase Admin SDK" 섹션에서 "새 비공개 키 생성" 클릭
4. JSON 파일 다운로드
5. 파일 이름을 `firebase-key.json`으로 변경

⚠️ **보안 주의사항:**
- 이 파일은 **절대 Git에 커밋하지 마세요!**
- `.gitignore`에 `firebase-key.json`이 이미 포함되어 있습니다
- Railway에 환경변수로만 업로드하세요

## 4. Firebase 키 파일 사용 방법

### 방법 1: JSON 문자열로 환경변수 설정 (권장)

1. `firebase-key.json` 파일 열기
2. 전체 내용 복사
3. JSON을 한 줄로 만들기 (줄바꿈 제거)
4. Railway 환경변수 `FIREBASE_CONFIG_JSON`에 붙여넣기

예시:
```json
{"type":"service_account","project_id":"prompthon-leaderboard",...}
```

### 방법 2: 파일 경로 지정

1. Railway에 `firebase-key.json` 파일 업로드
2. Railway 환경변수 `FIREBASE_KEY_FILE`에 파일 경로 설정
   - 예: `/app/firebase-key.json`

### 방법 3: 프로젝트 루트에 배치

1. 프로젝트 루트 디렉토리에 `firebase-key.json` 파일 배치
2. Railway에서 자동으로 인식됨 (로컬 개발용)

## 5. Firestore 보안 규칙 설정

프로덕션 배포 전에 **반드시** 보안 규칙을 설정하세요!

Firestore 콘솔 → "규칙" 탭:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // 리더보드: 모든 사용자가 읽기 가능, 쓰기는 서버만
    match /leaderboard/{nickname} {
      allow read: if true;
      allow write: if false;  // 서버(Admin SDK)에서만 쓰기
    }
    
    // 프롬프트 히스토리: 서버만 읽기/쓰기
    match /prompt_history/{nickname} {
      allow read: if false;  // 서버에서만 읽기
      allow write: if false;  // 서버에서만 쓰기
    }
  }
}
```

## 6. 데이터 구조 확인

### leaderboard 컬렉션

**문서 ID**: 사용자 닉네임

```json
{
  "nickname": "학생1",
  "best_score": 95.5,
  "submission_count": 3,
  "last_submission": "2025-11-02T15:30:00.000Z",
  "created_at": "2025-11-02T14:00:00.000Z"
}
```

### prompt_history 컬렉션

**문서 ID**: 사용자 닉네임

```json
{
  "nickname": "학생1",
  "submissions": [
    {
      "prompt": "당신은 한국어 문법 전문가입니다...",
      "score": 95.5,
      "timestamp": "2025-11-02T15:30:00.000Z",
      "submission_number": 1
    },
    {
      "prompt": "다음 문장을 교정해주세요...",
      "score": 92.3,
      "timestamp": "2025-11-02T16:00:00.000Z",
      "submission_number": 2
    }
  ],
  "last_updated": "2025-11-02T16:00:00.000Z"
}
```

## 7. 테스트

1. Firebase 콘솔 → Firestore Database
2. 데이터 탭에서 컬렉션 확인
3. Railway에서 리더보드 업데이트 테스트
4. Firestore에서 데이터 확인

## 8. 문제 해결

### Firebase 초기화 실패
- 키 파일이 올바른지 확인
- 환경변수 이름 확인 (`FIREBASE_CONFIG_JSON` 또는 `FIREBASE_KEY_FILE`)
- Railway 로그 확인

### 데이터가 저장되지 않음
- 보안 규칙 확인 (테스트 모드에서 시작했는지)
- Railway에서 `USE_FIREBASE=true` 설정 확인
- Firebase 콘솔에서 직접 데이터 추가 테스트

### 권한 오류
- 서비스 계정 키가 올바른지 확인
- Firebase 프로젝트 ID 확인
- Firestore 데이터베이스가 생성되었는지 확인

