import os
import sys
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("API"))
MODEL = os.getenv("MODEL", "gpt-4o-mini")

FUNCTIONS = [{
    "name": "generate_quiz",
    "description": "Генерирует школьный квиз по теме",
    "parameters": {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "grade_level": {"type": "string", "enum": ["K-3","4-6","7-9","10-12"]},
            "num_questions": {"type": "integer", "minimum":3, "maximum":20},
            "question_type": {"type": "string", "enum": ["mcq","short","mix"]},
            "language": {"type": "string", "enum": ["ru","kz"]},
        },
        "required": ["topic", "grade_level", "num_questions"],
        "strict": True
    }
}]

def generate_quiz(topic: str, grade_level: str, num_questions: int, question_type: str = "mix", language: str = "ru") -> str:
    system_prompt = "Ты строгий проверяющий и создатель викторин. Созвращай ТОЛЬКО JSON с вопросами викторины."
    user_prompt = f"""
topic: {topic}
grade_level: {grade_level}
num_questions: {num_questions}
question_type: {question_type}
language: {language}

Return JSON with:
- topic, grade_level
- items: list of {{
    id:int, q:str, type:"mcq"|"short",
    options:[str] (only if mcq), answer:str}}
- answer_key: list of {{id:int, answer:str}}
""".strip()

    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": user_prompt}],
        temperature=0.2
    )

    text = r.choices[0].message.content.strip()
    return text

AVAILABLE = {"generate_quiz": generate_quiz}
SYSTEM = "Ты - ассистент учителя. Если нужно, вызывай инструмент generate_quiz. Уточняй недостающие параметры."

def ask(user_text: str) -> str:
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_text}]

    r1 = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        functions=FUNCTIONS,
        function_call="auto",
        temperature=0
    )

    m1 = r1.choices[0].message

    if not getattr(m1, "function_call", None):
        return m1.content or ""
    
    fn_name = m1.function_call.name
    raw_args = m1.function_call.arguments or "{}"
    try:
        args = json.loads(raw_args)
    except json.JSONDecodeError:
        args = {}

    fn = AVAILABLE.get(fn_name)
    if not fn:
        return "Извините, этот инструмент не поддерживается."
    
    result_json = fn(**args)
    
    messages.append({"role": "assistant", "content": None,
                     "function_call": {"name": fn_name, "arguments": raw_args}})
    messages.append({"role": "function", "name": fn_name, "content": result_json})

    r2 = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0
    )
    return r2.choices[0].message.content

if __name__ == "__main__":
    print("Привет! Я помогу тебе создать викторину. Просто скажи мне тему и другие детали.")
    try:
        while True:
            q = input("> ").strip()
            if q:
                print(ask(q))  
    except KeyboardInterrupt:
        print("\nПока!")
