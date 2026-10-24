# Lab 01: Inicialización del Agente con Google ADK y Carga Progresiva de Skills

## 🎯 Objetivos de Aprendizaje

Al finalizar este laboratorio, serás capaz de:
1. Comprender la arquitectura fundamental de **Google Agent Development Kit (ADK)**.
2. Implementar el patrón de **Progressive Disclosure** cargando directivas operativas desde archivos de habilidades (`.skill`).
3. Instanciar un agente conversacional tipado (`Agent`) y ejecutarlo con `InMemoryRunner`.
4. Diseñar un sistema de prompts modulares que guíe la planificación de eventos de alta complejidad.

---

## 🏗️ 1. ¿Qué es Google ADK?

**Google Agent Development Kit (ADK)** es un framework ligero y modular para Python y TypeScript diseñado para crear agentes de inteligencia artificial fiables, conectables y listos para producción sobre los modelos Gemini.

A diferencia de otros frameworks orquestadores monolíticos, ADK se centra en tres pilares:
- **Agentes Tipados y Ligeros (`Agent`):** Definición clara de instrucciones, herramientas y esquemas.
- **Ejecutores Aislados (`Runner`):** Manejo de sesiones y llamadas deterministas (`InMemoryRunner`, streaming, etc.).
- **Protocolo de Herramientas Estándar:** Compatibilidad directa con funciones de Python, `AgentTool` (inter-agente) y servidores **MCP (Model Context Protocol)**.

---

## 🧩 2. Habilidades en ADK y Progressive Disclosure

En sistemas multi-agente complejos, inyectar todas las reglas de negocio y restricciones operativas en un único prompt estático causa saturación de atención en el modelo (*attention dilution*) y deriva de comportamiento (*agent drift*).

ADK promueve el patrón de **Progressive Disclosure** (Divulgación Progresiva):
- Las habilidades residen en archivos estructurados con extensión `.skill`.
- Cuentan con un bloque de metadatos frontmatter en **YAML** (nombre, versión, descripción para indexación rápida).
- El cuerpo en **Markdown** contiene las reglas detalladas, restricciones de negocio y directivas de formato.

### Estructura de `skills/race_director.skill`
```markdown
---
name: race_director
version: "1.0.0"
description: Reglas oficiales de atletismo y logística de maratones...
---

# Habilidad: Dirección y Reglas Oficiales de Maratón
- Distancia Reglamentaria: 42.195 km (±0.25%).
- Puestos de Hidratación: Cada <= 5.0 km.
...
```

---

## 💻 3. Paso a Paso: Implementación en Código

Abre el archivo [starter/agent.py](file:///C:/Users/aaron/Documents/GDE/Workshops/cloud_runner_2049/cloud-runner-2049-workshop/starter/agent.py) y localiza la sección **`TODO 1`**.

### Paso 3.1: Función de Carga de Skills
Implementa una función que lea el archivo `.skill` y separe el frontmatter YAML del cuerpo de directivas:

```python
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

def cargar_skill(nombre_archivo: str) -> str:
    """Lee y extrae las directivas de un archivo .skill en la carpeta skills/."""
    ruta = SKILLS_DIR / nombre_archivo
    if not ruta.exists():
        return f"[Habilidad {nombre_archivo} no disponible]"
    
    contenido = ruta.read_text(encoding="utf-8")
    partes = contenido.split("---", 2)
    # partes[2] contiene el Markdown descriptivo posterior al frontmatter YAML
    return partes[2].strip() if len(partes) >= 3 else contenido.strip()

SKILL_MAPPING = cargar_skill("mapping.skill")
SKILL_RACE_DIRECTOR = cargar_skill("race_director.skill")
```

### Paso 3.2: Definición de las Instrucciones del Agente
Compón las instrucciones del sistema ensamblando las habilidades cargadas:

```python
INSTRUCCIONES_PLANIFICADOR = f"""
Eres el Planificador Oficial de Maratón para Cloud Runner 2049 en Ciudad de Panamá.
Utiliza las siguientes directivas especializadas:

--- DIRECTIVAS GEOESPACIALES ---
{SKILL_MAPPING}

--- REGLAMENTACIÓN OFICIAL DE CARRERA ---
{SKILL_RACE_DIRECTOR}

Tu objetivo es planificar un recorrido de exactamente 42.195 km por Ciudad de Panamá.
"""
```

### Paso 3.3: Creación y Ejecución del Agente
Instancia el agente usando `google.adk.agents.Agent` y pruébalo con `InMemoryRunner`:

```python
import os
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner

MODEL_NAME = os.getenv("ADK_MODEL", "gemini-4-flash")

planner_agent = Agent(
    name="race_course_planner",
    model=MODEL_NAME,
    description="Agente autónomo para planificación de circuitos de maratón.",
    instruction=INSTRUCCIONES_PLANIFICADOR,
)

# Ejecución básica
runner = InMemoryRunner(agent=planner_agent)
respuesta = runner.run("Describe las 3 reglas principales que debes cumplir para el maratón.")
print(respuesta.text)
```

---

## 🧪 4. Verificación y Resultados

Ejecuta tu archivo starter desde la terminal:

```powershell
python starter/agent.py
```

Deberás observar que el agente reconoce de inmediato la distancia reglamentaria (**42.195 km**) y el intervalo máximo de puestos de hidratación (**≤ 5.0 km**) definidos en `race_director.skill`.

---

## 🚀 Próximo Paso
En el [Lab 02: Remote MCP con Google Maps](file:///C:/Users/aaron/Documents/GDE/Workshops/cloud_runner_2049/cloud-runner-2049-workshop/labs/02-remote-mcp-maps.md), conectaremos herramientas cartográficas remotas para consultar coordenadas reales en Ciudad de Panamá y calcular itinerarios viales.
