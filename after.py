import os
import json
import requests
import pytesseract
from PIL import Image

# ✅ LM Studio API 설정
api_base = "http://localhost:1234/api/v0/chat/completions"

# ✅ 이미지 OCR 처리
def ocr_image(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='eng+kor')
        return text
    except Exception as e:
        print(f"OCR 오류: {e}")
        return ""

# ✅ LM Studio에 메타데이터 요청
def extract_metadata_local(content: str):
    prompt = f"""
다음 공고문에서 가능한 모든 메타데이터를 JSON 형식으로 추출해줘:

- title
- announcement_date
- application_period
- education_period
- eligibility
- capacity
- tuition
- application_method
- required_documents
- contact
- required_conditions
- benefits
- all_content (크롤링한 전체 내용)

공고문 내용:
\"\"\"{content}\"\"\"

결과는 JSON 형식으로 출력하며, 정보가 없으면 빈 문자열("")로 넣어줘.
    """

    payload = {
        "model": "nous-hermes-2-mistral-7b-dpo",
        "messages": [
            {"role": "system", "content": "너는 공공기관 공고문 메타데이터 추출 전문가야."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 800
    }

    try:
        response = requests.post(api_base, json=payload)
        response.raise_for_status()
        reply = response.json()
        metadata_str = reply['choices'][0]['message']['content']
        return json.loads(metadata_str)
    except Exception as e:
        print(f"메타데이터 추출 오류: {e}")
        return {}

# ✅ 문자열인 경우만 strip 처리
def safe_strip(value):
    return value.strip() if isinstance(value, str) else ""

# ✅ 제목 키워드 기반 카테고리 추정
def guess_category(title: str) -> str:
    if "장학" in title or "학사" in title:
        return "학사"
    elif "도서관" in title or "식당" in title or "시설" in title:
        return "시설"
    elif "취업" in title or "채용" in title:
        return "취업"
    elif "해외" in title or "교환학생" in title:
        return "국제교류"
    else:
        return "기타"

# ✅ metadata.json 업데이트
def update_metadata(metadata_entry, metadata_path="metadata.json"):
    try:
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata_list = json.load(f)
        else:
            metadata_list = []

        if any(entry["filename"] == metadata_entry["filename"] for entry in metadata_list):
            print(f"중복 파일 스킵: {metadata_entry['filename']}")
            return

        max_id = max((entry["id"] for entry in metadata_list), default=0)
        metadata_entry["id"] = max_id + 1

        metadata_list.append(metadata_entry)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata_list, f, indent=2, ensure_ascii=False)
        print(f"metadata.json에 추가 완료: {metadata_entry['filename']}")
    except Exception as e:
        print(f"metadata.json 업데이트 중 오류: {e}")

# ✅ 메인 처리 함수
def process_files_in_directory(directory_path: str, image_directory: str):
    txt_files = [f for f in os.listdir(directory_path) if f.endswith(".txt")]
    image_files = [f for f in os.listdir(image_directory) if f.endswith((".jpg", ".png", ".jpeg"))]

    # ✅ .txt 파일 처리
    for txt_file in txt_files:
        file_path = os.path.join(directory_path, txt_file)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"파일 읽기 오류: {e}")
            continue

        metadata = extract_metadata_local(content)
        if not metadata:
            print(f"메타데이터 추출 실패: {txt_file}")
            continue

        json_output = os.path.join(directory_path, f"{os.path.splitext(txt_file)[0]}.json")
        with open(json_output, "w", encoding="utf-8") as out_f:
            json.dump(metadata, out_f, indent=2, ensure_ascii=False)

        # ✅ metadata.json용 데이터 구성
        title = safe_strip(metadata.get("title", ""))
        date = safe_strip(metadata.get("announcement_date", ""))
        contact = safe_strip(metadata.get("contact", ""))
        category = guess_category(title)

        update_metadata({
            "filename": txt_file,
            "title": title,
            "category": category,
            "date": date,
            "source": contact,
            "all_content": content.strip()  # ✅ 크롤링한 전체 내용 추가
        })

    # ✅ 이미지 파일 처리 (OCR만)
    for image_file in image_files:
        image_path = os.path.join(image_directory, image_file)
        text = ocr_image(image_path)
        if not text:
            continue

        print(f"\n🖼️ OCR 결과 - {image_file}:\n{text[:300]}...\n")

# ✅ 실행
if __name__ == "__main__":
    txt_dir = os.path.join(os.getcwd(), "contents")
    img_dir = os.path.join(os.getcwd(), "download")
    process_files_in_directory(txt_dir, img_dir)
