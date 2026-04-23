import os, shutil
from playwright.sync_api import sync_playwright
from html_generator import title_card, make_card

OUTPUT_DIR   = os.path.join(os.path.dirname(__file__), "output")
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(OUTPUT_DIR,   exist_ok=True)
os.makedirs(TEMPLATE_DIR, exist_ok=True)


def _html_to_image(html, path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350})
        page.set_content(html, wait_until="networkidle")
        page.screenshot(path=path, clip={"x":0,"y":0,"width":1080,"height":1350})
        browser.close()
    print(f"저장: {path}")
    return path


def _clear():
    for f in os.listdir(OUTPUT_DIR):
        if f.startswith("image_") and f.endswith(".jpg"):
            os.remove(os.path.join(OUTPUT_DIR, f))


def create_all_cards(title, analysis):
    """
    analysis: content_analyzer.analyze_post() 반환값
    {
      "post_type": "ranking|policy|news|analysis|general",
      "cards": [{"title": "...", "items": [...]}]
    }
    """
    _clear()
    paths = []

    post_type = analysis.get("post_type", "general") if analysis else "general"
    cards     = analysis.get("cards", []) if analysis else []

    print(f"포스팅 유형: {post_type} / 카드 {len(cards)}장")

    # 카드 0: 타이틀 (공통)
    p = os.path.join(OUTPUT_DIR, "image_0.jpg")
    _html_to_image(title_card(title), p)
    paths.append(p)

    # 카드 1~3: 유형별 콘텐츠 카드
    for idx, card in enumerate(cards[:3], start=1):
        html = make_card(post_type, card.get("title", ""), card.get("items", []))
        p = os.path.join(OUTPUT_DIR, f"image_{idx}.jpg")
        _html_to_image(html, p)
        paths.append(p)

    # 마지막 카드: 고정 템플릿
    tpl = os.path.join(TEMPLATE_DIR, "card_last_template.jpg")
    if os.path.exists(tpl):
        dest = os.path.join(OUTPUT_DIR, f"image_{len(paths)}.jpg")
        shutil.copy(tpl, dest)
        paths.append(dest)
        print(f"템플릿 카드 복사: image_{len(paths)-1}.jpg")
    else:
        print("※ templates/card_last_template.jpg 를 저장하면 마지막 카드 자동 포함됩니다.")

    print(f"\n총 {len(paths)}장 생성 완료")
    return paths
