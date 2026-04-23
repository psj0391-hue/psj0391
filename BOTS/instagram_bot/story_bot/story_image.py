"""
인스타그램 스토리 이미지 생성 (1080x1920, 9:16)
당일 테마 1위 + 종목 TOP5 + 일봉 미니차트 + AI 상승 이유
"""
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _color_class(change_str):
    if not change_str:
        return "neutral"
    clean = change_str.replace(",", "").replace("%", "").replace("+", "").strip()
    try:
        val = float(clean)
        if val > 0:   return "up"
        elif val < 0: return "down"
    except ValueError:
        pass
    return "neutral"


def _arrow(change_str):
    cls = _color_class(change_str)
    if cls == "up":   return "▲"
    elif cls == "down": return "▼"
    return "–"


def _flow_cls(val):
    try:
        return "up" if int(val) > 0 else ("down" if int(val) < 0 else "neutral")
    except Exception:
        return "neutral"


def _fmt(val):
    try:
        v = int(val)
        if v == 0: return "0"
        sign = "+" if v > 0 else ""
        return f"{sign}{v}억"
    except Exception:
        return "-"


def make_line_svg(prices, width=210, height=58):
    """종가 배열 → 인라인 선차트 SVG"""
    if not prices or len(prices) < 2:
        return ""

    # 40포인트로 다운샘플링
    if len(prices) > 40:
        step   = len(prices) // 40
        prices = prices[::step]

    p_min   = min(prices)
    p_max   = max(prices)
    p_range = (p_max - p_min) or 1
    n       = len(prices)
    pad_v, pad_h = 5, 4
    cw = width  - pad_h * 2
    ch = height - pad_v * 2

    def sx(i): return pad_h + i * cw / (n - 1)
    def sy(p):  return pad_v + ch * (1 - (p - p_min) / p_range)

    color      = "#FF6B6B" if prices[-1] >= prices[0] else "#6BA3FF"
    fill_color = "rgba(255,107,107,0.18)" if prices[-1] >= prices[0] else "rgba(107,163,255,0.18)"

    pts      = " ".join(f"{sx(i):.1f},{sy(p):.1f}" for i, p in enumerate(prices))
    area_pts = pts + f" {sx(n-1):.1f},{height} {sx(0):.1f},{height}"
    cx_end   = sx(n - 1)
    cy_end   = sy(prices[-1])

    return (
        f'<svg viewBox="0 0 {width} {height}" preserveAspectRatio="none" '
        f'style="display:block;width:100%;height:100%" xmlns="http://www.w3.org/2000/svg">'
        f'<polygon points="{area_pts}" fill="{fill_color}"/>'
        f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.2" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'<circle cx="{cx_end:.1f}" cy="{cy_end:.1f}" r="3.5" fill="{color}"/>'
        f'</svg>'
    )


def build_story_html(theme_name, theme_change, stocks, reason, date_str):
    stock_rows = ""
    for i, s in enumerate(stocks[:5], 1):
        cls   = _color_class(s.get("change", ""))
        arrow = _arrow(s.get("change", ""))

        # 투자자 흐름
        flow = s.get("flow") or {}
        if flow:
            ind_val  = flow.get("개인", 0)
            inst_val = flow.get("기관", 0)
            for_val  = flow.get("외인", 0)
            flow_html = f"""
            <div class="flow-row">
              <div class="flow-cell">
                <span class="flow-label">개인</span>
                <span class="flow-val {_flow_cls(ind_val)}">{_fmt(ind_val)}</span>
              </div>
              <div class="flow-div"></div>
              <div class="flow-cell">
                <span class="flow-label">기관</span>
                <span class="flow-val {_flow_cls(inst_val)}">{_fmt(inst_val)}</span>
              </div>
              <div class="flow-div"></div>
              <div class="flow-cell">
                <span class="flow-label">외인</span>
                <span class="flow-val {_flow_cls(for_val)}">{_fmt(for_val)}</span>
              </div>
            </div>"""
        else:
            flow_html = '<div class="flow-row flow-na"><span class="flow-na-text">집계중</span></div>'

        # 선차트
        prices = s.get("prices", [])
        chart_svg  = make_line_svg(prices) if len(prices) >= 2 else ""
        chart_html = f'<div class="chart-wrap">{chart_svg}</div>' if chart_svg else '<div class="chart-wrap chart-empty"></div>'

        summary = s.get("summary", "")
        summary_html = (f'<div class="summary-row"><span class="summary-icon">💡</span>'
                        f'<span class="summary-text">{summary}</span></div>') if summary else ""

        stock_rows += f"""
        <div class="stock-card">
          <div class="stock-top">
            <div class="stock-name-area">
              <span class="rank">{i}</span>
              <span class="stock-name">{s['name']}</span>
            </div>
            {chart_html}
            <div class="stock-right">
              <div class="price">{s.get('price', '-')}원</div>
              <div class="chg {cls}">{arrow} {s.get('change', '-')}</div>
            </div>
          </div>
          {summary_html}
          {flow_html}
        </div>"""

    theme_cls   = _color_class(theme_change)
    theme_arrow = _arrow(theme_change)

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{
    width:1080px; height:1920px; overflow:hidden;
    background: linear-gradient(160deg, #0A1628 0%, #142847 55%, #0A1628 100%);
    font-family: 'Malgun Gothic','맑은 고딕',sans-serif;
    color: white;
}}
.wrap {{
    width:1080px; height:1920px;
    display:flex; flex-direction:column; overflow:hidden;
}}

/* ── 헤더 ── */
.header {{
    flex-shrink: 0;
    padding: 34px 56px 28px;
    background: rgba(0,188,212,0.12);
    border-bottom: 3px solid #00BCD4;
    display: flex; align-items: center; justify-content: space-between;
}}
.brand {{ font-size: 30px; font-weight: 900; color: #00BCD4; text-shadow: 0 0 18px rgba(0,188,212,0.6); }}
.date-tag {{
    background: #00BCD4; color: white;
    padding: 9px 24px; border-radius: 32px;
    font-size: 28px; font-weight: 900;
}}

/* ── 메인 ── */
.main {{
    flex: 1; min-height: 0;
    display: flex; flex-direction: column;
    padding: 24px 48px 20px; gap: 18px; overflow: hidden;
}}

/* ── 테마 배너 ── */
.theme-banner {{
    flex-shrink: 0;
    background: linear-gradient(135deg, #007FA3, #1255A0);
    border-radius: 22px; padding: 24px 44px;
    text-align: center;
    border: 2px solid rgba(0,188,212,0.5);
    box-shadow: 0 6px 28px rgba(0,100,180,0.5);
}}
.theme-label {{ font-size: 24px; font-weight: 700; color: rgba(255,255,255,0.85); letter-spacing: 5px; margin-bottom: 8px; }}
.theme-name {{
    font-size: 58px; font-weight: 900; color: #C8EE5A;
    -webkit-text-stroke: 3px #1a3a00; paint-order: stroke fill;
    line-height: 1.2; word-break: keep-all; margin-bottom: 8px;
}}
.theme-chg {{ font-size: 42px; font-weight: 900; }}
.theme-chg.up     {{ color: #FF6B6B; }}
.theme-chg.down   {{ color: #6BA3FF; }}
.theme-chg.neutral {{ color: #ddd; }}

/* ── 상승 이유 ── */
.reason-box {{
    flex-shrink: 0;
    background: rgba(255,255,255,0.07);
    border-left: 5px solid #C8EE5A;
    border-radius: 0 14px 14px 0;
    padding: 18px 28px;
}}
.reason-label {{ font-size: 22px; font-weight: 900; color: #C8EE5A; letter-spacing: 2px; margin-bottom: 8px; }}
.reason-text {{ font-size: 24px; font-weight: 700; color: rgba(255,255,255,0.92); line-height: 1.6; word-break: keep-all; }}

/* ── 종목 섹션 ── */
.stocks-section {{
    flex: 1; min-height: 0;
    display: flex; flex-direction: column; overflow: hidden;
}}
.section-title {{
    flex-shrink: 0;
    font-size: 23px; font-weight: 900; color: white;
    border-left: 5px solid #00BCD4; padding-left: 16px; margin-bottom: 10px;
}}
.stocks-list {{
    flex: 1; min-height: 0;
    display: flex; flex-direction: column; gap: 8px; overflow: hidden;
}}

/* ── 종목 카드 ── */
.stock-card {{
    flex: 1; min-height: 0;
    background: rgba(255,255,255,0.07);
    border-radius: 14px; border: 1px solid rgba(255,255,255,0.13);
    display: flex; flex-direction: column; overflow: hidden;
}}
.stock-top {{
    flex: 1; min-height: 0;
    display: flex; align-items: center;
    padding: 0 16px; gap: 10px;
}}

/* 좌: 순위 + 종목명 (고정폭) */
.stock-name-area {{
    flex-shrink: 0; width: 220px;
    display: flex; align-items: center; gap: 8px;
}}
.rank {{ font-size: 22px; font-weight: 900; color: #00BCD4; flex-shrink: 0; }}
.stock-name {{
    font-size: 23px; font-weight: 900; color: white;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}

/* 중: 선차트 (남는 공간 전부 채움) */
.chart-wrap {{
    flex: 1; min-width: 0; height: 58px;
    display: flex; align-items: center;
    background: rgba(0,0,0,0.22); border-radius: 10px; padding: 3px 6px;
}}
.chart-wrap svg {{ width: 100%; height: 100%; }}
.chart-empty {{ opacity: 0; }}

/* 우: 금액 + 등락률 (고정폭) */
.stock-right {{
    flex-shrink: 0; width: 128px; text-align: right;
}}
.price {{
    font-size: 17px; font-weight: 700;
    color: rgba(255,255,255,0.58); margin-bottom: 4px;
}}
.chg {{ font-size: 26px; font-weight: 900; line-height: 1; }}
.chg.up     {{ color: #FF6B6B; }}
.chg.down   {{ color: #6BA3FF; }}
.chg.neutral {{ color: #bbb; }}

/* ── 종목 한줄 요약 ── */
.summary-row {{
    flex-shrink: 0; height: 36px;
    display: flex; align-items: center;
    padding: 0 16px; gap: 8px;
    background: rgba(200,238,90,0.06);
    border-top: 1px solid rgba(200,238,90,0.15);
}}
.summary-icon {{ font-size: 17px; flex-shrink: 0; }}
.summary-text {{
    font-size: 20px; font-weight: 700;
    color: rgba(255,255,255,0.82);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}

/* ── 투자자 흐름 ── */
.flow-row {{
    flex-shrink: 0;
    display: flex; align-items: center;
    background: rgba(0,0,0,0.25);
    border-top: 1px solid rgba(255,255,255,0.1);
    padding: 5px 18px; height: 44px;
}}
.flow-na {{
    justify-content: center;
}}
.flow-na-text {{
    font-size: 18px; font-weight: 700; color: rgba(255,255,255,0.35);
}}
.flow-cell {{
    flex: 1; display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 1px;
}}
.flow-div {{ width: 1px; height: 26px; background: rgba(255,255,255,0.2); }}
.flow-label {{ font-size: 16px; font-weight: 700; color: rgba(255,255,255,0.48); }}
.flow-val {{ font-size: 18px; font-weight: 900; }}
.flow-val.up      {{ color: #FF6B6B; }}
.flow-val.down    {{ color: #6BA3FF; }}
.flow-val.neutral {{ color: #aaa; }}

/* ── 푸터 ── */
.footer {{
    flex-shrink: 0;
    padding: 20px 56px;
    background: rgba(0,188,212,0.12);
    border-top: 3px solid #00BCD4;
    display: flex; align-items: center; justify-content: space-between;
}}
.footer-brand {{ font-size: 26px; font-weight: 900; color: #00BCD4; }}
.footer-note {{ font-size: 22px; font-weight: 700; color: rgba(255,255,255,0.52); }}
</style>
</head><body>
<div class="wrap">
  <div class="header">
    <div class="brand">나마나마 경제성장 팩토리</div>
    <div class="date-tag">{date_str}</div>
  </div>

  <div class="main">
    <div class="theme-banner">
      <div class="theme-label">오늘의 1위 테마</div>
      <div class="theme-name">{theme_name}</div>
      <div class="theme-chg {theme_cls}">{theme_arrow} {theme_change}</div>
    </div>

    <div class="reason-box">
      <div class="reason-label">📈 상승 이유</div>
      <div class="reason-text">{reason}</div>
    </div>

    <div class="stocks-section">
      <div class="section-title">테마 주요 종목 (순매수 단위: 억원)</div>
      <div class="stocks-list">
        {stock_rows}
      </div>
    </div>
  </div>

  <div class="footer">
    <div class="footer-brand">@namanama_economy</div>
    <div class="footer-note">매일 오후 6시 업데이트</div>
  </div>
</div>
</body></html>"""


def create_story_image(theme_name, theme_change, stocks, reason=""):
    date_str = datetime.now().strftime("%m/%d")
    html = build_story_html(theme_name, theme_change, stocks, reason, date_str)

    output_path = os.path.join(OUTPUT_DIR, "story_today.jpg")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        page.set_content(html, wait_until="networkidle")
        page.screenshot(
            path=output_path,
            clip={"x": 0, "y": 0, "width": 1080, "height": 1920}
        )
        browser.close()

    print(f"스토리 이미지 저장: {output_path}")
    return output_path
