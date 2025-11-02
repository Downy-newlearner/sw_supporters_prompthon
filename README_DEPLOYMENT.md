# 🚀 배포 빠른 시작

## 배포 완료 체크리스트

### ✅ 완료된 작업
- [x] Supabase 연동 코드 작성
- [x] Railway 배포 설정 파일 생성
- [x] Netlify 배포 설정 파일 생성
- [x] 환경변수 템플릿 생성
- [x] 배포 가이드 문서 작성

## 📋 배포 전 준비사항

1. **Supabase 프로젝트 생성 및 테이블 생성**
   - `SUPABASE_SETUP.md` 참고

2. **Solar API 키 6개 준비**
   - `API_KEYS_GUIDE.md` 참고

3. **GitHub 리포지토리에 푸시**
   - `deployment` 브랜치 푸시

## 🎯 배포 순서 (요약)

1. **Supabase 설정** → `SUPABASE_SETUP.md` 참고
2. **Railway 배포** → `DEPLOYMENT_GUIDE.md` 2단계 참고
3. **Netlify 배포** → `DEPLOYMENT_GUIDE.md` 3단계 참고

## 📚 상세 가이드

- **전체 배포 가이드**: `DEPLOYMENT_GUIDE.md`
- **Supabase 설정**: `SUPABASE_SETUP.md`
- **API 키 설정**: `API_KEYS_GUIDE.md`

## 🔧 주요 변경사항

### 백엔드
- `supabase_config.py`: Supabase 클라이언트 초기화
- `supabase_manager.py`: Supabase 기반 리더보드/히스토리 관리
- `main.py`: Supabase 사용 여부 환경변수로 제어 (`USE_SUPABASE`)

### 프론트엔드
- `config.js`: 환경별 설정 (백엔드 URL)
- `script.js`: 동적 백엔드 URL 사용
- `netlify.toml`: Netlify 배포 설정

### 배포 설정
- `Procfile`: Railway 배포 설정
- `railway.json`: Railway 상세 설정
- `nixpacks.toml`: Nixpacks 빌드 설정

## 💡 빠른 팁

### 로컬 테스트 (Supabase 없이)
```bash
# 환경변수 설정 안 함 → 자동으로 JSON 파일 사용
./run.sh
```

### Supabase 사용 (로컬)
```bash
export USE_SUPABASE=true
export SUPABASE_URL=https://xxxxx.supabase.co
export SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
./run.sh
```

## 🎉 배포 완료 후

학생들에게 Netlify URL을 공유하세요!
- 예: `https://prompthon.netlify.app`
