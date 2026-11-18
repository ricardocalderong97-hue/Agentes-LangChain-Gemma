"""Opcional: create_agent del notebook con un Gemma 3 adaptado para tool calling.

PRIMERO ejecutar: ollama pull lukaspetrik/gemma3-tools:1b
No usa el modelo estándar gemma3:1b; es una variante comunitaria.
La calidad de tool calling de 1B puede variar. No está verificada aquí en vivo.
"""
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from herramientas import clima, multiplicar
from agentes import buscar_politicas
from configuracion import OLLAMA_URL

modelo_tools = ChatOllama(
    model="lukaspetrik/gemma3-tools:1b", base_url=OLLAMA_URL, temperature=0,
)

agente_clima_y_multiplicar = create_agent(
    model=modelo_tools, tools=[clima, multiplicar],
    system_prompt="Usa las herramientas para obtener el clima y hacer multiplicaciones. Responde en español.",
)
agente_rag = create_agent(
    model=modelo_tools, tools=[buscar_politicas],
    system_prompt="SIEMPRE busca en políticas antes de responder. Responde solamente con la evidencia. Si no la hay, dilo.",
)


if __name__ == "__main__":
    for titulo, agente, pregunta in [
        ("HERRAMIENTAS", agente_clima_y_multiplicar, "¿Qué clima hace en Cali? ¿Y cuánto es 23.5 por 4?"),
        ("RAG", agente_rag, "¿Cuántos días puedo trabajar remoto?"),
    ]:
        print(f"\n=== {titulo} (agente nativo LangChain) ===")
        r = agente.invoke({"messages": [{"role": "user", "content": pregunta}]})
        for mensaje in r["messages"]:
            mensaje.pretty_print()
