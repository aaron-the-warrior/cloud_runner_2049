# Lab 04: Publicación de la Agent Card y Orquestación A2A (Agent-to-Agent)

## 🎯 Objetivos de Aprendizaje

Al finalizar este laboratorio, serás capaz de:
1. Comprender los fundamentos del protocolo **A2A (Agent-to-Agent)** para ecosistemas inter-agente federados.
2. Construir y validar un manifiesto **Agent Card (`agent_card.json`)** bajo estándares abiertos.
3. Comprender el patrón **Hub Session** de Google Cloud Next ("Race Condition") conectando múltiples agentes especializados.
4. Simular el flujo de orquestación donde el Planificador entrega el circuito validado al Simulador de Maratón.

---

## 🌐 1. ¿Qué es el Protocolo A2A?

El protocolo **Agent-to-Agent (A2A)** es una especificación abierta orientada a permitir que agentes autónomos desarrollados con diferentes tecnologías, lenguajes o frameworks puedan:
- **Descubrirse mutuamente:** A través de un manifiesto público estándar denominado **Agent Card**.
- **Negociar capacidades y contratos:** Validando esquemas JSON (`input_schema` y `output_schema`).
- **Coordinar tareas en tiempo real:** Utilizando transporte HTTP/REST, gRPC, SSE o WebSockets con control de concurrencia.

---

## 🗂️ 2. Anatomía de la Agent Card (`agent_card.json`)

La `Agent Card` es el pasaporte de identidad de un agente en la red. Inspecciona [solution/agent_card.json](file:///C:/Users/aaron/Documents/GDE/Workshops/cloud_runner_2049/cloud-runner-2049-workshop/solution/agent_card.json):

```json
{
  "$schema": "https://a2a-protocol.org/schemas/v1/agent-card.json",
  "name": "cloud-runner-2049-planner",
  "version": "1.0.0",
  "description": "Agente planificador de circuitos de maratón 2049...",
  "endpoints": {
    "invoke": "http://localhost:8080/a2a/v1/invoke",
    "card": "http://localhost:8080/.well-known/agent-card.json"
  },
  "capabilities": [
    { "name": "course_planning", "description": "Diseño de rutas viales de 42.195 km" },
    { "name": "race_director_evaluation", "description": "Validación con LLM-as-a-Judge" }
  ],
  "input_schema": { ... },
  "output_schema": { ... }
}
```

### Campos Clave:
- **`endpoints`:** Localización de los servicios de invocación y descubrimiento.
- **`capabilities`:** Lista semántica de lo que el agente sabe resolver.
- **`skills`:** Referencias a las directivas normativas (`mapping`, `race_director`).
- **`schemas`:** Contrato tipado estricto para garantizar compatibilidad inter-agente.

---

## 🏛️ 3. El Patrón Hub Session en "Race Condition"

En la arquitectura de Google Cloud Next, los agentes no se comunican de forma caótica en malla completa (*all-to-all*). Se utiliza el **Patrón Hub Session**:

```
                       ┌──────────────────────┐
                       │  Go Gateway (A2A Hub)│
                       │   WebSocket / SSE    │
                       └──────────┬───────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Agente Planner   │    │ Agente Simulator │    │ Runner Agents    │
│ (Diseña circuito)│    │ (Entorno y clima)│    │ (Atletas IA)     │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

1. **Paso 1 (Planificación):** El gateway solicita al **Planner Agent** el trazado del circuito.
2. **Paso 2 (Validación):** El Planner ejecuta el LLM-as-a-Judge y devuelve el GeoJSON certificado.
3. **Paso 3 (Simulación):** El **Simulator Agent** recibe el GeoJSON e inicia los ticks de carrera (temperatura, viento, densidad de corredores).
4. **Paso 4 (Toma de decisiones):** Cientos de **Runner Agents** consumen las coordenadas y estaciones de agua para decidir su ritmo de carrera en tiempo real.

---

## 💻 4. Paso a Paso: Simulación de Intercambio A2A

Podemos simular una invocación inter-agente A2A sencilla en Python validando contra el contrato del `Agent Card`:

```python
import json
from pathlib import Path
import jsonschema

BASE_DIR = Path(__file__).resolve().parent.parent

# 1. Cargar el manifiesto Agent Card
agent_card = json.loads((BASE_DIR / "solution" / "agent_card.json").read_text(encoding="utf-8"))

# 2. Carga del payload de solicitud inter-agente
payload_solicitud = {
    "city": "Ciudad de Panamá, PA",
    "target_distance_km": 42.195,
    "start_landmark": "calzada_amador",
    "finish_landmark": "panama_viejo",
    "max_hydration_interval_km": 5.0,
}

# 3. Validar payload de entrada contra el input_schema del agente
jsonschema.validate(instance=payload_solicitud, schema=agent_card["input_schema"])
print("✅ Solicitud A2A validada con éxito frente a la Agent Card.")
```

---

## ☁️ 5. Despliegue en Google Cloud

En un entorno de producción como el presentado en Cloud Next:
- **Cloud Run:** Aloja el servicio A2A (FastAPI o Go) empaquetado en contenedor Docker.
- **Vertex AI Agent Engine:** Gestiona los agentes de Python con auto-escalado a cero.
- **Memorystore Redis:** Almacena el estado y las sesiones A2A activas.

---

## 🎉 ¡Felicitaciones!

Has completado el taller técnico **Cloud Runner 2049**:
- Construiste agentes tipados con **Google ADK**.
- Implementaste el patrón **Progressive Disclosure** con archivos `.skill`.
- Conectaste herramientas geoespaciales y generaste **GeoJSON RFC 7946**.
- Protegiste tu arquitectura contra *agent drift* mediante **LLM-as-a-Judge** con contexto acotado.
- Definiste y expusiste un contrato **A2A** con **Agent Cards**.
