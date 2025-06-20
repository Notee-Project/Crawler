import os
import json
import requests
import pytesseract
from PIL import Image

# LM Studio 로컬 API 설정
api_base = "http://localhost:1234/api/v0/chat/completions"  # LM Studio OpenAI API 포트

# 이미지에서 텍스트 추출하는 함수 (OCR)
def ocr_image(image_path):
    """이미지에서 텍스트 추출"""
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='eng')  # 영어 텍스트 인식
        return text
    except Exception as e:
        print(f"OCR 처리 중 오류 발생: {e}")
        return ""

def extract_metadata_local(content: str):
    prompt = f"""
다음 공고문에서 가능한 모든 메타데이터를 JSON 형식으로 추출해줘:

- title (공지사항 제목)
- announcement_date (공고일)
- application_period (신청 기간)
- education_period (교육 기간)
- eligibility (지원 자격)
- capacity (모집 인원)
- tuition (학비)
- application_method (신청 방법)
- required_documents (필요 서류)
- contact (연락처)
- required_conditions (필수 조건)
- benefits (혜택)

공고문 내용:
\"\"\"{content}\"\"\"

결과는 JSON 형식으로 출력하며, 정보가 없으면 빈 문자열("")로 넣어줘.
    """
    
    # LM Studio API 호출
    payload = {
        "model": "llama3",  # LM Studio에서 실행 중인 모델 이름과 일치해야 함
        "messages": [
            {"role": "system", "content": "너는 공공기관 공고문에서 가능한 모든 정보를 정확히 추출하는 전문가야."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 500
    }

    try:
        # API 요청
        response = requests.post(api_base, json=payload)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        
        reply = response.json()  # JSON 응답 받기
        metadata_str = reply['choices'][0]['message']['content']
        
        # JSON 형식으로 파싱 (문자열이 JSON 형식이므로 파싱 필요)
        try:
            metadata = json.loads(metadata_str)  # 텍스트를 JSON으로 변환
            return metadata
        except json.JSONDecodeError:
            print(f"메타데이터 파싱 실패: {metadata_str}")
            return {}
    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류 발생: {e}")
        return {}

def process_files_in_directory(directory_path: str, image_directory: str):
    # .txt 파일과 이미지 파일 처리
    txt_files = [f for f in os.listdir(directory_path) if f.endswith(".txt")]
    image_files = [f for f in os.listdir(image_directory) if f.endswith((".jpg", ".png", ".jpeg"))]

    if not txt_files and not image_files:
        print("디렉토리에 처리할 .txt 파일과 이미지 파일이 없습니다.")
        return

    for txt_file in txt_files:
        file_path = os.path.join(directory_path, txt_file)
        
        # 텍스트 파일 내용 읽기
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"파일을 찾을 수 없습니다: {file_path}")
            continue
        except Exception as e:
            print(f"파일을 읽는 중 오류 발생: {e}")
            continue

        # 메타데이터 추출
        metadata = extract_metadata_local(content)
        
        if not metadata:
            print(f"파일: {txt_file}에서 메타데이터를 추출할 수 없습니다.")
            continue
        
        # 추출된 메타데이터를 해당 파일명으로 JSON 파일로 저장
        output_file = os.path.join(directory_path, f"{os.path.splitext(txt_file)[0]}.json")
        try:
            with open(output_file, "w", encoding="utf-8") as output_f:
                json.dump(metadata, output_f, indent=2, ensure_ascii=False)
            print(f"파일: {txt_file}의 메타데이터가 {output_file}에 저장되었습니다.")
        except Exception as e:
            print(f"파일 저장 중 오류 발생: {e}")
    
    # 이미지 파일 처리
    for image_file in image_files:
        image_path = os.path.join(image_directory, image_file)
        
        # 이미지에서 텍스트 추출
        image_text = ocr_image(image_path)
        
        # OCR로 추출한 텍스트 출력
        print(f"이미지: {image_file}에서 추출된 OCR 텍스트:\n")
        print(image_text)
        
        if not image_text:
            print(f"이미지: {image_file}에서 OCR 텍스트를 추출할 수 없습니다.")
            continue
        
        # OCR로 추출한 텍스트로 메타데이터 추출
        metadata = extract_metadata_local(image_text)
        
        if not metadata:
            print(f"이미지: {image_file}에서 메타데이터를 추출할 수 없습니다.")
            continue
        
        # 추출된 메타데이터와 내용을 포함하여 저장
        output_file = os.path.join(image_directory, f"{os.path.splitext(image_file)[0]}.json")
        try:
            with open(output_file, "w", encoding="utf-8") as output_f:
                json.dump({
                    "file_name": image_file,
                    "content": image_text,  # OCR로 추출된 텍스트
                    "metadata": metadata  # 추출된 메타데이터
                }, output_f, indent=2, ensure_ascii=False)
            print(f"이미지: {image_file}의 메타데이터가 {output_file}에 저장되었습니다.")
        except Exception as e:
            print(f"파일 저장 중 오류 발생: {e}")

# 상대 경로 설정
directory_path = os.path.join(os.getcwd(), "contents")  # 현재 작업 디렉토리에서 상대 경로 사용
image_directory = os.path.join(os.getcwd(), "download")  # 이미지 파일이 있는 download 폴더

# 파일 처리
process_files_in_directory(directory_path, image_directory)
