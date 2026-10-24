# Lab 02: Conexión de Herramientas Externas con Google Maps Remote MCP y GeoJSON

## 🎯 Objetivos de Aprendizaje

Al finalizar este laboratorio, serás capaz de:
1. Comprender la arquitectura de **Model Context Protocol (MCP)** y su variante **Remote MCP** sobre SSE (Server-Sent Events) o Stdio.
2. Integrar herramientas de consulta cartográfica y cálculo de distancias al agente ADK.
3. Modelar las restricciones urbanas de Ciudad de Panamá (Cinta Costera, Casco Antiguo, corredores viales, perfiles de elevación).
4. Generar y exportar la ruta oficial en formato **GeoJSON RFC 7946** con geometrías `LineString` y `Point`.

---

## 🗺️ 1. ¿Qué es MCP y por qué Remote MCP?

**Model Context Protocol (MCP)** es un estándar abierto desarrollado para permitir que los agentes de IA descubran, invoquen y consuman herramientas, fuentes de datos y contexto de forma interoperable.

En la demo de Google Cloud Next **Race Condition**, el simulador utiliza un servidor MCP para interactuar con los servicios geoespaciales de Google Maps:
- **Desacoplamiento:** El modelo no necesita conocer los detalles de autenticación o endpoints HTTP de Google Maps; solo invoca herramientas tipadas expuestas por el servidor MCP.
- **Remote MCP:** Permite que el servidor MCP se ejecute en un contenedor independiente (por ejemplo, en Cloud Run o en un pod de Kubernetes) y sea consumido por agentes a través de transporte de red SSE o WebSockets.

---

## 📍 2. Herramientas Cartográficas de Ciudad de Panamá

Para planificar el maratón, nuestro agente necesita interactuar con waypoints icónicos a lo largo de la Calzada de Amador, el Casco Antiguo y la Cinta Costera:

| Identificador | Nombre del Landmark | Coordenadas [Lon, Lat] | Rol en la Carrera |
| :--- | :--- | :--- | :--- |
| `calzada_amador` | Calzada de Amador | `[-79.5268, 8.9147]` | Línea de Salida (Km 0) |
| `biomuseo` | Biomuseo | `[-79.5459, 8.9323]` | Puesto de Hidratación 01 (Km 5) |
| `casco_antiguo` | Casco Antiguo - Plaza de la Independencia | `[-79.5352, 8.9524]` | Puesto de Hidratación 02 + Médico (Km 10) |
| `mercado_mariscos` | Mercado de Mariscos | `[-79.5333, 8.9593]` | Puesto de Hidratación 03 (Km 15) |
| `monumento_balboa` | Monumento a Vasco Núñez de Balboa | `[-79.5279, 8.9683]` | Puesto de Hidratación 04 + Médico (Km 20) |
| `parque_urraca` | Parque Urracá | `[-79.5214, 8.9737]` | Puesto de Hidratación 05 (Km 25) |
| `punta_paitilla` | Punta Paitilla | `[-79.5110, 8.9789]` | Puesto de Hidratación 06 + Médico (Km 30) |
| `panama_viejo` | Conjunto Monumental de Panamá Viejo | `[-79.4858, 9.0058]` | Línea de Meta (Km 42.195) |

---

## 💻 3. Paso a Paso: Implementación en Código

Abre el archivo [starter/agent.py](file:///C:/Users/aaron/Documents/GDE/Workshops/cloud_runner_2049/cloud-runner-2049-workshop/starter/agent.py) y dirígete a las secciones **`TODO 2`** y **`TODO 5`**.

### Paso 3.1: Registro de Herramientas en el Agente ADK
En ADK, cualquier función tipada de Python con docstrings descriptivos se convierte automáticamente en una herramienta invocable por el LLM:

```python
def consultar_landmarks_panama(filtro: str = "") -> list[dict[str, Any]]:
    """Consulta los puntos clave (landmarks) disponibles para el trazado del circuito.

    Args:
        filtro: Palabra clave para filtrar landmarks (ej. 'cinta', 'casco', etc.).
    """
    ...

def calcular_itinerario_maraton(waypoints_ids: list[str]) -> dict[str, Any]:
    """Calcula la distancia acumulada y valida la secuencia de puntos de paso de la carrera."""
    ...
```

Asigna estas herramientas a la lista `tools` del agente:

```python
planner_agent = Agent(
    name="race_course_planner",
    model=MODEL_NAME,
    description="Agente planificador de circuitos con capacidades de mapas.",
    instruction=INSTRUCCIONES_PLANIFICADOR,
    tools=[
        consultar_landmarks_panama,
        calcular_itinerario_maraton,
    ],
)
```

> **Nota para Remote MCP en Producción:**
> Cuando conectes un servidor MCP remoto en tiempo real, puedes utilizar la clase `McpToolset` provista por ADK:
> ```python
> from google.adk.tools.mcp_tool import McpToolset, SseConnectionParams
> 
> maps_mcp_toolset = McpToolset(
>     connection_params=SseConnectionParams(url="http://localhost:8000/sse", timeout=30)
> )
> planner_agent.tools.append(maps_mcp_toolset)
> ```

### Paso 3.2: Generación del Estándar GeoJSON RFC 7946
Un error crítico recurrente en modelos de lenguaje es invertir la latitud y la longitud.
El estándar GeoJSON exige obligatoriamente:
$$\text{Coordenadas} = [\text{Longitud}, \text{Latitud}]$$

Implementa la función `generar_geojson_oficial`:

```python
import geojson

def generar_geojson_oficial(archivo_salida: str | None = None) -> dict[str, Any]:
    coordenadas_trazado = [
        [-79.5268, 8.9147],  # Km 0: Calzada de Amador
        [-79.5459, 8.9323],  # Km 5: Biomuseo
        [-79.5352, 8.9524],  # Km 10: Casco Antiguo
        [-79.5333, 8.9593],  # Km 15: Mercado de Mariscos
        [-79.5279, 8.9683],  # Km 20: Monumento a Balboa
        [-79.5214, 8.9737],  # Km 25: Parque Urracá
        [-79.5110, 8.9789],  # Km 30: Punta Paitilla
        [-79.4858, 9.0058],  # Km 42.195: Panamá Viejo
    ]

    # Feature principal: Trayecto de carrera (LineString)
    linea = geojson.Feature(
        geometry=geojson.LineString(coordenadas_trazado),
        properties={
            "name": "Circuito Oficial Maratón Ciudad de Panamá 2049",
            "distance_km": 42.195,
            "stroke": "#00FFCC",
        },
    )

    coleccion = geojson.FeatureCollection([linea])

    if archivo_salida:
        with open(archivo_salida, "w", encoding="utf-8") as f:
            geojson.dump(coleccion, f, indent=2)

    return coleccion
```

---

## 🧪 4. Verificación y Resultados

Ejecuta el script de solución para verificar la generación cartográfica:

```powershell
python solution/agent.py
```

Comprueba que se genere el archivo `solution/marathon_route.geojson`. Puedes visualizar este archivo arrastrándolo directamente a visores web como [geojson.io](https://geojson.io).

---

## 🚀 Próximo Paso
En el [Lab 03: Evaluador Sub-Agente (LLM-as-a-Judge)](file:///C:/Users/aaron/Documents/GDE/Workshops/cloud_runner_2049/cloud-runner-2049-workshop/labs/03-evaluator-subagent.md), construiremos un subagente validador con ventana de contexto acotada para evitar desviaciones y certificar que la ruta cumpla todas las normas.
