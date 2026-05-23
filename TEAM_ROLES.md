# TEAM_ROLES: 3인 분업 및 AI 협업 매뉴얼

이 문서는 3명이 GitHub에서 동시에 개발하고, 각자 다른 Codex/Claude 계정을 사용해도 충돌을 줄이며 이어 작업할 수 있도록 만든 작업 매뉴얼입니다.

## 프로젝트 한 줄 설명

상담 메모를 AI로 구조화하고, 공공 복지서비스·지역기관 데이터를 조회해 상담 대상자에게 맞는 복지 연계 패키지와 추천서 초안을 생성하는 웹 MVP입니다.

## 현재 상태 요약

현재 서비스는 시연용 정적 화면이 아니라 실제 API와 LLM을 호출하는 웹입니다.

동작하는 것:

- Render 배포 URL 접속
- 상담 입력과 구조화
- Gemini API 기반 상담 메모 구조화
- 공공데이터/복지로 API 기반 복지서비스 목록·상세조회
- Gemini 기반 상세조회 요약
- 사회서비스 제공기관/민간자원 기관 조회
- 규칙 기반 후보 산출 + Gemini 후보 재정렬 방식의 패키지 추천
- 추천서 생성, 복사, 인쇄

아직 부족한 것:

- 실제 회원가입/로그인/권한 관리
- DB 기반 상담 저장
- 운영 수준 개인정보 보호와 마스킹
- 자동 테스트와 CI 확대
- 추천 품질 평가 체계
- 추천/AI/데이터 로직의 모듈화

## 역할 분배 원칙

세 사람은 “화면”, “데이터/API”, “AI/추천 품질”로 나누는 것을 권장합니다. 한 PR에서 여러 영역을 동시에 크게 바꾸면 충돌과 회귀가 생기기 쉽습니다.

| 역할 | 주 담당 | 주요 파일 |
| --- | --- | --- |
| 1. Product/UX & 현장 워크플로우 | 화면 흐름, 사용성, 문구, 출력물 | `index.html`, `styles.css`, `app.js`, `status-feedback-patch.js` |
| 2. Backend/Data & API 품질 | 공공 API, 기관 API, 서버, 배포 | `backend_server.py`, `backend_runtime_patch.py`, `detail_alias_patch.py`, `.env.example`, `render.yaml` |
| 3. AI/Recommendation & Safety | Gemini 프롬프트, 추천 로직, 안전장치 | `recommendation_relevance_patch.py`, `llm_enhancement_patch.py`, `age-filter-patch.js`, `backend_server.py` |

## 역할 1. Product/UX & 현장 워크플로우

목표: 현장 종사자가 상담 중 빠르고 헷갈리지 않게 사용할 수 있는 화면을 만듭니다.

주요 책임:

- 상담 입력 화면 개선
- 통합검색과 패키지 편집 UX 개선
- 상세 모달의 요약/원문/기관 후보 표시 방식 개선
- 추천서 화면의 문구와 출력 레이아웃 개선
- 모바일/태블릿 화면 점검

수정 가능 파일:

- `index.html`
- `styles.css`
- `app.js` 중 `render...` 함수
- `status-feedback-patch.js`
- README나 사용자 안내 문서

주의할 점:

- API 응답 필드명을 바꾸면 역할 2와 먼저 맞춥니다.
- 추천 점수나 대상 필터를 바꾸면 역할 3과 먼저 맞춥니다.
- 긴 서비스명, 긴 상세 원문, 긴 연락처가 UI 밖으로 넘치지 않는지 확인합니다.

완료 기준:

- 상담 입력 → 구조화 → 통합검색 → 패키지 추천 → 상세 확인 → 추천서 흐름이 깨지지 않습니다.
- 상세 모달에서 요약은 먼저 보이고, 긴 원문은 접혀 있습니다.
- 패키지에 포함된 서비스와 제외된 서비스가 화면에서 구분됩니다.

## 역할 2. Backend/Data & API 품질

목표: 공공데이터와 기관 데이터를 안정적으로 가져오고, 프론트가 신뢰할 수 있는 형태로 제공합니다.

주요 책임:

- 공공데이터포털/복지로 API 연결 유지
- 중앙부처/지자체 목록 및 상세조회 필드 매핑 개선
- 샘플 서비스와 실제 상세조회 ID 연결 안정화
- 사회서비스 제공기관/민간자원/지역기관 API 개선
- API timeout, retry, cache 정책 추가
- Render 배포 설정 관리
- 향후 DB 저장소 도입

수정 가능 파일:

- `backend_server.py`
- `backend_runtime_patch.py`
- `detail_alias_patch.py`
- `.env.example`
- `requirements.txt`
- `render.yaml`
- `runtime.txt`

주의할 점:

- API 키를 코드에 직접 넣지 않습니다.
- API 응답이 비어도 프론트가 깨지지 않게 fallback을 유지합니다.
- 상세조회가 불가능한 외부 포털 서비스는 이유를 `meta.detail.reason`에 남깁니다.
- Render에서는 `PORT`가 자동 주입되므로 고정 포트에 의존하지 않습니다.

완료 기준:

- `npm run check`가 통과합니다.
- `/api/health`가 정상 응답합니다.
- API 키가 없거나 API가 실패해도 로컬 fallback이 동작합니다.
- 신규 응답 필드는 README나 PR 설명에 기록합니다.

추천 이슈:

- 공공 API 결과 캐시 10분 적용
- `/api/health`에 API별 상태 점검 결과 추가
- 지역명 표준화 함수 추가
- SQLite로 상담 저장/최근 상담 조회 구현
- 검증된 민간 복지기관 DB 구축

## 역할 3. AI/Recommendation & Safety

목표: AI 구조화와 추천 결과가 현장 기준에 맞고, 개인정보와 안전 리스크를 줄입니다.

주요 책임:

- Gemini 프롬프트 개선
- 상담 구조화 JSON 스키마 검증
- 사용자가 선택한 욕구와 LLM 구조화 결과 병합
- 추천 패키지 점수 로직 개선
- 상세조회 원문 요약 품질 개선
- 노인/청소년/아동/장애/한부모 등 대상 조건 필터링 강화
- 추천서 근거 문장 품질 개선
- 개인정보/민감정보 마스킹

수정 가능 파일:

- `llm_enhancement_patch.py`
- `recommendation_relevance_patch.py`
- `age-filter-patch.js`
- `backend_server.py` 중 `analyze_case`, `generate_packages`, `build_report`
- 향후 `ai/`, `recommendation/`, `safety/`, `tests/`

중요한 원칙:

- LLM이 새 복지서비스를 만들게 하지 않습니다.
- 실제 API/로컬 목록으로 후보를 만든 뒤, LLM은 후보 안에서 요약·재정렬만 합니다.
- LLM이 실패해도 규칙 기반 구조화와 추천이 계속 동작해야 합니다.
- 상담 대상과 맞지 않는 서비스는 후보 보충 단계에서도 다시 들어오면 안 됩니다.

완료 기준:

- 대상 연령이나 조건이 맞지 않는 서비스가 추천 패키지에 들어가지 않습니다.
- 사용자가 선택한 욕구가 LLM 구조화 결과에서 누락되어도 추천 단계에서 유지됩니다.
- 상세 요약은 원문에 없는 자격, 금액, 연락처를 만들지 않습니다.
- 추천서에 허위 확정 표현을 쓰지 않고 확인 필요 사항을 남깁니다.

추천 이슈:

- 노인, 청소년, 한부모, 장애, 의료위기 상담별 기대 추천 결과 테스트 작성
- LLM 응답 JSON schema validation 강화
- 추천 결과에 “왜 이 서비스가 포함됐는지” 설명 필드 추가
- 주민번호, 전화번호, 상세주소 마스킹 추가
- 추천 품질 평가표 작성

## 공통 GitHub 작업 규칙

브랜치 이름:

```text
feature/<area>-<short-summary>
fix/<area>-<short-summary>
docs/<short-summary>
```

커밋 메시지 예시:

```text
Improve detail summary modal
Add provider API cache
Fix age-target package filtering
Document team workflow
```

PR 설명에는 아래를 포함합니다.

```text
## 변경 내용
- 무엇을 바꿨는지

## 확인 방법
- 실행한 명령
- 화면 확인 내용
- 테스트 상담 문장

## 영향 범위
- 화면/API/추천/배포 중 어디에 영향이 있는지

## 주의 사항
- 아직 남은 문제나 후속 작업
```

## AI 도구에 작업을 맡기는 템플릿

```text
저장소: hitori-gotoh2002/ai-welfare-referral-system
목표: <이번 작업 목표>
담당 영역: Product/UX | Backend/Data | AI/Recommendation 중 하나
수정해도 되는 파일: <파일 목록>
건드리지 말아야 할 파일: .env, API 키, 실제 개인정보 데이터
현재 배포: Render, main 브랜치 커밋 시 자동 배포
작업 전 반드시 읽을 문서: README.md, TEAM_ROLES.md
검증 명령: npm run check
PR 설명에 포함할 것: 변경 내용, 확인 방법, 영향 범위, 남은 작업
```

예시:

```text
AI/Recommendation 역할로 작업해줘.
노인 상담에서 청소년 전용 서비스가 추천되지 않도록 후보 보충 단계까지 점검해줘.
LLM은 새 서비스를 만들지 말고 실제 후보 id 안에서만 재정렬하게 해줘.
수정 가능 파일은 llm_enhancement_patch.py, recommendation_relevance_patch.py, age-filter-patch.js야.
검증 상담 문장은 README.md의 78세 독거 어르신 예시를 사용해줘.
```

## 테스트 상담 세트

노인 상담:

```text
서울 관악구에 거주하는 78세 독거 어르신입니다. 최근 낙상 이후 병원 이동이 어렵고 식사 준비와 복약 관리가 힘듭니다. 자녀는 지방에 있어 방문이 어렵고 월세와 병원비 부담도 있습니다. 방문 돌봄, 의료비, 생계 지원을 함께 확인하고 싶습니다.
```

청소년 상담:

```text
서울에 거주하는 16세 청소년입니다. 보호자와 갈등이 심해 임시 거처가 필요하고, 식비와 상담 지원이 필요합니다. 학교 밖 청소년 지원과 긴급 생계 지원 가능성을 함께 확인하고 싶습니다.
```

한부모 상담:

```text
인천에 거주하는 한부모 가정입니다. 초등학생 자녀 1명을 양육하고 있고 최근 실직으로 월세와 식비 부담이 큽니다. 아동 돌봄, 생계비, 주거 지원, 취업 상담을 함께 연계하고 싶습니다.
```

## 절대 하지 말아야 할 것

- `.env` 커밋
- API 키를 README, 이슈, PR, 코드에 직접 작성
- 실제 상담자의 개인정보를 테스트 데이터로 업로드
- 검증 없이 `main`에 큰 변경 반영
- Render 환경변수 값을 스크린샷으로 공유
