import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("Models your key can use:")
for m in client.models.list():
    print(" ", m.name)

model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
r = client.models.generate_content(model=model, contents="Reply with the word OK")
print("\nTest with", model, "->", r.text)
