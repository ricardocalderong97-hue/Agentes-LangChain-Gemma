"""Lanzador de las prácticas desde la terminal de VS Code (Windows/macOS/Linux)."""
import argparse
import sys

from configuracion import MODELO_NOMBRE
from agentes import consultar_herramientas, consultar_rag, traducir


def main():
    parser = argparse.ArgumentParser(description=f"Agentes LangChain con Ollama local ({MODELO_NOMBRE})")
    sub = parser.add_subparsers(dest="comando", required=True)
    p1 = sub.add_parser("herramientas", help="Clima y multiplicaciones (punto 6)")
    p1.add_argument("--pregunta", required=True)
    p2 = sub.add_parser("rag", help="Consulta políticas ficticias con BM25 (punto 7)")
    p2.add_argument("--pregunta", required=True)
    p3 = sub.add_parser("traducir", help="Traducción con Gemma local")
    p3.add_argument("--texto", required=True)
    p3.add_argument("--origen", default="español")
    p3.add_argument("--destino", default="inglés")
    sub.add_parser("demo", help="Ejecutar los tres casos en orden")
    sub.add_parser("memoria", help="Punto 10: checkpointer InMemorySaver")
    args = parser.parse_args()

    try:
        if args.comando in ("herramientas", "demo"):
            pregunta = args.pregunta if args.comando == "herramientas" else "¿Qué clima hace en Cali? Y ¿cuánto es 23.5 por 4?"
            r = consultar_herramientas(pregunta)
            print("\n=== 6. AGENTE DE HERRAMIENTAS ===")
            print("Resultado de las herramientas:")
            print("\n".join(r["resultados_herramientas"]))
            print("\nRespuesta de Gemma:", r["respuesta"])
        if args.comando in ("rag", "demo"):
            pregunta = args.pregunta if args.comando == "rag" else "¿Cuántos días de remoto puedo hacer?"
            r = consultar_rag(pregunta)
            print("\n=== 7. AGENTE RAG ===")
            print("Contexto recuperado:", r["contexto"])
            print("Respuesta:", r["respuesta"])
        if args.comando in ("traducir", "demo"):
            texto = args.texto if args.comando == "traducir" else "El presupuesto del proyecto está listo para revisión."
            origen = args.origen if args.comando == "traducir" else "español"
            destino = args.destino if args.comando == "traducir" else "inglés"
            print("\n=== 8. TRADUCTOR ===")
            print(traducir(texto=texto, origen=origen, destino=destino))
        if args.comando == "memoria":
            from memoria import demostracion_memoria
            print("\n=== 10. MEMORIA ===")
            print(demostracion_memoria())
    except Exception as exc:
        print(f"\nERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        print("Revisa que Ollama esté encendido, que 'ollama list' muestre el modelo y que .env sea correcto.", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
