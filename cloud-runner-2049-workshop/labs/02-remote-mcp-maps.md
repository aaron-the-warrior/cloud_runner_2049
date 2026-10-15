# Lab 02: Conexión de Herramientas Externas con Google Maps Remote MCP y GeoJSON

## 🎯 Objetivos de Aprendizaje

Al finalizar este laboratorio, serás capaz de:
1. Comprender la arquitectura de **Model Context Protocol (MCP)** y su variante **Remote MCP** sobre SSE (Server-Sent Events) o Stdio.
2. Integrar herramientas de consulta cartográfica y cálculo de distancias al agente ADK.
3. Modelar las restricciones urbanas de Las Vegas (The Strip, autopistas, perfiles de elevación).
4. Generar y exportar la ruta oficial en formato **GeoJSON RFC 7946** con geometrías `LineString` y `Point`.

---

## 🗺️ 1. ¿Qué es MCP y por qué Remote MCP?

**Model Context Protocol (MCP)** es un estándar abierto desarrollado para permitir que los agentes de IA descubran, invoquen y consuman herramientas, fuentes de datos y contexto de forma interoperable.

En la demo de Google Cloud Next **Race Condition**, el simulador utiliza un servidor MCP para interactuar con los servicios geoespaciales de Google Maps:
- **Desacoplamiento:** El modelo no necesita conocer los detalles de autenticación o endpoints HTTP de Google Maps; solo invoca herramientas tipadas expuestas por el servidor MCP.
- **Remote MCP:** Permite que el servidor MCP se ejecute en un contenedor independiente (por ejemplo, en Cloud Run o en un pod de Kubernetes) y sea consumido por agentes a través de transporte de red SSE o WebSockets.

---

## 📍 2. Herramientas Cartográficas de Las Vegas

Para planificar el maratón, nuestro agente necesita interactuar con waypoints icónicos a lo largo de Las Vegas Blvd y Downtown:

| Identificador | Nombre del Landmark | Coordenadas [Lon, Lat] | Rol en la Carrera |
| :--- | :--- | :--- | :--- |
| `welcome_sign` | Welcome to Fabulous Las Vegas Sign | `[-115.1728, 36.0820]` | Línea de Salida (Km 0) |
| `mandalay_bay` | Mandalay Bay Resort | `[-115.1752, 36.0919]` | Puesto de Hidratación 01 (Km 5) |
| `bellagio` | Bellagio Fountains | `[-115.1764, 36.1126]` | Puesto de Hidratación 02 + Médico (Km 10) |
| `the_sphere` | The Sphere Las Vegas | `[-115.1620, 36.1212]` | Puesto de Hidratación 03 (Km 15) |
| `convention_center` | Las Vegas Convention Center | `[-115.1523, 36.1315]` | Puesto de Hidratación 04 + Médico (Km 20) |
| `stratosphere` | The STRAT Hotel & Tower | `[-115.1558, 36.1475]` | Puesto de Hidratación 05 (Km 25) |
| `arts_district` | Las Vegas Arts District | `[-115.1525, 36.1565]` | Puesto de Hidratación 06 + Médico (Km 30) |
| `fremont_street` | Fremont Street Experience | `[-115.1438, 36.1707]` | Línea de Meta (Km 42.195) |

---

## 💻 3. Paso a Paso: Implementación en Código

Abre el archivo [starter/agent.py](file:///C:/Users/aaron/Documents/GDE/Workshops/cloud_runner_2049/cloud-runner-2049-workshop/starter/agent.py) y dirígete a las secciones **`TODO 2`** y **`TODO 5`**.

### Paso 3.1: Registro de Herramientas en el Agente ADK
En ADK, cualquier función tipada de Python con docstrings descriptivos se convierte automáticamente en una herramienta invocable por el LLM:

```python
def consultar_landmarks_las_vegas(filtro: str = "") -> list[dict[str, Any]]:
    """Consulta los puntos clave (landmarks) disponibles para el trazado del circuito.

    Args:
        filtro: Palabra clave para filtrar landmarks (ej. 'strip', 'sphere', etc.).
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
        consultar_landmarks_las_vegas,
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
        [-115.1728, 36.0820],  # Km 0: Welcome Sign
        [-115.1752, 36.0919],  # Km 5: Mandalay Bay
        [-115.1764, 36.1126],  # Km 10: Bellagio
        [-115.1620, 36.1212],  # Km 15: The Sphere
        [-115.1523, 36.1315],  # Km 20: Convention Center
        [-115.1558, 36.1475],  # Km 25: Stratosphere
        [-115.1525, 36.1565],  # Km 30: Arts District
        [-115.1438, 36.1707],  # Km 42.195: Fremont Street
    ]

    # Feature principal: Trayecto de carrera (LineString)
    linea = geojson.Feature(
        geometry=geojson.LineString(coordenadas_trazado),
        properties={
            "name": "Circuito Oficial Maratón Las Vegas 2049",
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
