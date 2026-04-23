"""
인스타그램 스토리 업로드 (Meta Graph API)
- 이미지 파일을 공개 URL로 먼저 호스팅 후 업로드 필요
- IG_USER_ID, IG_ACCESS_TOKEN 필요
"""
import os, requests
from dotenv import load_dotenv

load_dotenv()

IG_USER_ID    = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
GRAPH_URL     = "https://graph.facebook.com/v19.0"


def upload_story(image_url: str) -> dict:
    """
    image_url: 공개 접근 가능한 이미지 URL (ngrok, S3, imgbb 등)
    반환: {"success": True/False, "id": "...", "error": "..."}
    """
    if not IG_USER_ID or not IG_ACCESS_TOKEN:
        return {"success": False, "error": "IG_USER_ID 또는 IG_ACCESS_TOKEN이 설정되지 않았습니다."}

    # Step 1: 미디어 컨테이너 생성
    container_res = requests.post(
        f"{GRAPH_URL}/{IG_USER_ID}/media",
        data={
            "image_url":   image_url,
            "media_type":  "STORIES",
            "access_token": IG_ACCESS_TOKEN
        }
    )
    container = container_res.json()
    if "id" not in container:
        return {"success": False, "error": f"컨테이너 생성 실패: {container}"}

    container_id = container["id"]
    print(f"미디어 컨테이너 생성: {container_id}")

    # Step 2: 스토리 게시
    publish_res = requests.post(
        f"{GRAPH_URL}/{IG_USER_ID}/media_publish",
        data={
            "creation_id":  container_id,
            "access_token": IG_ACCESS_TOKEN
        }
    )
    result = publish_res.json()
    if "id" in result:
        print(f"스토리 업로드 성공: {result['id']}")
        return {"success": True, "id": result["id"]}
    else:
        return {"success": False, "error": f"게시 실패: {result}"}
