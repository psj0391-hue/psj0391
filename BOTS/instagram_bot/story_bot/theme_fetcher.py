"""
네이버 금융 테마 순위 스크래퍼
- 당일 테마 1위 이름 + 등락률
- 해당 테마 소속 종목 상위 5개 (종목명, 현재가, 등락률)
"""
import requests, os, re, json
from bs4 import BeautifulSoup
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://finance.naver.com/"
}


def get_top_theme():
    url = "https://finance.naver.com/sise/theme.naver"
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.encoding = "euc-kr"
    soup = BeautifulSoup(res.text, "html.parser")

    for row in soup.select("tr"):
        cols = row.select("td")
        if not cols or len(cols) < 2:
            continue
        name_tag = row.select_one("a")
        if not name_tag:
            continue
        theme_name = name_tag.get_text(strip=True)
        if not theme_name:
            continue
        theme_link = "https://finance.naver.com" + name_tag["href"]
        change_rate = cols[1].get_text(strip=True) if len(cols) > 1 else ""
        return {"name": theme_name, "change_rate": change_rate, "link": theme_link}
    return None


def get_theme_stocks(theme_link, limit=5):
    res = requests.get(theme_link, headers=HEADERS, timeout=10)
    res.encoding = "euc-kr"
    soup = BeautifulSoup(res.text, "html.parser")

    stocks = []
    for row in soup.select("tr"):
        cols = row.select("td")
        if not cols or len(cols) < 5:
            continue
        name_tag = row.select_one("a")
        if not name_tag:
            continue
        name = name_tag.get_text(strip=True)
        if not name or "테마" in cols[0].get_text() or len(name) < 2:
            continue
        href = name_tag.get("href", "")
        code = href.split("code=")[-1].split("&")[0] if "code=" in href else ""
        price  = cols[2].get_text(strip=True) if len(cols) > 2 else "-"
        change = cols[4].get_text(strip=True) if len(cols) > 4 else "-"
        stocks.append({"name": name, "code": code, "price": price, "change": change})
        if len(stocks) >= limit:
            break
    return stocks


def analyze_theme_reason(theme_name, change_rate, stock_names):
    print("상승 이유 분석 중...")
    stock_list = ", ".join(stock_names[:5])
    prompt = f"""오늘 한국 주식시장에서 '{theme_name}' 테마가 {change_rate} 급등했습니다.
주요 종목: {stock_list}

당신은 10년 경력의 증권사 리서치센터 수석 애널리스트입니다.
아래 3가지 관점을 녹여 2문장으로 분석해주세요.

① 거시 트리거: 글로벌 정책·금리·지정학·산업 트렌드 중 오늘 급등과 연결된 핵심 요인
② 섹터 모멘텀: 해당 테마의 구조적 수혜 논리 (수주·실적·규제·기술 등)
③ 수급 특징: 기관·외국인·개인 중 주도 주체와 그 시장적 의미

조건:
- ~됐어요, ~입니다 형태의 전문적이면서 친근한 어투
- 구체적 키워드(산업명, 정책명, 수급 주체) 반드시 포함
- 서두·결론 없이 첫 문장부터 핵심 시작
- 큰따옴표 없이 문장 2개만 출력"""

    res = _groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    raw = res.choices[0].message.content.strip().strip('"').strip("'")
    # 마침표·요·다 뒤 공백 기준으로 문장 분리
    sentences = [s.strip() for s in re.split(r'(?<=[요다.!])\s+', raw) if s.strip()]
    # "원인은", "다음과 같" 같은 서두 메타 문장 제거
    meta_keys = ["다음과 같", "원인은", "이유는", "결론"]
    sentences = [s for s in sentences if not any(k in s for k in meta_keys)]
    return " ".join(sentences[:2])


def get_investor_flow(code, price_str):
    """
    네이버 금융 frgn 페이지에서 기관/외국인 순매수(주) 스크래핑.
    개인 = -(기관 + 외국인). 억원 환산 반환.
    종목마다 테이블 위치가 달라 헤더('기관','외국인')로 테이블을 동적 탐색.
    """
    try:
        url = f"https://finance.naver.com/item/frgn.naver?code={code}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.encoding = "euc-kr"
        soup = BeautifulSoup(res.text, "html.parser")

        def parse_num(txt):
            cleaned = re.sub(r'[^0-9\-]', '', txt.replace(",", ""))
            return int(cleaned) if cleaned and cleaned != "-" else 0

        # 헤더에 '기관' + '외국인'이 있는 테이블 동적 탐색
        investor_table = None
        inst_idx = for_idx = None
        for table in soup.select("table"):
            header_row = table.select_one("tr")
            if not header_row:
                continue
            cells = [c.get_text(strip=True) for c in header_row.select("td, th")]
            if "기관" in cells and "외국인" in cells:
                investor_table = table
                inst_idx = cells.index("기관")
                for_idx  = cells.index("외국인")
                break

        if not investor_table:
            return None

        # 날짜 형식(YYYY.MM.DD)이 있는 첫 번째 데이터 행
        first_row = None
        for row in investor_table.select("tr"):
            tds = row.select("td")
            if not tds:
                continue
            date_text = tds[0].get_text(strip=True)
            if re.match(r'\d{4}\.\d{2}\.\d{2}', date_text):
                first_row = tds
                break

        if not first_row or len(first_row) <= max(inst_idx, for_idx):
            return None

        inst_shares = parse_num(first_row[inst_idx].get_text(strip=True))
        for_shares  = parse_num(first_row[for_idx].get_text(strip=True))
        ind_shares  = -(inst_shares + for_shares)

        try:
            price = int(price_str.replace(",", ""))
        except Exception:
            price = 0

        def to_uk(shares):
            return int(shares * price / 100_000_000) if price else 0

        return {
            "개인": to_uk(ind_shares),
            "기관": to_uk(inst_shares),
            "외인": to_uk(for_shares),
        }

    except Exception as e:
        print(f"  투자자 데이터 실패({code}): {e}")
        return None


def get_intraday_prices(code, count=40):
    """당일 장중 1분봉 종가 배열 (시간 오름차순). 부족하면 일봉 종가로 대체."""
    try:
        url = (f"https://fchart.stock.naver.com/sise.nhn"
               f"?symbol={code}&timeframe=minute&count={count}&requestType=0")
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.encoding = "euc-kr"
        prices = []
        for m in re.findall(r'data="([^"]+)"', res.text):
            cols = m.split("|")
            if len(cols) >= 5:
                prices.append(int(cols[4]))   # close
        if len(prices) >= 5:
            return prices
    except Exception as e:
        print(f"  장중 데이터 실패({code}): {e}")

    # fallback: 일봉 종가 5개
    try:
        url2 = (f"https://fchart.stock.naver.com/sise.nhn"
                f"?symbol={code}&timeframe=day&count=6&requestType=0")
        res2 = requests.get(url2, headers=HEADERS, timeout=10)
        res2.encoding = "euc-kr"
        prices2 = []
        for m in re.findall(r'data="([^"]+)"', res2.text):
            cols = m.split("|")
            if len(cols) >= 5:
                prices2.append(int(cols[4]))
        return prices2[-5:]
    except Exception:
        return []


def analyze_stock_summaries(theme_name, stocks):
    """각 종목 한줄 요약 (Groq) → {종목명: 요약} 딕셔너리"""
    print("종목 요약 생성 중...")
    lines = []
    for s in stocks:
        flow = s.get("flow") or {}
        lines.append(
            f"- {s['name']}: 등락률 {s.get('change','')}, "
            f"개인 {flow.get('개인',0)}억, 기관 {flow.get('기관',0)}억, 외인 {flow.get('외인',0)}억"
        )
    stock_info = "\n".join(lines)

    prompt = f"""오늘 '{theme_name}' 테마 종목 데이터:
{stock_info}

아래 규칙으로 각 종목 한줄 요약을 JSON으로만 출력해줘.

규칙:
1. 가장 많이 순매수한 주체(개인/기관/외인) + 등락률 특징만 사용
2. 20자 이내, 친근한 말투 (~했어요, ~예요 형태)
3. 데이터에 없는 내용 절대 추가 금지
4. 형식: {{"종목명": "요약"}}

예시 (이 형식만 사용):
- 개인+136억 + 급등 → "개인이 적극 매수, 15% 급등했어요"
- 외인+116억 + 상한가 → "외인 집중 매수로 상한가 도달했어요"
- 기관+47억 + 소폭 → "기관 꾸준히 담으며 5% 상승했어요" """

    try:
        res = _groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        import json as _json
        return _json.loads(res.choices[0].message.content)
    except Exception as e:
        print(f"  종목 요약 실패: {e}")
        return {}


def fmt_flow(val):
    try:
        v = int(val)
        if v == 0: return "0"
        sign = "+" if v > 0 else ""
        return f"{sign}{v}억"
    except Exception:
        return "-"


def fetch_today_top_theme():
    print("테마 순위 조회 중...")
    theme = get_top_theme()
    if not theme:
        print("테마 정보를 가져올 수 없습니다.")
        return None

    print(f"1위 테마: {theme['name']} ({theme['change_rate']})")
    print("종목 조회 중...")
    stocks = get_theme_stocks(theme["link"])
    if not stocks:
        stocks = _fallback_stocks(theme["link"])

    print("투자자 흐름 + 차트 데이터 조회 중...")
    for s in stocks:
        code = s.get("code", "")
        if code:
            flow = get_investor_flow(code, s.get("price", "0"))
            s["flow"] = flow
            if flow:
                print(f"  {s['name']}: 개인{fmt_flow(flow.get('개인',0))} "
                      f"기관{fmt_flow(flow.get('기관',0))} "
                      f"외인{fmt_flow(flow.get('외인',0))}")
            s["prices"] = get_intraday_prices(code)
        else:
            s["flow"] = None
            s["prices"] = []

    theme["stocks"] = stocks
    print(f"종목 {len(stocks)}개 수집 완료")

    stock_names = [s["name"] for s in stocks]
    theme["reason"] = analyze_theme_reason(theme["name"], theme["change_rate"], stock_names)
    print(f"분석 완료: {theme['reason'][:60]}...")

    summaries = analyze_stock_summaries(theme["name"], stocks)
    for s in stocks:
        s["summary"] = summaries.get(s["name"], "")

    return theme


def _fallback_stocks(url):
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.encoding = "euc-kr"
    soup = BeautifulSoup(res.text, "html.parser")
    stocks = []
    for a in soup.select("td a"):
        name = a.get_text(strip=True)
        if not name or len(name) < 2:
            continue
        parent = a.find_parent("tr")
        if not parent:
            continue
        cols = parent.select("td")
        price = cols[1].get_text(strip=True) if len(cols) > 1 else "-"
        change = next((td.get_text(strip=True) for td in cols if "%" in td.get_text()), "")
        stocks.append({"name": name, "price": price, "change": change, "candles": []})
        if len(stocks) >= 5:
            break
    return stocks
