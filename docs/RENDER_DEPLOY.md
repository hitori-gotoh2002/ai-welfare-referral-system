# Render 배포 가이드

## 1. GitHub 저장소 준비

저장소에는 아래 파일이 포함되어야 합니다.

- `backend_server.py`
- `index.html`
- `app.js`
- `styles.css`
- `requirements.txt`
- `runtime.txt`
- `render.yaml`
- `.env.example`
- `.gitignore`

절대 포함하면 안 되는 파일:

- `.env`
- 실제 개인정보가 들어간 테스트 파일

## 2. Render Web Service 생성

1. Render 대시보드에서 `New +` 선택
2. `Web Service` 선택
3. GitHub 저장소 연결
4. `render.yaml` 감지 또는 아래 설정 수동 입력

수동 설정:

- Runtime: Python
- Build Command:

```bash
pip install -r requirements.txt
```

- Start Command:

```bash
python backend_server.py
```

## 3. Environment Variables 설정

Render의 Environment 탭에 아래 값을 입력합니다.

필수:

```text
DATA_GO_KR_SERVICE_KEY=공공데이터포털_일반_인증키
GEMINI_API_KEY=Google_AI_Studio_Gemini_API_Key
GEMINI_MODEL=gemini-2.5-flash
```

선택:

```text
SOCIALSERVICE_SERVICE_KEY=사회서비스_제공기관_API_별도키
HOST=0.0.0.0
```

`PORT`는 Render가 자동으로 넣습니다.

## 4. 배포 후 확인

배포 URL에서 아래를 확인합니다.

```text
https://<render-app>.onrender.com/
https://<render-app>.onrender.com/api/health
```

`/api/health`에서 아래 값이 보여야 합니다.

- `publicData.enabled: true`
- `llm.enabled: true`

## 5. 운영 전 주의

현재 로그인은 데모용입니다. 링크를 아는 누구나 접속할 수 있으므로 실제 개인정보를 입력하기 전에 다음을 추가해야 합니다.

- 실제 인증
- 권한 분리
- 민감정보 마스킹
- 저장소 암호화 또는 접근통제
- API 호출량 제한
