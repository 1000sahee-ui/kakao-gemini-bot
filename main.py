import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai
from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()
executor = ThreadPoolExecutor(max_workers=5)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

if GEMINI_API_KEY:
    # client_options를 명시하여 인증 방식 오류(401) 및 엔드포인트 혼선 방지
    genai.configure(
        api_key=GEMINI_API_KEY,
        client_options={"api_endpoint": "generativelanguage.googleapis.com"}
    )

RESTRICTED_KEYWORDS = ["19금", "성인", "야동", "야설", "조건만남", "도박", "바카라", "토토", "대출", "마약", "섹스", "자살"]
RESTRICTED_RESPONSE = "어? 그건 가을이가 잘 모르는 나쁜 단어 같아요! 몰라요 몰라 🙈"

FIXED_RESPONSES = {
    "모델하우스": "모델하우스 전화번호는 1234-5678 이래요! 오전 10시부터 저녁 6시까지 문 연대요 🏢✨",
    "모델하우스 번호": "모델하우스 대표번호는 1234-5678 이에요! 히히 📞",
    "분양 문의": "분양 상담받으시려면 1234-5678 로 전화 주시면 친절하게 안내해 드린대요! 📞",
    "오시는 길": "모델하우스 위치는 대표번호로 물어보시면 엄청 자세하게 알려드려요! 🗺️",
    "주소": "모델하우스 위치는 대표번호 1234-5678 로 문의해 주세요! 🗺️",
}

BASE_INSTRUCTION = (
    "너는 10살 초등학생 여자아이 '가을이'야. "
    "밝고 씩씩하며 귀엽고 순수하게 말해줘. 이모티콘을 적절히 사용해주고, "
    "카카오톡 대화니까 답변은 무조건 2문장 이내로 아주 짧게 핵심만 말해줘."
)

def call_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return "❌ [오류]: GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다!"
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip()
        return "가을이가 뭐라고 답해야 할지 모르겠어요! 🐣"
    except Exception as e:
        return f"가을이 머리가 아파요! (오류: {str(e)})"

@app.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        user_message = body.get("userRequest", {}).get("utterance", "")
        user_properties = body.get("userRequest", {}).get("user", {}).get("properties", {})
        user_nickname = user_properties.get("nickname", "") if user_properties else ""

        # 1. 금지어 검사
        for bad_word in RESTRICTED_KEYWORDS:
            if bad_word in user_message:
                return {
                    "version": "2.0",
                    "template": {"outputs": [{"simpleText": {"text": RESTRICTED_RESPONSE}}]}
                }

        # 2. 고정 답변 검사
        for keyword, fixed_answer in FIXED_RESPONSES.items():
            if keyword in user_message:
                return {
                    "version": "2.0",
                    "template": {"outputs": [{"simpleText": {"text": fixed_answer}}]}
                }

        # 3. 호출어 검사
        if "가을아" not in user_message and "가을이" not in user_message:
            return {
                "version": "2.0",
                "template": {"outputs": [{"simpleText": {"text": "가을이를 부르시려면 '가을아' 또는 '가을이'라고 말씀해 주세요! 🐣"}}]}
            }

        # 4. 프롬프트 구성
        if "101동1604호" in user_nickname:
            full_prompt = f"{BASE_INSTRUCTION}\n상대방: 너의 아빠\n말투: 애교 섞인 10살 딸아이 반말\n질문: {user_message}"
        else:
            display_name = user_nickname if user_nickname else "선생"
            full_prompt = f"{BASE_INSTRUCTION}\n상대방: {display_name} 선생님\n말투: 예의바르고 귀여운 존댓말\n질문: {user_message}"

        # 5. 비동기 실행 (3.8초 타임아웃)
        loop = asyncio.get_running_loop()
        reply_text = await asyncio.wait_for(
            loop.run_in_executor(executor, call_gemini, full_prompt),
            timeout=3.8
        )

        return {
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": reply_text}}]}
        }

    except asyncio.TimeoutError:
        return {
            "version": "2.0",
            "template": {
                "outputs": [{"simpleText": {"text": "가을이가 생각하는 데 시간이 조금 걸려요! 다시 한번 말씀해 주세요 🐣"}}]
            }
        }
    except Exception as e:
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": f"가을이가 잠깐 딴생각을 했나 봐요! 다시 말해 주실래요? 🐣\n(에러: {str(e)})"
                        }
                    }
                ]
            }
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
