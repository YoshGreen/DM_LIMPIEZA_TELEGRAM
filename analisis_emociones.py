"""
Paso 2: tokenizacion por oracion + deteccion de 15 emociones (enero vs julio).
Requiere haber ejecutado antes analisis_telegram.py (usa salida/mensajes_limpios.csv).
Uso:  python analisis_emociones.py [salida/mensajes_limpios.csv]
Salidas (carpeta salida/):
  oraciones_tokenizadas.csv   -> una fila por oracion, con tokens y emociones detectadas
  resumen_emociones.csv       -> conteo y % de cada emocion por temporada y por estacion
  ejemplos_por_emocion.csv    -> oraciones de ejemplo para VALIDAR a mano cada emocion
  top_palabras_estacion.csv   -> palabras mas usadas en invierno vs verano
"""
import re, sys, unicodedata, os
from collections import Counter
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")        # evita errores con emojis en Windows
    except Exception:
        pass

def norm(t):
    """minusculas y sin tildes (las comparaciones se hacen sobre este texto)."""
    t = unicodedata.normalize("NFD", str(t))
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower()

# ------------------------------------------------------------------
# 1. LEXICO DE 15 EMOCIONES  (editalo: es tu parte de analisis!)
#    palabras: expresiones regulares sobre texto sin tildes (prefijo de palabra)
#    emojis:   caracteres que expresan esa emocion
#    positiva: si es True, se ignora cuando esta negada ("no gracias", "no estoy feliz")
# ------------------------------------------------------------------
LEXICO = {
    "Gratitud": dict(positiva=True, emojis="🙏",
        palabras=[r"gracias", r"agradec", r"muy amable", r"bendic"]),
    "Alegria/Entusiasmo": dict(positiva=True, emojis="😀😁😊😄🎉🥳🤩❤🔥",
        palabras=[r"feliz", r"felicidades", r"felicitaciones", r"alegr", r"genial",
                  r"excelente", r"que bien", r"contento", r"emocionad", r"vamos", r"aprobe", r"aprobamos"]),
    "Humor/Risa": dict(positiva=False, emojis="😂🤣😅😆😹",
        palabras=[r"ja(ja)+", r"je(je)+", r"jsjs", r"\bxd+\b", r"\blol\b"]),
    "Esperanza": dict(positiva=True, emojis="🤞",
        palabras=[r"ojala", r"espero", r"esperemos", r"confio", r"ojala"]),
    "Alivio": dict(positiva=True, emojis="😌",
        palabras=[r"menos mal", r"por fin", r"que alivio", r"aliviad", r"por suerte"]),
    "Aprobacion/Acuerdo": dict(positiva=True, emojis="👍👌✅💯",
        palabras=[r"de acuerdo", r"correcto", r"exacto", r"claro que si", r"asi es",
                  r"perfecto", r"\bdale\b", r"\bok\b", r"\blisto\b", r"entendido", r"enterado"]),
    "Confusion/Duda": dict(positiva=False, emojis="🤔😕🤷",
        palabras=[r"no entiendo", r"confus", r"no comprendo", r"no me queda claro",
                  r"estoy perdid", r"me siento perdid", r"como asi", r"no se que", r"no se como", r"no sabia"]),
    "Ansiedad/Preocupacion": dict(positiva=False, emojis="😰😨😱😬😟",
        palabras=[r"preocup", r"nervio", r"ansied", r"miedo", r"estres", r"angusti",
                  r"me asusta", r"inquiet", r"que pasara", r"sera que"]),
    "Urgencia/Presion": dict(positiva=False, emojis="⏰⌛🚨⚠",
        palabras=[r"urgente", r"urgencia", r"ultimo dia", r"hasta hoy", r"hasta manana",
                  r"a tiempo", r"apurar", r"rapido", r"cuanto antes", r"se acaba", r"plazo", r"vence", r"limite"]),
    "Frustracion": dict(positiva=False, emojis="😩😫😤",
        palabras=[r"no puedo", r"no me deja", r"no funciona", r"no carga", r"no aparece",
                  r"no sale", r"sigue sin", r"otra vez", r"de nuevo", r"siempre lo mismo",
                  r"cansad", r"harto", r"harta", r"\berror", r"falla", r"bloquead", r"problema"]),
    "Enojo/Indignacion": dict(positiva=False, emojis="😡🤬😠👿",
        palabras=[r"molest", r"me enoj", r"indign", r"injust", r"abuso", r"descaro", r"verguenza",
                  r"inaceptable", r"pesim", r"ridicul"]),
    "Tristeza/Decepcion": dict(positiva=False, emojis="😢😭😞😔💔🥲",
        palabras=[r"triste", r"lastima", r"lamentabl", r"decepcion", r"desilusion",
                  r"que pena", r"llorar", r"que mal\b", r"reprobe"]),
    "Desconfianza/Sospecha": dict(positiva=False, emojis="🧐🤨",
        palabras=[r"rumor", r"dicen que", r"sera verdad", r"sera cierto", r"estafa",
                  r"no confio", r"sospech", r"enga[nñ]", r"\bfake\b", r"supuestamente", r"mentira"]),
    "Burla/Ironia": dict(positiva=False, emojis="🤡🙄😏🤭💀☠",
        palabras=[r"claro claro", r"ahora si\b", r"genios"]),
    "Desaprobacion/Rechazo": dict(positiva=False, emojis="👎🙅🚫❌",
        palabras=[r"no estoy de acuerdo", r"no me parece", r"no deberian", r"mal hecho",
                  r"mal servicio", r"no corresponde"]),
}

NEG = r"(?<!\bno )(?<!\bni )(?<!\bnunca )(?<!\bsin )"
for emo, cfg in LEXICO.items():
    pre = NEG if cfg["positiva"] else ""
    cfg["regex"] = re.compile("|".join(pre + r"\b" + p for p in cfg["palabras"]))
    cfg["emoji_set"] = [e for e in cfg["emojis"]]

STOP = set("""que de la el en y a los las un una por para con del al se lo es no si mas pero como
 su sus le les me mi te tu ya muy este esta ese esa eso son hay ser fue o u e hasta desde sobre entre
 tambien solo nos cuando donde porque qu q x ah va ve""".split())

TOKEN = re.compile(r"[a-z]+|[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]")
SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+|\n+")

def detectar(oracion_norm):
    hallar = []
    for emo, cfg in LEXICO.items():
        if cfg["regex"].search(oracion_norm) or any(e in oracion_norm for e in cfg["emoji_set"]):
            hallar.append(emo)
    return hallar

def tokenizar_y_detectar(df_mensajes, solo_temporada=False):
    """
    Tokeniza por oraciones un DataFrame de mensajes limpios y detecta emociones.
    Si solo_temporada es True, filtra solo verano/invierno como el script original.
    """
    df = df_mensajes.copy()
    df["texto_limpio"] = df["texto_limpio"].fillna("")
    if not pd.api.types.is_datetime64_any_dtype(df["fecha"]):
        df["fecha"] = pd.to_datetime(df["fecha"])
    
    if solo_temporada:
        df = df[df["temporada"] != "otro"]                        # solo enero / julio
        
    df = df[(df["texto_limpio"].str.len() > 0) &
            (df["texto_limpio"].str.len() <= 300)]            # fuera anuncios largos y mensajes sin texto
    
    if "estacion" not in df.columns:
        df["estacion"] = df["temporada"].str.split("_").str[0]    # invierno / verano / otro

    filas = []
    for r in df.itertuples():
        for k, oracion in enumerate(SENT_SPLIT.split(r.texto_limpio)):
            oracion = oracion.strip()
            if not oracion:
                continue
            n = norm(oracion)
            tokens = TOKEN.findall(n)
            if not tokens:
                continue
            emos = detectar(n)
            filas.append({
                "id_mensaje": getattr(r, "id", 0),
                "n_oracion": k,
                "fecha": r.fecha,
                "temporada": getattr(r, "temporada", "otro"),
                "estacion": getattr(r, "estacion", "otro"),
                "autor_anon": getattr(r, "autor_anon", "desconocido"),
                "oracion": oracion,
                "tokens": " ".join(tokens),
                "n_tokens": len(tokens),
                "es_pregunta": ("?" in oracion) or bool(re.search(r"\balguien (sabe|me)|\bsaben (si|que|como)", n)),
                "emociones": ";".join(emos),
                "n_emociones": len(emos),
            })
    return pd.DataFrame(filas)

def procesar_emociones(entrada="salida/mensajes_limpios.csv"):
    os.makedirs("salida", exist_ok=True)
    df = pd.read_csv(entrada)
    oc = tokenizar_y_detectar(df, solo_temporada=True)
    oc.to_csv("salida/oraciones_tokenizadas.csv", index=False, encoding="utf-8-sig")

    # 4. RESUMEN POR TEMPORADA Y POR ESTACION
    exp = oc[oc["n_emociones"] > 0].assign(emocion=lambda d: d["emociones"].str.split(";")).explode("emocion")
    resumen = []
    for col in ["temporada", "estacion"]:
        tot = oc.groupby(col).size()
        cuenta = exp.groupby([col, "emocion"]).size().rename("n").reset_index()
        cuenta["total_oraciones"] = cuenta[col].map(tot)
        cuenta["por_cada_1000"] = (cuenta["n"] / cuenta["total_oraciones"] * 1000).round(1)
        cuenta = cuenta.rename(columns={col: "grupo"}); cuenta.insert(0, "nivel", col)
        resumen.append(cuenta)
    resumen = pd.concat(resumen).sort_values(["nivel", "grupo", "n"], ascending=[True, True, False])
    resumen.to_csv("salida/resumen_emociones.csv", index=False, encoding="utf-8-sig")

    # Ejemplos para validar manualmente
    partes = []
    for emo in exp["emocion"].unique():
        g = exp[exp["emocion"] == emo]
        partes.append(g.sample(min(10, len(g)), random_state=1))
    if partes:
        ej = pd.concat(partes)[["emocion", "temporada", "oracion"]]
        ej["correcto_si_no"] = ""
        ej.to_csv("salida/ejemplos_por_emocion.csv", index=False, encoding="utf-8-sig")

    # Palabras mas frecuentes por estacion
    rows = []
    for est, g in oc.groupby("estacion"):
        c = Counter(t for s in g["tokens"] for t in s.split() if t not in STOP and len(t) > 2)
        rows += [{"estacion": est, "palabra": w, "n": n} for w, n in c.most_common(40)]
    pd.DataFrame(rows).to_csv("salida/top_palabras_estacion.csv", index=False, encoding="utf-8-sig")

    # 5. RESUMEN EN PANTALLA
    print("Oraciones analizadas por estacion:\n", oc.groupby("estacion").size().to_string())
    print("\nOraciones con al menos una emocion (%):")
    print((oc.assign(c=oc.n_emociones > 0).groupby("estacion")["c"].mean() * 100).round(1).to_string())
    print("\nEmociones por cada 1000 oraciones:")
    tab = (resumen[resumen["nivel"] == "estacion"]
           .pivot(index="emocion", columns="grupo", values="por_cada_1000").fillna(0))
    print(tab.sort_values(tab.columns[0], ascending=False).to_string())

if __name__ == "__main__":
    entrada_input = sys.argv[1] if len(sys.argv) > 1 else "salida/mensajes_limpios.csv"
    procesar_emociones(entrada_input)