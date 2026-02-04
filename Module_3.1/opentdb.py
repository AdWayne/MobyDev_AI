import requests
import html
import random

URL = "https://opentdb.com/api.php?amount=10&type=boolean"

resp = requests.get(URL)
data = resp.json()
questions = data["results"]



for i, q in enumerate(questions):
    text = html.unescape(q["question"])
    correct = html.unescape(q["correct_answer"])
    incorrect = [html.unescape(ans) for ans in q["incorrect_answers"]]
    
    options = incorrect + [correct]
    random.shuffle(options)

    print(f"\n{i+1}: {text}")
    for idx, opt in enumerate(options):
        print(f"  {idx+1}. {opt}")
    
    print(f"Правильный ответ: {correct}")