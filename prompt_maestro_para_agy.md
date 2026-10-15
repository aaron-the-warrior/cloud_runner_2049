# Prompt Maestro: Generación del Taller Cloud Runner 2049 con Antigravity CLI (`agy`)

> **Instrucciones:** Copia y pega el siguiente bloque directamente en tu sesión de `agy` para que genere la estructura completa del repositorio y los archivos del taller.

---

```text
Actúa como un Senior Staff AI Engineer experto en Google Cloud, Agent Development Kit (ADK) y desarrollo de Codelabs técnicos.

Quiero crear un repositorio completo para un taller hands-on llamado `cloud-runner-2049-workshop`, inspirado en la demo oficial de Google Cloud Next ("Race Condition" / Las Vegas Marathon multi-agent simulation: https://developers.google.com/solutions/learn/race-condition).

El objetivo es que los asistentes construyan un sistema multi-agente en Python usando ADK, Remote MCP (Model Context Protocol), el protocolo A2A (Agent-to-Agent) y evaluación en tiempo real con sub-agentes (LLM-as-a-Judge).

Por favor, genera la estructura de archivos y el código correspondiente con las siguientes especificaciones:

---

### 1. Estructura de carpetas requerida
```text
cloud-runner-2049-workshop/
├── .env.example
├── pyproject.toml
├── README.md
├── scripts/
│   ├── setup.sh
│   └── setup.ps1
├── skills/
│   ├── mapping.skill
│   └── race_director.skill
├── labs/
│   ├── 01-adk-planner-skills.md
│   ├── 02-remote-mcp-maps.md
│   ├── 03-evaluator-subagent.md
│   └── 04-a2a-orchestration.md
├── starter/
│   ├── agent.py
│   ├── evaluator.py
│   └── agent_card.json
└── solution/
    ├── agent.py
    ├── evaluator.py
    └── agent_card.json
```

---

### 2. Requerimientos de los archivos

1. **`pyproject.toml`**:
   - Compatible con `uv` y Python `>=3.11`.
   - Dependencias requeridas: `google-adk`, `google-genai`, `mcp`, `pydantic`, `python-dotenv`, `geojson`.

2. **`scripts/setup.sh` y `scripts/setup.ps1`**:
   - Automatización multiplataforma (Bash para Linux/macOS/Cloud Shell y PowerShell para Windows).
   - Crear entorno virtual `.venv` con `uv venv`, activarlo e instalar dependencias con `uv pip install -e .`.
   - Validar que existan las credenciales de `gcloud` y advertir si falta copiar `.env.example` a `.env`.

3. **`skills/*.skill`**:
   - Formato ADK estándar: bloque inicial de frontmatter en YAML (nombre, versión, descripción para progressive disclosure) seguido por el cuerpo en Markdown con directivas operativas.
   - `mapping.skill`: Instrucciones para interactuar con herramientas geoespaciales y Google Maps MCP para consultar landmarks y calcular trayectos.
   - `race_director.skill`: Reglas de negocio para maratones (distancia reglamentaria de 42.195 km, ubicación de puestos de hidratación cada 5 km, zonas de meta seguras).

4. **`starter/` vs `solution/`**:
   - `starter/agent.py`: Esqueleto del `LlmAgent` con ADK, con placeholders y comentarios `# TODO:` para cargar skills, vincular herramientas MCP y conectar con el evaluador.
   - `starter/evaluator.py`: Esqueleto del sub-agente evaluador que actúa como herramienta de validación (LLM-as-a-Judge) con placeholders `# TODO:`.
   - `solution/agent.py` y `solution/evaluator.py`: Código completo, tipado, modular y ejecutable.
   - `agent_card.json`: Manifiesto bajo el estándar A2A (Agent-to-Agent) exponiendo nombre, versión, endpoints, schemas de entrada/salida y capabilities del agente planificador.

5. **`labs/*.md`**:
   - 4 guías prácticas tipo Codelab, concisas y directas:
     - `01-adk-planner-skills.md`: Inicialización del agente con ADK y carga progresiva de Skills.
     - `02-remote-mcp-maps.md`: Conexión de herramientas externas vía Google Maps Remote MCP.
     - `03-evaluator-subagent.md`: Configuración de LLM-as-a-Judge con ventana de contexto acotada para evitar agent drift.
     - `04-a2a-orchestration.md`: Publicación de la Agent Card y simulación de interacción inter-agente A2A.

6. **`README.md`**:
   - Documentación clara con diagrama de arquitectura en texto plano/ASCII, tabla de laboratorios, prerrequisitos en GCP y pasos de ejecución rápida tanto en Bash como en PowerShell.

---

Por favor, genera primero los scripts de setup (`setup.sh`, `setup.ps1`), `pyproject.toml`, los archivos `.skill` y los archivos Python (`starter/` y `solution/`).