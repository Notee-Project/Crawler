import os
import json
import re

# 정규화 함수
def normalize_text(text):
    text = text.replace('\n', ' ')
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'\s+([.,!?])', r'\1', text)
    text = re.sub(r'([.,!?])\s+', r'\1 ', text)
    text = re.sub(r'([「『(])\s+', r'\1', text)
    text = re.sub(r'\s+([」』)])', r'\1', text)
    return text.strip()

# 폴더 경로
input_dir = "contents"
output_dir = "Crawler/json"

# 출력 폴더가 없으면 생성
os.makedirs(output_dir, exist_ok=True)

# 모든 .txt 파일 처리
for filename in os.listdir(input_dir):
    if filename.endswith(".txt"):
        input_path = os.path.join(input_dir, filename)
        output_filename = filename.replace(".txt", ".json")
        output_path = os.path.join(output_dir, output_filename)

        # 파일 읽고 정규화
        with open(input_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
            normalized = normalize_text(raw_text)

        # JSON 형식으로 저장
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "filename": filename,
                "content": normalized
            }, f, ensure_ascii=False, indent=2)

print("✅ 모든 txt 파일이 정규화되어 JSON으로 저장되었습니다.")



