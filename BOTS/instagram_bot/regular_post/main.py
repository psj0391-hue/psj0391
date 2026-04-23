import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from rss_parser import get_latest_post
from content_analyzer import generate_caption, analyze_post
from image_generator import create_all_cards


def run(blog_url=None):
    print("=== 네이버 블로그 → 인스타그램 자동 업로드 시작 ===\n")

    # 1. 블로그 글 가져오기
    post = get_latest_post(blog_url)
    if not post:
        print("글을 가져올 수 없습니다.")
        return

    print(f"제목: {post['title']}")

    # 2. 캡션 생성
    print("\n캡션 생성 중...")
    caption = generate_caption(post["title"], post["summary"])
    print(f"\n[캡션]\n{caption}\n")

    # 3. 포스팅 유형 분석 + 카드 데이터 추출
    print("포스팅 분석 중...")
    analysis = analyze_post(post["title"], post["fulltext"])
    if analysis:
        print(f"유형: {analysis.get('post_type')} / 카드: {len(analysis.get('cards',[]))}개")
    else:
        print("분석 실패 - 타이틀 카드만 생성")

    # 4. 이미지 생성
    print("\n이미지 생성 중...")
    image_paths = create_all_cards(post["title"], analysis)

    print("\n=== 완료 ===")
    print(f"생성된 이미지 {len(image_paths)}장:")
    for p in image_paths:
        print(f"  - {p}")
    print("\n※ 인스타그램 업로드는 비즈니스 계정 설정 후 활성화됩니다.")
    return image_paths, caption


if __name__ == "__main__":
    # blog_url=None 이면 최신 글 자동 사용
    # 특정 글 지정시: run(blog_url="https://blog.naver.com/namanama-/XXXXX")
    run(blog_url=None)
