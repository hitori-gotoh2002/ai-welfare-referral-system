# 복지연계 코파일럿

현장 종사자가 상담 메모를 입력하면 AI가 욕구와 위험 신호를 구조화하고, 공공 복지서비스와 지역 기관 정보를 조회해 복지 연계 패키지와 추천서 초안을 만드는 웹 MVP입니다.

- 배포 URL: https://ai-welfare-referral-system.onrender.com
- 저장소: `hitori-gotoh2002/ai-welfare-referral-system`
- 배포 방식: GitHub `main` 브랜치 커밋 시 Render 자동 배포
- 실행 방식: Python 표준 라이브러리 기반 백엔드 + 정적 HTML/CSS/JavaScript 프론트엔드

## 서비스 목표

이 웹은 복지 상담 현장에서 반복되는 업무 흐름을 한 화면 안에서 연결하는 것을 목표로 합니다.

```text
상담 입력
→ AI 구조화
→ 복지서비스 통합 검색
→ 패키지 추천/편집
→ 기관 연결 확인
→ 추천서 초안 생성
```

현재 상태는 상용 운영 전 MVP입니다. 실제 API와 Gemini가 연결되어 작동하지만, 로그인/권한/개인정보 보호/운영 DB는 아직 운영 수준으로 구현되지 않았습니다.

## 현재 구현된 기능

| 영역 | 구현 내용 |
| --- | --- |
| 로그인 | 데모 로그인 화면. 실제 인증/회원 관리는 아직 없음 |
| 대시보드 | 현재 상담 요약, 상담 목록, 저장된 상담 이어서 진행/삭제 |
| 상담 저장 | `POST /api/cases`로 상담 저장, `GET /api/cases` 조회, `DELETE /api/cases/{id}` 삭제 |
| 저장소 | 기본값은 `.data/cases.json` 파일 저장. 운영 DB는 아직 미도입 |
| 상담 입력 | 대상 유형, 지역, 긴급도, 문제 유형, 상담 메모 입력 |
| AI 구조화 | Gemini 2.5 Flash 사용. 실패 시 규칙 기반 구조화 fallback |
| 통합 검색 | 공공데이터/복지로 중앙부처·지자체 복지서비스 목록 조회, 로컬 fallback |
| 상세 조회 | 공공데이터 상세조회, 상세 정보 요약, 공식 상세 링크 표시 |
| 외부 링크 | 복지로 외 마이홈, 고용24, 서울복지포털, 국민건강보험 등은 가능한 공식 상세/안내 페이지로 보정 |
| 기관 연결 | 사회서비스 제공기관 API, 민간자원/지역기관 API, 실패 시 fallback |
| 패키지 추천 | 규칙 기반 후보 산출 후 Gemini가 후보 목록 안에서 재정렬. 실패 시 규칙 기반 추천 |
| 안전 보정 | 연령/대상 불일치 서비스가 추천 상위에 섞이지 않도록 프론트/백엔드 보정 |
| 추천서 | 사례 요약, 우선순위 판단, 서비스별 실행계획, 신청 전 체크리스트, 기관 연결, 추가 질문, 기록 문구 생성 |
| 출력 | 추천서 텍스트 복사, 인쇄/PDF 저장 |
| CI | GitHub Actions `Validate` 워크플로에서 JS/Python 문법 검사 |
| Claude 연동 | GitHub 이슈/PR 코멘트에서 `@claude` 트리거 가능 |

## 아직 부족한 부분

| 우선순위 | 작업 | 이유 |
| --- | --- | --- |
| P0 | 실제 로그인/권한 관리 | 현재 로그인은 데모용이므로 링크를 아는 사용자가 접근 가능 |
| P0 | 개인정보 보호 정책 | 실제 상담 메모에는 민감정보가 포함될 수 있음 |
| P0 | 개인정보 마스킹 | 주민번호, 전화번호, 상세주소 등 자동 마스킹 필요 |
| P1 | 운영 DB 도입 | 현재 `.data/cases.json` 파일 저장은 MVP용이며 Render 재배포/재시작에 취약 |
| P1 | 감사 로그 | 상담 조회/저장/삭제 이력 추적 필요 |
| P1 | API 캐시/호출 제한 | 공공데이터 API 지연, 장애, 호출량 제한에 대비 필요 |
| P1 | 자동화 테스트 | 상담 흐름, 추천 로직, 상세 모달, 저장 API 테스트 필요 |
| P2 | 추천 로직 모듈화 | 현재 기능이 여러 패치 파일에 분산되어 있어 장기 유지보수에 불리 |
| P2 | 추천 품질 평가셋 | 노인/청소년/장애/한부모 등 사례별 기대 추천 결과 검증 필요 |

## 주요 파일 구조

```text
.
├─ index.html                    # 앱 진입 HTML
├─ app.js                        # 기본 프론트 상태, 화면 렌더링, API 호출
├─ styles.css                    # 기본 UI 스타일
├─ age-filter-patch.js           # 연령/대상 조건 불일치 서비스 보정
├─ auto-package-flow-patch.js    # 상담 후 패키지 자동 선택 흐름 보정
├─ status-feedback-patch.js      # AI 구조화 진행 상태, 상세 요약, 추천서 UI 보정
├─ case-loading-link-patch.js    # 상담 로딩 버튼/서비스 링크 UI 보정
├─ commercial-ui-polish.js       # 로그인/업무 화면 시각 보정
├─ commercial-ui-style-fix.js    # 로그인 미리보기 호환 스타일
├─ case-list-persistence-patch.js # 상담 목록 UI와 저장/조회/삭제 프론트 패치
├─ backend_server.py             # Python HTTP 서버, API, 공공데이터, Gemini, 추천 기본 로직
├─ server_entry.py               # Render 실행 진입점
├─ sitecustomize.py              # 런타임 패치 자동 적용 보조
├─ backend_runtime_patch.py      # 공공데이터 조회/추천 런타임 보정
├─ recommendation_relevance_patch.py # 상담 문맥 기반 추천 관련도 보정
├─ detail_alias_patch.py         # 상세조회 ID/별칭 매핑
├─ llm_enhancement_patch.py      # Gemini 구조화, 상세 요약, 패키지 재정렬, 추천서 개선
├─ rich_report_patch.py          # 추천서 품질/출력 보정
├─ welfare_link_patch.py         # 공식 상세 링크 보정
├─ commercial_ui_route_patch.py  # 보조 JS 정적 라우팅
├─ requirements.txt              # Python 의존성
├─ package.json                  # 검증 스크립트
├─ render.yaml                   # Render 배포 설정
├─ runtime.txt                   # Render Python 버전
├─ .env.example                  # 환경변수 예시
├─ CLAUDE.md                     # Claude/Codex 작업 기준 문서
├─ TEAM_ROLES.md                 # 3인 분업 및 AI 협업 매뉴얼
└─ docs/
   ├─ RENDER_DEPLOY.md           # Render 배포 가이드
   └─ TEAM_ROLES.md              # TEAM_ROLES 위치 안내
```

## 로컬 실행

PowerShell 기준입니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python server_entry.py
```

접속 주소:

```text
http://127.0.0.1:5173/
```

같은 Wi-Fi의 다른 기기에서 접속하려면 서버 PC의 내부 IP를 사용합니다.

```text
http://<서버-PC-내부-IP>:5173/
```

서로 다른 네트워크에서 접속하려면 로컬 주소가 아니라 Render 배포 URL을 사용해야 합니다.

## 환경변수

실제 키는 `.env` 또는 Render Environment Variables에 저장하고 GitHub에 올리지 않습니다.

필수:

```text
DATA_GO_KR_SERVICE_KEY=공공데이터포털 일반 인증키
GEMINI_API_KEY=Google AI Studio Gemini API 키
GEMINI_MODEL=gemini-2.5-flash
```

선택:

```text
SOCIALSERVICE_SERVICE_KEY=사회서비스 제공기관 API 별도 키
GEMINI_FALLBACK_MODELS=gemini-2.5-flash-lite
CASE_STORE_PATH=.data/cases.json
HOST=0.0.0.0
PORT=5173
```

Render에서는 `PORT`가 자동 주입됩니다.

## 백엔드 API

| API | 역할 |
| --- | --- |
| `GET /api/health` | 서버, 공공데이터, LLM 설정 상태 확인 |
| `GET /api/services` | 복지서비스 통합 검색 |
| `GET /api/services/{id}` | 서비스 상세조회, 요약, 공식 링크, 관련 기관 정보 |
| `GET /api/providers` | 사회서비스 제공기관/민간자원/지역기관 조회 |
| `GET /api/cases` | 저장된 상담 목록 조회 |
| `GET /api/cases/recent` | 기존 호환용 상담 목록 조회 |
| `POST /api/cases` | 상담 저장 또는 갱신 |
| `DELETE /api/cases/{id}` | 상담 삭제 |
| `POST /api/analyze` | 상담 메모 AI 구조화 |
| `POST /api/packages` | 추천 패키지 생성 |
| `POST /api/report` | 실무형 추천서 생성 |

## 테스트 상담 예시

```text
서울 관악구에 거주하는 72세 독거 어르신입니다. 최근 허리 통증으로 외출이 어렵고 식사를 거르는 날이 많습니다. 기초연금 외에는 소득이 거의 없고 월세 부담이 커서 생계비와 주거비 지원이 필요합니다. 병원 동행, 방문 돌봄, 도시락 또는 식사 지원을 함께 연계하고 싶습니다.
```

기대 동작:

- 노인/고령 대상 상담으로 구조화됩니다.
- 청소년 전용 서비스가 추천 패키지 상위에 섞이지 않아야 합니다.
- 생계, 주거, 돌봄, 의료 관련 서비스가 우선 후보로 나와야 합니다.
- 상담 저장 시 대시보드의 상담 목록에 표시되어야 합니다.

## 검증 명령

전체 검사:

```powershell
npm run check
```

개별 검사:

```powershell
npm run check:js
npm run check:py
```

`check:js`는 프론트엔드 JS 파일의 문법을 검사합니다. `check:py`는 현재 활성화된 Python 서버/패치 파일을 컴파일 검사합니다.

## 배포

Render의 Auto-Deploy가 `On Commit`이면 GitHub `main` 브랜치에 커밋이 올라갈 때 자동 배포됩니다.

배포 후 확인:

```text
https://ai-welfare-referral-system.onrender.com/
https://ai-welfare-referral-system.onrender.com/api/health
```

자세한 배포 설정은 [docs/RENDER_DEPLOY.md](docs/RENDER_DEPLOY.md)를 참고하세요.

## 협업 문서

- [CLAUDE.md](CLAUDE.md): Claude Code/Codex가 이어서 작업할 때 반드시 먼저 읽어야 하는 기준 문서
- [TEAM_ROLES.md](TEAM_ROLES.md): 3인 분업과 AI 협업 매뉴얼

새 AI 도구에게 작업을 맡길 때는 `CLAUDE.md`를 먼저 읽게 하세요. 특히 과거에 롤백된 HWP 가이드 카드, applicationDraft, 대시보드 마일스톤 테이블 기능은 사용자가 다시 요청하기 전까지 재도입하지 않습니다.

## 보안 주의

- `.env`와 실제 API 키를 커밋하지 않습니다.
- 실제 상담자의 개인정보를 GitHub 이슈, PR, 테스트 파일에 남기지 않습니다.
- 현재 로그인은 데모용입니다.
- 운영 전에는 인증, 권한, 감사 로그, 개인정보 마스킹, 저장소 암호화, API 호출량 제한을 추가해야 합니다.
- 현재 파일 기반 상담 저장은 MVP용입니다. 운영에서는 SQLite/PostgreSQL/Render Disk 등 별도 저장소로 교체해야 합니다.
