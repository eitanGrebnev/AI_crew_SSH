import os
from dotenv import load_dotenv

# Load env file from project root
ENV_PATH = os.getenv("AGENT_ENV", os.path.join(os.getcwd(), "agent.env"))
load_dotenv(ENV_PATH)

SSH_HOST = os.getenv("SSH_HOST", "")
SSH_USER = os.getenv("SSH_USER", "")
SSH_PASS = os.getenv("SSH_PASS", "")
SSH_PORT = int(os.getenv("SSH_PORT", "22"))
SSH_KEY_PATH = os.getenv("SSH_KEY_PATH")

COMPOSE_FILE = os.getenv("COMPOSE_FILE", "/opt/identity_stack/docker-compose.yml")
STACK_DIR = os.getenv("STACK_DIR", "/opt/identity_stack")

LLM_BACKEND = os.getenv("LLM_BACKEND", "lmstudio")
LMSTUDIO_ENDPOINT = os.getenv("LMSTUDIO_ENDPOINT", "http://localhost:1234")
LMSTUDIO_API_KEY = os.getenv("LMSTUDIO_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")

AUTH_URL = os.getenv("AUTH_URL", "")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
MAX_STEPS = int(os.getenv("MAX_STEPS", "3"))
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "120"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
