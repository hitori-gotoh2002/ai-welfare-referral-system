# 현장 종사자용 AI 복지 추천·연계 시스템

현장 상담사가 상담 메모를 입력하면 AI가 욕구·긴급도·대상 정보를 구조화하고, 공공 복지서비스와 지역 기관 정보를 바탕으로 연계 패키지와 추천서 초안을 만드는 웹 MVP입니다.

배포 URL: https://ai-welfare-referral-system.onrender.com

## 이 프로젝트가 하는 일

이 서비스는 복지 상담 현장에서 “상담 메모 → 욕구 구조화 → 서비스 검색 → 패키지 추천 → 추천서 작성” 흐름을 한 화면 안에서 빠르게 처리하는 것을 목표로 합니다.

핵심 사용자는 복지관, 지자체, 민간기관, 현장 상담 조직의 실무자입니다. 최종 목적은 상담사가 제도명과 기관 정보를 일일이 찾는 시간을 줄이고, 대상자에게 설명 가능한 추천 근거를 남기는 것입니다.

## 현재 구현된 부분

| 영역 | 구현 상태 |
| --- | --- |
| 화면 | 로그인 데모, 대시보드, 상담 입력, AI 구조화 결과, 복지 통합 검색, 패키지 추천, 패키지 편집, 기관 연결 리스트, 추천서 화면, 설정 화면 |
| 상담 구조화 | Gemini 2.5 Flash API 연결, API 실패 시 규칙 기반 로컬 구조화 |
| 복지서비스 조회 | 공공데이터포털/복지로 중앙부처 복지서비스 목록·상세조회, 지자체 복지서비스 목록·상세조회 |
| 기관 조회 | 사회서비스 제공기관 API, 민간자원/지역기관 API, 실패 시 로컬 샘플 기관 fallback |
| 패키지 추천 | 욕구, 긴급도, 지역, 대상 연령대를 이용한 규칙 기반 추천 |
| 추천서 생성 | Gemini 기반 추천서 초안 생성, 실패 시 로컬 추천서 생성 |
| 출력 | 추천서 복사, 인쇄/PDF 저장 |
| 배포 | GitHub main 브랜치와 Render 자동 배포 연결 |

## 아직 구현되지 않았거나 부족한 부분

운영 서비스로 쓰기 전에 아래 항목은 반드시 보강해야 합니다.

| 우선순위 | 작업 | 이유 |
| --- | --- | --- |
| P0 | 실제 로그인/권한 관리 | 현재 로그인은 데모용이라 링크를 아는 사람이 접근할 수 있습니다. |
| P0 | 개인정보 저장 정책과 마스킹 | 실제 상담 데이터에는 민감정보가 포함될 수 있습니다. |
| P0 | API 키 재발급·권한 제한 | 초기에 공유된 키는 운영 전 재발급하고 도메인/사용량 제한을 걸어야 합니다. |
| P1 | DB 저장소 도입 | 최근 상담, 추천 이력, 추천서 저장이 현재는 브라우저/메모리 중심입니다. |
| P1 | 백엔드 추천 로직 고도화 | 현재 일부 추천 보정은 `age-filter-patch.js`에서 후처리합니다. 장기적으로 `backend_server.py` 추천 엔진에 통합해야 합니다. |
| P1 | 자동 테스트/CI | Python API, 추천 로직, 프론트 핵심 플로우 테스트가 필요합니다. |
| P2 | API 캐시·재시도·타임아웃 정책 | 공공 API 장애나 지연에 대비해야 합니다. |
| P2 | 추천 품질 평가표 | 추천 결과가 현장 기준에 맞는지 시나리오별로 평가해야 합니다. |
| P3 | UI 접근성/모바일 최적화 | 현장 태블릿/작은 노트북 사용성을 높여야 합니다. |

## 주요 파일 구조

```text
.
├─ index.html              # 앱 진입 HTML
├─ app.js                  # 프론트 상태, 화면 렌더링, API 호출, 로컬 fallback
├─ age-filter-patch.js     # 대상 연령대 불일치 서비스 제거용 임시 프론트 패치
├─ styles.css              # 전체 UI 스타일
├─ backend_server.py       # 정적 파일 서버 + API 라우터 + 공공 API/LLM/추천 로직
├─ requirements.txt        # Python 의존성
├─ render.yaml             # Render 배포 설정
├─ runtime.txt             # Render Python 버전
├─ .env.example            # 환경변수 예시
├─ TEAM_ROLES.md           # 3인 분업 및 협업 매뉴얼
└─ docs/
   ├─ RENDER_DEPLOY.md     # Render 배포 가이드
   └─ TEAM_ROLES.md        # 기존 문서 위치 안내
```

## 로컬 실행 방법

Windows PowerShell 기준입니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python backend_server.py
```

접속 주소:

```text
http://127.0.0.1:5173/
```

같은 Wi-Fi나 내부망의 다른 컴퓨터에서 접속하려면 서버 PC의 IPv4 주소를 사용합니다.

```text
http://<서버-PC-내부망-IP>:5173/
```

외부 인터넷에서 누구나 접속하려면 로컬 주소가 아니라 Render 배포 URL을 사용해야 합니다.

## 환경변수

실제 키는 `.env`에 저장하고 GitHub에 올리지 않습니다. `.env.example`을 복사해서 값을 채우세요.

필수:

```text
DATA_GO_KR_SERVICE_KEY=공공데이터포털 일반 인증키
GEMINI_API_KEY=Google AI Studio Gemini API 키
GEMINI_MODEL=gemini-2.5-flash
```

선택:

```text
SOCIALSERVICE_SERVICE_KEY=사회서비스 제공기관 API가 별도 키를 요구할 때 사용
HOST=0.0.0.0
PORT=5173
```

Render에서는 `PORT`가 자동 주입됩니다.

## 백엔드 API 요약

| API | 역할 |
| --- | --- |
| `GET /api/health` | 서버, 공공데이터 키, LLM 설정 상태 확인 |
| `GET /api/services` | 복지서비스 검색, 공공 API 실패 시 로컬 fallback |
| `GET /api/providers` | 사회서비스 제공기관/민간자원/지역기관 조회 |
| `GET /api/cases/recent` | 최근 상담 샘플 조회 |
| `POST /api/cases` | 상담 저장 데모 |
| `POST /api/analyze` | 상담 메모 AI 구조화 |
| `POST /api/packages` | 추천 패키지 생성 |
| `POST /api/report` | 추천서 생성 |

## 테스트용 상담 예시

```text
서울 관악구에 거주하는 72세 독거 어르신입니다. 최근 허리 통증으로 외출이 어렵고 식사를 거르는 날이 많습니다. 기초연금 외에는 소득이 거의 없고 월세 부담이 커서 생계비와 주거비 지원이 필요합니다. 병원 동행, 방문 돌봄, 도시락 또는 식사 지원을 함께 연계하고 싶습니다.
```

이 예시에서는 청소년 전용 서비스가 추천 패키지에 들어가지 않아야 합니다.

## 기본 검증 명령

```powershell
python -m py_compile backend_server.py
```

Node.js가 정상 설치된 환경에서는 아래도 실행합니다.

```powershell
node --check app.js
node --check age-filter-patch.js
```

현재 일부 Windows PC에서는 `node.exe` 접근 권한 문제로 로컬 `node --check`가 실패할 수 있습니다. 그 경우 GitHub Actions나 다른 개발자 PC에서 JS 문법 검사를 대신 수행하세요.

## 배포 방식

현재 Render의 Auto-Deploy가 `On Commit`으로 설정되어 있습니다. 따라서 GitHub `main` 브랜치에 커밋이 올라가면 Render가 자동으로 새 버전을 배포합니다.

배포 후 아래 주소를 확인합니다.

```text
https://ai-welfare-referral-system.onrender.com/
https://ai-welfare-referral-system.onrender.com/api/health
```

자세한 절차는 [docs/RENDER_DEPLOY.md](docs/RENDER_DEPLOY.md)를 참고하세요.

## 협업 방식

3명이 동시에 개발할 때는 역할과 파일 경계를 나누는 것이 가장 중요합니다.

전체 분업 매뉴얼은 [TEAM_ROLES.md](TEAM_ROLES.md)를 참고하세요.

권장 역할:

- Product/UX & 현장 워크플로우
- Backend/Data & API 품질
- AI/Recommendation & Safety

권장 브랜치:

```text
feature/ux-case-input
feature/api-service-cache
fix/recommendation-age-target
docs/team-manual
```

## 다른 Codex/Claude 계정에게 작업을 맡길 때

새 AI 도구에게는 아래 정보를 먼저 알려주세요.

```text
저장소: hitori-gotoh2002/ai-welfare-referral-system
배포: Render, main 브랜치 커밋 시 자동 배포
중요 파일: README.md, TEAM_ROLES.md, backend_server.py, app.js, age-filter-patch.js, styles.css
주의: .env와 실제 개인정보는 절대 커밋하지 말 것
작업 전 확인: README.md와 TEAM_ROLES.md를 먼저 읽고, 담당 역할 범위의 파일만 수정할 것
검증: python -m py_compile backend_server.py, 가능하면 node --check app.js
```

## 보안 주의

- `.env`는 절대 커밋하지 않습니다.
- 실제 개인정보가 들어간 상담 메모를 GitHub 이슈, PR, 테스트 파일에 남기지 않습니다.
- 현재 로그인은 데모용입니다.
- 운영 전에는 인증, 권한, 감사 로그, 개인정보 마스킹, 저장소 암호화, API 호출량 제한을 추가해야 합니다.
- 이미 공유된 API 키는 운영 전에 재발급하거나 사용 제한을 걸어야 합니다.
