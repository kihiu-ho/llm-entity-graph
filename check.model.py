import os

from dotenv import load_dotenv
from openai import OpenAI
# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_BASE_URL"))
print([m.id for m in client.models.list().data])