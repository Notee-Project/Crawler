import os
import json
import requests

# LM Studio API 설정
API_URL = "http://localhost:1234/api/v0/chat/completions"
MODEL_NAME = "nous-hermes-2-mistral-7b-dpo"

# 프롬프트 생성 함수
def build_prompt(content, filename):
    return f"""
아래는 대학교 공지사항 공고문 원문이야. 문장이나 줄바꿈이 깨져 있을 수도 있어.
해당 내용을 기반으로 아래 항목들을 추출해서 JSON 형태로 정리해줘.

반드시 다음 형식을 따르고, 그 외 설명이나 텍스트는 포함하지 마.
형식은 정확히 이대로 맞춰줘:

{{
  "title": "",
  "category": "",
  "date": "",
  "source": ""
}}

조건:
- title은 공고문의 제목
- category는 ['학사', '시설', '취업', '국제교류', '기타'] 중 유추
- date는 공고 게시일 (없으면 공고 내 명시된 날짜 활용)
- source는 공고를 낸 부서명 또는 기관명
- filename은 "{filename}" 으로 고정
- id는 자동 부여되므로 응답에 포함하지 마

다음은 공고문 전문이야:
\"\"\"{content}\"\"\"
"""

# LM Studio 호출 함수
def extract_metadata(content, filename):
    prompt = build_prompt(content, filename)
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "너는 공고문 메타데이터 추출 전문가야."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 1000
    }

    try:
        res = requests.post(API_URL, json=payload)
        res.raise_for_status()
        result = res.json()
        message = result['choices'][0]['message']['content']
        return json.loads(message)
    except Exception as e:
        print(f"❌ {filename} 처리 오류: {e}")
        return None

# 디렉토리 내 모든 .txt 파일 처리
def process_all_txt(input_dir="contents", output_filename="metadata.json"):
    all_entries = []
    txt_files = sorted([f for f in os.listdir(input_dir) if f.endswith(".txt")])

    for idx, filename in enumerate(txt_files, start=1):
        path = os.path.join(input_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        metadata = extract_metadata(content, filename)
        if metadata:
            metadata["id"] = idx
            metadata["filename"] = filename
            all_entries.append(metadata)

    # ✅ 파일 저장 위치: contents/metadata.json
    final_output = {"documents": all_entries}
    output_path = os.path.join(input_dir, output_filename)
    with open(output_path, "w", encoding="utf-8") as out_f:
        json.dump(final_output, out_f, indent=2, ensure_ascii=False)
    print(f"\n✅ 완료: 총 {len(all_entries)}개 문서 메타데이터를 '{output_path}'에 저장함.")

# 실행
if __name__ == "__main__":
    process_all_txt(input_dir="contents_07/contents", output_filename="metadata.json")
