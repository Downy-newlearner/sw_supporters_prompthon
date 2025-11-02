# 프롬프톤 - 한국어 문법 교정 챌린지

고등학교 학생들을 위한 프롬프트 엔지니어링 대회 플랫폼입니다. 학생들은 프롬프트만 작성하면 자동으로 평가되고 리더보드에 순위가 표시됩니다.

## 🌟 주요 기능

- **간편한 로그인**: 닉네임만 입력하면 바로 시작
- **프롬프트 가이드**: 12개의 Solar Prompt Cookbook PDF를 바로 읽을 수 있음
- **자동 파이프라인**: 프롬프트 입력 → API 호출 → 평가 → 리더보드 업데이트까지 자동 처리
- **실시간 리더보드**: 제출 즉시 점수가 반영되고 순위 표시

## 📋 요구사항

- Python 3.8 이상
- Solar API 키 (Upstage에서 발급)
- 웹 브라우저 (Chrome, Firefox, Safari 등)

## 🚀 설치 및 실행

### 1. Solar API 키 설정

먼저 [Upstage Console](https://console.upstage.ai/)에서 API 키를 발급받으세요.

```bash
export SOLAR_API_KEY='your_api_key_here'
```

영구적으로 설정하려면 `~/.zshrc` 또는 `~/.bashrc` 파일에 추가하세요:

```bash
echo 'export SOLAR_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

### 2. 프로그램 실행

```bash
# 실행 권한 부여
chmod +x run.sh

# 서버 시작
./run.sh
```

### 3. 브라우저에서 접속

```
http://localhost:8000
```

## 📁 프로젝트 구조

```
.
├── backend/
│   ├── main.py              # FastAPI 메인 서버
│   ├── models.py            # 데이터 모델
│   ├── solar_api.py         # Solar API 연동
│   ├── evaluator.py         # 자동 평가 시스템
│   └── requirements.txt     # Python 패키지
├── frontend/
│   ├── index.html           # 메인 페이지
│   ├── style.css            # 스타일링
│   └── script.js            # 프론트엔드 로직
├── data/
│   ├── train.csv            # 학습 데이터 (평가용)
│   ├── test.csv             # 테스트 데이터
│   └── sample_submission.csv
├── Solar_prompt_cookbook/   # 프롬프트 가이드 PDF
├── run.sh                   # 실행 스크립트
├── README.md                # 이 파일
└── leaderboard.json         # 리더보드 데이터 (자동 생성)
```

## 🎯 사용 방법

### 학생용 가이드

1. **로그인**
   - 브라우저에서 `http://localhost:8000` 접속
   - 닉네임 입력 후 "시작하기" 클릭

2. **프롬프트 가이드 읽기**
   - 좌측 패널에서 PDF 선택
   - 다양한 프롬프트 작성 기법 학습

3. **프롬프트 작성**
   - 우측 패널의 텍스트 영역에 프롬프트 입력
   - 예시:
     ```
     당신은 한국어 문법 전문가입니다. 
     주어진 문장의 맞춤법, 띄어쓰기, 문법 오류를 교정하여 
     올바른 문장으로 수정해주세요.
     ```

4. **제출 및 결과 확인**
   - "제출하기" 버튼 클릭
   - 처리 진행 상황 확인
   - 점수 확인 및 리더보드에서 순위 확인

5. **재도전**
   - 더 나은 프롬프트로 여러 번 도전 가능
   - 최고 점수만 리더보드에 반영

## 🔧 기술 스택

- **백엔드**: FastAPI (Python)
- **프론트엔드**: HTML, CSS, JavaScript
- **PDF 뷰어**: PDF.js
- **AI API**: Solar API (Upstage)
- **평가**: 문자 단위 정확도 + 정확한 일치율

## 📊 평가 방식

### 테스트 데이터
- **소스**: train.csv에서 1000개 샘플 추출
- **테스트 파일**: `test_from_train.csv` (오류 문장)
- **정답 파일**: `answer_from_train.csv` (교정된 문장)

### 평가 기준: TP / (TP + FP + FM)
- **TP** (True Positive): 올바른 위치, 올바른 교정
- **FP** (False Positive): 잘못된 교정 또는 불필요한 교정
- **FM** (False Missing): 필요한 교정을 놓친 경우

**최종 점수 = TP / (TP + FP + FM) × 100**

자세한 내용은 `EVALUATION_INFO.md` 참고

## 🐛 문제 해결

### Solar API 오류
```bash
# API 키가 올바르게 설정되었는지 확인
echo $SOLAR_API_KEY
```

### 포트 충돌
다른 프로그램이 8000번 포트를 사용 중이라면:
```bash
# backend/main.py의 마지막 줄 수정
uvicorn.run(app, host="0.0.0.0", port=8001)  # 다른 포트 번호 사용
```

### 의존성 설치 오류
```bash
# 수동으로 의존성 설치
cd backend
pip install -r requirements.txt
```

## 📝 운영 팁

### 대회 진행자를 위한 팁

1. **사전 준비**
   - Solar API 키 발급 및 테스트
   - 샘플 데이터로 동작 확인
   - 네트워크 환경 점검

2. **대회 시작 전**
   - 학생들에게 접속 URL 공지
   - 프롬프트 작성 예시 설명
   - 리더보드 사용법 안내

3. **대회 중**
   - 리더보드를 스크린에 띄워서 실시간 순위 공유
   - 주기적으로 상위권 프롬프트 공유 (선택사항)

4. **대회 종료 후**
   - `leaderboard.json` 파일 백업
   - `submissions/` 폴더의 제출 파일 확인

### 리더보드 초기화

```bash
# 리더보드 데이터 삭제
rm leaderboard.json

# 제출 파일 삭제
rm -rf submissions/
```

## 🎓 교육적 가치

이 프로젝트를 통해 학생들은:

- **프롬프트 엔지니어링 기초** 학습
- **AI 모델과의 효과적인 소통** 방법 이해
- **반복적 개선** 과정 경험
- **경쟁을 통한 동기부여** 획득

## 📄 라이선스

이 프로젝트는 교육 목적으로 자유롭게 사용할 수 있습니다.

## 🤝 기여

버그 리포트나 기능 제안은 언제나 환영합니다!

---

**즐거운 프롬프톤 되세요! 🎉**

