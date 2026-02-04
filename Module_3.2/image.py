import os
import base64
from pathlib import Path
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv("API")

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

prompt = input("Введите промпт для изображения: ").strip()
if not prompt:
    prompt = "Красивый закат над горами, яркие цвета, стиль цифровой живописи"

response = openai.images.generate(
    model="gpt-image-1",
    prompt=prompt,
    size="1024x1024",
    n=1
)

image_data = response.data[0].b64_json
image_bytes = base64.b64decode(image_data)

output_path = OUTPUT_DIR / "image.png"
with open(output_path, "wb") as f:
    f.write(image_bytes)

print(f"Промпт: {prompt}")
print(f"Изображение сохранено в: {output_path.resolve()}")