"""
릴스 생성기 v2 - 캐릭터 + 굵은 텍스트 분할 레이아웃
상단 60% = 캐릭터(올빼미 박사) 일러스트, 하단 40% = 어두운 배경 + 굵은 핵심 메시지
"""
import os, asyncio
from playwright.sync_api import sync_playwright

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── 공통 스타일 ─────────────────────────────────────────────────────────────
BASE_CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
body {
    width:1080px; height:1920px; overflow:hidden;
    font-family: 'Malgun Gothic','맑은 고딕',sans-serif;
}
.slide { width:1080px; height:1920px; display:flex; flex-direction:column; }

/* 상단 캐릭터 존 (60%) */
.char-zone {
    height:1152px; flex-shrink:0; position:relative;
    background: linear-gradient(160deg, #0A1628 0%, #1a3a5c 50%, #0A1628 100%);
    display:flex; flex-direction:column;
    align-items:center; justify-content:center; overflow:hidden;
}
/* 배경 빛 효과 */
.char-zone::before {
    content:''; position:absolute;
    width:700px; height:700px; border-radius:50%;
    background:radial-gradient(circle, rgba(0,188,212,0.15) 0%, transparent 70%);
    top:50%; left:50%; transform:translate(-50%,-50%);
}
/* 하단 텍스트 존 (40%) */
.text-zone {
    flex:1; background:#0D0D0D;
    display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    padding:40px 60px; gap:24px; position:relative;
}
.text-zone::before {
    content:''; position:absolute; top:0; left:0; right:0; height:4px;
    background:linear-gradient(90deg, #00BCD4, #C8EE5A, #00BCD4);
}

/* 채널 로고 */
.channel-tag {
    position:absolute; top:36px; left:50%; transform:translateX(-50%);
    background:rgba(0,188,212,0.2); border:2px solid #00BCD4;
    color:#00BCD4; font-size:28px; font-weight:900;
    padding:10px 36px; border-radius:40px; white-space:nowrap;
    letter-spacing:1px;
}
/* 날짜 태그 */
.date-tag {
    position:absolute; bottom:30px; right:48px;
    color:rgba(255,255,255,0.35); font-size:26px; font-weight:700;
}
"""

# ── 캐릭터 SVG (올빼미 박사 - 나마나마 마스코트) ───────────────────────────
def _owl_svg(mood="normal", size=520):
    """CSS 기반 올빼미 박사 캐릭터 (mood: normal/excited/think/happy)"""
    eye_l = eye_r = "●"
    mouth = "▾" if mood == "excited" else ("〜" if mood == "think" else "ω")
    eyebrow = "▔▔" if mood == "excited" else ("〰" if mood == "think" else "—")
    accessory = ""
    if mood == "excited":
        accessory = '<div class="sparkle">✦ ✦ ✦</div>'
    elif mood == "think":
        accessory = '<div class="think-bubble">?</div>'

    return f"""
<style>
.owl-wrap {{
    position:relative; display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    width:{size}px; height:{size}px;
}}
.owl-body {{
    width:{int(size*0.65)}px; height:{int(size*0.75)}px;
    background:linear-gradient(160deg,#4a3728,#2d1f14);
    border-radius:48% 48% 40% 40%;
    position:relative; display:flex; flex-direction:column;
    align-items:center;
    box-shadow:0 20px 60px rgba(0,0,0,0.6), inset 0 2px 0 rgba(255,255,255,0.1);
}}
/* 배 */
.owl-belly {{
    position:absolute; bottom:{int(size*0.04)}px;
    width:{int(size*0.42)}px; height:{int(size*0.44)}px;
    background:linear-gradient(160deg,#f5deb3,#e8c88a);
    border-radius:50%; left:50%; transform:translateX(-50%);
}}
/* 눈 */
.owl-eyes {{
    display:flex; gap:{int(size*0.08)}px; margin-top:{int(size*0.14)}px; position:relative; z-index:2;
}}
.owl-eye {{
    width:{int(size*0.16)}px; height:{int(size*0.16)}px;
    background:white; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    box-shadow:0 0 12px rgba(255,255,255,0.3);
}}
.owl-pupil {{
    width:{int(size*0.09)}px; height:{int(size*0.09)}px;
    background:#1a0a00; border-radius:50%;
    position:relative;
}}
.owl-pupil::after {{
    content:''; position:absolute; top:15%; right:15%;
    width:35%; height:35%; background:white; border-radius:50%;
}}
/* 눈썹 */
.owl-brows {{
    display:flex; gap:{int(size*0.12)}px; margin-bottom:6px; z-index:3;
}}
.owl-brow {{
    width:{int(size*0.12)}px; height:4px;
    background:#2d1f14; border-radius:4px;
    transform: {'rotate(-8deg)' if mood=="excited" else ('rotate(8deg)' if mood=="think" else 'rotate(-3deg)')};
}}
.owl-brow:last-child {{ transform: {'rotate(8deg)' if mood=="excited" else ('rotate(-8deg)' if mood=="think" else 'rotate(3deg)')}; }}
/* 부리 */
.owl-beak {{
    width:{int(size*0.1)}px; height:{int(size*0.07)}px;
    background:#e8a020; clip-path:polygon(50% 100%, 0 0, 100% 0);
    margin-top:4px; z-index:2;
}}
/* 귀 (뿔) */
.owl-ear {{
    position:absolute; top:-{int(size*0.06)}px;
    width:{int(size*0.1)}px; height:{int(size*0.12)}px;
    background:#3d2a1a; clip-path:polygon(50% 0%, 0% 100%, 100% 100%);
}}
.owl-ear.left {{ left:{int(size*0.15)}px; }}
.owl-ear.right {{ right:{int(size*0.15)}px; }}
/* 안경 */
.owl-glasses {{
    position:absolute; top:{int(size*0.17)}px;
    width:{int(size*0.44)}px; height:{int(size*0.22)}px;
    border:3px solid #00BCD4; border-radius:50%; z-index:4;
    box-shadow:0 0 12px rgba(0,188,212,0.4);
    display:flex; align-items:center; justify-content:center;
}}
.owl-glasses::before, .owl-glasses::after {{
    content:''; position:absolute;
    width:{int(size*0.18)}px; height:{int(size*0.18)}px;
    border:3px solid #00BCD4; border-radius:50%;
    top:50%; transform:translateY(-50%);
    box-shadow:0 0 8px rgba(0,188,212,0.3);
}}
.owl-glasses::before {{ left:-{int(size*0.04)}px; }}
.owl-glasses::after {{ right:-{int(size*0.04)}px; }}
/* 날개 */
.owl-wings {{
    position:absolute; bottom:{int(size*0.12)}px;
    display:flex; width:100%; justify-content:space-between;
    padding:0 {int(size*0.02)}px;
}}
.owl-wing {{
    width:{int(size*0.18)}px; height:{int(size*0.28)}px;
    background:linear-gradient(160deg,#5a4030,#3d2a1a);
    border-radius:30% 30% 50% 50%;
}}
.owl-wing.right {{ transform:scaleX(-1); }}
/* 다리 */
.owl-legs {{
    display:flex; gap:{int(size*0.12)}px; margin-top:6px; z-index:0;
}}
.owl-leg {{
    width:{int(size*0.06)}px; height:{int(size*0.1)}px;
    background:#e8a020; border-radius:4px;
}}
/* 발 */
.owl-feet {{
    display:flex; gap:{int(size*0.1)}px;
}}
.owl-foot {{
    display:flex; gap:3px;
}}
.owl-toe {{
    width:{int(size*0.04)}px; height:{int(size*0.04)}px;
    background:#e8a020; border-radius:50% 50% 0 0;
}}
/* 학사모 */
.owl-hat {{
    position:absolute; top:-{int(size*0.22)}px; left:50%; transform:translateX(-50%);
    display:flex; flex-direction:column; align-items:center;
}}
.hat-top {{
    width:{int(size*0.5)}px; height:{int(size*0.14)}px;
    background:#0A1628; border-radius:4px 4px 0 0;
    border:2px solid #00BCD4;
}}
.hat-brim {{
    width:{int(size*0.7)}px; height:{int(size*0.04)}px;
    background:#0A1628; border:2px solid #00BCD4;
}}
.hat-tassel {{
    position:absolute; right:{int(size*0.04)}px; top:0;
    width:3px; height:{int(size*0.18)}px;
    background:#C8EE5A;
}}
.hat-tassel::after {{
    content:'●'; color:#C8EE5A; font-size:{int(size*0.04)}px;
    position:absolute; bottom:-4px; left:-4px;
}}
/* 이펙트 */
.sparkle {{
    position:absolute; top:-{int(size*0.05)}px; font-size:32px;
    color:#C8EE5A; letter-spacing:24px;
    text-shadow:0 0 10px rgba(200,238,90,0.8);
    animation:none;
}}
.think-bubble {{
    position:absolute; top:-{int(size*0.12)}px; right:0;
    width:{int(size*0.2)}px; height:{int(size*0.2)}px;
    background:rgba(255,255,255,0.9); border-radius:50%;
    color:#0A1628; font-size:{int(size*0.1)}px; font-weight:900;
    display:flex; align-items:center; justify-content:center;
    box-shadow:0 4px 20px rgba(0,0,0,0.3);
}}
</style>
<div class="owl-wrap">
  {accessory}
  <div class="owl-body">
    <div class="owl-hat">
      <div class="hat-top"></div>
      <div class="hat-brim"></div>
      <div class="hat-tassel"></div>
    </div>
    <div class="owl-ear left"></div>
    <div class="owl-ear right"></div>
    <div class="owl-brows">
      <div class="owl-brow"></div>
      <div class="owl-brow"></div>
    </div>
    <div class="owl-eyes">
      <div class="owl-eye"><div class="owl-pupil"></div></div>
      <div class="owl-eye"><div class="owl-pupil"></div></div>
    </div>
    <div class="owl-glasses"></div>
    <div class="owl-beak"></div>
    <div class="owl-belly"></div>
    <div class="owl-wings">
      <div class="owl-wing left"></div>
      <div class="owl-wing right"></div>
    </div>
  </div>
  <div class="owl-legs">
    <div class="owl-leg"></div>
    <div class="owl-leg"></div>
  </div>
  <div class="owl-feet">
    <div class="owl-foot">
      <div class="owl-toe"></div><div class="owl-toe"></div><div class="owl-toe"></div>
    </div>
    <div class="owl-foot">
      <div class="owl-toe"></div><div class="owl-toe"></div><div class="owl-toe"></div>
    </div>
  </div>
</div>"""


# ── 공통 슬라이드 빌더 ─────────────────────────────────────────────────────
def _slide(char_content, main_msg, sub_lines=None, date_str="", mood="normal"):
    sub_html = ""
    if sub_lines:
        for line in sub_lines[:3]:
            sub_html += f'<div class="sub-line">{line}</div>'

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
{BASE_CSS}
.char-content {{
    position:relative; z-index:1;
    display:flex; flex-direction:column;
    align-items:center; justify-content:center; gap:20px;
    padding-top:100px;
}}
.speech-bubble {{
    background:rgba(255,255,255,0.95); color:#0A1628;
    border-radius:20px; padding:18px 32px;
    font-size:32px; font-weight:900; text-align:center;
    max-width:800px; line-height:1.4; word-break:keep-all;
    box-shadow:0 8px 32px rgba(0,0,0,0.3);
    position:relative;
}}
.speech-bubble::after {{
    content:''; position:absolute; bottom:-20px; left:50%; transform:translateX(-50%);
    border:10px solid transparent; border-top-color:rgba(255,255,255,0.95);
}}
.main-msg {{
    font-size:64px; font-weight:900; color:white;
    text-align:center; line-height:1.25; word-break:keep-all;
    text-shadow:0 4px 20px rgba(0,0,0,0.8);
    letter-spacing:-1px;
}}
.main-msg .accent {{ color:#C8EE5A; }}
.sub-line {{
    font-size:34px; font-weight:700; color:rgba(255,255,255,0.7);
    text-align:center; word-break:keep-all;
}}
.handle {{
    font-size:30px; font-weight:900; color:#00BCD4;
    position:absolute; bottom:28px; left:50%; transform:translateX(-50%);
    white-space:nowrap; text-shadow:0 0 16px rgba(0,188,212,0.5);
}}
</style>
</head><body>
<div class="slide">
  <div class="char-zone">
    <div class="channel-tag">나마나마 경제성장 팩토리</div>
    <div class="char-content">
      {char_content}
      {_owl_svg(mood=mood, size=460)}
    </div>
    <div class="date-tag">{date_str}</div>
  </div>
  <div class="text-zone">
    <div class="main-msg">{main_msg}</div>
    {sub_html}
    <div class="handle">@namanama_economy</div>
  </div>
</div>
</body></html>"""


# ── 각 씬 HTML 생성 ───────────────────────────────────────────────────────

def intro_html(title, date_str=""):
    bubble = f'<div class="speech-bubble">📊 오늘의 주식 리포트!</div>'
    # 제목에서 회사명 추출 (첫 10자)
    short = title[:18] + ("…" if len(title) > 18 else "")
    main = f'<span class="accent">{short}</span><br>지금 분석해드릴게요!'
    return _slide(bubble, main, date_str=date_str, mood="excited")


def earnings_html(data, date_str=""):
    items = data.get("items", [])[:4]
    highlight = data.get("highlight", "실적 분석")
    bubble = f'<div class="speech-bubble">💰 실적을 살펴볼게요</div>'
    main = f'<span class="accent">{highlight}</span>'
    subs = [f"{'▸'} {i['label']}  {i['value']}" for i in items]
    return _slide(bubble, main, sub_lines=subs, date_str=date_str, mood="excited")


def stock_html(data, date_str=""):
    items = data.get("items", [])[:4]
    highlight = data.get("highlight", "주가 분석")
    bubble = f'<div class="speech-bubble">📈 주가 흐름이에요</div>'
    main = f'<span class="accent">{highlight}</span>'
    subs = [f"{'▸'} {i['label']}  {i['value']}" for i in items]
    return _slide(bubble, main, sub_lines=subs, date_str=date_str, mood="think")


def business_html(data, date_str=""):
    items = data.get("items", [])[:4]
    highlight = data.get("highlight", "사업 현황")
    bubble = f'<div class="speech-bubble">🏢 사업 현황입니다</div>'
    main = f'<span class="accent">{highlight}</span>'
    subs = [f"{'▸'} {i['label']}  {i['value']}" for i in items]
    return _slide(bubble, main, sub_lines=subs, date_str=date_str, mood="normal")


def outro_html(date_str=""):
    bubble = '<div class="speech-bubble">함께해 주셔서 감사해요! 🙏</div>'
    main = '팔로우하고<br><span class="accent">매일 경제 정보</span><br>받아보세요!'
    subs = ["투자는 본인 책임입니다"]
    return _slide(bubble, main, sub_lines=subs, date_str=date_str, mood="happy")


# ── 렌더링 ────────────────────────────────────────────────────────────────

def _clear():
    for f in os.listdir(OUTPUT_DIR):
        if f.startswith("reel_") and (f.endswith(".jpg") or f.endswith(".mp4") or f.endswith(".mp3")):
            os.remove(os.path.join(OUTPUT_DIR, f))


def _render_all(html_list):
    paths = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for html, filename in html_list:
            pg = browser.new_page(viewport={"width": 1080, "height": 1920})
            pg.set_content(html, wait_until="networkidle")
            path = os.path.join(OUTPUT_DIR, filename)
            pg.screenshot(path=path, clip={"x": 0, "y": 0, "width": 1080, "height": 1920})
            pg.close()
            print(f"  생성: {filename}")
            paths.append(path)
        browser.close()
    return paths


def create_reels_images(title, data, date_str=""):
    _clear()
    html_list = [
        (intro_html(title, date_str),             "reel_01_intro.jpg"),
        (earnings_html(data["earnings"], date_str), "reel_02_earnings.jpg"),
        (stock_html(data["stock"], date_str),       "reel_03_stock.jpg"),
        (business_html(data["business"], date_str), "reel_04_business.jpg"),
        (outro_html(date_str),                      "reel_05_outro.jpg"),
    ]
    return _render_all(html_list)


# ── TTS 나레이션 생성 ──────────────────────────────────────────────────────

async def _tts_async(texts, paths, voice="ko-KR-SunHiNeural"):
    import edge_tts
    for text, path in zip(texts, paths):
        comm = edge_tts.Communicate(text, voice)
        await comm.save(path)
        print(f"  TTS: {os.path.basename(path)}")


def create_narrations(data, title):
    """각 씬 TTS 음성 파일 생성 → 파일 경로 리스트 반환"""
    scripts = [
        data.get("intro_narration",
                 f"안녕하세요, 나마나마 경제성장 팩토리입니다! {title[:20]} 리포트를 시작할게요."),
        data.get("earnings", {}).get("narration",
                 f"실적을 살펴볼게요. {data.get('earnings',{}).get('highlight','어닝 서프라이즈를 달성했습니다.')}"),
        data.get("stock", {}).get("narration",
                 f"주가 현황입니다. {data.get('stock',{}).get('highlight','추세 전환을 시도하고 있습니다.')}"),
        data.get("business", {}).get("narration",
                 f"사업 현황을 정리했어요. {data.get('business',{}).get('highlight','내부 혁신 효과가 나타나고 있어요.')}"),
        data.get("outro_narration",
                 "오늘 경제 리포트 어떠셨나요? 팔로우하고 매일 경제 정보를 받아보세요!"),
    ]
    audio_paths = [os.path.join(OUTPUT_DIR, f"reel_{i+1:02d}_voice.mp3") for i in range(5)]
    asyncio.run(_tts_async(scripts, audio_paths))
    return audio_paths


# ── 영상 변환 ─────────────────────────────────────────────────────────────

def create_video(image_paths, audio_paths=None, output_name="reels.mp4"):
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip

    durations = [4, 7, 7, 7, 5]  # 30초
    clips = []

    for i, (img_path, dur) in enumerate(zip(image_paths, durations)):
        clip = ImageClip(img_path).with_duration(dur)

        if audio_paths and i < len(audio_paths) and os.path.exists(audio_paths[i]):
            try:
                audio = AudioFileClip(audio_paths[i])
                # 오디오가 씬보다 길면 자름, 짧으면 무음 패딩 없이 그냥 사용
                if audio.duration > dur:
                    audio = audio.subclipped(0, dur)
                clip = clip.with_audio(audio)
            except Exception as e:
                print(f"  오디오 합성 실패 ({i+1}): {e}")

        clips.append(clip)

    final = concatenate_videoclips(clips, method="compose")
    out_path = os.path.join(OUTPUT_DIR, output_name)
    final.write_videofile(out_path, fps=30, codec="libx264",
                          audio_codec="aac", logger=None)
    print(f"\n영상 저장: {out_path}")
    return out_path
