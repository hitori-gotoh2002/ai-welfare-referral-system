# TEAM_ROLES: 3인 분업 및 AI 협업 매뉴얼

이 문서는 3명이 GitHub에서 동시에 개발하고, 각자 다른 Codex/Claude 계정을 사용해도 충돌을 줄이며 이어 작업할 수 있도록 만든 작업 매뉴얼입니다.

AI 도구가 이어서 작업할 때의 최신 기준 문서는 `CLAUDE.md`입니다. 작업을 맡기기 전에는 `CLAUDE.md`를 먼저 읽게 하고, 롤백된 HWP/dashboard/applicationDraft 관련 파일을 다시 만들지 않도록 확인하세요.

## 프로젝트 한 줄 설명

상담 메모를 AI로 구조화하고, 공공 복지서비스·지역기관 데이터를 조회해 상담 대상자에게 맞는 복지 연계 패키지와 추천서 초안을 생성하는 웹 MVP입니다.

## 현재 상태 요약

현재 서비스는 “시연만 되는 정적 화면”이 아니라 실제로 동작하는 웹입니다.

동작하는 것:

- Render 배포 URL 접속
- 상담 입력
- Gemini API 기반 상담 구조화
- 공공데이터/복지로 API 기반 복지서비스 조회
- Gemini 기반 상세조회 요약
- 사회서비스 제공기관/민간자원 기관 조회
- 규칙 기반 후보 산출 + Gemini 후보 재정렬 방식의 추천 패키지 생성
- 실무형 추천서 생성: 사례 요약, 실행계획, 체크리스트, 기록 문구
- 추천서 복사/인쇄

아직 부족한 것:

- 실제 회원가입/로그인/권한 관리
- DB 기반 상담 저장
- 운영 수준 개인정보 보호
- 자동 테스트와 CI
- 추천 품질 평가 체계
- 백엔드 추천 로직의 완전한 모듈화

## 역할 분배 원칙

세 사람은 “화면”, “데이터/API”, “AI/추천 품질”로 나누는 것을 권장합니다. 한 PR에서 여러 영역을 동시에 크게 바꾸면 충돌과 회귀가 생기기 쉽습니다.

| 역할 | 주 담당 | 주요 파일 |
| --- | --- | --- |
| 1. Product/UX & 현장 워크플로우 | 화면 흐름, 사용성, 문구, 출력물 | `index.html`, `styles.css`, `app.js`의 렌더링 함수 |
| 2. Backend/Data & API 품질 | 공공 API, 기관 API, 서버, 배포 | `backend_server.py`, `.env.example`, `render.yaml`, `requirements.txt` |
| 3. AI/Recommendation & Safety | Gemini 프롬프트, 추천 로직, 안전장치 | `backend_server.py`, `recommendation_relevance_patch.py`, `llm_enhancement_patch.py`, `age-filter-patch.js`, 향후 `ai/`, `recommendation/`, `safety/` |

## 역할 1. Product/UX & 현장 워크플로우

목표: 현장 종사자가 상담 중 빠르고 헷갈리지 않게 사용할 수 있는 화면을 만듭니다.

주요 책임:

- 상담 입력 화면 개선
- 대시보드, 최근 상담, 복지 검색, 패키지 편집 화면 개선
- 추천서 화면의 문구와 출력 레이아웃 개선
- 모바일/태블릿 화면 점검
- 실제 현장 상담 시나리오 정리

수정 가능 파일:

- `index.html`
- `styles.css`
- `app.js` 중 `render...`로 시작하는 화면 렌더링 함수
- README나 사용자 안내 문서

주의할 점:

- `app.js`의 API 호출 함수나 추천 점수 함수까지 함께 바꾸면 역할 2, 3과 충돌할 수 있습니다.
- 큰 UI 개편은 스크린샷 또는 변경 전후 설명을 PR에 남깁니다.
- 버튼, 탭, 검색 필터 같은 조작 요소는 실제로 클릭 가능한 상태까지 구현합니다.

추천 이슈:

- 상담 입력 화면에 “대상자 정보/문제/긴급도” 섹션 분리
- 패키지 편집 화면에서 서비스 제외 사유 메모 기능 추가
- 추천서 PDF 출력 레이아웃 개선
- 모바일에서 좌우 패널이 너무 좁아지는 문제 개선

완료 기준:

- 상담 입력 → 구조화 → 패키지 추천 → 추천서까지 화면 이동이 깨지지 않습니다.
- 긴 문장이나 긴 서비스명이 카드 밖으로 넘치지 않습니다.
- 변경한 화면을 최소 데스크톱 1개, 모바일 폭 1개에서 확인합니다.

## 역할 2. Backend/Data & API 품질

목표: 공공데이터와 기관 데이터를 안정적으로 가져오고, 프론트가 신뢰할 수 있는 형태로 제공합니다.

주요 책임:

- 공공데이터포털/복지로 API 연결 유지
- 중앙부처/지자체 목록 및 상세조회 필드 매핑 개선
- 사회서비스 제공기관/민간자원/지역기관 API 개선
- 지역명, 서비스명, 중복 데이터 정규화
- API timeout, retry, cache 정책 추가
- Render 배포 설정 관리
- 향후 DB 저장소 도입

수정 가능 파일:

- `backend_server.py`
- `.env.example`
- `requirements.txt`
- `render.yaml`
- `runtime.txt`
- 향후 `services/`, `data/`, `db/` 디렉터리

주의할 점:

- API 키를 코드에 직접 넣지 않습니다.
- 공공 API 응답이 비어도 프론트가 깨지지 않게 fallback을 유지합니다.
- 응답 필드명을 바꿀 때는 `app.js`에서 사용하는 필드와 맞춰야 합니다.
- Render에서는 `PORT`가 자동 주입되므로 고정 포트에 의존하지 않습니다.

추천 이슈:

- `/api/services` 응답에 API 출처와 상세조회 성공 여부 표시
- 지역명 표준화 함수 추가
- 공공 API 결과 캐시 10분 적용
- SQLite로 상담 저장/최근 상담 조회 구현
- `/api/health`에 API별 상태 점검 결과 추가

완료 기준:

- `npm run check`가 통과합니다.
- JS 변경 시 `npm run check:js`가 통과합니다.
- `/api/health`가 정상 응답합니다.
- API 키가 없거나 API가 실패해도 로컬 fallback이 동작합니다.
- 신규 응답 필드는 README나 PR 설명에 기록합니다.

## 역할 3. AI/Recommendation & Safety

목표: AI 구조화와 추천 결과가 현장 기준에 맞고, 개인정보와 안전 리스크를 줄입니다.

주요 책임:

- Gemini 프롬프트 개선
- 상담 구조화 JSON 스키마 검증
- 추천 패키지 점수 로직 개선
- 상세조회 원문을 현장 실무자가 읽기 쉬운 요약으로 정리
- 추천서를 서비스 목록이 아니라 서비스 제공계획·점검계획 형태로 구성
- 노인/청소년/아동/장애/한부모 등 대상 조건 필터링 강화
- 추천 근거 문장 품질 개선
- 개인정보/민감정보 마스킹
- 위기 신호 감지와 안내 문구 개선

수정 가능 파일:

- `backend_server.py` 중 `analyze_case`, `generate_packages`, `build_report`
- `recommendation_relevance_patch.py`
- `llm_enhancement_patch.py`
- `age-filter-patch.js`
- 향후 `ai/`, `recommendation/`, `safety/`, `tests/`

중요한 현재 이슈:

- `age-filter-patch.js`는 노인 상담에 `청소년특별지원` 같은 청소년 전용 서비스가 섞이는 문제를 막기 위한 프론트 후처리 패치입니다.
- `llm_enhancement_patch.py`는 LLM이 서비스를 새로 만들지 못하게 하고, 실제 후보 목록 안에서 요약·재정렬만 수행하도록 제한합니다.
- 장기적으로는 이 로직을 백엔드 추천 엔진에 통합하고, 프론트 패치는 제거하는 것이 좋습니다.

추천 이슈:

- 추천 점수표를 문서화하고 테스트 케이스 작성
- 노인 상담, 청소년 상담, 한부모 상담, 장애 상담 샘플별 추천 결과 검증
- LLM 응답 JSON schema validation 추가
- 추천서에 “추천 근거/확인 필요 사항/신청 전 유의사항” 분리
- 주민번호, 전화번호, 상세주소 마스킹 추가

완료 기준:

- 대상 연령이나 조건이 맞지 않는 서비스가 추천 패키지에 들어가지 않습니다.
- LLM이 실패해도 로컬 추천 결과가 생성됩니다.
- 추천서에 허위 확정 표현을 쓰지 않고, 확인 필요 사항을 남깁니다.
- 추천서에 서비스별 역할, 추천 근거, 확인 조건, 단계별 실행계획이 포함됩니다.
- 테스트 상담 예시를 PR에 포함합니다.

## 공통 GitHub 작업 규칙

브랜치 이름:

```text
feature/<area>-<short-summary>
fix/<area>-<short-summary>
docs/<short-summary>
```

예시:

```text
feature/ux-report-print
feature/api-service-cache
fix/recommendation-age-target
docs/team-manual
```

커밋 메시지:

```text
Improve report print layout
Add service API cache
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

## AI 도구에게 작업을 맡기는 방법

다른 계정의 Codex나 Claude에게 요청할 때는 아래 템플릿을 사용하면 됩니다.

```text
저장소: hitori-gotoh2002/ai-welfare-referral-system
목표: <이번 작업 목표>
담당 영역: Product/UX | Backend/Data | AI/Recommendation 중 하나
수정해도 되는 파일: <파일 목록>
건드리지 말아야 할 파일: .env, API 키, 실제 개인정보 데이터
현재 배포: Render, main 브랜치 커밋 시 자동 배포
작업 전 반드시 읽을 문서: CLAUDE.md, README.md, TEAM_ROLES.md
검증 명령: npm run check, 또는 CLAUDE.md의 개별 Python/Node 검증 명령
PR 설명에 포함할 것: 변경 내용, 확인 방법, 영향 범위, 남은 작업
```

작업 요청 예시:

```text
AI/Recommendation 역할로 작업해줘.
노인 상담에서 청소년 전용 서비스가 추천되지 않도록 백엔드 generate_packages 로직에 대상 연령 필터를 통합해줘.
age-filter-patch.js의 임시 후처리는 최종적으로 제거할 수 있게 해줘.
수정 파일은 backend_server.py, app.js, age-filter-patch.js까지 가능해.
검증 상담 문장은 README.md의 72세 독거 어르신 예시를 사용해줘.
```

## 충돌을 줄이는 파일 경계

동시에 작업할 때는 아래 기준을 지킵니다.

- UX 담당자는 주로 `styles.css`와 `app.js`의 `render...` 함수만 수정합니다.
- Backend 담당자는 주로 `backend_server.py`의 API 함수와 서버 라우터를 수정합니다.
- AI 담당자는 추천/LLM 함수와 테스트 케이스를 수정합니다.
- 같은 파일을 같이 수정해야 하면 먼저 GitHub 이슈에 “내가 이 줄 근처 작업 중”이라고 남깁니다.

## 현재 추천 개선 로드맵

1. `age-filter-patch.js` 로직을 `backend_server.py`의 `generate_packages`에 완전히 통합
2. 추천 점수 계산을 별도 함수/모듈로 분리
3. 상담 대상 조건과 서비스 대상 조건을 공통 스키마로 정규화
4. 샘플 상담 10개와 기대 추천 결과를 테스트로 작성
5. 추천 결과에 “왜 이 서비스가 포함됐는지” 설명 필드 추가
6. 현장 피드백으로 점수 가중치 조정

## 현재 운영 준비 로드맵

1. 실제 인증과 권한
2. DB 저장소
3. 개인정보 마스킹
4. 감사 로그
5. API 호출량 제한
6. 오류 모니터링
7. 정기 백업

## 테스트 상담 세트

노인 상담:

```text
서울 관악구에 거주하는 72세 독거 어르신입니다. 최근 허리 통증으로 외출이 어렵고 식사를 거르는 날이 많습니다. 기초연금 외에는 소득이 거의 없고 월세 부담이 커서 생계비와 주거비 지원이 필요합니다. 병원 동행, 방문 돌봄, 도시락 또는 식사 지원을 함께 연계하고 싶습니다.
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
- `main`에 검증 없이 직접 큰 변경 반영
- 화면/API/추천 로직을 한 PR에서 동시에 대규모로 변경
- Render 환경변수 값을 스크린샷으로 공유

## 팀원이 작업을 마친 뒤 확인할 것

- GitHub PR이 작고 읽기 쉬운지
- 변경한 역할 범위를 넘지 않았는지
- `.env`나 개인정보가 포함되지 않았는지
- Render 배포 후 `/api/health`가 정상인지
- 테스트 상담 예시로 핵심 플로우가 깨지지 않는지
