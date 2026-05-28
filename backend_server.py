from __future__ import annotations

import json
import os
import re
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, unquote, urlencode, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parent


def load_dotenv(path: Path = ROOT / ".env") -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv()


PUBLIC_DATA_KEY_ENV_NAMES = ("DATA_GO_KR_SERVICE_KEY", "BOKJIRO_SERVICE_KEY", "PUBLIC_DATA_SERVICE_KEY")
NATIONAL_WELFARE_URL = os.getenv(
    "BOKJIRO_NATIONAL_WELFARE_URL",
    "https://apis.data.go.kr/B554287/NationalWelfareInformationsV001/NationalWelfarelistV001",
)
NATIONAL_WELFARE_DETAIL_URL = os.getenv(
    "BOKJIRO_NATIONAL_WELFARE_DETAIL_URL",
    "https://apis.data.go.kr/B554287/NationalWelfareInformationsV001/NationalWelfaredetailedV001",
)
LOCAL_WELFARE_URL = os.getenv(
    "BOKJIRO_LOCAL_WELFARE_URL",
    "https://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations/LcgvWelfarelist",
)
LOCAL_WELFARE_DETAIL_URL = os.getenv(
    "BOKJIRO_LOCAL_WELFARE_DETAIL_URL",
    "https://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations/LcgvWelfaredetailed",
)
SOCIALSERVICE_PROVIDER_URL = os.getenv(
    "SOCIALSERVICE_PROVIDER_URL",
    "https://api.socialservice.or.kr:444/api/service/provider/providerList",
)
RESOURCE_INFO_URL = os.getenv(
    "RESOURCE_INFO_URL",
    "http://apis.data.go.kr/B554287/resrceInfoInqireService/getPrvateResrcInfoInqire",
)
def first_env_value(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def normalize_gemini_key(value: str) -> str:
    raw = (value or "").strip().strip('"').strip("'")
    match = re.search(r"AIza[0-9A-Za-z_-]{20,}", raw)
    if match:
        return match.group(0)
    return raw.split(",", 1)[0].split(";", 1)[0].split()[0] if raw else ""


def split_env_list(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[,;\s]+", value or "") if item.strip()]


GEMINI_API_KEY = normalize_gemini_key(
    first_env_value("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY")
)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta").strip()
GEMINI_FALLBACK_MODELS = split_env_list(os.getenv("GEMINI_FALLBACK_MODELS", "gemini-2.0-flash,gemini-1.5-flash"))
GEMINI_LAST_ERROR = ""

NEEDS = ["주거", "생계", "심리", "취업", "의료", "돌봄", "안전", "교육"]

KEYWORD_MAP = {
    "주거": ["월세", "임대료", "체납", "퇴거", "주거", "거처", "보증금"],
    "생계": ["소득", "생활비", "식비", "생계", "실직", "근로시간", "긴급지원"],
    "심리": ["우울", "불안", "수면", "자살", "정신", "상담", "고립"],
    "취업": ["구직", "취업", "일자리", "직업", "훈련", "근로"],
    "의료": ["치료비", "의료비", "병원", "진료", "약값", "간병"],
    "돌봄": ["돌봄", "양육", "보호자", "아동", "청소년", "노인"],
    "안전": ["폭력", "학대", "자해", "자살", "위험", "가출"],
    "교육": ["학교", "학습", "장학", "검정고시", "교육"],
}

SERVICES = [
    {
        "id": "svc-1",
        "name": "긴급복지 생계지원",
        "source": "중앙",
        "region": "전국",
        "target": "저소득",
        "domains": ["생계", "주거"],
        "urgency": "긴급",
        "summary": "갑작스러운 위기 상황으로 생계 유지가 어려운 가구에 생계비와 주거비 등을 신속 지원합니다.",
        "eligibility": "소득·재산 기준, 위기사유, 금융재산 기준 확인 필요",
        "support": "생계비, 의료비, 주거지원, 사회복지시설 이용 지원",
        "process": "읍면동 상담 → 위기사유 확인 → 현장 확인 → 지원 결정",
        "docs": ["신분증", "소득 감소 증빙", "임대차계약서", "통장 사본"],
        "contact": "보건복지상담센터 129 / 관할 읍면동",
        "url": "https://www.bokjiro.go.kr",
        "updated": "2026 기준",
        "group": "emergency-basic",
    },
    {
        "id": "svc-2",
        "name": "서울형 긴급복지",
        "source": "지자체",
        "region": "서울",
        "target": "저소득",
        "domains": ["생계", "주거"],
        "urgency": "긴급",
        "summary": "서울 거주 위기가구에 생계비, 주거비, 의료비를 보완 지원합니다.",
        "eligibility": "서울 거주, 위기사유, 소득·재산 기준 확인",
        "support": "생계비, 주거비, 의료비, 교육비 일부",
        "process": "동주민센터 접수 → 구청 심의 → 지급",
        "docs": ["주민등록등본", "위기사유 증빙", "임대료 체납 내역"],
        "contact": "다산콜센터 120 / 관할 동주민센터",
        "url": "https://wis.seoul.go.kr",
        "updated": "2026 기준",
        "group": "emergency-basic",
    },
    {
        "id": "svc-3",
        "name": "주거취약계층 주거상향 지원",
        "source": "중앙",
        "region": "전국",
        "target": "주거취약",
        "domains": ["주거"],
        "urgency": "일반",
        "summary": "고시원·쪽방·반지하 등 주거취약 상태의 가구가 공공임대주택으로 이전할 수 있도록 지원합니다.",
        "eligibility": "주거취약 형태, 소득·자산 기준, 무주택 여부",
        "support": "공공임대 연계, 이주비·보증금 상담, 정착 지원",
        "process": "주거복지센터 상담 → 자격 확인 → LH/SH 신청 → 입주 지원",
        "docs": ["임대차계약서", "주거환경 확인 자료", "소득 증빙"],
        "contact": "마이홈 1600-1004 / 지역 주거복지센터",
        "url": "https://www.myhome.go.kr",
        "updated": "2026 기준",
        "group": "housing-upgrade",
    },
    {
        "id": "svc-4",
        "name": "청년월세 한시 특별지원",
        "source": "중앙",
        "region": "전국",
        "target": "청년",
        "domains": ["주거", "생계"],
        "urgency": "일반",
        "summary": "부모와 별도 거주하는 무주택 청년에게 월세 일부를 한시 지원합니다.",
        "eligibility": "연령, 거주, 소득·재산, 임차료 기준 확인",
        "support": "월세 일부를 일정 기간 지원",
        "process": "복지로 또는 주민센터 신청 → 소득·재산 조사 → 지급",
        "docs": ["임대차계약서", "월세 이체 증빙", "가족관계증명서"],
        "contact": "복지로 / 관할 주민센터",
        "url": "https://www.bokjiro.go.kr",
        "updated": "2026 기준",
        "group": "youth-rent",
    },
    {
        "id": "svc-5",
        "name": "청년 마음건강 지원사업",
        "source": "중앙",
        "region": "전국",
        "target": "청년",
        "domains": ["심리"],
        "urgency": "일반",
        "summary": "심리·정서적 어려움이 있는 청년에게 전문 심리상담 서비스를 제공합니다.",
        "eligibility": "연령 기준, 지역별 모집 여부, 우선순위 대상 확인",
        "support": "전문 심리상담 바우처, 사전·사후 검사",
        "process": "주민센터 신청 → 대상자 선정 → 제공기관 선택 → 상담 진행",
        "docs": ["신분증", "신청서", "우선순위 증빙"],
        "contact": "관할 읍면동 / 지역사회서비스지원단",
        "url": "https://www.socialservice.or.kr",
        "updated": "2026 기준",
        "group": "mental-youth",
    },
    {
        "id": "svc-6",
        "name": "정신건강복지센터 상담 연계",
        "source": "기관",
        "region": "서울",
        "target": "전국민",
        "domains": ["심리", "안전"],
        "urgency": "긴급",
        "summary": "우울, 불안, 자살위험 등 정신건강 어려움에 대해 지역 센터 상담과 위기 개입을 연결합니다.",
        "eligibility": "지역 거주 또는 생활권, 위기 수준 확인",
        "support": "초기 상담, 사례관리, 치료 연계, 응급 개입",
        "process": "센터 전화 → 초기 평가 → 상담 일정 배정 → 필요 시 의료기관 연계",
        "docs": ["상담 의뢰서", "보호자 연락처", "위험 신호 기록"],
        "contact": "정신건강위기상담 1577-0199 / 지역 정신건강복지센터",
        "url": "https://www.mentalhealth.go.kr",
        "updated": "2026 기준",
        "group": "mental-youth",
    },
    {
        "id": "svc-7",
        "name": "국민취업지원제도",
        "source": "중앙",
        "region": "전국",
        "target": "구직자",
        "domains": ["취업", "생계"],
        "urgency": "일반",
        "summary": "취업 취약계층에게 취업지원서비스와 구직촉진수당 또는 취업활동비용을 지원합니다.",
        "eligibility": "연령, 소득·재산, 취업경험, 구직 의사 확인",
        "support": "취업상담, 직업훈련, 일경험, 수당",
        "process": "고용24 신청 → 자격 심사 → 취업활동계획 수립 → 서비스 참여",
        "docs": ["신분증", "소득 관련 자료", "구직 신청 정보"],
        "contact": "고용노동부 1350 / 고용복지플러스센터",
        "url": "https://www.work24.go.kr",
        "updated": "2026 기준",
        "group": "employment",
    },
    {
        "id": "svc-8",
        "name": "지역 푸드마켓·푸드뱅크",
        "source": "민간",
        "region": "서울",
        "target": "저소득",
        "domains": ["생계"],
        "urgency": "긴급",
        "summary": "식료품과 생필품 지원이 필요한 가구에 지역 나눔 자원을 연계합니다.",
        "eligibility": "기초생활수급, 차상위, 긴급 위기가구 등 지역 기준",
        "support": "식료품, 생필품, 정기·긴급 물품 지원",
        "process": "동주민센터 또는 복지관 추천 → 이용 등록 → 물품 수령",
        "docs": ["추천서", "신분 확인 자료", "위기상황 기록"],
        "contact": "지역 사회복지관 / 푸드뱅크",
        "url": "https://www.foodbank1377.org",
        "updated": "2026 기준",
        "group": "food",
    },
    {
        "id": "svc-9",
        "name": "의료비 긴급지원",
        "source": "중앙",
        "region": "전국",
        "target": "저소득",
        "domains": ["의료", "생계"],
        "urgency": "긴급",
        "summary": "중대한 질병 또는 부상으로 의료비 부담이 큰 위기가구에 의료비를 지원합니다.",
        "eligibility": "위기사유, 의료 필요성, 소득·재산 기준",
        "support": "검사·치료비, 입원비 일부",
        "process": "병원 사회사업팀 상담 → 주민센터 또는 시군구 신청 → 지원 결정",
        "docs": ["진단서", "진료비 내역서", "소득 증빙"],
        "contact": "보건복지상담센터 129 / 병원 사회사업팀",
        "url": "https://www.bokjiro.go.kr",
        "updated": "2026 기준",
        "group": "medical",
    },
    {
        "id": "svc-10",
        "name": "위기청소년 통합지원",
        "source": "기관",
        "region": "전국",
        "target": "청소년",
        "domains": ["돌봄", "교육", "안전", "심리"],
        "urgency": "긴급",
        "summary": "위기 청소년에게 상담, 보호, 교육, 자립 서비스를 통합 연계합니다.",
        "eligibility": "청소년 위기상황, 보호 필요성, 학교·가정 상황 확인",
        "support": "상담, 긴급보호, 학업 복귀, 자립 지원",
        "process": "청소년상담복지센터 의뢰 → 위기 평가 → 통합지원회의 → 서비스 연계",
        "docs": ["상담기록", "보호자 동의", "학교 협조 자료"],
        "contact": "청소년상담 1388 / 지역 청소년상담복지센터",
        "url": "https://www.kyci.or.kr",
        "updated": "2026 기준",
        "group": "youth-crisis",
    },
    {
        "id": "svc-11",
        "name": "기초생활보장 생계급여",
        "source": "중앙",
        "region": "전국",
        "target": "기초생활수급자",
        "domains": ["생계"],
        "urgency": "일반",
        "summary": "소득인정액이 기준 중위소득 32% 이하인 가구에 매달 생계비를 현금 지원합니다.",
        "eligibility": "소득인정액 기준 중위소득 32% 이하 가구, 부양의무자 기준 완화, 수급자·기초생활",
        "support": "현금 지급 (가구별 생계급여 기준액 – 소득인정액)",
        "process": "주민센터 신청 → 소득·재산 조사 → 급여 결정 → 매월 지급",
        "docs": ["사회보장급여 신청서", "소득·재산 관련 증빙", "가족관계증명서"],
        "contact": "주민센터 / 복지로 / 보건복지상담 129",
        "url": "https://www.bokjiro.go.kr",
        "updated": "2026 기준",
        "group": "basic-livelihood",
    },
    {
        "id": "svc-12",
        "name": "기초생활보장 주거급여",
        "source": "중앙",
        "region": "전국",
        "target": "기초생활수급자",
        "domains": ["주거"],
        "urgency": "일반",
        "summary": "소득인정액 기준 중위소득 48% 이하 가구에 임차료 또는 수선유지비를 지원합니다.",
        "eligibility": "소득인정액 기준 중위소득 48% 이하, 임차 가구·자가 가구 구분, 저소득 임대 주거",
        "support": "임차가구: 임차료 지원 / 자가가구: 수선유지비 지원",
        "process": "주민센터 신청 → LH 조사 → 급여 결정 → 지급",
        "docs": ["임대차계약서", "통장 사본", "소득·재산 증빙"],
        "contact": "마이홈 1600-1004 / 주민센터",
        "url": "https://www.myhome.go.kr",
        "updated": "2026 기준",
        "group": "basic-housing",
    },
    {
        "id": "svc-13",
        "name": "기초생활보장 의료급여",
        "source": "중앙",
        "region": "전국",
        "target": "기초생활수급자",
        "domains": ["의료"],
        "urgency": "일반",
        "summary": "기준 중위소득 40% 이하 가구에 의료비 본인부담을 최소화하는 의료급여를 제공합니다.",
        "eligibility": "소득인정액 기준 중위소득 40% 이하 수급자, 1종·2종 구분",
        "support": "입원·외래 진료비 본인부담 감면, 약제비 지원",
        "process": "주민센터 신청 → 대상자 선정 → 의료급여증 발급",
        "docs": ["사회보장급여 신청서", "소득·재산 증빙"],
        "contact": "주민센터 / 국민건강보험공단 1577-1000",
        "url": "https://www.bokjiro.go.kr",
        "updated": "2026 기준",
        "group": "basic-medical",
    },
    {
        "id": "svc-14",
        "name": "한부모가족 복지급여",
        "source": "중앙",
        "region": "전국",
        "target": "한부모가족",
        "domains": ["생계", "돌봄"],
        "urgency": "일반",
        "summary": "한부모·미혼부모·조손가족에게 아동양육비, 교육지원비, 생활보조금 등을 지원합니다.",
        "eligibility": "소득인정액 기준 중위소득 63% 이하 한부모가족(모자·부자·조손가족), 편부·편모",
        "support": "아동양육비(월 21만원), 청소년한부모 지원, 교육지원비, 생활보조금",
        "process": "주민센터 신청 → 소득·재산 조사 → 대상자 결정 → 급여 지급",
        "docs": ["가족관계증명서", "소득·재산 증빙", "양육 확인 자료"],
        "contact": "주민센터 / 복지로 / 한부모가족상담 1644-6621",
        "url": "https://www.bokjiro.go.kr",
        "updated": "2026 기준",
        "group": "single-parent",
    },
    {
        "id": "svc-15",
        "name": "노인맞춤돌봄서비스",
        "source": "중앙",
        "region": "전국",
        "target": "노인",
        "domains": ["돌봄", "안전"],
        "urgency": "일반",
        "summary": "일상생활 지원이 필요한 65세 이상 독거·노인부부 가구에 안전 확인·생활지원·사회참여 서비스를 제공합니다.",
        "eligibility": "만 65세 이상, 독거노인 또는 노인단독 부부 가구, 신체·정신·인지기능 취약자 우선",
        "support": "안전확인, 가사지원, 신체기능 지원, 정신건강 지원, 사회참여 서비스",
        "process": "주민센터 신청 → 욕구 평가 → 제공기관 연계 → 서비스 제공",
        "docs": ["신분증", "건강 상태 관련 자료"],
        "contact": "주민센터 / 복지로 / 노인맞춤돌봄 수행기관",
        "url": "https://www.bokjiro.go.kr",
        "updated": "2026 기준",
        "group": "elder-care",
    },
    {
        "id": "svc-16",
        "name": "재난적의료비 지원",
        "source": "중앙",
        "region": "전국",
        "target": "저소득",
        "domains": ["의료", "생계"],
        "urgency": "긴급",
        "summary": "소득 대비 의료비 부담이 과도한 환자에게 진료비 일부를 지원합니다.",
        "eligibility": "건강보험료 기준 중위소득 200% 이하, 연간 의료비 본인부담 기준 초과, 치료비 부담 과다",
        "support": "입원·외래·약제비 중 본인부담 의료비 일부 지원 (연 최대 3000만원)",
        "process": "국민건강보험공단 지사 신청 → 심사 → 지원 결정",
        "docs": ["진료비 영수증", "의사 소견서", "건강보험료 납부 확인서"],
        "contact": "국민건강보험공단 1577-1000",
        "url": "https://www.nhis.or.kr",
        "updated": "2026 기준",
        "group": "catastrophic-medical",
    },
    {
        "id": "svc-17",
        "name": "장애인 활동지원",
        "source": "중앙",
        "region": "전국",
        "target": "장애인",
        "domains": ["돌봄", "안전"],
        "urgency": "일반",
        "summary": "혼자서 일상생활이 어려운 장애인에게 활동보조·방문목욕·방문간호 서비스를 제공합니다.",
        "eligibility": "만 6세 이상 장애인, 장애 정도·장애등급 확인, 활동지원 필요도 평가",
        "support": "활동보조, 방문목욕, 방문간호",
        "process": "주민센터 신청 → 서비스 조사 → 수급자 결정 → 이용",
        "docs": ["장애인등록증", "신분증", "활동지원 신청서"],
        "contact": "주민센터 / 국민연금공단 1355",
        "url": "https://www.bokjiro.go.kr",
        "updated": "2026 기준",
        "group": "disability-care",
    },
    {
        "id": "svc-18",
        "name": "자활사업",
        "source": "중앙",
        "region": "전국",
        "target": "기초생활수급자",
        "domains": ["취업", "생계"],
        "urgency": "일반",
        "summary": "근로 능력이 있는 저소득층에게 자활근로 기회와 자립역량 강화 서비스를 제공합니다.",
        "eligibility": "기초생활수급자(조건부 수급자), 차상위계층 근로 능력자, 저소득 구직자",
        "support": "자활근로 일자리, 자활 기업 창업 지원, 취업 훈련",
        "process": "주민센터 상담 → 자활 참여 계획 수립 → 지역자활센터 연계",
        "docs": ["신분증", "소득·재산 증빙"],
        "contact": "지역자활센터 / 주민센터",
        "url": "https://www.cjagis.go.kr",
        "updated": "2026 기준",
        "group": "self-reliance",
    },
    {
        "id": "svc-19",
        "name": "노인장기요양보험",
        "source": "중앙",
        "region": "전국",
        "target": "노인",
        "domains": ["돌봄", "의료"],
        "urgency": "일반",
        "summary": "치매·뇌혈관 등 노인성 질환으로 일상생활이 어려운 노인에게 요양급여를 제공합니다.",
        "eligibility": "만 65세 이상 또는 노인성 질환자, 장기요양등급 1~5등급 또는 인지지원등급",
        "support": "재가급여(방문요양·방문목욕·방문간호), 시설급여, 특별현금급여",
        "process": "국민건강보험공단 신청 → 방문조사 → 등급 판정 → 서비스 이용",
        "docs": ["신청서", "의사 소견서(필요 시)"],
        "contact": "국민건강보험공단 1577-1000",
        "url": "https://longtermcare.or.kr",
        "updated": "2026 기준",
        "group": "elder-care",
    },
    {
        "id": "svc-20",
        "name": "아동수당 및 양육 지원",
        "source": "중앙",
        "region": "전국",
        "target": "아동",
        "domains": ["돌봄", "생계"],
        "urgency": "일반",
        "summary": "만 8세 미만 아동에게 월 10만원 아동수당을 지급하고, 양육 관련 급여를 연계합니다.",
        "eligibility": "만 8세 미만(0~95개월) 아동 보호자, 주민등록 기준 거주",
        "support": "월 10만원 현금 지급, 양육수당, 어린이집 보육료 지원",
        "process": "복지로 또는 주민센터 신청 → 심사 → 매월 25일 지급",
        "docs": ["신분증", "통장 사본", "가족관계증명서"],
        "contact": "주민센터 / 복지로 / 보건복지상담 129",
        "url": "https://www.bokjiro.go.kr",
        "updated": "2026 기준",
        "group": "child-allowance",
    },
]

RECENT_CASES = [
    {
        "id": "case-20260522-01",
        "title": "청년 1인가구 월세 체납 우려",
        "region": "서울 관악구",
        "status": "추천서 생성",
        "needs": ["주거", "생계", "심리", "취업"],
        "memo": "청년 1인가구. 최근 근로시간 감소로 소득이 줄었고 월세 2개월 체납 우려가 있음. 식비 부담이 크며 우울감과 수면 문제가 있어 상담 연계를 희망함. 구직도 함께 알아보고 싶다고 함.",
    },
    {
        "id": "case-20260521-03",
        "title": "치료비 부담 환자 보호자 상담",
        "region": "경기 성남시",
        "status": "패키지 조정",
        "needs": ["의료", "생계"],
        "memo": "입원 치료비 부담이 크고 보호자 소득이 일정하지 않음. 의료비와 생계 지원을 함께 확인하고 싶음.",
    },
    {
        "id": "case-20260520-02",
        "title": "위기 청소년 보호체계 연계",
        "region": "서울 은평구",
        "status": "구조화 완료",
        "needs": ["돌봄", "심리", "안전", "교육"],
        "memo": "가정 내 갈등과 등교 거부가 지속됨. 상담과 보호, 학습 지원이 필요함.",
    },
]

SAVED_CASES: list[dict[str, Any]] = []


def get_public_data_key() -> str:
    for name in PUBLIC_DATA_KEY_ENV_NAMES:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def get_socialservice_key() -> str:
    return os.getenv("SOCIALSERVICE_SERVICE_KEY", "").strip() or get_public_data_key()


def clean_text(value: str) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if any(marker in text for marker in ("ì", "ë", "ê", "í")):
        try:
            return text.encode("latin1").decode("utf-8")
        except UnicodeError:
            return text
    return text


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def gemini_models() -> list[str]:
    result = []
    for model in [GEMINI_MODEL, *GEMINI_FALLBACK_MODELS]:
        if model and model not in result:
            result.append(model)
    return result or ["gemini-2.5-flash"]


def compact_error_text(value: str, limit: int = 180) -> str:
    return re.sub(r"\s+", " ", value or "").strip()[:limit]


def read_http_error(error: HTTPError) -> str:
    try:
        body = error.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""
    try:
        payload = json.loads(body)
        message = payload.get("error", {}).get("message") or body
    except Exception:
        message = body
    return compact_error_text(message)


def call_gemini_json(prompt: str, temperature: float = 0.2) -> dict[str, Any]:
    global GEMINI_LAST_ERROR
    if not GEMINI_API_KEY:
        GEMINI_LAST_ERROR = "missing_gemini_api_key"
        raise RuntimeError("missing_gemini_api_key")

    errors = []
    for model in gemini_models():
        for json_mode in (True, False):
            endpoint = f"{GEMINI_API_URL}/models/{model}:generateContent?{urlencode({'key': GEMINI_API_KEY})}"
            generation_config = {"temperature": temperature}
            if json_mode:
                generation_config["responseMimeType"] = "application/json"
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": generation_config,
            }
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            request = Request(
                endpoint,
                data=body,
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            try:
                with urlopen(request, timeout=35) as response:
                    data = json.loads(response.read().decode("utf-8"))

                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                text = "".join(part.get("text", "") for part in parts)
                if not text:
                    raise RuntimeError("empty_gemini_response")
                result = extract_json_object(text)
                GEMINI_LAST_ERROR = ""
                return result
            except HTTPError as error:
                detail = read_http_error(error)
                errors.append(f"{model}:http_{error.code}:{detail}")
                if error.code in (401, 403):
                    break
            except URLError as error:
                errors.append(f"{model}:network:{compact_error_text(str(error.reason))}")
            except Exception as error:
                errors.append(f"{model}:parse:{compact_error_text(str(error))}")

    GEMINI_LAST_ERROR = " | ".join(errors[-4:]) or "unknown_gemini_error"
    raise RuntimeError(f"gemini_failed:{GEMINI_LAST_ERROR}")


def unique(values: list[Any]) -> list[Any]:
    result = []
    seen = set()
    for value in values:
        key = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else value
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def service_by_id(service_id: str) -> dict[str, Any] | None:
    return next((service for service in SERVICES if service["id"] == service_id), None)


def find_service(service_id: str, catalog: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    if catalog:
        found = next((service for service in catalog if service.get("id") == service_id), None)
        if found:
            return found
    return service_by_id(service_id)


def parse_public_service_id(service_id: str) -> tuple[str, str] | None:
    match = re.match(r"^public-(중앙|지자체)-(.+)$", service_id)
    if not match:
        return None
    return match.group(1), match.group(2)


PUBLIC_DETAIL_ALIASES: dict[str, tuple[str, str]] = {
    "svc-1": ("중앙", "WLF00003180"),
    "긴급복지 생계지원": ("중앙", "WLF00003180"),
    "긴급복지 지원": ("중앙", "WLF00003180"),
    "의료비 긴급지원": ("중앙", "WLF00003180"),
}


def public_detail_identity(service: dict[str, Any]) -> tuple[str, str]:
    parsed = parse_public_service_id(service.get("id", ""))
    if parsed:
        return parsed
    alias = PUBLIC_DETAIL_ALIASES.get(service.get("id", "")) or PUBLIC_DETAIL_ALIASES.get(service.get("name", ""))
    if alias:
        return alias
    return service.get("source", ""), service.get("externalId") or service.get("id", "")


def xml_tag_name(element: ElementTree.Element) -> str:
    return element.tag.rsplit("}", 1)[-1] if "}" in element.tag else element.tag


def xml_text(element: ElementTree.Element, *names: str) -> str:
    wanted = set(names)
    for found in element.iter():
        if xml_tag_name(found) in wanted and found.text:
            return clean_text(found.text)
    return ""


def xml_direct_text(element: ElementTree.Element, *names: str) -> str:
    wanted = set(names)
    for found in list(element):
        if xml_tag_name(found) in wanted and found.text:
            return clean_text(found.text)
    return ""


def xml_all_text(element: ElementTree.Element, name: str) -> list[str]:
    return [clean_text(item.text or "") for item in element.iter() if xml_tag_name(item) == name and clean_text(item.text or "")]


def xml_items(root: ElementTree.Element) -> list[ElementTree.Element]:
    candidates = []
    for element in root.iter():
        if xml_direct_text(element, "servId", "wlfareInfoId") and xml_direct_text(
            element, "servNm", "wlfareInfoNm", "bizNm"
        ):
            candidates.append(element)
    return candidates


def infer_domains_from_text(text: str) -> list[str]:
    found = []
    lowered = text.lower()
    for need, words in KEYWORD_MAP.items():
        if any(word.lower() in lowered for word in words):
            found.append(need)
    return found or ["생계"]


def infer_target_from_text(text: str) -> str:
    if re.search(r"청년|청소년|아동|노인|장애|임산|한부모|다문화|저소득|기초생활|차상위", text):
        matched = re.search(r"청년|청소년|아동|노인|장애인|장애|임산부|한부모|다문화|저소득|기초생활|차상위", text)
        return matched.group(0) if matched else "전국민"
    return "전국민"


def normalize_public_service(element: ElementTree.Element, source: str) -> dict[str, Any]:
    service_id = xml_text(element, "servId", "wlfareInfoId", "bizId") or f"{source}-{abs(hash(ElementTree.tostring(element)))}"
    name = xml_text(element, "servNm", "wlfareInfoNm", "bizNm", "servName") or "복지서비스"
    summary = xml_text(element, "servDgst", "servDgstCn", "wlfareInfoOutlCn", "bizDc", "summary")
    ministry = xml_text(element, "jurMnofNm", "jurOrgNm", "cnsgNm", "jrsdDptAllNm")
    detail_url = xml_text(element, "servDtlLink", "servDtlUrl", "link", "url")
    registered = xml_text(element, "svcfrstRegTs", "frstRegTs", "lastModYmd")
    searchable = " ".join([name, summary, ministry])
    domains = infer_domains_from_text(searchable)
    return {
        "id": f"public-{source}-{service_id}",
        "externalId": service_id,
        "name": name,
        "source": source,
        "region": "전국" if source == "중앙" else "지자체",
        "target": infer_target_from_text(searchable),
        "domains": domains,
        "urgency": "긴급" if any(word in searchable for word in ["긴급", "위기", "응급", "체납"]) else "일반",
        "summary": summary or "공공데이터포털 복지로 API에서 제공한 복지서비스입니다.",
        "eligibility": "상세 링크에서 지원대상과 선정기준을 확인하세요.",
        "support": summary or "서비스 상세 정보를 확인하세요.",
        "process": "복지로 상세 페이지 또는 관할 기관에서 신청 절차를 확인합니다.",
        "docs": ["신분증", "소득·재산 관련 증빙", "서비스별 추가 서류"],
        "contact": ministry or "복지로 / 관할 기관",
        "url": detail_url or "https://www.bokjiro.go.kr",
        "updated": registered or "공공데이터포털 실시간",
        "group": f"public-{source}-{service_id}",
        "external": True,
    }


def fetch_public_welfare_detail(service: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    service_key = get_public_data_key()
    if not service_key:
        return service, {"enabled": False, "reason": "missing_service_key"}

    source, service_id = public_detail_identity(service)

    if source not in ("중앙", "지자체") or not service_id:
        return service, {"enabled": True, "detail": False, "reason": "unsupported_service_source"}

    endpoint = NATIONAL_WELFARE_DETAIL_URL if source == "중앙" else LOCAL_WELFARE_DETAIL_URL
    params = {"serviceKey": service_key, "servId": service_id}
    if source == "중앙":
        params["callTp"] = "D"
    url = f"{endpoint}?{urlencode(params)}"

    try:
        with urlopen(url, timeout=15) as response:
            raw = response.read()
        root = ElementTree.fromstring(raw)
        result_code = xml_text(root, "resultCode")
        result_message = xml_text(root, "resultMessage", "resultMsg")
        if result_code and result_code not in ("0", "00", "NORMAL_CODE"):
            return service, {"enabled": True, "detail": False, "errors": [f"{source}:{result_code}:{result_message}"]}

        application_steps = xml_all_text(root, "applmetList")
        contacts = xml_all_text(root, "inqplCtadrList")
        homepages = xml_all_text(root, "inqplHmpgReldList")
        forms = xml_all_text(root, "basfrmList")
        laws = xml_all_text(root, "baslawList")

        detail = {
            **service,
            "name": xml_text(root, "servNm", "wlfareInfoNm", "bizNm", "servName") or service.get("name", ""),
            "summary": xml_text(root, "wlfareInfoOutlCn", "servDgst", "servDgstCn", "bizDc", "summary")
            or service.get("summary", ""),
            "eligibility": xml_text(root, "tgtrDtlCn", "sprtTrgtCn", "trgterIndvdlArray", "tgtrCn")
            or service.get("eligibility", ""),
            "selectionCriteria": xml_text(root, "slctCritCn", "slctCrit", "selectnStdr"),
            "support": xml_text(root, "alwServCn", "servCn", "sportCn", "sprtCn") or service.get("support", ""),
            "process": xml_text(root, "aplyMtdCn", "aplyMtd", "reqstProces", "useMthd")
            or " → ".join(application_steps)
            or service.get("process", ""),
            "docs": unique([*service.get("docs", []), *forms]) or service.get("docs", []),
            "contact": xml_text(root, "rprsCtadr", "inqplCtadr", "bizChrDeptNm")
            or (contacts[0] if contacts else service.get("contact", "")),
            "url": xml_text(root, "servDtlLink", "servDtlUrl", "inqplHmpgReld", "url")
            or service.get("url")
            or (homepages[0] if homepages else "https://www.bokjiro.go.kr"),
            "updated": xml_text(root, "crtrYr", "lastModYmd", "svcfrstRegTs", "frstRegTs") or service.get("updated", ""),
            "applicationSteps": application_steps,
            "contacts": contacts,
            "homepages": homepages,
            "laws": laws,
            "detailLoaded": True,
        }
        if source == "지자체":
            detail["region"] = " ".join([xml_text(root, "ctpvNm"), xml_text(root, "sggNm")]).strip() or service.get("region", "")
            detail["contact"] = contacts[0] if contacts else xml_text(root, "bizChrDeptNm") or service.get("contact", "")
        return detail, {"enabled": True, "detail": True, "source": "data.go.kr/bokjiro-detail"}
    except Exception as error:
        return service, {"enabled": True, "detail": False, "errors": [f"{source}:{error}"]}


def region_to_public_params(region: str) -> dict[str, str]:
    mapping = {
        "서울": "서울특별시",
        "부산": "부산광역시",
        "대구": "대구광역시",
        "인천": "인천광역시",
        "광주": "광주광역시",
        "대전": "대전광역시",
        "울산": "울산광역시",
        "세종": "세종특별자치시",
        "경기": "경기도",
        "강원": "강원특별자치도",
        "충북": "충청북도",
        "충남": "충청남도",
        "전북": "전북특별자치도",
        "전남": "전라남도",
        "경북": "경상북도",
        "경남": "경상남도",
        "제주": "제주특별자치도",
    }
    tokens = region.split()
    if not tokens:
        return {}
    ctpv = mapping.get(tokens[0], tokens[0])
    params = {"ctpvNm": ctpv}
    if len(tokens) > 1:
        params["sggNm"] = tokens[1]
    return params


def fetch_public_welfare_services(query: dict[str, list[str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    service_key = get_public_data_key()
    if not service_key:
        return [], {"enabled": False, "reason": "missing_service_key"}

    q = (query.get("q", [""])[0] or "").strip()
    domain = query.get("domain", ["전체"])[0] or "전체"
    needs = [item for item in query.get("needs", [""])[0].split(",") if item]
    region = query.get("region", [""])[0] or ""
    search_word = q or (domain if domain != "전체" else (needs[0] if needs else ""))
    source_filter = query.get("source", ["전체"])[0] or "전체"
    num_rows = min(int((query.get("numOfRows", ["30"])[0] or "30")), 100)

    endpoints = []
    if source_filter in ("전체", "중앙"):
        endpoints.append(
            (
                NATIONAL_WELFARE_URL,
                "중앙",
                {
                    "callTp": "L",
                    "pageNo": query.get("pageNo", ["1"])[0] or "1",
                    "numOfRows": str(num_rows),
                    "srchKeyCode": "003",
                    "searchWrd": search_word,
                    "orderBy": "popular",
                },
            )
        )
    if source_filter in ("전체", "지자체"):
        endpoints.append(
            (
                LOCAL_WELFARE_URL,
                "지자체",
                {
                    "pageNo": query.get("pageNo", ["1"])[0] or "1",
                    "numOfRows": str(num_rows),
                    "srchKeyCode": "003",
                    "searchWrd": search_word,
                    "arrgOrd": "001",
                    **region_to_public_params(region),
                },
            )
        )

    services: list[dict[str, Any]] = []
    errors: list[str] = []
    for endpoint, source, params in endpoints:
        request_params = {key: value for key, value in params.items() if value}
        request_params["serviceKey"] = service_key
        url = f"{endpoint}?{urlencode(request_params)}"
        try:
            with urlopen(url, timeout=8) as response:
                raw = response.read()
            root = ElementTree.fromstring(raw)
            result_code = xml_text(root, "resultCode")
            result_message = xml_text(root, "resultMessage", "resultMsg")
            if result_code and result_code not in ("0", "00", "NORMAL_CODE"):
                errors.append(f"{source}:{result_code}:{result_message}")
                continue
            services.extend(normalize_public_service(item, source) for item in xml_items(root))
        except Exception as error:
            errors.append(f"{source}:{error}")

    return unique_services(services), {
        "enabled": True,
        "source": "data.go.kr/bokjiro",
        "count": len(services),
        "errors": errors,
    }


def normalize_provider_item(item: ElementTree.Element, source: str) -> dict[str, Any]:
    provider_id = xml_text(item, "providerId", "fcltCd", "svcCd") or str(abs(hash(ElementTree.tostring(item))))
    name = xml_text(item, "providerName", "fcltNm") or "지역 기관"
    sido = xml_text(item, "sidoName", "sidoNm")
    signgu = xml_text(item, "signguName", "sggNm")
    service_name = xml_text(item, "serviceName", "svcNm", "serviceTypeName")
    address = " ".join(
        [
            xml_text(item, "loadAddress", "address"),
            xml_text(item, "loadAddressDetail", "addressDetail"),
        ]
    ).strip()
    return {
        "id": f"{source}-{provider_id}-{abs(hash(name + service_name))}",
        "name": name,
        "source": source,
        "serviceName": service_name,
        "serviceType": xml_text(item, "serviceTypeName"),
        "region": " ".join([sido, signgu]).strip(),
        "address": address or "주소 정보 없음",
        "contact": xml_text(item, "telNumber") or "문의처 확인 필요",
        "email": xml_text(item, "email"),
    }


def fetch_socialservice_providers(query: dict[str, list[str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    service_key = get_socialservice_key()
    if not service_key:
        return [], {"enabled": False, "reason": "missing_service_key"}

    q = (query.get("q", [""])[0] or "").strip()
    domain = query.get("domain", ["전체"])[0] or "전체"
    needs = [item for item in query.get("needs", [""])[0].split(",") if item]
    provider_name = q if q and len(q) >= 2 else ""
    service_type_name = domain if domain != "전체" else (needs[0] if needs else "")

    params = {
        "serviceKey": service_key,
        "pageNo": query.get("pageNo", ["1"])[0] or "1",
        "numOfRows": min(int((query.get("numOfRows", ["20"])[0] or "20")), 100),
    }
    if provider_name:
        params["providerName"] = provider_name
    if service_type_name:
        params["serviceTypeName"] = service_type_name

    url = f"{SOCIALSERVICE_PROVIDER_URL}?{urlencode(params)}"
    try:
        with urlopen(url, timeout=8) as response:
            raw = response.read()
        root = ElementTree.fromstring(raw)
        result_code = xml_text(root, "resultCode")
        result_message = xml_text(root, "resultMsg", "resultMessage")
        if result_code and result_code != "00":
            return [], {"enabled": True, "source": "socialservice-provider", "errors": [f"{result_code}:{result_message}"]}
        providers = [normalize_provider_item(item, "사회서비스") for item in root.findall(".//item")]
        return providers, {"enabled": True, "source": "socialservice-provider", "count": len(providers)}
    except Exception as error:
        return [], {"enabled": True, "source": "socialservice-provider", "errors": [str(error)]}


def fetch_resource_providers(query: dict[str, list[str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    service_key = get_public_data_key()
    if not service_key:
        return [], {"enabled": False, "reason": "missing_service_key"}

    region = query.get("region", [""])[0] or ""
    q = (query.get("q", [""])[0] or "").strip()
    domain = query.get("domain", ["전체"])[0] or "전체"
    params = {
        "ServiceKey": service_key,
        "pageNo": query.get("pageNo", ["1"])[0] or "1",
        "numOfRows": min(int((query.get("numOfRows", ["50"])[0] or "50")), 100),
    }
    url = f"{RESOURCE_INFO_URL}?{urlencode(params)}"
    try:
        with urlopen(url, timeout=8) as response:
            raw = response.read()
        root = ElementTree.fromstring(raw)
        result_code = xml_text(root, "resultCode")
        result_message = xml_text(root, "resultMsg", "resultMessage")
        if result_code and result_code != "00":
            return [], {"enabled": True, "source": "resource-info", "errors": [f"{result_code}:{result_message}"]}
        providers = [normalize_provider_item(item, "민간자원") for item in root.findall(".//item")]
        if region:
            tokens = region.split()
            providers = [
                provider
                for provider in providers
                if not tokens or any(token in provider.get("region", "") for token in tokens[:2])
            ] or providers
        if domain != "전체":
            providers = [
                provider for provider in providers if domain in provider.get("serviceName", "") or domain in provider.get("serviceType", "")
            ] or providers
        if q:
            providers = [
                provider
                for provider in providers
                if q in " ".join([provider.get("name", ""), provider.get("serviceName", ""), provider.get("region", "")])
            ] or providers
        return providers[:20], {"enabled": True, "source": "resource-info", "count": len(providers)}
    except Exception as error:
        return [], {"enabled": True, "source": "resource-info", "errors": [str(error)]}


def provider_fallback(query: dict[str, list[str]]) -> list[dict[str, Any]]:
    region = query.get("region", [""])[0] or "서울 관악구"
    return [
        {
            "id": "fallback-mental",
            "name": "지역 정신건강복지센터",
            "source": "샘플",
            "serviceName": "정신건강 상담 및 사례관리",
            "serviceType": "심리",
            "region": region,
            "address": "관할 보건소 또는 정신건강복지센터 확인",
            "contact": "1577-0199",
            "email": "",
        },
        {
            "id": "fallback-welfare",
            "name": "관할 읍면동 행정복지센터",
            "source": "샘플",
            "serviceName": "긴급복지·통합사례관리 접수",
            "serviceType": "생계/주거",
            "region": region,
            "address": "주민등록지 관할 센터",
            "contact": "보건복지상담센터 129",
            "email": "",
        },
    ]


def fetch_providers(query: dict[str, list[str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    social_providers, social_meta = fetch_socialservice_providers(query)
    resource_providers, resource_meta = fetch_resource_providers(query)
    providers = unique([*social_providers, *resource_providers])
    fallback = False
    if not providers:
        providers = provider_fallback(query)
        fallback = True
    return providers, {
        "fallback": fallback,
        "sources": [social_meta, resource_meta],
        "count": len(providers),
    }


def analyze_case_local(case: dict[str, Any]) -> dict[str, Any]:
    issue_types = case.get("issueTypes") or []
    memo = f"{case.get('memo', '')} {' '.join(issue_types)} {case.get('title', '')}".lower()
    detected = set(issue_types)
    keywords: list[str] = []

    for need, words in KEYWORD_MAP.items():
        matched = [word for word in words if word.lower() in memo]
        if matched:
            detected.add(need)
            keywords.extend(matched[:3])

    # ── 소득 수준 ──────────────────────────────────────────
    income_level = "불명"
    if re.search(r"기초수급|수급자|기초생활보장|생계급여|주거급여|의료급여", memo):
        income_level = "기초수급"
    elif re.search(r"차상위|차상위계층", memo):
        income_level = "차상위"
    elif re.search(r"저소득|취약계층|소득감소|소득\s*줄|실직|무직|소득\s*없", memo):
        income_level = "저소득"

    # ── 가구 유형 ──────────────────────────────────────────
    family_type = "일반"
    if re.search(r"한부모|미혼모|미혼부|편부|편모", memo):
        family_type = "한부모"
    elif re.search(r"조손|조부모.*손자|손자.*조부모|할머니.*손자|할아버지.*손자", memo):
        family_type = "조손"
    elif re.search(r"독거노인|노인\s*1인|어르신.*혼자|혼자.*어르신", memo):
        family_type = "노인단독"
    elif re.search(r"1인\s*가구|혼자\s*살|독거|독신", memo):
        family_type = "독거"
    elif re.search(r"다자녀|3자녀|세\s*자녀|셋째|넷째|4자녀", memo):
        family_type = "다자녀"

    # ── 주거 형태 ──────────────────────────────────────────
    housing_type = "불명"
    if re.search(r"고시원|쪽방|반지하|옥탑방|비닐하우스", memo):
        housing_type = "고시원쪽방반지하"
    elif re.search(r"퇴거|노숙|집\s*없|거처\s*없|주거\s*불안|쫓겨", memo):
        housing_type = "노숙위험"
    elif re.search(r"월세|임대|보증금|임차|전세", memo):
        housing_type = "임대"
    elif re.search(r"자가|본인\s*소유|집\s*있|소유\s*주택", memo):
        housing_type = "자가"

    # ── 취업 상태 ──────────────────────────────────────────
    employment_status = "불명"
    if re.search(r"실직|해고|실업|직장\s*잃|무직|일\s*없", memo):
        employment_status = "실직"
    elif re.search(r"일용직|단기\s*근로|파트타임|소득\s*불안|근로시간\s*감소|아르바이트", memo):
        employment_status = "불안정취업"
    elif re.search(r"돌봄\s*때문에|병간호|건강\s*문제로\s*일|간병\s*중|요양\s*중", memo):
        employment_status = "비경활"
    elif re.search(r"직장\s*다니|재직|근무\s*중|취업\s*중|일하고", memo):
        employment_status = "취업"

    # ── 장애 여부 ──────────────────────────────────────────
    has_disability = bool(re.search(
        r"장애인|장애\s*정도|장애\s*등급|발달장애|지체장애|정신장애|시각장애|청각장애|뇌병변|자폐|지적장애", memo
    ))

    # ── 위기 요인 ──────────────────────────────────────────
    crisis_factors: list[str] = []
    if re.search(r"월세\s*체납|임대료\s*체납|월세\s*밀|집세\s*못", memo):
        crisis_factors.append("월세체납")
    if re.search(r"소득\s*감소|수입\s*줄|생계\s*어렵|실직|소득\s*없", memo):
        crisis_factors.append("소득감소")
    if re.search(r"의료비|치료비|병원\s*비용|진료비|수술비", memo):
        crisis_factors.append("의료비부담")
    if re.search(r"식비|먹을\s*것|결식|굶|끼니", memo):
        crisis_factors.append("식비부족")
    if re.search(r"단전|단수|공과금\s*체납|가스\s*끊|전기\s*끊", memo):
        crisis_factors.append("공과금체납")
    if re.search(r"가정폭력|학대|피해자|맞고", memo):
        crisis_factors.append("가정폭력")
    if re.search(r"자살|자해|스스로.*해|극단", memo):
        crisis_factors.append("자살위험")
    if re.search(r"고립|외롭|혼자\s*오래|아무도|단절", memo):
        crisis_factors.append("고립")

    # ── 위험 신호 ──────────────────────────────────────────
    risk_checks = []
    if re.search(r"체납|퇴거|식비|긴급|소득|실직", memo):
        risk_checks.append({
            "label": "경제·주거 위기",
            "text": "체납, 식비 부담, 소득 감소 표현이 있어 긴급복지와 주거비 지원을 먼저 확인합니다.",
        })
    if re.search(r"자살|자해|폭력|학대|위험", memo):
        risk_checks.append({
            "label": "즉시 안전 확인",
            "text": "위험 신호가 포함되어 보호자·응급기관·위기상담 연결 여부를 확인합니다.",
        })
    if re.search(r"우울|불안|수면|고립", memo):
        risk_checks.append({
            "label": "정신건강 확인",
            "text": "우울감 또는 수면 문제 표현이 있어 정신건강복지센터와 상담 바우처를 함께 검토합니다.",
        })
    if not risk_checks:
        risk_checks.append({"label": "일반 확인", "text": "소득·재산·거주지·연령 기준을 상담 중 확인합니다."})

    return {
        "needs": [need for need in NEEDS if need in detected],
        "keywords": unique(keywords)[:10],
        "urgency": "긴급" if len(risk_checks) > 1 or case.get("urgency") == "긴급" else case.get("urgency", "주의"),
        "target": case.get("targetType", ""),
        "region": case.get("region", ""),
        "riskChecks": risk_checks,
        "incomeLevel": income_level,
        "familyType": family_type,
        "housingType": housing_type,
        "employmentStatus": employment_status,
        "hasDisability": has_disability,
        "crisisFactors": crisis_factors,
        "provider": "backend-rule-engine",
    }


def normalize_structured_result(data: dict[str, Any], case: dict[str, Any], provider: str) -> dict[str, Any]:
    needs = [need for need in data.get("needs", []) if need in NEEDS]
    risk_checks = data.get("riskChecks") or data.get("risk_checks") or []
    normalized_risks = []
    for item in risk_checks:
        if isinstance(item, dict):
            normalized_risks.append(
                {
                    "label": clean_text(str(item.get("label", "확인 필요"))),
                    "text": clean_text(str(item.get("text", item.get("description", "")))),
                }
            )
        elif isinstance(item, str):
            normalized_risks.append({"label": "확인 필요", "text": clean_text(item)})
    if not normalized_risks:
        normalized_risks = [{"label": "일반 확인", "text": "소득·재산·거주지·연령 기준을 상담 중 확인합니다."}]
    urgency = data.get("urgency") if data.get("urgency") in ("일반", "주의", "긴급") else case.get("urgency", "주의")
    local = analyze_case_local(case)
    valid_income = {"기초수급", "차상위", "저소득", "일반", "불명"}
    valid_family = {"독거", "한부모", "다자녀", "조손", "노인단독", "부부", "일반"}
    valid_housing = {"임대", "고시원쪽방반지하", "자가", "전세", "노숙위험", "불명"}
    valid_employ = {"취업", "실직", "불안정취업", "비경활", "불명"}
    income_level = data.get("incomeLevel", "") if data.get("incomeLevel") in valid_income else local.get("incomeLevel", "불명")
    family_type = data.get("familyType", "") if data.get("familyType") in valid_family else local.get("familyType", "일반")
    housing_type = data.get("housingType", "") if data.get("housingType") in valid_housing else local.get("housingType", "불명")
    employment_status = data.get("employmentStatus", "") if data.get("employmentStatus") in valid_employ else local.get("employmentStatus", "불명")
    has_disability = bool(data.get("hasDisability", local.get("hasDisability", False)))
    raw_cf = data.get("crisisFactors") or local.get("crisisFactors") or []
    crisis_factors = unique([clean_text(str(cf)) for cf in raw_cf if cf])[:8]
    return {
        "needs": needs or local["needs"],
        "keywords": unique([clean_text(str(keyword)) for keyword in data.get("keywords", [])])[:10],
        "urgency": urgency,
        "target": clean_text(str(data.get("target") or case.get("targetType", ""))),
        "region": clean_text(str(data.get("region") or case.get("region", ""))),
        "riskChecks": normalized_risks[:5],
        "incomeLevel": income_level,
        "familyType": family_type,
        "housingType": housing_type,
        "employmentStatus": employment_status,
        "hasDisability": has_disability,
        "crisisFactors": crisis_factors,
        "provider": provider,
        "llmUsed": provider.startswith("gemini"),
    }


def llm_error_message(error: Exception) -> str:
    raw = compact_error_text(GEMINI_LAST_ERROR or str(error), 260)
    lower = raw.lower()
    if "missing_gemini_api_key" in lower:
        return "Gemini API 키가 설정되지 않았습니다."
    if "http_401" in lower or "http_403" in lower or "api key not valid" in lower or "permission" in lower:
        return "Gemini API 키 값 또는 권한 설정을 확인해야 합니다."
    if "http_429" in lower or "quota" in lower or "rate" in lower:
        return "Gemini API 사용량 한도 또는 요청 제한에 걸렸습니다."
    if "http_400" in lower or "not found" in lower or "model" in lower:
        return "Gemini 모델명 또는 응답 형식 설정이 현재 키와 맞지 않습니다."
    if "timeout" in lower or "network" in lower:
        return "Gemini API 네트워크 연결 또는 응답 지연 문제가 발생했습니다."
    return "Gemini 응답을 JSON으로 해석하지 못했습니다."


def analyze_case(case: dict[str, Any]) -> dict[str, Any]:
    fallback = analyze_case_local(case)
    if not GEMINI_API_KEY:
        return fallback

    prompt = f"""
너는 한국 복지 현장 종사자를 돕는 상담 메모 구조화 보조자다.
아래 상담 정보를 분석해서 JSON 객체만 반환한다.

반드시 지킬 규칙:
- needs는 다음 목록 중에서만 고른다: {", ".join(NEEDS)}
- urgency는 "일반", "주의", "긴급" 중 하나만 쓴다.
- incomeLevel 허용값: "기초수급"(기초생활수급자), "차상위"(차상위계층), "저소득"(저소득·소득감소), "일반"(일반가구), "불명"
- familyType 허용값: "독거"(1인가구), "한부모"(편부모·미혼모·미혼부), "다자녀"(3자녀↑), "조손"(조부모+손자녀), "노인단독"(노인 1~2인), "일반"
- housingType 허용값: "임대"(전월세), "고시원쪽방반지하", "자가", "노숙위험"(퇴거·노숙위험), "불명"
- employmentStatus 허용값: "취업", "실직", "불안정취업"(일용직·단기·소득불안정), "비경활"(돌봄·건강이유 비취업), "불명"
- hasDisability: true 또는 false (메모에 장애인 언급 기준)
- crisisFactors: 메모에서 확인되는 구체적 위기 요인 목록
  가능한 값: "월세체납", "소득감소", "의료비부담", "식비부족", "공과금체납", "가정폭력", "자살위험", "고립"
- 메모에 근거 없는 내용은 만들지 않는다.
- 최종 판단은 현장 종사자가 하므로 보수적으로 작성한다.

반환 JSON 스키마:
{{
  "needs": ["주거", "생계"],
  "keywords": ["월세", "체납"],
  "urgency": "긴급",
  "target": "청년",
  "region": "서울 관악구",
  "incomeLevel": "저소득",
  "familyType": "독거",
  "housingType": "임대",
  "employmentStatus": "불안정취업",
  "hasDisability": false,
  "crisisFactors": ["월세체납", "소득감소"],
  "riskChecks": [{{"label": "경제·주거 위기", "text": "확인할 내용"}}]
}}

상담 정보:
{json.dumps(case, ensure_ascii=False)}
"""
    try:
        data = call_gemini_json(prompt, temperature=0.1)
        return normalize_structured_result(data, case, GEMINI_MODEL)
    except Exception as error:
        return {**fallback, "llmError": True, "llmErrorReason": llm_error_message(error)}


AGE_TARGET_PATTERNS = {
    "아동": r"아동|영유아|유아|어린이|초등학생|초등|미취학",
    "청소년": r"청소년|중학생|고등학생|학교\s*밖|위기청소년|청소년특별지원",
    "청년": r"청년|대학생|사회초년생",
    "노인": r"노인|어르신|고령|독거노인|기초연금|장기요양",
}


def age_groups_from_text(text: str) -> set[str]:
    cleaned = clean_text(text)
    groups = {group for group, pattern in AGE_TARGET_PATTERNS.items() if re.search(pattern, cleaned)}

    for match in re.finditer(r"(?<!\d)(\d{1,3})\s*세", cleaned):
        try:
            age = int(match.group(1))
        except ValueError:
            continue
        if age >= 65:
            groups.add("노인")
        elif age >= 19:
            groups.add("청년")
        elif age >= 13:
            groups.add("청소년")
        else:
            groups.add("아동")

    return groups


def case_age_groups(case: dict[str, Any], structured: dict[str, Any] | None = None) -> set[str]:
    case_text_groups = age_groups_from_text(" ".join(str(case.get(key, "")) for key in ("title", "memo")))
    if case_text_groups:
        return case_text_groups

    structured_groups = age_groups_from_text(str(structured.get("target", ""))) if structured else set()
    if structured_groups:
        return structured_groups

    return age_groups_from_text(str(case.get("targetType", "")))


def service_age_groups(service: dict[str, Any]) -> set[str]:
    parts = [
        service.get("name", ""),
        service.get("target", ""),
        service.get("summary", ""),
        service.get("eligibility", ""),
        service.get("support", ""),
        service.get("process", ""),
    ]
    return age_groups_from_text(" ".join(str(part) for part in parts if part))


def target_compatible(
    service: dict[str, Any], case: dict[str, Any], structured: dict[str, Any] | None = None
) -> bool:
    case_groups = case_age_groups(case, structured)
    service_groups = service_age_groups(service)
    if not case_groups or not service_groups:
        return True
    return bool(case_groups & service_groups)


def service_score(
    service: dict[str, Any], needs: list[str], case: dict[str, Any], structured: dict[str, Any] | None = None
) -> int:
    if not target_compatible(service, case, structured):
        return 0

    overlap = len([domain for domain in service["domains"] if domain in needs])
    urgent = 1 if service["urgency"] == "긴급" else 0
    region = case.get("region", "")
    region_match = 1 if service["region"] == "전국" or service["region"] in region else 0
    target_match = 1 if case_age_groups(case, structured) & service_age_groups(service) else 0
    return overlap * 4 + urgent * 2 + region_match + target_match


def filter_local_services(query: dict[str, list[str]], catalog: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    q = (query.get("q", [""])[0] or "").strip().lower()
    source = query.get("source", ["전체"])[0] or "전체"
    domain = query.get("domain", ["전체"])[0] or "전체"
    urgency = query.get("urgency", ["전체"])[0] or "전체"
    needs = [item for item in query.get("needs", [""])[0].split(",") if item]
    case = {"region": query.get("region", [""])[0] or "", "targetType": query.get("target", [""])[0] or ""}
    source_catalog = catalog or SERVICES
    hide_target_mismatch = bool(case_age_groups(case)) and not q

    def matches(service: dict[str, Any]) -> bool:
        searchable = " ".join(
            [
                service["name"],
                service["summary"],
                service["target"],
                service["region"],
                service["source"],
                *service["domains"],
            ]
        ).lower()
        return (
            (not q or q in searchable)
            and (source == "전체" or service["source"] == source)
            and (domain == "전체" or domain in service["domains"])
            and (urgency == "전체" or service["urgency"] == urgency)
            and (not hide_target_mismatch or target_compatible(service, case))
        )

    return sorted(
        [service for service in source_catalog if matches(service)],
        key=lambda service: service_score(service, needs, case),
        reverse=True,
    )


def filter_services(query: dict[str, list[str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    public_services, public_meta = fetch_public_welfare_services(query)
    local_services = filter_local_services(query)
    source_filter = query.get("source", ["전체"])[0] or "전체"
    if public_services:
        if source_filter in ("중앙", "지자체"):
            selected = filter_local_services(query, public_services)
        else:
            selected = filter_local_services(query, unique_services([*public_services, *local_services]))
        return selected, {**public_meta, "fallback": False}
    return local_services, {**public_meta, "fallback": True}


def unique_services(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    seen = set()
    for service in items:
        if service["id"] not in seen:
            seen.add(service["id"])
            result.append(service)
    return result


def ensure_coverage(
    items: list[dict[str, Any]],
    needs: list[str],
    catalog: list[dict[str, Any]] | None = None,
    case: dict[str, Any] | None = None,
    structured: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    selected = list(items)
    source_catalog = catalog or SERVICES
    case = case or {}
    domains = {domain for service in selected for domain in service["domains"]}
    for need in needs[:4]:
        if need not in domains:
            found = next(
                (
                    service
                    for service in source_catalog
                    if need in service["domains"]
                    and service not in selected
                    and target_compatible(service, case, structured)
                ),
                None,
            )
            if found:
                selected.append(found)
                domains.update(found["domains"])
    if len({domain for service in selected for domain in service["domains"]}) < 2:
        fallback = next(
            (service for service in source_catalog if service not in selected and target_compatible(service, case, structured)),
            None,
        )
        if fallback:
            selected.append(fallback)
    return selected[:5]


def build_package(package_id: str, title: str, summary: str, items: list[dict[str, Any]], score: int) -> dict[str, Any]:
    return {
        "id": package_id,
        "title": title,
        "summary": summary,
        "score": score,
        "items": [{"serviceId": service["id"], "included": True} for service in items],
        "provider": "backend-package-engine",
    }


def generate_packages(
    case: dict[str, Any], structured: dict[str, Any] | None, catalog: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    if not structured:
        structured = analyze_case(case)
    needs = structured.get("needs") or ["생계", "주거"]
    source_catalog = [service for service in (catalog or SERVICES) if target_compatible(service, case, structured)]
    ranked = sorted(
        [service for service in source_catalog if service_score(service, needs, case, structured) > 0],
        key=lambda service: service_score(service, needs, case, structured),
        reverse=True,
    )
    urgent_first = [service for service in ranked if service["urgency"] == "긴급"]
    general = [service for service in ranked if service["urgency"] != "긴급"]
    mixed = unique_services([*urgent_first, *general])

    top_a = ensure_coverage(mixed[:4], needs, source_catalog, case, structured)
    top_b = ensure_coverage(
        unique_services(
            [
                *[service for service in ranked if "취업" in service["domains"] or "심리" in service["domains"]],
                *ranked,
            ]
        )[:4],
        needs,
        source_catalog,
        case,
        structured,
    )
    top_c = ensure_coverage(
        unique_services(
            [
                *[service for service in ranked if service["source"] in ("기관", "민간")],
                *ranked,
            ]
        )[:4],
        needs,
        source_catalog,
        case,
        structured,
    )

    return [
        build_package("pkg-1", "긴급 안정 패키지", "체납·생계·심리 위험을 먼저 낮추는 조합", top_a, 94),
        build_package("pkg-2", "회복·자립 패키지", "단기 지원 이후 취업과 마음건강을 함께 연결", top_b, 88),
        build_package("pkg-3", "지역기관 연계 패키지", "공공 제도와 민간·지역기관 접점을 병합", top_c, 83),
    ]

def build_report(
    case: dict[str, Any],
    structured: dict[str, Any] | None,
    package: dict[str, Any],
    catalog: list[dict[str, Any]] | None = None,
    providers: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not structured:
        structured = analyze_case(case)

    selected_services = [
        find_service(item["serviceId"], catalog)
        for item in package.get("items", [])
        if item.get("included", True) and find_service(item.get("serviceId", ""), catalog)
    ]
    selected_services = [service for service in selected_services if service]
    docs = unique([doc for service in selected_services for doc in service["docs"]])
    contacts = unique(
        [
            {"service": service["name"], "contact": service["contact"], "url": service["url"]}
            for service in selected_services
        ]
    )
    if providers:
        contacts = unique(
            [
                *contacts,
                *[
                    {
                        "service": provider.get("name", ""),
                        "contact": provider.get("contact", ""),
                        "url": provider.get("address", ""),
                    }
                    for provider in providers[:8]
                ],
            ]
        )
    needs = structured.get("needs") or case.get("issueTypes") or []

    report = {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "generatedBy": "backend-report-engine",
        "title": case.get("title", "상담 추천서"),
        "packageTitle": package.get("title", ""),
        "needs": needs,
        "reason": f"{package.get('summary', '추천 패키지')}입니다. 상담 메모에서 {', '.join(needs)} 욕구가 확인되어 관련 제도와 지역 기관을 조합했습니다.",
        "services": [
            {
                "name": service["name"],
                "summary": service["summary"],
                "source": service["source"],
                "updated": service["updated"],
                "url": service["url"],
            }
            for service in selected_services
        ],
        "conditions": [{"service": service["name"], "text": service["eligibility"]} for service in selected_services],
        "docs": docs,
        "steps": [service["process"] for service in selected_services],
        "contacts": contacts,
    }
    if not GEMINI_API_KEY or not selected_services:
        return report

    service_context = [
        {
            "name": service.get("name"),
            "source": service.get("source"),
            "summary": service.get("summary"),
            "eligibility": service.get("eligibility"),
            "selectionCriteria": service.get("selectionCriteria", ""),
            "support": service.get("support"),
            "process": service.get("process"),
            "docs": service.get("docs", []),
            "contact": service.get("contact"),
            "url": service.get("url"),
            "updated": service.get("updated"),
        }
        for service in selected_services
    ]
    provider_context = providers[:8] if providers else []
    prompt = f"""
너는 한국 복지 현장 종사자가 사례기록에 첨부할 추천서 초안을 작성하는 보조자다.
아래 공공데이터/기관 데이터에 근거해서 JSON 객체만 반환한다.

엄격한 규칙:
- 제공된 서비스와 기관 데이터에 없는 제도, 혜택, 금액, 자격, 연락처를 만들지 않는다.
- 신청 가능 여부를 확정하지 말고 "확인 필요" 표현을 사용한다.
- 최종 판단은 현장 종사자가 한다.
- 개인정보와 민감정보를 새로 쓰지 않는다.
- 문장은 간결한 실무 문체로 쓴다.

반환 JSON 스키마:
{{
  "reason": "추천 이유 2~4문장",
  "conditions": [{{"service": "서비스명", "text": "확인 조건"}}],
  "docs": ["준비 서류"],
  "steps": ["연계 순서"],
  "caseNote": "사례기록에 붙여넣기 좋은 요약"
}}

상담:
{json.dumps(case, ensure_ascii=False)}

구조화 결과:
{json.dumps(structured, ensure_ascii=False)}

선택 패키지:
{json.dumps(package, ensure_ascii=False)}

서비스 근거 데이터:
{json.dumps(service_context, ensure_ascii=False)}

기관 데이터:
{json.dumps(provider_context, ensure_ascii=False)}
"""
    try:
        data = call_gemini_json(prompt, temperature=0.2)
        if isinstance(data.get("reason"), str):
            report["reason"] = clean_text(data["reason"])
        if isinstance(data.get("conditions"), list):
            report["conditions"] = [
                {"service": clean_text(str(item.get("service", ""))), "text": clean_text(str(item.get("text", "")))}
                for item in data["conditions"]
                if isinstance(item, dict) and item.get("text")
            ] or report["conditions"]
        if isinstance(data.get("docs"), list):
            report["docs"] = unique([clean_text(str(doc)) for doc in data["docs"] if clean_text(str(doc))]) or report["docs"]
        if isinstance(data.get("steps"), list):
            report["steps"] = unique([clean_text(str(step)) for step in data["steps"] if clean_text(str(step))]) or report["steps"]
        if isinstance(data.get("caseNote"), str):
            report["caseNote"] = clean_text(data["caseNote"])
        report["generatedBy"] = f"{GEMINI_MODEL}+backend-report-engine"
        report["llmUsed"] = True
    except Exception:
        report["llmError"] = True
    return report


class WelfareHandler(SimpleHTTPRequestHandler):
    server_version = "WelfareCopilot/0.1"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/"):
            return super().do_GET()

        query = parse_qs(parsed.query)
        if parsed.path == "/api/health":
            return self.write_json(
                {
                    "ok": True,
                    "service": "welfare-copilot-backend",
                    "time": datetime.now().isoformat(),
                    "runtimePatch": "inline-backend-server",
                    "publicData": {
                        "enabled": bool(get_public_data_key()),
                        "keyEnvNames": PUBLIC_DATA_KEY_ENV_NAMES,
                        "nationalEndpoint": NATIONAL_WELFARE_URL,
                        "nationalDetailEndpoint": NATIONAL_WELFARE_DETAIL_URL,
                        "localEndpoint": LOCAL_WELFARE_URL,
                        "localDetailEndpoint": LOCAL_WELFARE_DETAIL_URL,
                        "socialserviceProviderEndpoint": SOCIALSERVICE_PROVIDER_URL,
                        "resourceInfoEndpoint": RESOURCE_INFO_URL,
                    },
                    "llm": {
                        "enabled": bool(GEMINI_API_KEY),
                        "provider": "google-gemini",
                        "model": GEMINI_MODEL,
                    },
                }
            )
        if parsed.path == "/api/services":
            services, meta = filter_services(query)
            return self.write_json({"services": services, "meta": meta})
        if parsed.path.startswith("/api/services/"):
            service_id = unquote(parsed.path.rsplit("/", 1)[-1])
            services, meta = filter_services(query)
            service = find_service(service_id, services)
            if not service and parse_public_service_id(service_id):
                source, external_id = parse_public_service_id(service_id) or ("", "")
                service = {
                    "id": service_id,
                    "externalId": external_id,
                    "name": "복지서비스 상세",
                    "source": source,
                    "region": "전국" if source == "중앙" else "지자체",
                    "target": "전국민",
                    "domains": ["생계"],
                    "urgency": "일반",
                    "summary": "",
                    "eligibility": "",
                    "support": "",
                    "process": "",
                    "docs": [],
                    "contact": "",
                    "url": "https://www.bokjiro.go.kr",
                    "updated": "",
                    "group": service_id,
                    "external": True,
                }
            if not service:
                return self.write_json({"error": "service_not_found"}, HTTPStatus.NOT_FOUND)
            detail, detail_meta = fetch_public_welfare_detail(service)
            return self.write_json({"service": detail, "meta": {**meta, "detail": detail_meta}})
        if parsed.path == "/api/providers":
            providers, meta = fetch_providers(query)
            return self.write_json({"providers": providers, "meta": meta})
        if parsed.path == "/api/cases/recent":
            return self.write_json({"cases": [*RECENT_CASES, *SAVED_CASES[-5:]][:8]})

        return self.write_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/"):
            return self.write_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

        payload = self.read_json()
        if parsed.path == "/api/cases":
            case = payload.get("case", payload)
            saved = {
                **case,
                "id": case.get("id") or f"case-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "status": "임시저장",
                "savedAt": datetime.now().isoformat(timespec="seconds"),
            }
            SAVED_CASES.append(saved)
            return self.write_json({"case": saved})

        if parsed.path == "/api/analyze":
            return self.write_json({"structured": analyze_case(payload.get("case", payload))})

        if parsed.path == "/api/packages":
            case = payload.get("case", {})
            structured = payload.get("structured")
            catalog = payload.get("services") or SERVICES
            return self.write_json({"packages": generate_packages(case, structured, catalog)})

        if parsed.path == "/api/report":
            case = payload.get("case", {})
            structured = payload.get("structured")
            package = payload.get("package", {})
            catalog = payload.get("services") or SERVICES
            providers = payload.get("providers") or []
            return self.write_json({"report": build_report(case, structured, package, catalog, providers)})

        return self.write_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length == 0:
            return {}
        body = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {}

    def write_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run(host: str | None = None, port: int | None = None) -> None:
    host = host or os.getenv("HOST", "0.0.0.0")
    port = port or int(os.getenv("PORT", "5173"))
    server = ThreadingHTTPServer((host, port), WelfareHandler)
    print(f"Welfare Copilot backend running at http://{host}:{port}/")
    server.serve_forever()


if __name__ == "__main__":
    try:
        import sys

        sys.modules["backend_server"] = sys.modules[__name__]
        import backend_runtime_patch

        backend_runtime_patch.apply()
    except Exception as error:
        print(f"Runtime patch skipped: {error}")
    run()
