"""
미리캔버스 스타일 HTML 이미지 생성기
포스팅 유형에 따라 다른 카드 레이아웃 적용
"""

# ── 공통 CSS ──────────────────────────────────────────────────────────────

BASE_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { width: 1080px; height: 1350px; overflow: hidden; background: white; }

.wrap {
    width: 1080px; height: 1350px; position: relative;
    font-family: 'Malgun Gothic', '맑은 고딕', sans-serif;
    background: white;
}
.lines {
    position: absolute; top: 145px; left: 0; right: 0; bottom: 145px;
    background-image: repeating-linear-gradient(
        to bottom, transparent, transparent 37px, #D0D5DE 37px, #D0D5DE 38px
    ); z-index: 0;
}
.margin {
    position: absolute; top: 145px; bottom: 145px; left: 95px;
    width: 2px; background: #B0BAC9; z-index: 1;
}
.header {
    position: absolute; top: 0; left: 0; right: 0; height: 145px;
    background: #00BCD4; z-index: 10;
    display: flex; align-items: center; padding: 0 22px; gap: 14px;
}
.search-bar {
    flex: 1; background: white; border-radius: 50px;
    padding: 16px 30px; font-size: 33px; color: #555;
    white-space: nowrap; overflow: hidden;
}
.search-btn {
    width: 88px; height: 88px; flex-shrink: 0;
    background: #1B6ECC; border-radius: 50px;
    display: flex; align-items: center; justify-content: center; font-size: 42px;
}
.username {
    position: absolute; bottom: 7px; right: 22px;
    color: white; font-size: 21px;
}
.footer {
    position: absolute; bottom: 0; left: 0; right: 0; height: 145px;
    background: #00BCD4; z-index: 10;
    display: flex; align-items: center; justify-content: space-around;
}
.fi { font-size: 58px; color: white; }
.content {
    position: absolute; top: 145px; left: 0; right: 0; bottom: 145px; z-index: 5;
}
.big-title {
    font-size: 62px; font-weight: 900; color: #C8EE5A;
    -webkit-text-stroke: 6px #000; paint-order: stroke fill;
    line-height: 1.25; text-align: center; word-break: keep-all;
}
"""

HEADER = """
<div class="header">
    <div class="search-bar">나마나마 경제성장 팩토리</div>
    <div class="search-btn">🔍</div>
    <div class="username">@namanama_economy</div>
</div>"""

FOOTER = """
<div class="footer">
    <span class="fi">🏠</span><span class="fi">☆</span>
    <span class="fi">💬</span><span class="fi">⊞</span><span class="fi">☰</span>
</div>"""


def _page(extra_css, body):
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>{BASE_CSS}{extra_css}</style></head><body>
<div class="wrap">
  <div class="lines"></div><div class="margin"></div>
  {HEADER}
  <div class="content">{body}</div>
  {FOOTER}
</div></body></html>"""


# ── 카드 0: 타이틀 (모든 유형 공통) ─────────────────────────────────────

def title_card(title):
    css = ".content{display:flex;align-items:center;justify-content:center;padding:40px 70px;}"
    return _page(css, f'<div class="big-title">{title}</div>')


# ── 카드 유형별 아이템 카드 ──────────────────────────────────────────────

CARD_BASE_CSS = """
.content      { display: flex; flex-direction: column; }
.card-title   { padding: 22px 60px 0; text-align: center; flex-shrink: 0; }
.big-title    { font-size: 54px; }
.top-divider  { height: 2px; background: #D0D5DE; margin: 14px 30px 0 95px; flex-shrink: 0; }
.rows         { flex: 1; display: flex; flex-direction: column; }
.row-wrap     { flex: 1; display: flex; flex-direction: column; justify-content: center;
                border-bottom: 2px solid #D0D5DE; margin-left: 95px; padding-right: 30px; }
.row          { display: flex; align-items: center; padding: 10px 0 10px 15px; gap: 16px; }
.row-text     { flex: 1; }
.row-main     { font-size: 36px; font-weight: 700; color: #111; word-break: keep-all; }
.row-sub      { font-size: 28px; color: #555; margin-top: 5px; word-break: keep-all; }
"""

# 순위 유형 (ranking)
RANKING_EXTRA_CSS = """
.rank-num   { font-size: 42px; font-weight: 900; color: #00BCD4; flex-shrink: 0; min-width: 52px; text-align: right; }
"""

def ranking_card(card_title, items):
    rows_html = ""
    for idx, i in enumerate(items[:5]):
        rows_html += f"""
        <div class="row-wrap">
          <div class="row">
            <div class="rank-num">{i.get('rank', idx+1)}</div>
            <div class="row-text">
              <div class="row-main">{i.get('main','')}</div>
              <div class="row-sub">{i.get('sub','')}</div>
            </div>
          </div>
        </div>"""
    body = f"""
    <div class="card-title"><div class="big-title">{card_title}</div></div>
    <div class="top-divider"></div>
    <div class="rows">{rows_html}</div>"""
    return _page(CARD_BASE_CSS + RANKING_EXTRA_CSS, body)


# 정책/지원금 유형 (policy): 번호 배지 스타일
POLICY_EXTRA_CSS = """
.badge      {
    min-width: 52px; height: 52px; border-radius: 50%;
    background: #00BCD4; color: white;
    display: flex; align-items: center; justify-content: center;
    font-size: 28px; font-weight: 700; flex-shrink: 0;
}
"""

def policy_card(card_title, items):
    rows_html = ""
    for idx, i in enumerate(items[:5]):
        rows_html += f"""
        <div class="row-wrap">
          <div class="row">
            <div class="badge">{idx+1}</div>
            <div class="row-text">
              <div class="row-main">{i.get('main','')}</div>
              <div class="row-sub">{i.get('sub','')}</div>
            </div>
          </div>
        </div>"""
    body = f"""
    <div class="card-title"><div class="big-title">{card_title}</div></div>
    <div class="top-divider"></div>
    <div class="rows">{rows_html}</div>"""
    return _page(CARD_BASE_CSS + POLICY_EXTRA_CSS, body)


# 뉴스/분석/일반 유형 (news, analysis, general): 이모지 불릿 스타일
GENERAL_EXTRA_CSS = """
.bullet     { font-size: 42px; flex-shrink: 0; }
"""

BULLETS = ["📌", "💡", "📊", "🔑", "✅"]

def general_card(card_title, items):
    rows_html = ""
    for idx, i in enumerate(items[:5]):
        rows_html += f"""
        <div class="row-wrap">
          <div class="row">
            <div class="bullet">{BULLETS[idx % len(BULLETS)]}</div>
            <div class="row-text">
              <div class="row-main">{i.get('main','')}</div>
              <div class="row-sub">{i.get('sub','')}</div>
            </div>
          </div>
        </div>"""
    body = f"""
    <div class="card-title"><div class="big-title">{card_title}</div></div>
    <div class="top-divider"></div>
    <div class="rows">{rows_html}</div>"""
    return _page(CARD_BASE_CSS + GENERAL_EXTRA_CSS, body)


# ── 유형에 따라 카드 HTML 선택 ────────────────────────────────────────────

def make_card(post_type, card_title, items):
    if post_type == "ranking":
        return ranking_card(card_title, items)
    elif post_type == "policy":
        return policy_card(card_title, items)
    else:  # news, analysis, general
        return general_card(card_title, items)
