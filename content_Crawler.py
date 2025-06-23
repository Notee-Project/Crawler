import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ✅ 1. JSON 파일 경로 지정
json_path = "gknu_results.json"

# ✅ 2. 새로운 폴더 이름 생성 함수
def generate_unique_folder(base_name="contents"):
    if not os.path.exists(base_name):
        return base_name
    i = 1
    while True:
        new_name = f"{base_name}_{i:02d}"
        if not os.path.exists(new_name):
            return new_name
        i += 1

# ✅ 3. 폴더 생성
base_folder = generate_unique_folder("contents")
os.makedirs(base_folder, exist_ok=True)

contents_dir = os.path.join(base_folder, "contents")
download_dir = os.path.join(base_folder, "download")
os.makedirs(contents_dir, exist_ok=True)
os.makedirs(download_dir, exist_ok=True)

# ✅ 4. JSON 로드
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

base_url = "https://www.gknu.ac.kr"

# ✅ 5. 항목별 처리
for idx, item in enumerate(data, start=1):
    title = item["title"]
    url = item["url"]
    print(f"\n🔍 [{idx}] 처리 중: {title}")

    try:
        response = requests.get(url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")

        # ✅ 본문 추출 및 저장
        content_div = soup.select_one("div.board-view-cont")
        if content_div:
            spans = content_div.select("p span")
            full_text = "\n".join(span.get_text(strip=True) for span in spans if span.get_text(strip=True))

            text_file = os.path.join(contents_dir, f"{idx:02d}_content.txt")
            with open(text_file, "w", encoding="utf-8") as f:
                f.write(full_text)
            print(f"📝 본문 저장 완료: {text_file}")
        else:
            print("❌ 본문 콘텐츠 없음")

        # ✅ 첨부파일 다운로드
        clip_div = soup.select_one("div.clip")
        if clip_div:
            for a_tag in clip_div.find_all("a", href=True):
                file_url = urljoin(base_url, a_tag["href"])
                file_name = a_tag.get_text(strip=True).split("(")[0]

                try:
                    file_data = requests.get(file_url)
                    file_path = os.path.join(download_dir, file_name)
                    with open(file_path, "wb") as f:
                        f.write(file_data.content)
                    print(f"✅ 첨부파일 저장 완료: {file_path}")
                except Exception as e:
                    print(f"❌ 첨부파일 다운로드 실패: {file_url} / 이유: {e}")
        else:
            print("📂 첨부파일 없음")
    except Exception as e:
        print(f"❌ 페이지 요청 실패: {url} / 이유: {e}")
