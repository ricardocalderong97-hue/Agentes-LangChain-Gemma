# Taller: 3 agentes con LangChain, Ollama (`gemma3:1b`) y LangSmith

Preparado a partir del **tutorial_langchain_langsmith.ipynb** del curso, especialmente los puntos 6 a 10.

**Qué incluye**

| Parte | Archivo | Qué hace |
|---|---|---|
| Punto 6 | `agentes.py` / `herramientas.py` | Consulta de clima y multiplicación con herramientas `@tool` |
| Punto 7 | `agentes.py` / `datos/politicas_ejemplo.txt` | RAG con recuperador local BM25 y respuestas basadas en políticas ficticias |
| Ejercicio adicional | `agentes.py` | Traductor español ↔ inglés (u otros idiomas) con Gemma local |
| Punto 8 | `@traceable` en `agentes.py` | Registro del pipeline y las llamadas del modelo en LangSmith |
| Punto 9 | `evaluar.py` | Dataset y evaluación de 3 preguntas RAG en LangSmith |
| Punto 10 | `memoria.py` | Ejemplo con `InMemorySaver` y `thread_id` |
| Opcional | `agente_nativo_opcional.py` | Versión con `create_agent` usando **otra variante Gemma** que admite tools |

Puedes ejecutar `notebook_puntos_6_al_10.ipynb` por celdas dentro de VS Code o usar `main.py` en la terminal.

## 1. Prepara Ollama (Windows)

Abre PowerShell en Windows y comprueba el modelo ya descargado:

```powershell
ollama list
```

Debe aparecer `gemma3:1b`. Si no está:

```powershell
ollama pull gemma3:1b
```

Comprueba que responde:

```powershell
ollama run gemma3:1b
```

Escribe una pregunta; para terminar, `/bye`. En Windows normalmente Ollama ya se ejecuta en segundo plano. Si no está en marcha, abre Ollama o inicia `ollama serve` en una **terminal distinta** (no intentes ejecutar dos servidores al mismo tiempo).

**No es necesario encender ConstructAI (FastAPI/Vite) para estos ejercicios.** LangChain hablará directamente con Ollama en `http://localhost:11434`.

## 2. Abre el proyecto en VS Code

Extrae el ZIP y usa **File → Open Folder** para abrir la carpeta `agentes_langchain_gemma_local`. En la terminal de VS Code (**Terminal → New Terminal**, PowerShell):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Recomendación: Python 3.12 para minimizar incompatibilidades. Si no está instalado, instala Python 3.12 o usa otra versión compatible con las dependencias (`py --list`). Si PowerShell bloquea la activación, en esa misma terminal ejecuta temporalmente:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

En VS Code selecciona **Python: Select Interpreter → .venv**. Para el `.ipynb`, selecciona el mismo entorno como kernel (VS Code puede solicitar la extensión Jupyter).

## 3. Prueba los tres agentes localmente

En `.env` deja inicialmente `LANGSMITH_TRACING=false` y `CLIMA_REAL=false`.

```powershell
python main.py demo
```

También puedes ejecutarlos por separado:

```powershell
python main.py herramientas --pregunta "¿Qué clima hace en Cali? Y ¿cuánto es 23.5 por 4?"
python main.py rag --pregunta "¿Cuántos días de remoto puedo hacer?"
python main.py traducir --texto "El presupuesto está listo para revisión." --origen español --destino inglés
```

**Resultados que debes comprobar:** la herramienta matemática produce **94.0**; el clima del tutorial responde **24 °C soleado (SIMULADO)**; el RAG encuentra **2 días de remoto por semana con aprobación previa**. La redacción exacta de Gemma puede variar y no se ha validado en tu equipo.

Para consultar clima real, cambia `CLIMA_REAL=true` en `.env` y vuelve a lanzar el proceso: consulta la API pública de Open-Meteo por Internet. Si no hay conexión, devolverá un error explicativo en vez de inventar una temperatura.

## 4. Regístrate en LangSmith y registra el agente

**LangChain** es la biblioteca Python, **no requiere cuenta**. La cuenta es en **LangSmith**, donde se ven las ejecuciones (*traces*).

1. Abre [smith.langchain.com](https://smith.langchain.com) e inicia sesión o regístrate (Google, GitHub o correo).
2. En **Settings → API Keys**, crea una clave; para el ejercicio completo y `evaluar.py`, usa una **Personal Access Token (PAT)** o una service key con permisos suficientes. Copia la clave, que se muestra una sola vez.
3. Si tu espacio de trabajo tiene la interfaz **Agents**, pulsa **+ Agent → Connect → Connect an existing agent**. Registra un agente externo, por ejemplo nombre `Taller Gemma local` e ID **`taller-gemma-local`** (sin espacios; este ID es texto, no UUID).
4. Edita `.env` con la clave y el ID:

   ```dotenv
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=tu-clave-aqui
   LANGSMITH_AGENT_ID=taller-gemma-local
   LANGSMITH_AGENT_ENVIRONMENT=local
   ```

5. **No** dejes también `LANGSMITH_PROJECT` activo si usas las variables `LANGSMITH_AGENT_*`. En la plantilla está comentado.
6. Ejecuta `python main.py demo` otra vez. Abre **LangSmith → agente Taller Gemma local → entorno Local → Traces**. Debes ver los nombres de las ejecuciones, las herramientas, el recuperador y las respuestas del LLM.

**Si LangSmith te muestra la interfaz clásica de Projects/Tracing Projects** (sin registro de agentes), no uses `LANGSMITH_AGENT_*`. En lugar de eso, configura:

```dotenv
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=tu-clave-aqui
LANGSMITH_PROJECT=tutorial-gemma-local
```

Después abre **Tracing Projects** y selecciona ese proyecto. Si una clave pertenece a una región diferente de US, revisa `LANGSMITH_ENDPOINT`; si tiene varios workspaces, puede requerir `LANGSMITH_WORKSPACE_ID`.

### ¿Qué datos salen de tu computador?

El **modelo sigue procesándose en Ollama local**. Cuando `LANGSMITH_TRACING=true`, las trazas **sí se transmiten a LangSmith**, incluyendo entradas/salidas de la aplicación y posiblemente textos recuperados. **No habilites trazas con documentos reales o confidenciales de la empresa sin autorización**. Para pruebas sin compartir datos, mantén `LANGSMITH_TRACING=false`.

## 5. Punto 7: RAG y sus datos

Se ha conservado el ejemplo del tutorial: `datos/politicas_ejemplo.txt` contiene las cuatro políticas de ejemplo. Son **ficticias**, no las políticas de una empresa real ni un resumen de legislación laboral.

- `BM25Retriever` busca por coincidencia de palabras; no utiliza embeddings ni bases vectoriales.
- `buscar_politicas` es una herramienta LangChain con `@tool` que recupera fragmentos y se registra en las trazas.
- Un filtro sencillo evita responder cuando no se comparte ninguna palabra relevante; **no es una garantía de relevancia semántica**.
- El LLM responde usando el contexto encontrado y se muestra el origen al final.

Si quieres probar otras políticas, edita las líneas de ese archivo y **reinicia el programa/kernel** para regenerar el índice BM25.

Para PDFs, el notebook original propone `PyPDFLoader` + `RecursiveCharacterTextSplitter`; puedes incorporarlos después, y convendría evaluar recuperación y citas con documentos reales. Por ahora se respeta el RAG BM25 de la actividad y no se necesita descargar un segundo modelo.

## 6. Punto 9: evaluación en LangSmith

Con `.env` y una credencial que pueda crear datasets/experimentos:

```powershell
python evaluar.py
```

El script crea (solo si no existe) el dataset `tutorial-gemma-rag-preguntas`, ejecuta tres preguntas sobre el RAG y mide si la respuesta contiene el dato esperado. Revisa **Datasets & Experiments** en LangSmith. Un evaluador por coincidencia de texto es solo una primera métrica: no verifica por completo la fidelidad o la calidad de las respuestas.

## 7. Punto 10: memoria

```powershell
python main.py memoria
```

Demuestra dos turnos en el mismo `thread_id`. El histórico vive **en memoria mientras el programa esté abierto**: no se almacena en un servidor o base de datos persistente.

## 8. Importante: `gemma3:1b` y `create_agent`

El notebook del profesor usa:

```python
from langchain.agents import create_agent
agent = create_agent(model=model, tools=[clima, multiplicar])
```

La versión estándar `gemma3:1b` de Ollama **no admite de forma fiable llamadas nativas de herramientas**, y puede producir errores `does not support tools`. Esto no es un error de LangSmith ni de VS Code.

Para **conservar exactamente tu modelo ya instalado**, `agentes.py` utiliza grafos de **LangGraph** (incluido en el ecosistema LangChain):

- El código identifica la multiplicación y la ciudad; ejecuta `@tool`.
- La recuperación RAG se ejecuta explícitamente mediante `BM25Retriever`.
- Gemma genera las respuestas finales.
- Los pasos quedan registrados en LangSmith.

**Distinción académica:** estos son flujos orquestados con herramientas; no son agentes autónomos en los que `gemma3:1b` elige libremente qué herramienta invocar. Si tu profesor exige estrictamente `create_agent` y la decisión de herramientas por el LLM, tendrás que usar una variante entrenada/adaptada para herramientas.

Se incluye **solo como alternativa**, no como requisito, `agente_nativo_opcional.py`:

```powershell
ollama pull lukaspetrik/gemma3-tools:1b
python agente_nativo_opcional.py
```

Es una variante comunitaria distinta de tu `gemma3:1b` original; requiere descarga adicional y su fiabilidad no está garantizada. El ejemplo opcional sí usa `create_agent`, `@tool` y el bucle de llamadas de herramientas.

## 9. Errores comunes

| Error | Qué revisar |
|---|---|
| `ModuleNotFoundError: langchain_ollama` | Ejecutar `pip install -r requirements.txt` con el `.venv` correcto |
| `Connection refused` en localhost:11434 | Arrancar Ollama y verificar `ollama list` |
| `model ... not found` | Comprobar el nombre exacto `gemma3:1b` en `ollama list` |
| `does not support tools` | Usar `python main.py demo` y no el ejemplo nativo con el modelo estándar |
| Trazas no aparecen | `LANGSMITH_TRACING=true`, clave válida, agente registrado, ID y entorno correctos |
| `403` en LangSmith | Revisar permisos de la clave y workspace |
| Mala traducción o respuestas imprecisas | `gemma3:1b` es un modelo pequeño; revisar y repetir pruebas |

## Documentación oficial de referencia

- [ChatOllama y `langchain-ollama`](https://docs.langchain.com/oss/python/integrations/chat/ollama)
- [Agentes con `create_agent`](https://docs.langchain.com/oss/python/langchain/agents)
- [Registro de agente externo en LangSmith](https://docs.langchain.com/langsmith/create-an-agent)
- [Crear cuenta y API key de LangSmith](https://docs.langchain.com/langsmith/create-account-api-key)
- [Trazar ejecuciones LangChain](https://docs.langchain.com/langsmith/trace-with-langchain)
- [Evaluación con LangSmith](https://docs.langchain.com/langsmith/evaluate-llm-application)
