import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from theme_fetcher import fetch_today_top_theme
from story_image import create_story_image


def run():
    print("=== 테마 스토리 봇 시작 ===\n")

    # 1. 오늘의 1위 테마 + 종목 수집
    theme = fetch_today_top_theme()
    if not theme:
        print("테마 데이터를 가져오지 못했습니다.")
        return

    print(f"\n테마명  : {theme['name']}")
    print(f"등락률  : {theme['change_rate']}")
    print(f"종목수  : {len(theme['stocks'])}개")
    for s in theme["stocks"]:
        print(f"  {s['name']}  {s['price']}  {s['change']}")

    # 2. 스토리 이미지 생성
    print("\n이미지 생성 중...")
    path = create_story_image(
        theme_name=theme["name"],
        theme_change=theme["change_rate"],
        stocks=theme["stocks"],
        reason=theme.get("reason", "")
    )
    print(f"완료: {path}")

    # 3. 인스타그램 스토리 업로드 (계정 설정 후 활성화)
    # from story_uploader import upload_story
    # result = upload_story(image_url="https://YOUR_PUBLIC_URL/story_today.jpg")
    # print(result)

    print("\n※ 인스타그램 업로드는 비즈니스 계정 설정 후 활성화됩니다.")
    return path


if __name__ == "__main__":
    run()
