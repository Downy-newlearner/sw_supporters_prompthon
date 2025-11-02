# 환경변수 설정 템플릿

## Railway (백엔드) 환경변수

```bash
# Firebase 사용 여부
USE_FIREBASE=true

# Solar API Keys (6개 필요)
SOLAR_API_KEY_1=your_api_key_1_here
SOLAR_API_KEY_2=your_api_key_2_here
SOLAR_API_KEY_3=your_api_key_3_here
SOLAR_API_KEY_4=your_api_key_4_here
SOLAR_API_KEY_5=your_api_key_5_here
SOLAR_API_KEY_6=your_api_key_6_here

# Firebase 설정 (방법 1: JSON 문자열 - 권장)
FIREBASE_CONFIG_JSON={"type":"service_account","project_id":"your-project-id","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}

# Firebase 설정 (방법 2: 파일 경로)
# FIREBASE_KEY_FILE=/path/to/firebase-key.json

# Netlify URL (CORS 설정용 - 선택사항)
NETLIFY_URL=https://your-netlify-app.netlify.app
```

## Netlify (프론트엔드) 환경변수

```bash
# 백엔드 URL (Railway URL)
BACKEND_URL=https://your-railway-app.up.railway.app

# 환경 설정
NETLIFY_ENV=production
```

## 로컬 개발용 (.env 파일)

프로젝트 루트에 `.env` 파일 생성:

```bash
# Solar API Keys
SOLAR_API_KEY_1=your_api_key_1_here
SOLAR_API_KEY_2=your_api_key_2_here
SOLAR_API_KEY_3=your_api_key_3_here
SOLAR_API_KEY_4=your_api_key_4_here
SOLAR_API_KEY_5=your_api_key_5_here
SOLAR_API_KEY_6=your_api_key_6_here

# Firebase 사용 여부 (로컬에서는 false 권장)
USE_FIREBASE=false

# 또는 Firebase 사용 (프로젝트 루트에 firebase-key.json 파일 배치)
# USE_FIREBASE=true
```

## 주의사항

⚠️ **절대 Git에 커밋하지 마세요!**
- `.env` 파일은 이미 `.gitignore`에 포함되어 있습니다
- `firebase-key.json` 파일도 `.gitignore`에 포함되어 있습니다
- Railway와 Netlify 대시보드에서만 환경변수를 설정하세요

