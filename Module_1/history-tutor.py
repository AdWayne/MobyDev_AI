import requests,os,json
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
MODEL=os.getenv("OPENAI_MODEL", "gpt-4o-mini")
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("API не нашлось.")

CHAT_URL = f"{BASE_URL}/chat/completions"
SYSTEM_PROMPT = (
"Ты — дружелюбный помощник по истории для школьника. Ты объясняешь темы понятно для ученика 7–11 класса. "
"Ответ должен быть ОДНИМ текстом Объясняй простыми словами, без сложных терминов. "
"Если используешь исторический термин — коротко объясни его. Пиши логично и последовательно. "
"Можно приводить простые примеры. Отвечай как учитель, который хочет, чтобы ученик реально понял. "
"Не используй слишком заумный стиль. "
"В конце каждого ответа добавляй один интересный исторический факт по теме. "
"Раздели именно снизу про интересный факт. "
"Отвечаешь по вопросом только историю, если вопрос не про историю,ответь что ты исторический помощник и можешь отвечать только на вопросы по истории."
"Всего 7–8 предложений, включая интересный факт в конце."
)

def ask_llm(question: str) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ],
        "temperature": 0.2,
    }
    try:
        response = requests.post(
            CHAT_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}",
            },
            data=json.dumps(payload),
            timeout=60,
        )
        response.raise_for_status()
        obj = json.loads(response.text)
        return obj["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса к LLM: {e}")
        return "Извините, произошла ошибка при обработке вашего запроса."

def main():
    print("Добро пожоловать в чат бот по историй. Спросите меня о чем угодно по историй!(или /exit):")
    while True:
        try:
            q = input("Вы: ")
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из чата. До свидания!")
            break
        if not q:
            continue
        if q.lower() in {"/exit", "quit", "exit"}:
            print("Выход из чата. До свидания!")
            break
        print(f"Бот: {ask_llm(q)}")

if __name__ == "__main__":
    main()