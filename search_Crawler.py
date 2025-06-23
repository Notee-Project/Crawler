import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 검색어 입력
keyword = input("🔍 크롤링할 키워드를 입력하세요: ").strip()

# JSON 로드
with open("gknu_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 키워드 필터링
filtered_data = [item for item in data if keyword in item["title"]]

if not filtered_data:
    print("❌ 해당 키워드가 포함된 공지사항이 없습니다.")
    exit()

# 저장 폴더 준비
os.makedirs("download", exist_ok=True)
os.makedirs("contents", exist_ok=True)

base_url = "https://www.gknu.ac.kr"

# 필터링된 항목 처리
for idx, item in enumerate(filtered_data, start=1):
    title = item["title"]
    url = item["url"]
    print(f"\n🔍 [{idx}] 처리 중: {title}")

    # 페이지 요청
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # ✅ 본문 추출
    content_div = soup.select_one("div.board-view-cont")
    if content_div:
        spans = content_div.select("p span")
        full_text = "\n".join(span.get_text(strip=True) for span in spans if span.get_text(strip=True))

        # 저장 파일 이름에 검색어 포함
        text_file = f"contents/{keyword}_Page{idx}.txt"
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"📝 본문 저장 완료: {text_file}")

        # 이미지 URL 출력
        images = [urljoin(base_url, img["src"]) for img in content_div.find_all("img") if img.get("src")]
        for img_url in images:
            print(f"📸 이미지 URL: {img_url}")
    else:
        print("❌ 본문 콘텐츠 없음")

    # ✅ 첨부파일 처리
    clip_div = soup.select_one("div.clip")
    if clip_div:
        for i, a_tag in enumerate(clip_div.find_all("a", href=True), start=1):
            file_url = urljoin(base_url, a_tag["href"])
            file_ext = os.path.splitext(file_url)[1]
            file_name = f"{keyword}_Page{idx}_File{i}{file_ext}"

            try:
                file_data = requests.get(file_url)
                file_path = os.path.join("download", file_name)

                with open(file_path, "wb") as f:
                    f.write(file_data.content)
                print(f"✅ 첨부파일 저장 완료: {file_path}")
            except Exception as e:
                print(f"❌ 첨부파일 다운로드 실패: {file_url} / 이유: {e}")
    else:
        print("📂 첨부파일 없음")
