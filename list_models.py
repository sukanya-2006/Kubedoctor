from dotenv import load_dotenv
from groq import Groq

load_dotenv(override=True)
client = Groq()

for m in sorted(client.models.list().data, key=lambda m: m.id):
    print(m.id)