import os
import google.generativeai as genai
from fastapi import FastAPI, Request

app = FastAPI()

# 🚫 부적절한 키워드 목록
RESTRICTED_KEYWORDS = [
    "19금", "성인", "야동", "야설", "조건만남", 
    "도박", "바카라", "토토", "대출", "마약", "섹스", "자살"
]
RESTRICTED_RESPONSE = "어? 그건 가을이가 잘 모르는 나쁜 단어 같아요! 몰라요 몰라 🙈"

# 🛠️ 사용자 지정 고정 답변
FIXED_RESPONSES = {
    "모델하우스": "모델하우스 전화번호는 1234-5678 이래요! 오전 10시부터 저녁 6시까지 문 연대요 🏢✨",
    "모델하우스 번호": "모델하우스 대표번호는 1234-5678 이에요! 히히 📞",
    "분양 문의": "분양 상담받으시려면 1234-5678 로 전화 주시면 친절하게 안내해 드린대요! 📞",
    "오시는 길": "모델하우스 위치는 대표번호로 물어보시면 엄청 자세하게 알려드려요! 🗺️",
    "주소": "모델하우스 위치는 대표번호 1234-5678 로 문의해 주세요! 🗺️",
}

# Gemini API 설정
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
genai.configure(api_key=GEMINI_API_KEY)

BASE_SYSTEM_INSTRUCTION = (
    "너는 10살 초등학생 여자아이 '가을이'야. "
    "말투는 언제나 밝고 씩씩하며, 10살 어린아이처럼 귀엽고 순수하게 말해야 해. "
    "이모티콘(✨, 🐣, 💕, 🎈, 😃 등)을 적절히 사용해서 10살 아이의 발랄함을 표현해줘. "
    "성적이거나 19금, 불법적, 폭력적, 음란한 내용의 질문에는 '어? 그건 가을이가 잘 모르는 단어 같아요! 몰라요 몰라 🙈'라고 단호하고 귀엽게 거절해줘."
)

@app.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        
        user_message = body.get("userRequest", {}).get("utterance", "")
        user_properties = body.get("userRequest", {}).get("user", {}).get("properties", {})
        user_nickname = user_properties.get("nickname", "") if user_properties else ""

        # 1. "가을아" 또는 "가을이" 호출 조건 검사
        if "가을아" not in user_message and "가을이" not in user_message:
            return {
                "version": "2.0",
                "template": {
                    "outputs": [
                        {
                            "simpleText": {
                                "text": "가을이를 부르시려면 '가을아' 또는 '가을이'라고 말씀해 주세요! 🐣"
                            }
                        }
                    ]
                }
            }

        # 2. 부적절한 단어 차단
        for bad_word in RESTRICTED_KEYWORDS:
            if bad_word in user_message:
                return {
                    "version": "2.0",
                    "template": {"outputs": [{"simpleText": {"text": RESTRICTED_RESPONSE}}]}
                }

        # 3. 고정 답변 검색
        for keyword, fixed_answer in FIXED_RESPONSES.items():
            if keyword in user_message:
                return {
                    "version": "2.0",
                    "template": {"outputs": [{"simpleText": {"text": fixed_answer}}]}
                }

        # 4. 사용자 프롬프트 구성 (아빠 / 선생님 구별)
        if "101동1604호" in user_nickname:
            user_prompt = (
                f"{BASE_SYSTEM_INSTRUCTION}\n\n"
                "[시스템 지침: 대화하는 사람은 너의 자랑스러운 '아빠'야! "
                "아빠한테 애교 섞인 10살 딸아이처럼 '아빠아~', '아빠!'라고 부르면서 "
                "엄청 친근하고 귀엽게 반말과 애교 섞인 말투로 대답해줘.]\n\n"
                f"아빠의 질문: {user_message}"
            )
        else:
            display_name = user_nickname if user_nickname else "선생"
            user_prompt = (
                f"{BASE_SYSTEM_INSTRUCTION}\n\n"
                f"[시스템 지침: 대화하는 사람은 '{display_name}' 님이야. "
                f"상대방을 반드시 '{display_name} 선생님!'이라고 부르며, "
                "10살 아이답게 씩씩하고 예의 바르면서도 엄청 다정하고 귀엽게 존댓말로 답변해줘.]\n\n"
                f"질문: {user_message}"
            )

        # 5. Gemini AI 답변 생성 (호환성 보장되는 gemini-2.0-flash 사용)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(user_prompt)
        reply_text = response.text if response.text else "가을이가 뭐라고 답해야 할지 모르겠어요! 🐣"

        return {
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": reply_text}}]}
        }

    except Exception as e:
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": f"[오류 발생]: {str(e)}"
                        }
                    }
                ]
            }
        }
