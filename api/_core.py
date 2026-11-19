"""연구 질문 코치의 핵심 로직.

파일명이 밑줄(_)로 시작하므로 Vercel은 이 파일을 별도 엔드포인트로 배포하지 않는다.
엔드포인트는 api/coach.py 이며, 이 모듈의 handle()을 호출한다.
"""
import json
import os

MAX_FIELD = 60
MAX_KEYWORDS = 200
LEVELS = {"학부": "학부 졸업논문", "석사": "석사 학위논문", "박사": "박사 학위논문"}
DEFAULT_MODEL = "gemini-2.5-flash"
TIMEOUT_SECONDS = 20

SYSTEM_PROMPT = (
    "당신은 대학원 연구 지도 경험이 풍부한 연구 방법론 코치입니다. "
    "사용자가 준 전공 분야와 관심 키워드를 바탕으로 연구 질문 후보를 제안합니다. "
    "존재하지 않는 논문이나 저자를 만들어 내지 않습니다. "
    "반드시 아래 JSON 형식만 출력하고, 다른 문장은 쓰지 않습니다.\n"
    '{"questions":[{"question":"연구 질문","why":"이 질문이 의미 있는 이유 한 문장"}],'
    '"keywords":["문헌 검색용 키워드"],"caution":"범위가 넓거나 좁을 때의 주의점 한 문장"}\n'
    "questions는 정확히 3개, keywords는 5개에서 8개로 작성하고, 한국어로 답합니다."
)


def validate(payload):
    """입력을 검증한다. (오류 메시지 또는 None, 정리된 입력)을 돌려준다."""
    if not isinstance(payload, dict):
        return "요청 형식이 올바르지 않습니다.", None
    field = str(payload.get("field", "")).strip()
    keywords = str(payload.get("keywords", "")).strip()
    level = str(payload.get("level", "석사")).strip()
    if not field or not keywords:
        return "필수값을 입력하세요. 전공 분야와 관심 키워드가 모두 필요합니다.", None
    if len(field) > MAX_FIELD:
        return f"전공 분야는 {MAX_FIELD}자 이하로 입력하세요.", None
    if len(keywords) > MAX_KEYWORDS:
        return f"관심 키워드는 {MAX_KEYWORDS}자 이하로 입력하세요.", None
    if level not in LEVELS:
        level = "석사"
    return None, {"field": field, "keywords": keywords, "level": level}


def build_user_prompt(data):
    return (
        f"학위 과정: {LEVELS[data['level']]}\n"
        f"전공 분야: {data['field']}\n"
        f"관심 키워드: {data['keywords']}"
    )


def parse_model_text(text):
    """모델 출력에서 JSON을 추출한다. 실패하면 None."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        obj = json.loads(text[start : end + 1])
    except ValueError:
        return None
    questions = obj.get("questions")
    if not isinstance(questions, list) or not questions:
        return None
    return {
        "questions": [
            {"question": str(q.get("question", "")), "why": str(q.get("why", ""))}
            for q in questions
            if isinstance(q, dict)
        ][:3],
        "keywords": [str(k) for k in obj.get("keywords", [])][:8],
        "caution": str(obj.get("caution", "")),
    }


def call_gemini(user_prompt, api_key, model, timeout=TIMEOUT_SECONDS):
    """Google Gemini API(generateContent)를 호출해 텍스트를 돌려준다."""
    import requests  # 지연 import: 단위 테스트에서는 필요 없다.

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    resp = requests.post(url, json=body, headers={"x-goog-api-key": api_key}, timeout=timeout)
    resp.raise_for_status()
    parts = resp.json()["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts)


def handle(payload, caller=call_gemini, env=None):
    """(HTTP 상태 코드, 응답 딕셔너리)를 돌려준다. caller는 테스트에서 교체한다."""
    env = os.environ if env is None else env
    error, data = validate(payload)
    if error:
        return 400, {"error": error}
    api_key = env.get("GEMINI_API_KEY")
    if not api_key:
        return 500, {"error": "서버 설정이 완료되지 않았습니다. 관리자에게 문의하세요."}
    model = env.get("GEMINI_MODEL", DEFAULT_MODEL)
    try:
        text = caller(build_user_prompt(data), api_key, model)
    except Exception:  # 키와 내부 오류 내용을 사용자에게 노출하지 않는다.
        return 502, {"error": "AI 서비스 호출에 실패했습니다. 잠시 후 다시 시도하세요."}
    result = parse_model_text(text)
    if result is None:
        return 502, {"error": "AI 응답을 해석하지 못했습니다. 다시 시도하세요."}
    return 200, result
