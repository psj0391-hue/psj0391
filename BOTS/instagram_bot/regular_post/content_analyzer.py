from groq import Groq
import os, json, re
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def _ask_json(prompt):
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(res.choices[0].message.content)


def _ask(prompt):
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content


def generate_caption(title, summary):
    """인스타그램 캡션 + 해시태그 생성"""
    prompt = f"""아래 경제 블로그 글을 인스타그램 게시물 캡션으로 만들어줘.

[제목] {title}
[내용] {summary[:600]}

[규칙]
- 첫 줄: 흥미로운 한 줄 (이모지 포함)
- 본문: 핵심 3줄 (친근한 말투)
- 해시태그: 10개

캡션만 출력해줘."""
    return _ask(prompt)


def analyze_post(title, fulltext):
    """
    블로그 글을 분석하여 포스팅 유형과 카드 데이터를 반환.

    반환 형식:
    {
      "post_type": "ranking | policy | news | analysis | general",
      "cards": [
        {
          "title": "카드 제목",
          "items": [
            {"rank": 1, "main": "주요 내용", "sub": "부가 설명"}
          ]
        }
      ]
    }
    """
    prompt = f"""아래 경제 블로그 글을 분석해서 JSON으로만 반환해줘.

[제목] {title}
[본문] {fulltext[:5000]}

[포스팅 유형 분류]
- ranking: 순매수/순매도/수익률 등 순위 목록이 있는 글
- policy: 정부 정책, 지원금, 제도 안내
- news: 경제 뉴스, 시황 요약
- analysis: 주식/종목/경제 심층 분석
- general: 기타 경제 정보, 재테크 팁

[JSON 형식]
{{
  "post_type": "위 5가지 중 하나",
  "cards": [
    {{
      "title": "카드 소제목 (예: 기관 순매수 TOP 5)",
      "items": [
        {{"rank": 1, "main": "핵심 항목명 또는 수치", "sub": "한줄 설명 (20자 이내)"}}
      ]
    }}
  ]
}}

[중요 규칙 - 반드시 지켜야 함]
- cards는 정확히 3개 생성 (항상 3개, 절대 줄이지 말 것)
- 각 card의 items는 반드시 5개 생성 (항상 5개, 절대 줄이지 말 것)
- 본문에서 항목이 부족하면 관련 내용을 재구성하거나 추론해서라도 5개를 채울 것
- sub는 반드시 20자 이내로 요약
- ranking 유형이면 amount(금액/수치)도 main에 포함 (예: "삼성전자 (7,131억)")
- policy 유형:
    card1 = 지원 대상 5가지
    card2 = 지원 금액/혜택 5가지
    card3 = 신청 방법/기간/주의사항 5가지
- news/analysis 유형이면 핵심 포인트를 카드별로 5개씩 구성
- general 유형이면 주요 정보를 카드별로 5개씩 구성
- items가 5개 미만이면 틀린 응답임"""

    try:
        data = _ask_json(prompt)
        # items 유효성 필터링
        for card in data.get("cards", []):
            card["items"] = [
                item for item in card.get("items", [])
                if item.get("main")
            ][:5]
        # 카드 3개 미만이면 경고
        if len(data.get("cards", [])) < 3:
            print(f"경고: 카드 {len(data.get('cards',[]))}개만 생성됨 (목표: 3개)")
        for i, card in enumerate(data.get("cards", [])):
            if len(card.get("items", [])) < 5:
                print(f"경고: 카드{i+1} 아이템 {len(card.get('items',[]))}개 (목표: 5개)")
        return data
    except Exception as e:
        print(f"분석 실패: {e}")
        return None
