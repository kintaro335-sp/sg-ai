import os
from dotenv import load_dotenv
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")

MONGO_DATABASE = os.getenv("MONGO_DATABASE", "sgai")

# provider ai

AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
