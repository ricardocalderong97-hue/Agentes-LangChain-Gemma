"""Punto 6: herramientas del agente, como en el notebook original."""
import os
import requests
from langchain.tools import tool


@tool
def multiplicar(a: float, b: float) -> float:
    """Multiplica exactamente dos números dados por el usuario."""
    return a * b


@tool
def clima(ciudad: str) -> str:
    """Consulta el clima de una ciudad. Por defecto usa el clima FICTICIO del tutorial.

    Para usar datos actuales, define CLIMA_REAL=true en el archivo .env.
    """
    if os.getenv("CLIMA_REAL", "false").lower() != "true":
        return f"Clima SIMULADO del ejercicio para {ciudad}: 24 °C y soleado. No son datos actuales."

    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": ciudad, "count": 1, "language": "es", "format": "json"},
            timeout=15,
        )
        geo.raise_for_status()
        lugares = geo.json().get("results", [])
        if not lugares:
            return f"No encontré la ciudad '{ciudad}' en Open-Meteo."
        lugar = lugares[0]
        meteo = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lugar["latitude"],
                "longitude": lugar["longitude"],
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                "timezone": "auto",
            },
            timeout=15,
        )
        meteo.raise_for_status()
        actual = meteo.json()["current"]
        return (
            f"Clima ACTUAL según Open-Meteo en {lugar['name']}, {lugar.get('country', '')}: "
            f"{actual['temperature_2m']} °C, humedad {actual['relative_humidity_2m']} %, "
            f"viento {actual['wind_speed_10m']} km/h, código meteorológico WMO "
            f"{actual['weather_code']}. Hora local de medición: {actual['time']}."
        )
    except (requests.RequestException, KeyError, ValueError) as exc:
        return f"No fue posible obtener datos actuales de clima: {exc}"
