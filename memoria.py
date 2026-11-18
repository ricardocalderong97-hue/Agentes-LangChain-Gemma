"""Punto 10 (opcional): memoria conversacional en un grafo local."""
from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from configuracion import crear_modelo


class EstadoConversacion(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def crear_agente_memoria():
    modelo = crear_modelo()

    def responder(estado: EstadoConversacion):
        mensajes = [SystemMessage(content="Eres un asistente amable. Responde en español.")]
        mensajes.extend(estado["messages"])
        return {"messages": [modelo.invoke(mensajes)]}

    grafo = StateGraph(EstadoConversacion)
    grafo.add_node("responder", responder)
    grafo.add_edge(START, "responder")
    grafo.add_edge("responder", END)
    return grafo.compile(checkpointer=InMemorySaver())


def demostracion_memoria():
    agente = crear_agente_memoria()
    config = {"configurable": {"thread_id": "clase-1"}}
    agente.invoke({"messages": [{"role": "user", "content": "Hola, me llamo José y vivo en Cali."}]}, config)
    respuesta = agente.invoke({"messages": [{"role": "user", "content": "¿Cómo me llamo y dónde vivo?"}]}, config)
    return respuesta["messages"][-1].content
