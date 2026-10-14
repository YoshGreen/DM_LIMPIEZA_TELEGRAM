"""
Paso 1-3: carga, limpieza, separacion por temporada y diccionario de emojis.
Uso:  python analisis_telegram.py [result.json]
Salidas (carpeta salida/):
  mensajes_limpios.csv   -> un mensaje por fila, texto limpio
  emojis_frecuencia.csv  -> TODOS los emojis con conteo (texto, stickers, reacciones)
  diccionario_emojis.csv -> plantilla para que TU escribas el significado en el grupo
"""
import json, re, sys, os, unicodedata, hashlib
from collections import Counter
import pandas as pd

# Expresiones regulares para limpieza
RE_URL = re.compile(r"https?://\S+|www\.\S+")
RE_TEL = re.compile(r"\+?\d[\d\s\-]{6,}\d")
RE_MENCION = re.compile(r"@\w+")

# Deteccion de emojis
try:
    import emoji                                   # pip install emoji
    def extraer_emojis(t):
        return [e["emoji"] for e in emoji.emoji_list(t)]
except ImportError:                                # plan B sin libreria
    RE_EMOJI = re.compile(
        "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF"
        "\U00002B00-\U00002BFF\U00002300-\U000023FF\U0000FE0F\U0000200D]+")
    def extraer_emojis(t):
        out = []
        for bloque in RE_EMOJI.findall(t):
            # separa secuencias, conservando ZWJ (ej. ❤️‍🔥)
            out += re.findall(r".\ufe0f?(?:\u200d.\ufe0f?)*", bloque)
        return [e for e in out if e.strip()]

def norm_emoji(e):                                 # ❤ y ❤️ son el mismo emoji
    if not isinstance(e, str):
        return ""
    return e.replace("\ufe0f", "")

def aplanar(texto):
    """El campo 'text' es str o lista mezclada de str y dicts {'type','text'}."""
    if isinstance(texto, str):
        return texto
    return "".join(p if isinstance(p, str) else p.get("text", "") for p in texto)

def limpiar(t):
    if not isinstance(t, str):
        return ""
    t = unicodedata.normalize("NFC", t)
    t = RE_URL.sub(" ", t)
    t = RE_TEL.sub(" ", t)
    t = RE_MENCION.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def temporada(f):
    if hasattr(f, "month"):
        m, y = f.month, f.year
    else:
        f = pd.to_datetime(f)
        m, y = f.month, f.year
    if m == 7:  return f"invierno_{y}"
    if m == 1:  return f"verano_{y}"
    return "otro"

def procesar_telegram(ruta="result.json"):
    """Carga y procesa el archivo exportado de Telegram."""
    with open(ruta, encoding="utf-8") as f:
        data = json.load(f)

    filas = []
    for m in data.get("messages", []):
        if m.get("type") != "message":          # descarta mensajes de servicio (joins, etc.)
            continue
        filas.append({
            "id": m["id"],
            "fecha": m["date"],
            "autor_id": m.get("from_id"),
            "autor": m.get("from"),
            "texto_original": aplanar(m.get("text", "")),
            "responde_a": m.get("reply_to_message_id"),
            "media": m.get("media_type") or ("photo" if "photo" in m else None),
            "sticker_emoji": m.get("sticker_emoji"),
            "reacciones": m.get("reactions", []),
            "editado": "edited" in m,
            "n_enlaces": sum(1 for e in m.get("text_entities", []) if e.get("type") == "link"),
        })
    df = pd.DataFrame(filas)
    df["fecha"] = pd.to_datetime(df["fecha"])

    # Anonimizar autores (importante: son datos de personas reales)
    df["autor_anon"] = df["autor_id"].fillna("desconocido").map(
        lambda x: "U_" + hashlib.md5(str(x).encode()).hexdigest()[:6])
    df = df.drop(columns=["autor", "autor_id"])

    df["texto_limpio"] = df["texto_original"].map(limpiar)
    df["texto_minus"] = df["texto_limpio"].str.lower()

    df["emojis"] = df["texto_original"].map(lambda t: [norm_emoji(e) for e in extraer_emojis(t)])
    df["n_emojis"] = df["emojis"].str.len()

    df["temporada"] = df["fecha"].map(temporada)
    df["hora"] = df["fecha"].dt.hour
    df["dia_semana"] = df["fecha"].dt.day_name()

    # Conteo de fuentes
    fuentes = {"texto": Counter(), "sticker": Counter(), "reaccion": Counter()}
    for lista in df["emojis"]:
        fuentes["texto"].update(lista)
    fuentes["sticker"].update(norm_emoji(e) for e in df["sticker_emoji"].dropna())
    for reacs in df["reacciones"]:
        for r in reacs:
            if r.get("type") == "emoji":
                fuentes["reaccion"][norm_emoji(r["emoji"])] += r.get("count", 0)

    todos = set().union(*[set(c) for c in fuentes.values()])
    frec = pd.DataFrame({
        "emoji": list(todos),
        **{f"n_{k}": [fuentes[k][e] for e in todos] for k in fuentes},
    })
    frec["total"] = frec[[c for c in frec.columns if c.startswith("n_")]].sum(axis=1)
    frec = frec.sort_values("total", ascending=False)
    frec["nombre_oficial"] = frec["emoji"].map(
        lambda e: unicodedata.name(e[0], "") if e else "")

    return df, frec, fuentes

def main(ruta="result.json"):
    os.makedirs("salida", exist_ok=True)
    df, frec, fuentes = procesar_telegram(ruta)

    frec.to_csv("salida/emojis_frecuencia.csv", index=False, encoding="utf-8-sig")

    def ejemplos(e, k=3):
        sub = df[df["texto_original"].str.contains(re.escape(e), regex=True)]
        return " || ".join(sub["texto_limpio"].head(k).str.slice(0, 80))

    dic = frec.head(60)[["emoji", "total", "nombre_oficial"]].copy()
    dic["ejemplos_de_uso"] = dic["emoji"].map(ejemplos)
    dic["significado_en_el_grupo"] = ""
    dic["categoria"] = ""
    dic["sentimiento"] = ""
    dic.to_csv("salida/diccionario_emojis.csv", index=False, encoding="utf-8-sig")

    out = df.drop(columns=["reacciones"]).copy()
    out["emojis"] = out["emojis"].map("".join)
    out.to_csv("salida/mensajes_limpios.csv", index=False, encoding="utf-8-sig")

    print("Mensajes:", len(df))
    print("\nMensajes por temporada:")
    print(df[df.temporada != "otro"].groupby("temporada").size())
    print("\nTop 15 emojis (texto+stickers+reacciones):")
    print(frec.head(15)[["emoji", "n_texto", "n_sticker", "n_reaccion", "total"]].to_string(index=False))

if __name__ == "__main__":
    ruta_input = sys.argv[1] if len(sys.argv) > 1 else "result.json"
    main(ruta_input)
