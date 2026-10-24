# Lab 03: Evaluador Sub-Agente (LLM-as-a-Judge) y Prevención de Agent Drift

## 🎯 Objetivos de Aprendizaje

Al finalizar este laboratorio, serás capaz de:
1. Diseñar un patrón de evaluación **LLM-as-a-Judge** como compuerta de calidad (*quality gate*).
2. Comprender y mitigar el fenómeno de **Agent Drift** y sesgo de complacencia (*sycophancy*).
3. Implementar el patrón de **Ventana de Contexto Acotada (Bounded Context)** aislando la sesión del evaluador.
4. Construir un **Bucle de Retroalimentación Reflexiva (Reflection Loop)** entre el planificador y el juez.

---

## ⚖️ 1. ¿Qué es LLM-as-a-Judge y por qué es crítico?

En flujos agenticos autónomos, un agente generativo que evalúa sus propias respuestas tiende a cometer dos fallos graves:
- **Sesgo de confirmación / Complacencia (*Sycophancy*):** El modelo asume que lo que acaba de generar es correcto aunque viole directivas explícitas.
- **Agent Drift (Deriva del Agente):** A medida que la conversación crece con decenas de llamadas intermedias a herramientas, las restricciones iniciales del prompt pierden peso en los pesos de atención del transformador.

### La Solución: Un Sub-Agente con Ventana de Contexto Acotada
El sub-agente evaluador opera en una sesión de ejecución completamente independiente (`isolated runner turn`):
1. **Sin historial conversacional previo:** No hereda el chat del planificador ni sus intentos fallidos.
2. **Solo dos entradas:**
   - La norma objetiva (`skills/race_director.skill`).
   - El artefacto propuesto a evaluar (el plan de carrera o GeoJSON).
3. **Salida estrictamente estructurada:** Genera un esquema tipado con Pydantic (`EvaluationReport`).

```
┌────────────────────────────────┐
│   Planificador (Planner Agent) │
│       Genera propuesta         │
└──────────────┬─────────────────┘
               │  Propuesta aislada
               ▼
┌─────────────────────────────────────────┐
│     Juez (Race Director Judge)          │
│   Ventana de contexto 100% limpia       │
│   Evalúa contra race_director.skill     │
└──────────────┬──────────────────────────┘
               │
       Dictamen: ¿APPROVED?
        ├── NO  ──> Veredicto REJECTED con recomendaciones  ──> Re-planificar
        └── SÍ  ──> Veredicto APPROVED  ──> Emitir circuito oficial
```

---

## 📋 2. Esquema Estructurado con Pydantic

El evaluador debe devolver un dictamen predecible y parseable. Usamos `pydantic.BaseModel`:

```python
from pydantic import BaseModel, Field

class EvaluationReport(BaseModel):
    verdict: str = Field(description="'APPROVED' o 'REJECTED'")
    compliance_score: float = Field(ge=0.0, le=1.0, description="Puntuación de 0.0 a 1.0")
    distance_km: float = Field(description="Distancia calculada")
    distance_valid: bool = Field(description="¿Cumple 42.195 km ± 0.25%?")
    hydration_valid: bool = Field(description="¿Puestos de agua cada <= 5 km?")
    finish_safety_valid: bool = Field(description="¿Meta segura con desaceleración >= 400m?")
    violations: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    summary: str
```

---

## 💻 3. Paso a Paso: Implementación en Código

Abre el archivo [starter/evaluator.py](file:///C:/Users/aaron/Documents/GDE/Workshops/cloud_runner_2049/cloud-runner-2049-workshop/starter/evaluator.py) y revisa las secciones **`TODO 1`** a **`TODO 4`**.

### Paso 3.1: Aislamiento del Ejecutor (Isolated Runner)
Observa cómo la función `evaluar_plan_carrera` crea una instancia fresca de `InMemoryRunner` en cada invocación:

```python
from google.adk.runners import InMemoryRunner

def evaluar_plan_carrera(plan_propuesto: str | dict[str, Any]) -> EvaluationReport:
    # 1. Serializar el plan a evaluar
    texto_plan = json.dumps(plan_propuesto, indent=2, ensure_ascii=False) if isinstance(plan_propuesto, dict) else str(plan_propuesto)

    # 2. Prompt acotado y limpio
    prompt_evaluacion = f"""
    Evalúa la siguiente propuesta frente a race_director.skill:
    {texto_plan}
    """

    # 3. Runner aislado sin memoria de sesiones anteriores
    runner = InMemoryRunner(agent=evaluator_agent)
    resultado = runner.run(prompt_evaluacion)

    # 4. Parseo estricto del JSON a Pydantic
    json_str = extraer_bloque_json(resultado.text)
    return EvaluationReport(**json.loads(json_str))
```

### Paso 3.2: Integración Reflexiva en el Planificador
En [solution/agent.py](file:///C:/Users/aaron/Documents/GDE/Workshops/cloud_runner_2049/cloud-runner-2049-workshop/solution/agent.py), exponemos el evaluador como una herramienta (`tool`) para el planificador:

```python
def herramienta_evaluar_con_race_director(propuesta_carrera_json: str) -> str:
    """Envía la propuesta al subagente evaluador y devuelve el informe en JSON."""
    reporte = evaluar_plan_carrera(propuesta_carrera_json)
    return reporte.model_dump_json(indent=2)
```

Al incluir esta herramienta en el planificador:
- Si el planificador propone una distancia de 40.5 km, el evaluador responde:
  `verdict: "REJECTED", violations: ["Distancia insuficiente (40.5 km vs 42.195 km)"]`
- El planificador lee las `recommendations`, ajusta los waypoints y vuelve a solicitar evaluación hasta que el reporte emita `APPROVED`.

---

## 🧪 4. Verificación y Pruebas

Ejecuta el evaluador de forma independiente:

```powershell
python solution/evaluator.py
```

Observa cómo procesa la propuesta de ejemplo:
- Detecta los puestos de hidratación en los km 5, 10, 15, 20, 25, 30, 35 y 40.
- Valida la zona de amortiguación de la meta en Panamá Viejo.
- Emite un `compliance_score >= 0.85` y el veredicto oficial `APPROVED`.

---

## 🚀 Próximo Paso
En el [Lab 04: Orquestación A2A (Agent-to-Agent)](file:///C:/Users/aaron/Documents/GDE/Workshops/cloud_runner_2049/cloud-runner-2049-workshop/labs/04-a2a-orchestration.md), publicaremos la **Agent Card** y simularemos la interacción entre el planificador y el simulador de carrera mediante el protocolo inter-agente.
