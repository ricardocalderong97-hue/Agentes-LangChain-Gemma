"""Ejercicios del notebook (puntos 6 y 7) + traductor con Gemma 3 1B.

IMPORTANTE: el modelo gemma3:1b estándar no tiene llamadas nativas fiables a tools.
Por eso los grafos ejecutan las herramientas de manera explícita: evitan el error
'Ollama ... does not support tools'. El LLM local redacta la respuesta final.
Esta variante es una ORQUESTACIÓN de agentes, no un agente autónomo de tool calling.
"""
import re
import unicodedata
from typing import TypedDict

from langchain.tools import tool
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.retrievers import BM25Retriever
from langgraph.graph import StateGraph, START, END
from langsmith import traceable

from configuracion import RAIZ, crear_modelo
from herramientas import clima, multiplicar

modelo = crear_modelo()

# ---------------- 6. HERRAMIENTAS Y AGENTES ----------------
class EstadoHerramientas(TypedDict, total=False):
    pregunta: str
    resultados_herramientas: list[str]
    respuesta: str


PATRON_MULTIPLICACION = re.compile(
    r"(-?\d+(?:[.,]\d+)?)\s*(?:por|[x×*]|multiplicado\s+por)\s*(-?\d+(?:[.,]\d+)?)",
    flags=re.IGNORECASE,
)
PATRON_CIUDAD = re.compile(
    r"\b(?:en|de)\s+([a-záéíóúüñ]+(?:\s+[a-záéíóúüñ]+){0,2}?)"
    r"(?=\s*(?:[?¿,;.]|\s+y\b|\s+cu[aá]nto\b|$))",
    flags=re.IGNORECASE,
)


def detectar_ciudad(pregunta: str) -> str | None:
    """Extracción simple para este tutorial (no es NER completo)."""
    m = PATRON_CIUDAD.search(pregunta)
    return m.group(1).strip() if m else None


def ejecutar_herramientas(estado: EstadoHerramientas):
    pregunta = estado["pregunta"]
    resultados: list[str] = []
    texto = pregunta.lower()

    if re.search(r"\b(clima|tiempo|temperatura|pron[oó]stico)\b", texto):
        ciudad = detectar_ciudad(pregunta)
        if ciudad:
            resultados.append(clima.invoke({"ciudad": ciudad}))
        else:
            resultados.append("Falta la ciudad para consultar el clima; pídela al usuario.")

    encontrados = list(PATRON_MULTIPLICACION.finditer(pregunta))
    for m in encontrados:
        a = float(m.group(1).replace(",", "."))
        b = float(m.group(2).replace(",", "."))
        valor = multiplicar.invoke({"a": a, "b": b})
        resultados.append(f"Multiplicación EXACTA: {a:g} × {b:g} = {valor:g}.")

    if not resultados:
        resultados.append("No detecté una consulta de clima ni una multiplicación a × b.")
    return {"resultados_herramientas": resultados}


prompt_herramientas = ChatPromptTemplate.from_messages([
    ("system", "Eres un asistente en español. Resume brevemente los RESULTADOS DE "
               "HERRAMIENTAS suministrados. Los números y mediciones deben copiarse "
               "tal como están. No inventes valores ni supongas que datos simulados son reales."),
    ("human", "Solicitud: {pregunta}\nResultados de herramientas:\n{resultados}"),
])
cadena_herramientas = prompt_herramientas | modelo | StrOutputParser()


def responder_herramientas(estado: EstadoHerramientas):
    resultados = estado["resultados_herramientas"]
    if resultados == ["No detecté una consulta de clima ni una multiplicación a × b."]:
        return {"respuesta": "Pídeme el clima en una ciudad o una multiplicación, por ejemplo '23.5 por 4'."}
    return {"respuesta": cadena_herramientas.invoke({
        "pregunta": estado["pregunta"], "resultados": "\n".join(resultados)
    })}


def crear_agente_herramientas():
    grafo = StateGraph(EstadoHerramientas)
    grafo.add_node("usar_herramientas", ejecutar_herramientas)
    grafo.add_node("responder_con_gemma", responder_herramientas)
    grafo.add_edge(START, "usar_herramientas")
    grafo.add_edge("usar_herramientas", "responder_con_gemma")
    grafo.add_edge("responder_con_gemma", END)
    return grafo.compile()


agente_herramientas = crear_agente_herramientas()


@traceable(name="Punto_6_agente_clima_multiplicar", run_type="chain")
def consultar_herramientas(pregunta: str) -> dict:
    return agente_herramientas.invoke({"pregunta": pregunta})


# ---------------- 7. RAG BÁSICO CON BM25 ----------------
RUTA_POLITICAS = RAIZ / "datos" / "politicas_ejemplo.txt"
lineas = [x.strip() for x in RUTA_POLITICAS.read_text(encoding="utf-8").splitlines() if x.strip()]
documentos = [Document(page_content=x, metadata={"fuente": RUTA_POLITICAS.name}) for x in lineas]
retriever = BM25Retriever.from_documents(documentos, k=min(2, len(documentos)))

STOPWORDS = {
    "a", "al", "con", "como", "cual", "cuales", "cuanto", "cuantos", "cuanta", "cuantas",
    "de", "del", "el", "en", "es", "esta", "hace", "hacer", "hay", "la", "las", "lo",
    "los", "me", "mi", "mis", "para", "por", "puedo", "que", "se", "si", "son", "su",
    "tengo", "un", "una", "unos", "unas", "y", "yo", "dias", "dia", "empresa",
}


def palabras_relevantes(texto: str) -> set[str]:
    normalizado = unicodedata.normalize("NFD", texto.lower())
    normalizado = "".join(c for c in normalizado if unicodedata.category(c) != "Mn")
    return {p for p in re.findall(r"[a-z0-9]+", normalizado) if p not in STOPWORDS and len(p) > 2}


@tool
def buscar_politicas(consulta: str) -> str:
    """Recupera fragmentos de las políticas ficticias de la empresa usando BM25."""
    candidatos = retriever.invoke(consulta)
    palabras = palabras_relevantes(consulta)
    pertinentes = [d for d in candidatos if palabras & palabras_relevantes(d.page_content)]
    if not pertinentes:
        return "SIN_EVIDENCIA"
    return "\n".join(f"[Fuente: {d.metadata['fuente']}] {d.page_content}" for d in pertinentes)


class EstadoRAG(TypedDict, total=False):
    pregunta: str
    contexto: str
    respuesta: str


def recuperar(estado: EstadoRAG):
    return {"contexto": buscar_politicas.invoke({"consulta": estado["pregunta"]})}


prompt_rag = ChatPromptTemplate.from_messages([
    ("system", "Responde en español SOLO con la evidencia de CONTEXTO. Estas políticas son "
               "FICTICIAS del tutorial, no normas laborales reales. Si no hay información "
               "suficiente, responde 'No tengo esa información en los documentos'. "
               "No inventes políticas, cifras ni fechas."),
    ("human", "CONTEXTO:\n{contexto}\n\nPREGUNTA: {pregunta}"),
])
cadena_rag = prompt_rag | modelo | StrOutputParser()


def responder_rag(estado: EstadoRAG):
    if estado["contexto"] == "SIN_EVIDENCIA":
        return {"respuesta": "No tengo esa información en los documentos."}
    respuesta = cadena_rag.invoke({"contexto": estado["contexto"], "pregunta": estado["pregunta"]})
    return {"respuesta": f"{respuesta}\n\nFuente: {RUTA_POLITICAS.name} (datos de ejemplo)."}


def crear_agente_rag():
    grafo = StateGraph(EstadoRAG)
    grafo.add_node("buscar_documentos_BM25", recuperar)
    grafo.add_node("responder_con_gemma", responder_rag)
    grafo.add_edge(START, "buscar_documentos_BM25")
    grafo.add_edge("buscar_documentos_BM25", "responder_con_gemma")
    grafo.add_edge("responder_con_gemma", END)
    return grafo.compile()


agente_rag = crear_agente_rag()


@traceable(name="Punto_7_agente_RAG", run_type="chain")
def consultar_rag(pregunta: str) -> dict:
    return agente_rag.invoke({"pregunta": pregunta})


# ---------------- 8. TRADUCTOR (ADICIÓN DEL ESTUDIANTE) ----------------
prompt_traductor = ChatPromptTemplate.from_messages([
    ("system", "Eres un traductor profesional. Traduce del idioma {origen} al {destino}. "
               "Devuelve SOLAMENTE el texto traducido, sin comentarios. Conserva nombres, "
               "cifras, tono y significado."),
    ("human", "{texto}"),
])
cadena_traductor = prompt_traductor | modelo | StrOutputParser()


@traceable(name="Agente_traductor_con_Gemma", run_type="chain")
def traducir(texto: str, origen: str = "español", destino: str = "inglés") -> str:
    return cadena_traductor.invoke({"texto": texto, "origen": origen, "destino": destino})
