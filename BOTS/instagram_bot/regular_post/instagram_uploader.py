import requests
import os
from dotenv import load_dotenv

load_dotenv()

IG_USER_ID = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
BASE_URL = "https://graph.facebook.com/v19.0"


def _create_container(image_url, caption=None, is_carousel_item=False):
    data = {"image_url": image_url, "access_token": IG_ACCESS_TOKEN}
    if is_carousel_item:
        data["is_carousel_item"] = "true"
    if caption:
        data["caption"] = caption
    res = requests.post(f"{BASE_URL}/{IG_USER_ID}/media", data=data)
    return res.json().get("id")


def upload_single(image_url, caption):
    """이미지 1장 업로드"""
    container_id = _create_container(image_url, caption)
    if not container_id:
        print("컨테이너 생성 실패")
        return False
    res = requests.post(f"{BASE_URL}/{IG_USER_ID}/media_publish", data={
        "creation_id": container_id,
        "access_token": IG_ACCESS_TOKEN,
    })
    data = res.json()
    if "id" in data:
        print(f"업로드 성공: {data['id']}")
        return True
    print(f"업로드 실패: {data}")
    return False


def upload_carousel(image_urls, caption):
    """카로셀(여러 장) 업로드"""
    # 1. 각 이미지 컨테이너 생성
    item_ids = []
    for url in image_urls:
        item_id = _create_container(url, is_carousel_item=True)
        if item_id:
            item_ids.append(item_id)
            print(f"카로셀 아이템 생성: {item_id}")

    if not item_ids:
        print("카로셀 아이템 생성 실패")
        return False

    # 2. 카로셀 컨테이너 생성
    res = requests.post(f"{BASE_URL}/{IG_USER_ID}/media", data={
        "media_type": "CAROUSEL",
        "children": ",".join(item_ids),
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN,
    })
    carousel_id = res.json().get("id")
    if not carousel_id:
        print(f"카로셀 컨테이너 생성 실패: {res.json()}")
        return False

    # 3. 발행
    res = requests.post(f"{BASE_URL}/{IG_USER_ID}/media_publish", data={
        "creation_id": carousel_id,
        "access_token": IG_ACCESS_TOKEN,
    })
    data = res.json()
    if "id" in data:
        print(f"카로셀 업로드 성공: {data['id']}")
        return True
    print(f"업로드 실패: {data}")
    return False
