"""
wiki.py — Wikipedia API para perfil base de empresa.
100% gratuito. Sin API key necesaria.
"""
import wikipedia
import time

wikipedia.set_lang("es")


def get_company_profile(empresa: str) -> str:
    """
    Obtiene resumen de Wikipedia en español.
    Fallback a inglés si no hay artículo en español.
    """
    time.sleep(0.5)
    try:
        summary = wikipedia.summary(empresa, sentences=4, auto_suggest=True)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        # Tomar la primera opción si hay ambigüedad
        try:
            summary = wikipedia.summary(e.options[0], sentences=4)
            return summary
        except Exception:
            pass
    except Exception:
        pass

    # Fallback a inglés
    try:
        wikipedia.set_lang("en")
        summary = wikipedia.summary(empresa, sentences=4, auto_suggest=True)
        wikipedia.set_lang("es")
        return f"[Inglés] {summary}"
    except Exception:
        wikipedia.set_lang("es")
        return f"No se encontró perfil en Wikipedia para '{empresa}'."
