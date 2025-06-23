import os
import requests
import pytesseract
from PIL import Image

# LM Studio 로컬 API 설정
api_base = "http://localhost:1234/api/v0/chat/completions"

# 이미지에서 텍스트 추출
def ocr_image(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='eng')
        return text
    except Exception as e:
        print(f"OCR 처리 중 오류 발생: {e}")
        return ""

# LM Studio에게 텍스트 복원 요청
def restore_text(content: str):
    prompt = f"""
아래는 줄바꿈이 이상하거나 단어가 중간에 띄어져서 깨진 상태의 공고문 텍스트야.  
이 텍스트를 사람이 읽을 수 있는 형태로 **복원**해줘.

🛠️ 지켜야 할 규칙:
- 단어가 띄어져 있거나 줄이 중간에 끊긴 경우, 자연스럽게 붙이거나 이어줘  
예: "교 육 비" → "교육비", "공 고 문" → "공고문"
- 문장 단위로 줄바꿈을 해줘 (의미 없는 줄바꿈 제거)
- 리스트(1., 2., 3. 등)나 항목 구조는 유지하되, 들여쓰기나 서식은 보기 좋게 정리
- 내용은 **절대 요약하거나 삭제하지 말고 그대로 복원**해
- 최종 결과는 보기 좋은 공고문 텍스트 (.txt 형태)로 출력해줘

\"\"\"  
{content}  
\"\"\"
"""

    payload = {
        "model": "llama3",
        "messages": [
            {"role": "system", "content": "너는 공고문 복원 전문가야."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1500
    }

    try:
        response = requests.post(api_base, json=payload)
        response.raise_for_status()
        reply = response.json()
        restored_text = reply['choices'][0]['message']['content']
        return restored_text
    except Exception as e:
        print(f"LM Studio 요청 오류: {e}")
        return ""

# 메인 처리
def process_files_in_directory(directory_path: str, image_directory: str):
    txt_files = [f for f in os.listdir(directory_path) if f.endswith(".txt")]
    image_files = [f for f in os.listdir(image_directory) if f.endswith((".jpg", ".png", ".jpeg"))]

    # ✅ 텍스트 파일 처리
    for txt_file in txt_files:
        file_path = os.path.join(directory_path, txt_file)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"파일 읽기 오류: {e}")
            continue

        restored = restore_text(content)
        if restored:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(restored)
                print(f"복원 완료: {txt_file}")
            except Exception as e:
                print(f"복원된 텍스트 저장 실패: {e}")
        else:
            print(f"복원 실패: {txt_file}")

    # ✅ 이미지 파일 OCR 후 복원
    for image_file in image_files:
        image_path = os.path.join(image_directory, image_file)
        text = ocr_image(image_path)
        if not text:
            continue

        restored = restore_text(text)
        if restored:
            output_txt = os.path.join(image_directory, f"{os.path.splitext(image_file)[0]}.txt")
            try:
                with open(output_txt, "w", encoding="utf-8") as f:
                    f.write(restored)
                print(f"OCR 복원 저장 완료: {image_file} → {output_txt}")
            except Exception as e:
                print(f"OCR 저장 오류: {e}")
        else:
            print(f"OCR 복원 실패: {image_file}")

# 실행
if __name__ == "__main__":
    directory_path = os.path.join(os.getcwd(), "contents_07/contents")
    image_directory = os.path.join(os.getcwd(), "contents_07/download")
    process_files_in_directory(directory_path, image_directory)
