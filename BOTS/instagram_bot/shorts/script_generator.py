import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'regular_post'))

from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def extract_reels_data(title, fulltext):
    """블로그 본문에서 실적/주가/사업 3페이지 데이터 + TTS 나레이션 추출"""
    prompt = f"""아래 경제 블로그 글을 분석해서 JSON으로만 반환해줘. 개인적인 이야기, 감정, 투자 경험은 절대 포함하지 말 것.

[제목] {title}
[본문] {fulltext[:4000]}

[JSON 형식]
{{
  "intro_narration": "안녕하세요! 나마나마 경제성장 팩토리입니다. 오늘은 [회사명] [기간] 실적을 살펴볼게요.",
  "earnings": {{
    "title": "26년 1분기 실적 요약",
    "headline": "어닝 서프라이즈 달성!",
    "items": [
      {{"label": "매출액", "value": "1,117억 달러", "note": "예상치 상회"}},
      {{"label": "영업이익", "value": "90억 달러", "note": "전년比 질적 성장"}},
      {{"label": "영업이익률", "value": "8.1%", "note": "4Q 7.5% 개선"}},
      {{"label": "조정 EPS", "value": "$7.23", "note": "예상치 상회"}},
      {{"label": "의료손해율", "value": "83.9%", "note": "4Q 85.0% 개선"}}
    ],
    "highlight": "어닝 서프라이즈 달성",
    "narration": "실적을 볼게요. 매출과 영업이익 모두 예상치를 상회했어요. 어닝 서프라이즈입니다!"
  }},
  "stock": {{
    "title": "주가 현황",
    "headline": "추세 전환 시도 중",
    "items": [
      {{"label": "핵심 돌파", "value": "$320~330", "note": "장기 저항선 돌파"}},
      {{"label": "기술 신호", "value": "골든크로스", "note": "이평선 돌파"}},
      {{"label": "볼린저밴드", "value": "상단 이탈", "note": "밴드 확장 중"}},
      {{"label": "거래량", "value": "대량 동반", "note": "장대 양봉 출현"}},
      {{"label": "단기 주의", "value": "조정 가능성", "note": "이격 확대"}}
    ],
    "highlight": "추세 전환 시도 중",
    "narration": "주가를 분석해볼게요. 골든크로스가 발생했고 장기 저항선을 돌파했어요. 추세 전환 신호입니다."
  }},
  "business": {{
    "title": "사업 부문 현황",
    "headline": "내부 혁신 효과 가시화",
    "items": [
      {{"label": "UnitedHealthcare", "value": "영업이익 57억$", "note": "회원 4,910만명"}},
      {{"label": "Optum", "value": "헬스케어 플랫폼", "note": "기술 기반 견조"}},
      {{"label": "MCR 개선", "value": "보험료 재산정", "note": "2026 범위 조정"}},
      {{"label": "비용 절감", "value": "AI 기술 투자", "note": "운영비율 개선"}},
      {{"label": "회사 전략", "value": "고정비 절감", "note": "재무 정상화"}}
    ],
    "highlight": "내부 혁신 효과 가시화",
    "narration": "사업 부문입니다. AI 기술 투자로 비용이 절감되고 내부 혁신 효과가 나타나고 있어요."
  }},
  "outro_narration": "오늘 경제 정보 어떠셨나요? 더 많은 정보는 팔로우하고 확인하세요! 투자는 본인 책임입니다."
}}

위 형식 그대로 실제 본문 내용 기반으로 채워서 반환해줘. narration은 자연스러운 한국어 TTS 문장으로 작성해줘. JSON만 출력."""

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(res.choices[0].message.content)
