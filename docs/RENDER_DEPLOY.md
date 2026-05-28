# Render 배포 가이드

이 프로젝트는 Render Web Service로 배포합니다.

## 1. 저장소 준비

GitHub 저장소:

```text
hitori-gotoh2002/ai-welfare-referral-system
```

필수 파일:

```text
backend_server.py
server_entry.py
index.html
app.js
styles.css
requirements.txt
package.json
runtime.txt
render.yaml
.env.example
.gitignore
```

커밋하면 안 되는 파일:

```text
.env
.data/
__pycache__/
*.pyc
tmp-*.log
실제 개인정보가 들어간 테스트 파일
```

## 2. Render Web Service 생성

1. Render 대시보드에서 `New +` 선택
2. `Web Service` 선택
3. GitHub 저장소 연결
4. `render.yaml`을 사용하거나 아래 값을 직접 입력

수동 설정값:

```text
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: python server_entry.py
```

`render.yaml`에도 같은 값이 들어 있습니다.

## 3. Environment Variables

Render의 Environment 탭에 아래 값을 입력합니다.

필수:

```text
DATA_GO_KR_SERVICE_KEY=<공공데이터포털 일반 인증키>
GEMINI_API_KEY=<Google AI Studio Gemini API 키>
GEMINI_MODEL=gemini-2.5-flash
HOST=0.0.0.0
```

선택:

```text
SOCIALSERVICE_SERVICE_KEY=<사회서비스 제공기관 API 별도 키>
GEMINI_FALLBACK_MODELS=gemini-2.0-flash,gemini-1.5-flash
CASE_STORE_PATH=.data/cases.json
```

`PORT`는 Render가 자동으로 넣으므로 직접 설정하지 않아도 됩니다.

## 4. 배포 확인

배포가 끝나면 아래 주소를 확인합니다.

```text
https://ai-welfare-referral-system.onrender.com/
https://ai-welfare-referral-system.onrender.com/api/health
https://ai-welfare-referral-system.onrender.com/api/cases
```

`/api/health`에서 아래 값이 보이면 정상입니다.

```json
{
  "ok": true,
  "publicData": {
    "enabled": true
  },
  "llm": {
    "enabled": true
  }
}
```

## 5. Auto-Deploy

Render의 Auto-Deploy가 `On Commit`이면 GitHub `main` 브랜치에 push할 때 자동 배포됩니다.

배포가 안 될 때 확인할 것:

- Render Settings의 Repository 연결 상태
- GitHub 저장소 접근 권한
- Environment Variables 누락 여부
- Build/Start Command가 `render.yaml`과 맞는지
- Render 로그의 Python 예외 또는 인증 오류

## 6. 상담 저장 주의

현재 상담 목록은 기본적으로 `.data/cases.json`에 저장됩니다. 이 방식은 MVP용이며, 운영 환경에서 장기 보관을 보장하는 DB가 아닙니다.

운영 전 권장:

- Render Disk 연결 또는 PostgreSQL 도입
- 개인정보 마스킹
- 접근 권한 관리
- 감사 로그
- 백업 정책

## 7. 운영 전 보안 체크

현재 로그인은 데모용입니다. 링크를 아는 사용자가 접근할 수 있으므로 실제 개인정보를 입력하기 전에 아래 기능을 추가해야 합니다.

- 실제 인증
- 역할 기반 권한
- 민감정보 마스킹
- 저장소 암호화 또는 접근통제
- API 호출량 제한
- 상담 조회/삭제 감사 로그
