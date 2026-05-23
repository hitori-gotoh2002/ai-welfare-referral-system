# 현장 종사자용 AI 복지 추천·연계 시스템

현장 상담사가 상담 메모를 입력하면 AI가 욕구·긴급도·대상 정보를 구조화하고, 공공 복지서비스와 지역 기관 정보를 바탕으로 연계 패키지와 추천서 초안을 만드는 웹 MVP입니다.

배포 URL: https://ai-welfare-referral-system.onrender.com

## 핵심 흐름

1. 상담 입력: 대상, 지역, 욕구, 긴급도, 상담 메모를 기록합니다.
2. AI 구조화: Gemini가 메모를 구조화하고, 실패하면 규칙 기반 분석으로 전환합니다.
3. 통합 검색: 공공데이터/복지로 API와 로컬 후보를 함께 조회합니다.
4. 패키지 추천: 규칙 기반으로 후보를 만들고, Gemini가 후보 목록 안에서만 재정렬합니다.
5. 상세 확인: 공공데이터 상세조회 원문을 가져오고, LLM 요약과 민간·지역기관 후보를 함께 보여줍니다.
6. 추천서 생성: 선택한 패키지로 설명형 추천서 초안을 만듭니다.

## 현재 구현된 부분

| 영역 | 구현 상태 |
| --- | --- |
| 화면 | 대시보드, 상담 입력, AI 구조화 결과, 통합 검색, 패키지 추천/편집, 추천서, 설정 화면 |
| 상담 구조화 | Gemini 2.5 Flash API 연결, API 실패 시 규칙 기반 구조화 |
| 복지서비스 조회 | 공공데이터포털/복지로 중앙부처·지자체 목록 및 상세조회 API 연결 |
| 상세 요약 | 상세조회 원문을 `detailBrief`로 짧게 요약, 원문 필드는 접어서 표시 |
| 기관 조회 | 사회서비스 제공기관 API, 민간자원/지역기관 API, fallback 기관 후보 |
| 패키지 추천 | 규칙 기반 후보 산출 + Gemini 후보 재정렬, 실패 시 규칙 기반 추천 유지 |
| 추천서 생성 | Gemini 기반 추천서 초안, 실패 시 로컬 추천서 생성 |
| 배포 | GitHub `main` 브랜치와 Render 자동 배포 연결 |

## 중요한 설계 원칙

LLM은 복지서비스를 직접 만들어내지 않습니다. 실제 공공 API, 로컬 서비스 목록, 기관 API로 후보를 먼저 만들고, Gemini는 다음 역할만 맡습니다.

- 상담 메모 구조화
- 상세조회 원문 요약
- 후보 목록 안에서 패키지 재정렬
- 추천서 문장 정리

이 방식은 환각 위험을 줄이고, 화면에 나온 제도와 기관의 출처를 추적하기 쉽게 만듭니다.

## 주요 파일

```text
index.html                    # 앱 진입 HTML
app.js                        # 프론트 상태, 렌더링, API 호출
age-filter-patch.js           # 대상 연령/패키지 편집 UX 보강
status-feedback-patch.js      # API 상태 표시, 상세 요약 모달 UI
auto-package-flow-patch.js    # 상담 구조화 후 자동 패키지 준비
backend_server.py             # 기본 API 서버
backend_runtime_patch.py      # 런타임 API/상세조회 보강
recommendation_relevance_patch.py # 추천 관련성/대상 필터 보강
detail_alias_patch.py         # 샘플 서비스와 실제 상세조회 ID 연결
llm_enhancement_patch.py      # LLM 요약, 욕구 병합, 후보 재정렬
TEAM_ROLES.md                 # 3인 분업 및 AI 협업 매뉴얼
```

## 로컬 실행

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

## 환경변수

실제 키는 `.env` 또는 Render Environment Variables에 넣고 GitHub에 올리지 않습니다.

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
ENABLE_LLM_DETAIL_SUMMARY=true
ENABLE_LLM_PACKAGE_RERANK=true
ENABLE_DETAIL_PROVIDERS=true
```

## API 요약

| API | 역할 |
| --- | --- |
| `GET /api/health` | 서버, 공공데이터 키, LLM 설정 상태 확인 |
| `GET /api/services` | 복지서비스 통합 검색 |
| `GET /api/services/{id}` | 상세조회 API 호출, LLM 요약, 관련 기관 후보 조회 |
| `GET /api/providers` | 사회서비스 제공기관/민간자원/지역기관 조회 |
| `POST /api/analyze` | 상담 메모 AI 구조화 |
| `POST /api/packages` | 추천 패키지 생성 및 LLM 후보 재정렬 |
| `POST /api/report` | 추천서 생성 |

## 테스트용 상담 예시

```text
서울 관악구에 거주하는 78세 독거 어르신입니다. 최근 낙상 이후 병원 이동이 어렵고 식사 준비와 복약 관리가 힘듭니다. 자녀는 지방에 있어 방문이 어렵고 월세와 병원비 부담도 있습니다. 방문 돌봄, 의료비, 생계 지원을 함께 확인하고 싶습니다.
```

기대 확인:

- 구조화 결과에 `돌봄`, `의료`, `생계`, `주거`가 유지됩니다.
- 노인 상담에 청소년 전용 서비스가 패키지 후보로 들어가지 않습니다.
- 패키지 응답의 `provider`가 `gemini-2.5-flash+candidate-rerank`이면 LLM 재정렬이 적용된 것입니다.
- 상세 모달에는 `Gemini 요약`, 접힌 원문 상세 필드, 민간·지역 연계 후보가 표시됩니다.

## 검증 명령

```powershell
npm run check
```

이 명령은 JS 문법 검사와 Python 컴파일 검사를 함께 실행합니다.

## 아직 부족한 부분

| 우선순위 | 작업 | 이유 |
| --- | --- | --- |
| P0 | 실제 로그인/권한 관리 | 현재 로그인은 데모 수준입니다. |
| P0 | 개인정보 저장 정책과 마스킹 | 실제 상담 데이터에는 민감정보가 포함될 수 있습니다. |
| P0 | API 키 재발급·권한 제한 | 운영 전 키를 재발급하고 사용량/도메인 제한을 걸어야 합니다. |
| P1 | DB 저장소 도입 | 최근 상담, 추천 이력, 추천서를 영구 저장해야 합니다. |
| P1 | 추천 로직 모듈화 | 현재 패치 파일로 분산되어 있어 `ai/`, `recommendation/` 모듈로 분리하는 것이 좋습니다. |
| P1 | 자동 테스트/CI 확대 | 상담 시나리오별 추천 품질 회귀 테스트가 필요합니다. |
| P2 | API 캐시·재시도 정책 | 공공 API 지연과 장애에 대비해야 합니다. |
| P2 | 민간 복지 DB 확장 | 웹검색보다 검증된 기관 DB/API를 우선 구축하는 편이 안전합니다. |

## 배포

Render Auto-Deploy가 `On Commit`이면 GitHub `main`에 커밋될 때 자동 배포됩니다. 배포 후 아래를 확인합니다.

```text
https://ai-welfare-referral-system.onrender.com/
https://ai-welfare-referral-system.onrender.com/api/health
```

## 협업

3명이 동시에 개발할 때는 `TEAM_ROLES.md`의 역할 경계를 우선 따릅니다.

권장 역할:

- Product/UX & 현장 워크플로우
- Backend/Data & API 품질
- AI/Recommendation & Safety

## 보안 주의

- `.env`와 실제 API 키는 절대 커밋하지 않습니다.
- 실제 개인정보가 들어간 상담 메모를 GitHub 이슈, PR, 테스트 파일에 남기지 않습니다.
- 현재 서비스는 MVP입니다. 운영 전 인증, 권한, 감사 로그, 마스킹, 저장소 암호화를 추가해야 합니다.
