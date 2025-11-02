# 빠른 시작 가이드 ⚡

프롬프톤 플랫폼을 5분 안에 실행해보세요!

## 1단계: Solar API 키 설정 (2분)

### API 키 발급
1. [Upstage Console](https://console.upstage.ai/) 접속
2. 회원가입 또는 로그인
3. 좌측 메뉴에서 **API Keys** 클릭
4. **Create API Key** 버튼 클릭
5. 생성된 키를 복사

### 환경변수 설정
터미널에서 다음 명령어 실행:

```bash
export SOLAR_API_KEY='여기에_복사한_API_키_붙여넣기'
```

> 💡 **팁**: 다음번에도 사용하려면 `~/.zshrc` 파일에 추가하세요:
> ```bash
> echo 'export SOLAR_API_KEY="여기에_API_키"' >> ~/.zshrc
> source ~/.zshrc
> ```

## 2단계: 프로그램 실행 (1분)

```bash
# 프로젝트 폴더로 이동
cd "/Users/downy/Documents/SW Supporters Prompthon"

# 실행
./run.sh
```

## 3단계: 브라우저에서 접속 (1분)

```
http://localhost:8000
```

## 4단계: 테스트 (1분)

1. **닉네임 입력**: 아무 이름이나 입력하고 "시작하기"
2. **프롬프트 작성**: 예시 프롬프트 입력
   ```
   당신은 한국어 문법 전문가입니다. 주어진 문장의 맞춤법, 띌어쓰기, 문법 오류를 교정하여 올바른 문장으로 수정해주세요.
   ```
3. **제출하기**: 버튼 클릭 후 결과 확인
4. **리더보드 확인**: 점수와 순위 확인

---

## 🎉 완료!

이제 학생들이 접속해서 사용할 수 있습니다!

## ❓ 문제가 생겼나요?

### Solar API 키 오류
```bash
# API 키가 설정되었는지 확인
echo $SOLAR_API_KEY
```
아무것도 출력되지 않으면 1단계로 돌아가세요.

### 포트가 이미 사용중
```bash
# 다른 포트로 실행 (backend/main.py 수정)
# 마지막 줄을: port=8001 로 변경
```

### Python 버전 오류
```bash
# Python 버전 확인 (3.8 이상 필요)
python3 --version
```

더 자세한 내용은 `README.md`를 참고하세요!

