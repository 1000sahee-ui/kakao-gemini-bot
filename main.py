import os
import google.generativeai as genai
from fastapi import FastAPI, Request

app = FastAPI()

# ==============================================================================
# 🚫 [19금 / 부적절한 질문 차단 키워드 목록]
# ==============================================================================
RESTRICTED_KEYWORDS = [
    "19금",
    "성인",
    "야동",
    "야설",
    "조건만남",
    "도박",
    "바카라",
    "토토",
    "대출",
    "마약",
    "섹스",
    "자살",
]

RESTRICTED_RESPONSE = "어? 그건 가을이가 잘 모르는 나쁜 단어 같아요! 몰라요 몰라 🙈"

# ==============================================================================
# 🛠️ [사용자 지정 답변 설정 구역]
# ==============================================================================
FIXED_RESPONSES = {
    # 예시 1: 모델하우스 번호 관련 질문
    "모델하우스": "모델하우스 전화번호는 1234-5678 이래요! 오전 10시부터 저녁 6시까지 문 연대요 🏢✨",
    "모델하우스 번호": "모델하우스 대표번호는 1234-5678 이에요! 히히 📞",
    "분양 문의": "분양 상담받으시려면 1234-5678 로 전화 주시면 친절하게 안내해 드린대요! 📞",
    # 예시 2: 위치/주소 질문
    "오시는 길": "모델하우스 위치는 대표번호로 물어보시면 엄청 자세하게 알려드려요! 🗺️",
    "주소": "모델하우스 위치는 대표번호 1234-5678 로 문의해 주세요! 🗺️",
}

# ==============================================================================
# Gemini API 및 10살 가을이 말투 설정
# ==============================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# 10살 아이 페르소나 지침
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
        user_message = body["userRequest"]["utterance"]  # 카톡 사용자 입력값

        # 발송자 정보 추출
        user_properties = (
            body.get("userRequest", {}).get("user", {}).get("properties", {})
        )
        user_nickname = user_properties.get("nickname", "")

        # 1. "가을아" 또는 "가을이" 트리거 검사
        if "가을아" not in user_message and "가을이" not in user_message:
            return {"version": "2.0", "template": {"outputs": []}}

        # 2. 부적절한 단어(19금/규정 위반 키워드) 사전 차단
        for bad_word in RESTRICTED_KEYWORDS:
            if bad_word in user_message:
                return {
                    "version": "2.0",
                    "template": {
                        "outputs": [
                            {"simpleText": {"text": RESTRICTED_RESPONSE}}
                        ]
                    },
                }

        # 3. 지정된 고정 답변 검색
        for keyword, fixed_answer in FIXED_RESPONSES.items():
            if keyword in user_message:
                return {
                    "version": "2.0",
                    "template": {
                        "outputs": [{"simpleText": {"text": fixed_answer}}]
                    },
                }

        # 4. 발송자에 따른 호칭 및 10살 아이 말투 지침 적용
        if "101동1604호" in user_nickname or user_nickname == "101동1604호":
            user_prompt = (
                f"[시스템 지침: 대화하는 사람은 너의 자랑스러운 '아빠'야! "
                f"아빠한테 애교 섞인 10살 딸아이처럼 '아빠아~', '아빠!'라고 부르면서 "
                f"엄청 친근하고 귀엽게 반말과 애교 섞인 말투로 대답해줘.]\n\n"
                f"아빠의 질문: {user_message}"
            )
        else:
            display_name = user_nickname if user_nickname else "회원"
            user_prompt = (
                f"[시스템 지침: 대화하는 사람은 '{display_name}' 님이야. "
                f"상대방을 반드시 '{display_name} 선생님!'이라고 부르며, "
                f"10살 아이답게 씩씩하고 예의 바르면서도 엄청 다정하고 귀엽게 존댓말로 답변해줘.]\n\n"
                f"선생님의 질문: {user_message}"
            )

        # 5. Gemini AI 답변 생성
        model = genai.GenerativeModel(
            "gemini-1.5-flash", system_instruction=BASE_SYSTEM_INSTRUCTION
        )
        response = model.generate_content(user_prompt)
        reply_text = response.text

        return {
            "version": "2.0",
            "template": {
                "outputs": [{"simpleText": {"text": reply_text}}]
            },
        }

    except Exception as e:
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "가을이가 머리가 머쓱해요 😥 잠시 오류가 생겼나 봐요!"
                        }
                    }
                ]
            },
        }
