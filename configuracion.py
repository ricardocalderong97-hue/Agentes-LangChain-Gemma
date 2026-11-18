"""Configuración común: Gemma 3 1B local con Ollama + trazabilidad opcional."""
import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent
load_dotenv(RAIZ / ".env")

# Sin API key de LangSmith, el proyecto funciona localmente sin enviar trazas.
if os.getenv("LANGSMITH_TRACING", "false").lower() == "true" and not os.getenv("LANGSMITH_API_KEY"):
    print("AVISO: LANGSMITH_API_KEY vacía. Desactivando las trazas de LangSmith.")
    os.environ["LANGSMITH_TRACING"] = "false"

MODELO_NOMBRE = os.getenv("OLLAMA_MODEL", "gemma3:1b")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def crear_modelo():
    """No requiere API de ningún proveedor comercial."""
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=MODELO_NOMBRE,
        base_url=OLLAMA_URL,
        temperature=0,
    )
