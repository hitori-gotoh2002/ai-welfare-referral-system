# TEAM_ROLES: 3인 분업 및 AI 협업 매뉴얼

이 문서는 3명이 GitHub에서 분업하고, 각자 Codex 또는 Claude Code를 사용해도 충돌을 줄이며 이어서 작업할 수 있도록 만든 기준 문서입니다.

AI 도구가 이어서 작업할 때의 최신 기준은 [CLAUDE.md](CLAUDE.md)입니다. 새 작업을 맡기기 전에는 반드시 `CLAUDE.md`를 먼저 읽게 하세요.

## 현재 서비스 요약

복지연계 코파일럿은 현장 종사자가 상담 메모를 입력하면 AI가 욕구와 위험 신호를 구조화하고, 공공 복지서비스/기관 데이터를 조회해 추천 패키지와 추천서 초안을 생성하는 웹 MVP입니다.

현재 실제로 작동하는 기능:

- Render 배포 URL 접속
- 데모 로그인
- 상담 입력
- 상담 목록 저장/조회/삭제
- Gemini 기반 상담 구조화
- 공공데이터/복지로 API 기반 복지서비스 목록·상세조회
- 사회서비스 제공기관/민간자원/지역기관 조회
- 공식 상세 링크 보정
- 규칙 기반 후보 산출 + Gemini 후보 재정렬
- 패키지 선택/해제/추가
- 추천서 생성, 복사, 인쇄/PDF 저장

아직 운영 수준이 아닌 기능:

- 실제 계정 로그인과 권한 관리
- 운영 DB와 장기 보관 정책
- 개인정보 마스킹/암호화
- 감사 로그
- API 캐시, 호출량 제한, 장애 대응 체계
- 자동화 테스트와 추천 품질 평가셋

## 권장 역할 분담

| 역할 | 담당 범위 | 주요 파일 |
| --- | --- | --- |
| 1. Product/UX & Workflow | 화면 흐름, 상담 입력 UX, 대시보드/상담 목록, 추천서 출력, 문구 | `app.js`, `styles.css`, `commercial-ui-polish.js`, `commercial-ui-style-fix.js`, `case-list-persistence-patch.js`, `README.md` |
| 2. Backend/Data & Deployment | API, 공공데이터, 기관 조회, 상담 저장, Render 배포, 환경변수 | `backend_server.py`, `backend_runtime_patch.py`, `detail_alias_patch.py`, `welfare_link_patch.py`, `server_entry.py`, `render.yaml`, `.env.example` |
| 3. AI/Recommendation & Safety | Gemini 프롬프트, 추천 로직, 대상/연령/지역 안전장치, 추천서 품질 | `recommendation_relevance_patch.py`, `llm_enhancement_patch.py`, `rich_report_patch.py`, `age-filter-patch.js`, `status-feedback-patch.js` |

한 PR에서 세 영역을 크게 동시에 바꾸면 충돌과 회귀가 생기기 쉽습니다. 가능하면 한 PR은 한 역할 범위에 맞춰 작게 유지합니다.

## 역할 1. Product/UX & Workflow

목표: 현장 종사자가 상담을 입력하고, 결과를 검토하고, 추천서를 출력하는 흐름이 자연스럽게 이어지도록 합니다.

주요 책임:

- 상담 입력 화면 개선
- 대시보드와 상담 목록 UX 개선
- 통합 검색/패키지 추천 화면의 선택 상태 표시 개선
- 추천서 화면 문구와 출력 레이아웃 개선
- 모바일/태블릿 화면 점검
- 빈 상태, 로딩 상태, 오류 상태 정리

주의할 점:

- 데모용 숫자 지표처럼 실제 데이터와 연결되지 않은 UI는 넣지 않습니다.
- 버튼은 실제 동작까지 연결합니다.
- 화면에서 “상담 목록”은 백엔드 `/api/cases`와 연결되어야 합니다.
- HWP 가이드 카드 UI는 롤백된 기능이므로 다시 넣지 않습니다.

완료 기준:

- 상담 입력 → AI 구조화 → 통합 검색 → 패키지 추천 → 추천서 흐름이 깨지지 않습니다.
- 저장한 상담이 상담 목록에 나타나고 이어서 진행할 수 있습니다.
- `npm run check`가 통과합니다.

## 역할 2. Backend/Data & Deployment

목표: 공공데이터와 저장 API가 안정적으로 작동하고, 배포 환경에서도 같은 동작을 유지하게 합니다.

주요 책임:

- 공공데이터포털/복지로 API 연결 유지
- 중앙부처/지자체 서비스 목록·상세조회 필드 매핑 개선
- 사회서비스 제공기관/민간자원 API 개선
- 공식 상세 링크 보정
- 상담 저장 API 유지
- Render 설정, 환경변수, 배포 로그 점검
- 운영 DB 전환 준비

주의할 점:

- API 키를 코드, README, 이슈, PR에 적지 않습니다.
- API 실패 시에도 프론트가 깨지지 않도록 fallback을 유지합니다.
- 현재 `.data/cases.json`은 MVP용 저장소입니다. Render 재배포/재시작까지 안정적으로 보장되는 운영 DB가 아닙니다.
- 외부 사이트 링크는 가능한 공식 상세/안내 페이지로 연결하되, 안정적인 딥링크가 없으면 공식 검색/안내 페이지로 연결합니다.

완료 기준:

- `/api/health`가 정상 응답합니다.
- `/api/services`, `/api/services/{id}`, `/api/cases`가 정상 동작합니다.
- `npm run check`가 통과합니다.

## 역할 3. AI/Recommendation & Safety

목표: 상담 메모가 추천 결과에 실제로 반영되고, 대상자 조건과 맞지 않는 제도가 추천되지 않도록 합니다.

주요 책임:

- Gemini 구조화 프롬프트 개선
- Gemini 실패 원인 메시지와 fallback 품질 개선
- 패키지 추천 점수와 후보 다양성 개선
- 노인/청소년/아동/장애/한부모 등 대상 조건 필터링 강화
- 지역 기반 지자체 서비스 오추천 방지
- 추천서 문장 품질과 안전 문구 개선
- 테스트 상담 사례별 기대 결과 정리

주의할 점:

- LLM이 새로운 복지제도를 임의 생성하게 하지 않습니다.
- Gemini는 후보 목록 재정렬, 상세 요약, 추천서 작성 보조에 사용합니다.
- 최종 수급 가능성을 확정적으로 표현하지 않습니다.
- 위기 신호가 있는 경우 “확인 필요”와 “기관 문의” 문구를 남깁니다.

완료 기준:

- 노인 상담에서 청소년 전용 서비스가 상위 추천되지 않습니다.
- 상담 메모의 지역, 대상, 욕구가 검색/추천 결과에 반영됩니다.
- LLM 실패 시에도 규칙 기반 결과가 생성됩니다.

## Git 작업 규칙

권장 브랜치명:

```text
feature/<area>-<short-summary>
fix/<area>-<short-summary>
docs/<short-summary>
```

예시:

```text
feature/ux-case-list
feature/api-service-cache
fix/recommendation-age-target
docs/update-readme
```

PR 설명에는 아래를 포함합니다.

```text
## 변경 내용
- 무엇을 바꿨는지

## 확인 방법
- 실행한 명령
- 화면에서 확인한 흐름

## 영향 범위
- 화면/API/추천/배포 중 어디에 영향이 있는지

## 남은 작업
- 다음에 이어서 해야 할 일
```

## 검증 명령

전체:

```powershell
npm run check
```

개별:

```powershell
npm run check:js
npm run check:py
```

Render 배포 후:

```text
https://ai-welfare-referral-system.onrender.com/api/health
https://ai-welfare-referral-system.onrender.com/api/cases
```

## AI 도구에게 작업을 맡기는 템플릿

```text
저장소: hitori-gotoh2002/ai-welfare-referral-system
먼저 읽을 문서: CLAUDE.md, README.md, TEAM_ROLES.md
목표: <이번 작업 목표>
담당 영역: Product/UX | Backend/Data | AI/Recommendation 중 하나
수정 가능 파일: <파일 목록>
건드리지 말 파일: .env, 실제 API 키, 실제 개인정보 데이터
검증 명령: npm run check
배포: main 브랜치 push 시 Render 자동 배포
주의: HWP 가이드 카드, applicationDraft, 대시보드 마일스톤 테이블은 롤백된 기능이므로 다시 만들지 말 것
```

## 테스트 상담 예시

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

## 절대 하지 말 것

- `.env` 커밋
- API 키를 README, 이슈, PR, 코드에 직접 작성
- 실제 개인정보가 담긴 상담 메모를 테스트 데이터로 업로드
- 검증 없이 `main`에 직접 큰 변경 push
- 롤백된 HWP/applicationDraft/대시보드 마일스톤 기능을 임의로 재도입
- Render 환경변수 화면을 스크린샷으로 공유

## 다음 개선 로드맵

1. 파일 기반 상담 저장을 SQLite/PostgreSQL로 교체
2. 개인정보 마스킹과 민감정보 저장 정책 추가
3. 추천 결과 평가셋 작성
4. 공공데이터 API 캐시/재시도 정책 추가
5. 추천 로직을 별도 모듈로 분리
6. Playwright 기반 화면 흐름 테스트 추가
