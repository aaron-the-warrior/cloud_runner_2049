"""Sub-agente evaluador (LLM-as-a-Judge) para Cloud Runner 2049 - [CÓDIGO STARTER].

En este laboratorio construirás un juez de carrera con ventana de contexto acotada
para evaluar de manera imparcial si una propuesta de maratón cumple con las reglas oficiales
de World Athletics descritas en 'skills/race_director.skill'.

Completa los bloques marcados con # TODO.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
from typing import Any
import time
import uuid

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types
from pydantic import BaseModel, Field

# Soporte para caracteres UTF-8 en consolas Windows (cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Cargar variables de entorno (.env)
load_dotenv()

MODEL_NAME = os.getenv("ADK_MODEL", "gemini-4-argon")
BASE_DIR = Path(__file__).resolve().parent.parent
SKILL_PATH = BASE_DIR / "skills" / "race_director.skill"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


class EvaluationReport(BaseModel):
    """Esquema de salida estructurada para el veredicto del evaluador de carrera."""

    verdict: str = Field(
        ...,
        description="Resultado de la evaluación: 'APPROVED' o 'REJECTED'",
    )
    compliance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Puntaje de cumplimiento de 0.0 a 1.0 (mínimo 0.85 para ser aprobado)",
    )
    distance_km: float = Field(
        ...,
        description="Distancia total detectada o calculada de la ruta en kilómetros",
    )
    distance_valid: bool = Field(
        ...,
        description="Indica si la distancia cumple con 42.195 km ± 0.25% (entre 42.090 km y 42.300 km)",
    )
    hydration_valid: bool = Field(
        ...,
        description="Indica si existen puestos de hidratación ubicados cada 5.0 km o menos",
    )
    finish_safety_valid: bool = Field(
        ...,
        description="Indica si la zona de meta cumple requisitos de seguridad (área de desaceleración y soporte)",
    )
    violations: list[str] = Field(
        default_factory=list,
        description="Lista de violaciones reglamentarias detectadas en la propuesta",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recomendaciones correctivas precisas para el agente planificador",
    )
    summary: str = Field(
        ...,
        description="Resumen ejecutivo del dictamen de carrera",
    )


# ==============================================================================
# TODO 1: Carga de la Habilidad (Skill)
# ==============================================================================
def cargar_directivas_carrera() -> str:
    """Lee y extrae el cuerpo normativo de race_director.skill."""
    # TODO 1: Verifica si SKILL_PATH existe, lee su contenido en UTF-8 y extrae
    # el cuerpo de instrucciones omitiendo el frontmatter YAML inicial (separado por '---').
    if not SKILL_PATH.exists():
        return "Reglas: Distancia 42.195 km ± 0.25%, hidratación cada <= 5 km, meta segura."

    # IMPLEMENTA AQUÍ TU CÓDIGO:
    contenido = SKILL_PATH.read_text(encoding="utf-8")
    partes = contenido.split("---", 2)
    return partes[2].strip() if len(partes) >= 3 else contenido.strip()


# ==============================================================================
# TODO 2: Instrucciones del Juez con Ventana de Contexto Acotada
# ==============================================================================
def construir_instrucciones_evaluador() -> str:
    """Construye las instrucciones para el LLM-as-a-Judge con contexto acotado."""
    reglas = cargar_directivas_carrera()

    # TODO 2: Redacta el prompt del sistema para el juez.
    # Debe indicarle que actúe como Race Director Evaluator, que NO arrastre contexto
    # externo (previene agent drift), y que obligatoriamente devuelva un JSON
    # con los campos del esquema EvaluationReport.
    return f"""
    Eres el Juez Oficial de Carrera (Race Director Evaluator) para Cloud Runner 2049.
    Evalúa ÚNICAMENTE la propuesta suministrada frente a estas directivas reglamentarias:
    
    {reglas}
    
    Responde estrictamente en formato JSON conforme a las propiedades de EvaluationReport.
    """


# ==============================================================================
# TODO 3: Instanciación del Agente Evaluador con ADK
# ==============================================================================
# TODO 3: Crea una instancia de `Agent` de google.adk con:
# - name="race_director_judge"
# - model=MODEL_NAME
# - description="Sub-agente evaluador reglamentario..."
# - instruction=construir_instrucciones_evaluador()
evaluator_agent = Agent(
    name="race_director_judge",
    model=MODEL_NAME,
    description="Sub-agente evaluador reglamentario para maratones.",
    instruction=construir_instrucciones_evaluador(),
)

# Convención ADK CLI (adk run / adk web)
root_agent = evaluator_agent


def ejecutar_agente_adk(agente: Agent, prompt: str, max_intentos: int = 3) -> str:
    """Ejecuta un agente de Google ADK de forma limpia y síncrona con reintentos para mitigar saturación de API."""
    ultimo_error = None
    for intento in range(1, max_intentos + 1):
        try:
            runner = InMemoryRunner(agent=agente)
            user_id = "juez_carrera_user"
            session_id = f"sesion_{uuid.uuid4().hex[:8]}"

            # Inicializar sesión síncrona en el servicio de sesiones de ADK
            runner.session_service.create_session_sync(
                app_name=runner.app_name,
                user_id=user_id,
                session_id=session_id,
            )

            mensaje = types.Content(parts=[types.Part.from_text(text=prompt)])
            eventos = list(runner.run(user_id=user_id, session_id=session_id, new_message=mensaje))

            textos = []
            for evento in eventos:
                if hasattr(evento, "content") and evento.content:
                    for parte in evento.content.parts:
                        if hasattr(parte, "text") and parte.text:
                            textos.append(parte.text)
            resultado = "\n".join(textos).strip()
            if resultado:
                return resultado
        except Exception as e:
            ultimo_error = e
            err_msg = str(e)
            if ("limit: 0" in err_msg or "RESOURCE_EXHAUSTED" in err_msg) and getattr(agente, "model", None) == "gemini-4-argon":
                print("ℹ️ Cuenta Free Tier detectada (cuota 0 en Gemini 4). Activando compatibilidad para completar la evaluación...")
                agente.model = "gemini-3.1-flash-lite"
                continue
            if intento < max_intentos:
                tiempo_espera = intento * 2.5
                print(f"⚠️ Reintentando evaluación por alta demanda de API ({intento}/{max_intentos}) en {tiempo_espera}s...")
                time.sleep(tiempo_espera)
            else:
                raise ultimo_error
    return ""


# ==============================================================================
# TODO 4: Invocación en Contexto Aislado (LLM-as-a-Judge Runner)
# ==============================================================================
def evaluar_plan_carrera(plan_propuesto: str | dict[str, Any]) -> EvaluationReport:
    """Evalúa un plan de carrera o GeoJSON utilizando el sub-agente evaluador."""
    if isinstance(plan_propuesto, dict):
        texto_plan = json.dumps(plan_propuesto, indent=2, ensure_ascii=False)
    else:
        texto_plan = str(plan_propuesto)

    prompt_evaluacion = f"""
Por favor evalúa la siguiente propuesta de circuito de maratón y genera el informe reglamentario en JSON:

--- PROPUESTA ---
{texto_plan}
-----------------
"""

    # TODO 4: Utiliza InMemoryRunner de ADK para ejecutar evaluator_agent con prompt_evaluacion,
    # limpia posibles delimitadores de código markdown (```json ... ```) y deserializa
    # la respuesta en una instancia de EvaluationReport.
    respuesta_texto = ejecutar_agente_adk(evaluator_agent, prompt_evaluacion)

    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", respuesta_texto)
    json_str = match.group(1) if match else respuesta_texto.strip()

    try:
        datos = json.loads(json_str)
        return EvaluationReport(**datos)
    except Exception as e:
        return EvaluationReport(
            verdict="REJECTED",
            compliance_score=0.0,
            distance_km=0.0,
            distance_valid=False,
            hydration_valid=False,
            finish_safety_valid=False,
            violations=[f"Error al procesar salida del evaluador: {e}"],
            recommendations=["Verificar formato JSON generado."],
            summary="Fallo en la evaluación por formato inválido.",
        )


def main() -> None:
    print("🧪 Probando esqueleto de evaluador starter...")
    ejemplo = {
        "distancia_total_km": 42.195,
        "linea_salida": "Calzada de Amador",
        "linea_meta": "Panamá Viejo (embudo 450m)",
        "puestos_hidratacion": [{"km": 5.0}, {"km": 10.0}, {"km": 15.0}, {"km": 20.0}],
    }
    reporte = evaluar_plan_carrera(ejemplo)
    print(f"Resultado: {reporte.verdict} - Score: {reporte.compliance_score}")


if __name__ == "__main__":
    main()
