import requests
from bs4 import BeautifulSoup
import json
import urllib.parse

search_keyword = input("검색어를 입력하세요: ")

base_url = "https://www.gknu.ac.kr"
search_url = "https://www.gknu.ac.kr/search/search_detail.do"

params = {
    "search_type": "BOARD",
    "search_text": search_keyword,
    "start_date": "",
    "end_date": ""
}

res = requests.get(search_url, params=params)
res.encoding = 'utf-8'
soup = BeautifulSoup(res.text, "html.parser")

results = soup.select("li > p.tit > a")

data = []
seen = set()  # 중복 확인을 위한 집합

for a_tag in results:
    title = a_tag.get("title")
    href = a_tag.get("href")
    if not href.startswith("http"):
        post_url = urllib.parse.urljoin(base_url, href)
    else:
        post_url = href

    if post_url in seen:
        continue  # 같은 URL이면 패스
    seen.add(post_url)

    post_res = requests.get(post_url)
    post_res.encoding = 'utf-8'
    post_soup = BeautifulSoup(post_res.text, "html.parser")

    content_div = post_soup.select_one("div.board-view-cont")
    content = content_div.get_text(strip=True) if content_div else "본문을 찾을 수 없음"

    # 제목과 내용이 모두 동일한 경우도 중복으로 간주
    duplicate_check = f"{title}_{content}"
    if duplicate_check in seen:
        continue
    seen.add(duplicate_check)

    data.append({
        "title": title,
        "url": post_url,
        "content": content
    })

with open("gknu_results.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("크롤링 완료. 중복을 제거한 결과가 gknu_results.json 파일에 저장되었습니다.")
