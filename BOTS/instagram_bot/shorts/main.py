import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'regular_post'))

from datetime import datetime
from rss_parser import get_latest_post
from script_generator import extract_reels_data
from video_generator import create_reels_images, create_narrations, create_video


def run(blog_url=None):
    print("=== 릴스 자동 생성 시작 ===\n")

    post = get_latest_post(blog_url)
    if not post:
        print("글을 가져올 수 없습니다.")
        return

    print(f"제목: {post['title']}\n")
    date_str = datetime.now().strftime("%Y.%m.%d")

    # 1. 데이터 추출
    print("데이터 추출 중...")
    data = extract_reels_data(post["title"], post["fulltext"])
    print(f"  실적: {len(data.get('earnings',{}).get('items',[]))}개")
    print(f"  주가: {len(data.get('stock',{}).get('items',[]))}개")
    print(f"  사업: {len(data.get('business',{}).get('items',[]))}개\n")

    # 2. 이미지 생성
    print("이미지 생성 중...")
    image_paths = create_reels_images(post["title"], data, date_str=date_str)

    # 3. TTS 나레이션
    print("\n나레이션 생성 중...")
    audio_paths = create_narrations(data, post["title"])

    # 4. 영상 변환
    print("\n영상 변환 중...")
    video_path = create_video(image_paths, audio_paths)

    print(f"\n=== 완료 ===")
    print(f"영상: {video_path}")
    return video_path, image_paths


if __name__ == "__main__":
    run()
