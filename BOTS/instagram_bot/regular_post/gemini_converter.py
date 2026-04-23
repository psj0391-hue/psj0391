from groq import Groq
import os, json
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def _ask(prompt):
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content


def convert_to_instagram(title, summary):
    """인스타 캡션 + 해시태그 생성"""
    prompt = f"""아래 경제 블로그 글을 인스타그램 게시물로 변환해줘.

[블로그 제목] {title}
[블로그 내용] {summary[:800]}

[규칙]
- 첫 줄: 흥미로운 한 줄 요약 (이모지 포함)
- 본문: 핵심 내용 3줄 (친근한 말투)
- 마지막: 해시태그 10개

캡션과 해시태그만 출력해줘."""
    return _ask(prompt)


def extract_structured_data(title, fulltext):
    """블로그 본문에서 구조화된 데이터 추출 (JSON)"""
    prompt = f"""아래 경제 블로그 글에서 데이터를 추출해서 JSON으로만 반환해줘. 설명 없이 JSON만.

[제목] {title}
[본문] {fulltext[:3000]}

JSON 형식:
{{
  "market": {{
    "kospi": "지수값 (예: 6191.92)",
    "kosdaq": "지수값 (예: 1170.04)"
  }},
  "institution": [
    {{"rank": 1, "name": "종목명", "amount": "금액숫자만 (예: 7,131)", "reason": "한줄 매수 이유"}},
    ...최대 5개
  ],
  "foreigner": [
    {{"rank": 1, "name": "종목명", "amount": "금액숫자만", "reason": "한줄 매수 이유"}},
    ...최대 5개
  ],
  "pension": [
    {{"rank": 1, "name": "종목명", "amount": "금액숫자만", "reason": "한줄 매수 이유"}},
    ...최대 5개
  ]
}}"""
    # JSON 모드로 강제 요청
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    raw = res.choices[0].message.content
    try:
        data = json.loads(raw)
        # 빈 항목 필터링
        for key in ("institution", "foreigner", "pension"):
            data[key] = [
                item for item in data.get(key, [])
                if item.get("name") and item.get("rank")
            ]
            # rank 순서로 정렬하여 1~5위만
            data[key] = sorted(data[key], key=lambda x: int(str(x["rank"])) if str(x["rank"]).isdigit() else 99)[:5]
            for i, item in enumerate(data[key]):
                item["rank"] = i + 1  # 연속 순위로 재정렬
        return data
    except Exception as e:
        print(f"JSON 파싱 오류: {e}")
        return None


import re
