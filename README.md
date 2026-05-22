# 현장 종사자용 AI 복지 추천·연계 시스템

현장 상담 메모를 구조화하고, 공공데이터 기반 복지서비스와 지역 기관을 조회한 뒤, 사례관리형 패키지 추천과 설명형 추천서를 생성하는 웹 MVP입니다.

## 현재 기능

- 상담 기본정보/메모 입력
- Gemini 2.5 Flash 기반 상담 메모 구조화
- 공공데이터포털/복지로 중앙부처·지자체 복지서비스 목록 조회
- 중앙부처·지자체 복지서비스 상세조회
- 민간자원/지역기관 API 조회
- 규칙 기반 패키지 추천
- Gemini 기반 추천서 초안 생성
- 추천서 텍스트 복사 및 인쇄/PDF

## 로컬 실행

```powershell
python backend_server.py
```

접속:

```text
http://127.0.0.1:5173/
```

같은 내부망에서 접속하려면 서버가 실행 중인 PC의 IPv4 주소를 사용합니다.

```text
http://<내부망-IP>:5173/
```

## 환경변수

실제 키는 `.env`에 저장하고 GitHub에 올리지 않습니다. `.env.example`을 참고해 값을 채워주세요.

필수:

- `DATA_GO_KR_SERVICE_KEY`: 공공데이터포털 일반 인증키
- `GEMINI_API_KEY`: Google AI Studio Gemini API 키
- `GEMINI_MODEL`: 기본값 `gemini-2.5-flash`

선택:

- `SOCIALSERVICE_SERVICE_KEY`: 사회서비스 제공기관 API가 별도 승인 키를 요구할 때 사용
- `HOST`: 기본값 `0.0.0.0`
- `PORT`: Render 배포 시 자동 주입

## 배포

Render 배포 설정은 `render.yaml`에 포함되어 있습니다.

자세한 배포 절차는 [docs/RENDER_DEPLOY.md](docs/RENDER_DEPLOY.md)를 참고하세요.

## 3인 분업 구조

역할과 작업 경계는 [docs/TEAM_ROLES.md](docs/TEAM_ROLES.md)에 정리되어 있습니다.

권장 역할:

- Product/UX & 현장 워크플로우
- Backend/Data & API 품질
- AI/Recommendation & Safety

## 보안 주의

- `.env`는 절대 커밋하지 않습니다.
- 현재 로그인은 데모용입니다.
- 실제 개인정보를 입력받기 전 인증, 권한, 마스킹, 저장 정책을 먼저 추가해야 합니다.
- 이미 공유된 API 키는 운영 전 재발급 또는 키 제한을 권장합니다.
