# 🚀 배포 빠른 시작

## 배포 완료 체크리스트

### ✅ 완료된 작업
- [x] Firebase Firestore 연동 코드 작성
- [x] Railway 배포 설정 파일 생성
- [x] Netlify 배포 설정 파일 생성
- [x] 환경변수 템플릿 생성
- [x] 배포 가이드 문서 작성

## 📋 배포 전 준비사항

1. **Firebase 프로젝트 생성 및 키 발급**
   - `FIREBASE_SETUP.md` 참고

2. **Solar API 키 6개 준비**
   - `API_KEYS_GUIDE.md` 참고

3. **GitHub 리포지토리에 푸시**
   - `deployment` 브랜치 푸시

## 🎯 배포 순서 (요약)

1. **Firebase 설정** → `FIREBASE_SETUP.md` 참고
2. **Railway 배포** → `DEPLOYMENT_GUIDE.md` 2단계 참고
3. **Netlify 배포** → `DEPLOYMENT_GUIDE.md` 3단계 참고

## 📚 상세 가이드

- **전체 배포 가이드**: `DEPLOYMENT_GUIDE.md`
- **Firebase 설정**: `FIREBASE_SETUP.md`
- **API 키 설정**: `API_KEYS_GUIDE.md`

## 🔧 주요 변경사항

### 백엔드
- `firebase_config.py`: Firebase Admin SDK 초기화
- `firebase_manager.py`: Firestore 기반 리더보드/히스토리 관리
- `main.py`: Firebase 사용 여부 환경변수로 제어 (`USE_FIREBASE`)

### 프론트엔드
- `config.js`: 환경별 설정 (백엔드 URL)
- `script.js`: 동적 백엔드 URL 사용
- `netlify.toml`: Netlify 배포 설정

### 배포 설정
- `Procfile`: Railway 배포 설정
- `railway.json`: Railway 상세 설정
- `nixpacks.toml`: Nixpacks 빌드 설정

## 💡 빠른 팁

### 로컬 테스트 (Firebase 없이)
```bash
# 환경변수 설정 안 함 → 자동으로 JSON 파일 사용
./run.sh
```

### Firebase 사용 (로컬)
```bash
export USE_FIREBASE=true
export FIREBASE_CONFIG_JSON='{"type":"service_account",...}'
./run.sh
```

## 🎉 배포 완료 후

학생들에게 Netlify URL을 공유하세요!
- 예: `https://prompthon.netlify.app`

