"""Punto 9: evaluación reproducible del RAG con LangSmith, sin LLM como juez."""
import os
from langsmith import Client
from agentes import consultar_rag

DATASET = "tutorial-gemma-rag-preguntas"
EJEMPLOS = [
    {"inputs": {"pregunta": "¿Cuántos días de trabajo remoto se permiten?"}, "outputs": {"respuesta_esperada": "2 días"}},
    {"inputs": {"pregunta": "¿Cuántos días de vacaciones tengo?"}, "outputs": {"respuesta_esperada": "15 días"}},
    {"inputs": {"pregunta": "¿Hasta qué porcentaje de cursos financia la empresa?"}, "outputs": {"respuesta_esperada": "70%"}},
]


def target(inputs: dict) -> dict:
    return {"respuesta": consultar_rag(inputs["pregunta"])["respuesta"]}


def contiene_respuesta(inputs: dict, outputs: dict, reference_outputs: dict) -> bool:
    """Métrica sencilla del notebook: no equivale a evaluación semántica exhaustiva."""
    return reference_outputs["respuesta_esperada"].lower() in outputs["respuesta"].lower()


def main():
    if not os.getenv("LANGSMITH_API_KEY"):
        raise SystemExit("Crea una API key en LangSmith y configúrala en .env antes de evaluar.")
    client = Client()
    if not client.has_dataset(dataset_name=DATASET):
        dataset = client.create_dataset(dataset_name=DATASET, description="Evaluación de políticas ficticias RAG")
        client.create_examples(dataset_id=dataset.id, examples=EJEMPLOS)
    resultados = client.evaluate(
        target,
        data=DATASET,
        evaluators=[contiene_respuesta],
        experiment_prefix="gemma3-1b-bm25",
        max_concurrency=1,
    )
    print(resultados.to_pandas().to_string(index=False))


if __name__ == "__main__":
    main()
