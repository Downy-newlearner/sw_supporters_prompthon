# 환경변수 설정 템플릿

## Railway (백엔드) 환경변수

```bash
# Supabase 사용 여부
USE_SUPABASE=true

# Supabase 설정
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Solar API Keys (6개 필요)
SOLAR_API_KEY_1=your_api_key_1_here
SOLAR_API_KEY_2=your_api_key_2_here
SOLAR_API_KEY_3=your_api_key_3_here
SOLAR_API_KEY_4=your_api_key_4_here
SOLAR_API_KEY_5=your_api_key_5_here
SOLAR_API_KEY_6=your_api_key_6_here

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

# Supabase 사용 여부 (로컬에서는 false 권장)
USE_SUPABASE=false

# 또는 Supabase 사용
# USE_SUPABASE=true
# SUPABASE_URL=https://xxxxx.supabase.co
# SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 주의사항

⚠️ **절대 Git에 커밋하지 마세요!**
- `.env` 파일은 이미 `.gitignore`에 포함되어 있습니다
- Railway와 Netlify 대시보드에서만 환경변수를 설정하세요
