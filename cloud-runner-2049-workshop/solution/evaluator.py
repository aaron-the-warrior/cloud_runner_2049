"""Sub-agente evaluador (LLM-as-a-Judge) para Cloud Runner 2049.

Este módulo implementa el evaluador de rutas de maratón con ventana de
contexto acotada para prevenir 'agent drift' y validar el cumplimiento
reglamentario (42.195 km, puestos de hidratación cada 5 km y zonas de meta seguras)
según la habilidad 'race_director.skill'.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types
from pydantic import BaseModel, Field

# Soporte para caracteres UTF-8 en consolas Windows (cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Cargar variables de entorno
load_dotenv()

# Modelo configurable vía .env (por defecto Gemini 4 Argon)
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


def cargar_directivas_carrera() -> str:
    """Lee y extrae el cuerpo normativo de race_director.skill."""
    if not SKILL_PATH.exists():
        return (
            "Reglas oficiales: Distancia exacta 42.195 km (tolerancia 42.090-42.300 km). "
            "Puestos de hidratación obligatorios cada <= 5.0 km. Meta segura con desaceleración >= 400m."
        )

    contenido = SKILL_PATH.read_text(encoding="utf-8")
    partes = contenido.split("---", 2)
    if len(partes) >= 3:
        return partes[2].strip()
    return contenido.strip()


def construir_instrucciones_evaluador() -> str:
    """Construye las instrucciones para el LLM-as-a-Judge con contexto acotado."""
    reglas = cargar_directivas_carrera()
    return f"""
Eres el Juez Oficial de Carrera (Race Director Evaluator) para el maratón Cloud Runner 2049 en Ciudad de Panamá.
Tu función es actuar como un árbitro imparcial (LLM-as-a-Judge) con ventana de contexto acotada.

NO arrastres conversaciones previas ni asumas intenciones. Evalúa ÚNICAMENTE la propuesta suministrada
frente a las siguientes directivas reglamentarias oficiales:

{reglas}

REGLAS DE EVALUACIÓN ESTRICTAS:
1. Distancia: Debe estar en el rango [42.090 km, 42.300 km]. Si está fuera, marca distance_valid=False.
2. Hidratación: Debe haber puestos de hidratación en intervalos de no más de 5.0 km (ej. km 5, 10, 15, 20, 25, 30, 35, 40).
3. Meta: Debe contar con zona segura de desaceleración (mínimo 400m) y servicios de asistencia.
4. Veredicto:
   - Si compliance_score >= 0.85 Y distance_valid=True Y hydration_valid=True Y finish_safety_valid=True -> verdict='APPROVED'.
   - En cualquier otro caso -> verdict='REJECTED'.

DEBES responder con un objeto JSON válido que cumpla estrictamente con el esquema de EvaluationReport:
{{
  "verdict": "APPROVED" | "REJECTED",
  "compliance_score": float,
  "distance_km": float,
  "distance_valid": bool,
  "hydration_valid": bool,
  "finish_safety_valid": bool,
  "violations": ["string"],
  "recommendations": ["string"],
  "summary": "string"
}}
"""


# Agente evaluador configurado con ADK
evaluator_agent = Agent(
    name="race_director_judge",
    model=MODEL_NAME,
    description="Sub-agente evaluador reglamentario para maratones bajo estándares World Athletics.",
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


def evaluar_plan_carrera(plan_propuesto: str | dict[str, Any]) -> EvaluationReport:
    """Evalúa un plan de carrera o GeoJSON utilizando el sub-agente evaluador.

    Aísla la llamada en un contexto limpio (isolated turn) para evitar agent drift.
    """
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

    respuesta_texto = ejecutar_agente_adk(evaluator_agent, prompt_evaluacion)

    # Limpiar posibles bloques markdown de código ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", respuesta_texto)
    json_str = match.group(1) if match else respuesta_texto.strip()

    try:
        datos = json.loads(json_str)
        return EvaluationReport(**datos)
    except Exception as e:
        # Fallback de seguridad en caso de error de parseo
        return EvaluationReport(
            verdict="REJECTED",
            compliance_score=0.0,
            distance_km=0.0,
            distance_valid=False,
            hydration_valid=False,
            finish_safety_valid=False,
            violations=[f"Error al procesar salida del evaluador: {e}"],
            recommendations=["Verificar que el evaluador devuelva JSON con el formato requerido."],
            summary=f"Evaluación fallida debido a error de parseo. Respuesta obtenida: {respuesta_texto[:200]}",
        )


def main() -> None:
    """Ejecución de prueba CLI del evaluador."""
    print("=" * 60)
    print("🧪 Evaluando sub-agente LLM-as-a-Judge (Race Director)")
    print("=" * 60)

    propuesta_valida_ejemplo = {
        "nombre_evento": "Maratón del Canal de Panamá 2049",
        "distancia_total_km": 42.195,
        "linea_salida": "Calzada de Amador frente a Isla Perico (calzada 14m)",
        "linea_meta": "Vía Cincuentenario frente a Panamá Viejo con 450m de embudo de desaceleración e hidratación de choque",
        "puestos_hidratacion": [
            {"km": 5.0, "ubicacion": "Biomuseo"},
            {"km": 10.0, "ubicacion": "Casco Antiguo"},
            {"km": 15.0, "ubicacion": "Mercado de Mariscos"},
            {"km": 20.0, "ubicacion": "Monumento a Balboa"},
            {"km": 25.0, "ubicacion": "Parque Urracá"},
            {"km": 30.0, "ubicacion": "Punta Paitilla"},
            {"km": 35.0, "ubicacion": "Coco del Mar"},
            {"km": 40.0, "ubicacion": "Atlapa"},
        ],
        "puestos_agua_intermedios_km": [7.5, 12.5, 17.5, 22.5, 27.5, 32.5, 37.5],
        "hora_salida": "05:00 (antes del amanecer, clima tropical húmedo)",
        "asistencia_medica": ["km 10", "km 20", "km 30", "km 40", "Zona de Meta (Hospital de campaña)"],
    }

    print("\n🔍 Enviando propuesta de prueba al modelo...")
    reporte = evaluar_plan_carrera(propuesta_valida_ejemplo)

    print(f"\n📊 Dictamen: {reporte.verdict}")
    print(f"🎯 Puntaje de cumplimiento: {reporte.compliance_score * 100:.1f}%")
    print(f"📏 Distancia detectada: {reporte.distance_km} km (Válida: {reporte.distance_valid})")
    print(f"💧 Hidratación válida: {reporte.hydration_valid}")
    print(f"🏁 Meta segura: {reporte.finish_safety_valid}")
    print(f"📝 Resumen: {reporte.summary}")

    if reporte.violations:
        print("\n⚠️ Violaciones encontradas:")
        for v in reporte.violations:
            print(f"  - {v}")

    if reporte.recommendations:
        print("\n💡 Recomendaciones:")
        for r in reporte.recommendations:
            print(f"  - {r}")


if __name__ == "__main__":
    main()
