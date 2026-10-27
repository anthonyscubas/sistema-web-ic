import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def generar_analisis_gerencial(periodo, resumen, por_canal, resultados):
    """
    Envía a Ollama únicamente los datos necesarios para analizar el periodo.
    Las notas y los estados ya vienen calculados por el proyecto.
    """

    datos = {
        "periodo": periodo,
        "resumen": resumen,
        "canales": [
            {
                "canal": canal["canal"],
                "analistas": canal["total"],
                "evaluados": canal["evaluados"],
                "promedio": canal["promedio"],
            }
            for canal in por_canal
        ],
        "analistas": [
            {
                "nombre": r["analista"].nombre,
                "canal": r["analista"].canal,
                "estado": r.get("estado"),
                "nota_final": r.get("nota_final"),
                "nota_interna": r.get("nota_interna"),
                "nota_alicorp": r.get("nota_alicorp"),
                "evaluaciones_realizadas": r.get("evaluaciones_realizadas"),
                "evaluacion_completa": r.get("evaluacion_completa"),

                # Indicadores internos
                "cumplimiento_interno": r.get("cumplimiento_interno"),
                "calidad_interna": r.get("calidad_interna"),
                "autonomia": r.get("autonomia"),
                "prevencion_comunicacion": r.get("prevencion_comunicacion"),
                "mejora_continua": r.get("mejora_continua"),

                # Evaluación Alicorp
                "publica_reportes_tiempo": r.get("publica_reportes_tiempo"),
                "participa_reuniones": r.get("participa_reuniones"),
                "comunica_incidencias_tiempo": r.get("comunica_incidencias_tiempo"),
                "resuelve_incidencias_tiempo": r.get("resuelve_incidencias_tiempo"),
                "comunica_status_tiempo": r.get("comunica_status_tiempo"),
                "verifica_consistencia_datos": r.get("verifica_consistencia_datos"),
                "propone_soluciones": r.get("propone_soluciones"),

                # Porcentajes
                "porcentaje_interno": r.get("porcentaje_interno"),
                "porcentaje_alicorp": r.get("porcentaje_alicorp"),
            }
            for r in resultados
        ],
    }

    instrucciones = """
Eres un analista de inteligencia comercial que escribe para gerencia.
Analiza exclusivamente los datos JSON proporcionados.

Devuelve solamente un objeto JSON con estas cuatro claves:
"resumen_ejecutivo", "canales_prioritarios",
"acciones_recomendadas" y "datos_pendientes".

Cada valor debe ser un texto breve en español, claro y profesional.
Menciona las cifras que justifican tus observaciones.
Distingue IC sin encuestas, con una encuesta y con evaluación completa.
No inventes causas, tendencias ni comparaciones con meses anteriores.
El puntaje final está sobre 100: la evaluación interna aporta hasta 45 puntos y Alicorp hasta 55. No recalcules notas ni cambies los estados recibidos.
Si falta información para recomendar una acción específica, indica qué revisar.
No incluyas direcciones de correo ni datos que no estén en el JSON.
"""

    cuerpo = {
        "model": os.getenv("OLLAMA_MODEL", "gemma3:4b"),
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2},
        "messages": [
            {"role": "system", "content": instrucciones},
            {
                "role": "user",
                "content": json.dumps(datos, ensure_ascii=False),
            },
        ],
    }

    url = os.getenv(
        "OLLAMA_URL",
        "http://127.0.0.1:11434/api/chat",
    )

    peticion = Request(
        url,
        data=json.dumps(cuerpo, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(peticion, timeout=120) as respuesta:
            contenido = json.load(respuesta)

        texto = contenido["message"]["content"]
        analisis = json.loads(texto)

    except (URLError, HTTPError, TimeoutError, OSError) as exc:
        raise RuntimeError(
            "No se pudo conectar con Ollama. Comprueba que esté instalado "
            "y en ejecución en la computadora donde corre la web."
        ) from exc

    except (KeyError, ValueError, TypeError) as exc:
        raise RuntimeError(
            "Ollama respondió, pero no devolvió un análisis válido. "
            "Intenta generar el análisis nuevamente."
        ) from exc

    campos = (
        "resumen_ejecutivo",
        "canales_prioritarios",
        "acciones_recomendadas",
        "datos_pendientes",
    )

    if not all(
        isinstance(analisis.get(campo), str)
        for campo in campos
    ):
        raise RuntimeError(
            "El análisis recibido no tiene todos los apartados esperados."
        )

    return analisis