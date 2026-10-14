"""
=============================================================================
DASHBOARD INTERACTIVO: ANÁLISIS DE TELEGRAM (EMOJIS Y EMOCIONES 2025 - 2026)
Minería de Datos - Presentación Académica
Tema: Oscuro puro (#000000) con estética Neón de alto contraste
Ejecución: streamlit run dashboard.py
=============================================================================
"""

import os
import json
import re
import unicodedata
from collections import Counter

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# Importar funciones y constantes de los scripts originales (reutilización sin duplicar)
from analisis_telegram import norm_emoji, temporada, limpiar
from analisis_emociones import norm, detectar, LEXICO, STOP, TOKEN, SENT_SPLIT, tokenizar_y_detectar

# =============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO NEÓN
# =============================================================================
st.set_page_config(
    page_title="Dashboard Telegram | Emojis & Emociones",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta de colores Neón de alta luminosidad
NEON = {
    "cyan": "#00F5FF",
    "magenta": "#FF007F",
    "lime": "#39FF14",
    "yellow": "#FFE600",
    "orange": "#FF6B00",
    "purple": "#9D00FF",
    "pink": "#FF1493",
    "electric_blue": "#0080FF",
    "chartreuse": "#DFFF00",
    "red_orange": "#FF3300",
    "bright_teal": "#00FFCC",
    "deep_violet": "#7928CA"
}

PALETA_NEON = [
    NEON["cyan"], NEON["magenta"], NEON["lime"], NEON["yellow"],
    NEON["orange"], NEON["purple"], NEON["pink"], NEON["electric_blue"],
    NEON["chartreuse"], NEON["bright_teal"], NEON["red_orange"], NEON["deep_violet"]
]

# Inyección de estilos CSS para fondo negro puro y detalles fluorescentes
st.markdown("""
<style>
    /* Fondo negro absoluto en toda la aplicación */
    .stApp {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    /* Sidebar fondo negro con borde sutil */
    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #1a1a1a !important;
    }
    /* Métricas estilizadas con tarjetas neón */
    [data-testid="stMetric"] {
        background: #080808;
        border: 1px solid #1e1e1e;
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 0 12px rgba(0, 245, 255, 0.08);
        transition: all 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        border-color: #00F5FF;
        box-shadow: 0 0 18px rgba(0, 245, 255, 0.25);
    }
    [data-testid="stMetricLabel"] {
        color: #A0A0A0 !important;
        font-weight: 500;
        font-size: 0.9rem;
    }
    [data-testid="stMetricValue"] {
        color: #00F5FF !important;
        font-weight: 700;
        font-size: 1.8rem;
        text-shadow: 0 0 8px rgba(0, 245, 255, 0.4);
    }
    /* Pestañas modernas con indicador cian neón */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #050505;
        padding: 6px;
        border-radius: 10px;
        border: 1px solid #1a1a1a;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #888888;
        font-size: 1rem;
        font-weight: 600;
        padding: 0 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #111111 !important;
        color: #00F5FF !important;
        border-bottom: 2px solid #00F5FF !important;
        text-shadow: 0 0 10px rgba(0, 245, 255, 0.5);
    }
    /* Títulos con brillo */
    h1, h2, h3 {
        color: #FFFFFF !important;
        letter-spacing: -0.5px;
    }
    .neon-title {
        color: #00F5FF;
        text-shadow: 0 0 12px rgba(0, 245, 255, 0.5), 0 0 25px rgba(0, 245, 255, 0.2);
        font-weight: 800;
    }
    /* Botones de descarga */
    .stDownloadButton button {
        background-color: #0a0a0a !important;
        color: #00F5FF !important;
        border: 1px solid #00F5FF !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stDownloadButton button:hover {
        background-color: #00F5FF !important;
        color: #000000 !important;
        box-shadow: 0 0 15px rgba(0, 245, 255, 0.6) !important;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# 2. CARGA DE DATOS EN CACHÉ (@st.cache_data)
# =============================================================================
MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}
MESES_NUM = {v: k for k, v in MESES_ES.items()}

@st.cache_data(show_spinner=False)
def cargar_datos_base():
    """
    Carga y estructura los datos de mensajes, diccionario de emojis y oraciones.
    Aplica anonimización determinista 'Persona 1', 'Persona 2', etc.
    """
    os.makedirs("salida", exist_ok=True)

    # 1. Mensajes completos (con texto, stickers y reacciones)
    if os.path.exists("salida/mensajes_completos.csv"):
        df_m = pd.read_csv("salida/mensajes_completos.csv")
    elif os.path.exists("salida/mensajes_limpios.csv"):
        df_m = pd.read_csv("salida/mensajes_limpios.csv")
        df_m["emojis_str"] = df_m["emojis"].fillna("")
        df_m["reacciones_str"] = "[]"
    else:
        # Fallback al json original
        from analisis_telegram import procesar_telegram
        df_m, _, _ = procesar_telegram("result.json")
        df_m["reacciones_str"] = df_m["reacciones"].map(json.dumps)
        df_m["emojis_str"] = df_m["emojis"].map(lambda x: ",".join(x) if x else "")

    df_m["fecha"] = pd.to_datetime(df_m["fecha"])
    df_m["año"] = df_m["fecha"].dt.year
    df_m["mes_num"] = df_m["fecha"].dt.month
    df_m["mes_nombre"] = df_m["mes_num"].map(MESES_ES)
    df_m["periodo"] = df_m["fecha"].dt.to_period("M").astype(str)

    # Anonimización determinista: de mayor a menor número de mensajes
    conteos_autores = df_m["autor_anon"].value_counts()
    mapa_personas = {}
    for i, (autor_hash, _) in enumerate(conteos_autores.items()):
        if str(autor_hash).lower() in ["desconocido", "none", "nan"]:
            mapa_personas[autor_hash] = "Usuario Desconocido"
        else:
            mapa_personas[autor_hash] = f"Persona {i+1}"

    df_m["remitente"] = df_m["autor_anon"].map(mapa_personas)

    # 2. Diccionario de emojis
    if os.path.exists("salida/diccionario_emojis.csv"):
        df_dict = pd.read_csv("salida/diccionario_emojis.csv")
    else:
        df_dict = pd.DataFrame(columns=["emoji", "total", "nombre_oficial", "categoria", "significado_en_el_grupo", "sentimiento"])

    # 3. Oraciones tokenizadas para emociones
    if os.path.exists("salida/oraciones_2025_2026.csv"):
        df_o = pd.read_csv("salida/oraciones_2025_2026.csv")
    elif os.path.exists("salida/oraciones_tokenizadas.csv"):
        df_o = pd.read_csv("salida/oraciones_tokenizadas.csv")
    else:
        # Generar sobre mensajes
        df_sub = df_m[df_m["año"].isin([2025, 2026])]
        df_o = tokenizar_y_detectar(df_sub, solo_temporada=False)
        df_o.to_csv("salida/oraciones_2025_2026.csv", index=False, encoding="utf-8-sig")

    df_o["fecha"] = pd.to_datetime(df_o["fecha"])
    df_o["año"] = df_o["fecha"].dt.year
    df_o["mes_num"] = df_o["fecha"].dt.month
    df_o["mes_nombre"] = df_o["mes_num"].map(MESES_ES)
    df_o["periodo"] = df_o["fecha"].dt.to_period("M").astype(str)
    df_o["remitente"] = df_o["autor_anon"].map(mapa_personas).fillna("Persona Desconocida")

    return df_m, df_dict, df_o, mapa_personas


# =============================================================================
# 3. FUNCIONES AUXILIARES DE ESTILO PLOTLY (NEÓN Y FONDO NEGRO)
# =============================================================================
def aplicar_estilo_neon(fig, titulo="", subtitulo="", altura=460):
    """
    Aplica diseño oscuro puro (#000000) y detalles neón a cualquier figura Plotly.
    """
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(color="#FFFFFF", family="Segoe UI, sans-serif"),
        title=dict(
            text=f"<b style='color:#00F5FF; font-size:17px;'>{titulo}</b>" +
                 (f"<br><span style='color:#888888; font-size:12px;'>{subtitulo}</span>" if subtitulo else ""),
            x=0.01,
            y=0.96
        ),
        margin=dict(l=40, r=40, t=65, b=45),
        height=altura,
        hoverlabel=dict(
            bgcolor="#0a0a0a",
            font_size=13,
            font_family="Segoe UI, sans-serif",
            bordercolor="#00F5FF"
        ),
        legend=dict(
            bgcolor="rgba(8,8,8,0.85)",
            bordercolor="#222222",
            borderwidth=1,
            font=dict(color="#E0E0E0", size=11)
        ),
        xaxis=dict(
            gridcolor="#151515",
            zerolinecolor="#252525",
            showline=True,
            linecolor="#333333"
        ),
        yaxis=dict(
            gridcolor="#151515",
            zerolinecolor="#252525",
            showline=True,
            linecolor="#333333"
        )
    )
    return fig

def extraer_conteo_emojis(df_filtrado):
    """
    Extrae la frecuencia de emojis considerando texto, stickers y reacciones.
    """
    c_texto = Counter()
    c_sticker = Counter()
    c_reaccion = Counter()

    for ems in df_filtrado["emojis_str"].dropna():
        if ems:
            for e in str(ems).split(","):
                e = e.strip()
                if e:
                    c_texto[e] += 1

    if "sticker_emoji" in df_filtrado.columns:
        for stk in df_filtrado["sticker_emoji"].dropna():
            stk = str(stk).strip()
            if stk:
                c_sticker[stk] += 1

    if "reacciones_str" in df_filtrado.columns:
        for r_json in df_filtrado["reacciones_str"].dropna():
            r_str = str(r_json).strip()
            if r_str and r_str != "[]":
                try:
                    reacs = json.loads(r_str)
                    for r in reacs:
                        if r.get("type") == "emoji" and r.get("emoji"):
                            c_reaccion[r["emoji"]] += r.get("count", 1)
                except Exception:
                    pass

    todos = set().union(c_texto.keys(), c_sticker.keys(), c_reaccion.keys())
    c_total = Counter()
    for e in todos:
        c_total[e] = c_texto[e] + c_sticker[e] + c_reaccion[e]

    return c_total, c_texto, c_sticker, c_reaccion


# =============================================================================
# 4. CARGA PRINCIPAL Y BARRA LATERAL (FILTROS)
# =============================================================================
df_mensajes_raw, df_diccionario, df_oraciones_raw, mapa_personas = cargar_datos_base()

# Filtrar base inicial a 2025 y 2026 (alcance del estudio)
df_base_mensajes = df_mensajes_raw[df_mensajes_raw["año"].isin([2025, 2026])].copy()
df_base_oraciones = df_oraciones_raw[df_oraciones_raw["año"].isin([2025, 2026])].copy()

# ----------------- SIDEBAR -----------------
st.sidebar.markdown("<h2 class='neon-title'>⚙️ Filtros de Control</h2>", unsafe_allow_html=True)
st.sidebar.caption("Personaliza el alcance temporal y los remitentes analizados.")

# 1. Filtro Año
opcion_año = st.sidebar.radio(
    "📅 Año de análisis:",
    options=["Ambos (2025 y 2026)", "2025", "2026"],
    index=0
)

if opcion_año == "2025":
    años_sel = [2025]
elif opcion_año == "2026":
    años_sel = [2026]
else:
    años_sel = [2025, 2026]

# 2. Filtro Mes
lista_meses = [MESES_ES[i] for i in range(1, 13)]
col_m1, col_m2 = st.sidebar.columns([1, 1])
todos_meses = col_m1.checkbox("Todos los meses", value=True)

if todos_meses:
    meses_sel = lista_meses
else:
    meses_sel = st.sidebar.multiselect(
        "📆 Selecciona los meses:",
        options=lista_meses,
        default=["Enero", "Febrero", "Junio", "Julio"]
    )

meses_num_sel = [MESES_NUM[m] for m in meses_sel if m in MESES_NUM]

# 3. Filtro Remitente (Anonimizado)
autores_mas_activos = df_base_mensajes["remitente"].value_counts().head(40).index.tolist()
opciones_remitente = ["Todos los remitentes"] + autores_mas_activos
remitente_sel = st.sidebar.selectbox(
    "👤 Remitente (Identidad protegida):",
    options=opciones_remitente,
    index=0
)

# 4. Filtro Top N
top_n = st.sidebar.slider(
    "🔝 Elementos en Rankings (Top N):",
    min_value=5,
    max_value=30,
    value=10,
    step=1
)

# Aplicación de Filtros a Mensajes y Oraciones
df_m_filtrado = df_base_mensajes[
    (df_base_mensajes["año"].isin(años_sel)) &
    (df_base_mensajes["mes_num"].isin(meses_num_sel))
].copy()

if remitente_sel != "Todos los remitentes":
    df_m_filtrado = df_m_filtrado[df_m_filtrado["remitente"] == remitente_sel]

df_o_filtrado = df_base_oraciones[
    (df_base_oraciones["año"].isin(años_sel)) &
    (df_base_oraciones["mes_num"].isin(meses_num_sel))
].copy()

if remitente_sel != "Todos los remitentes":
    df_o_filtrado = df_o_filtrado[df_o_filtrado["remitente"] == remitente_sel]

# Panel informativo en sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Estado del Dataset")
st.sidebar.write(f"**Mensajes filtrados:** `{len(df_m_filtrado):,}`")
st.sidebar.write(f"**Oraciones analizadas:** `{len(df_o_filtrado):,}`")

# Descarga de datos filtrados
if len(df_m_filtrado) > 0:
    csv_filtrado = df_m_filtrado[["id", "fecha", "remitente", "texto_limpio", "emojis_str", "temporada"]].to_csv(index=False, encoding="utf-8-sig")
    st.sidebar.download_button(
        label="📥 Descargar Dataset Filtrado (CSV)",
        data=csv_filtrado,
        file_name=f"telegram_filtrado_{opcion_año.replace(' ', '_')}.csv",
        mime="text/csv",
        use_container_width=True
    )

st.sidebar.markdown("---")
st.sidebar.caption("⚡ Proyecto Minería de Datos | UMSA 2026")


# =============================================================================
# 5. ENCABEZADO PRINCIPAL DEL DASHBOARD
# =============================================================================
st.markdown("<h1 class='neon-title'>⚡ Dashboard Analítico de Telegram (2025 - 2026)</h1>", unsafe_allow_html=True)
st.markdown(
    "Plataforma interactiva para la exploración y visualización de **minería de texto, patrones de emojis y perfiles emocionales** "
    "en comunidades académicas universitarias. Diseñado con fondo negro puro y estética fluorescente para proyección en clase."
)

# Manejo de dataset vacío por filtros extremos
if len(df_m_filtrado) == 0:
    st.warning("⚠️ **No se encontraron mensajes** para la combinación de filtros seleccionada. "
               "Por favor, selecciona otros meses, años o remitentes en la barra lateral.")
    st.stop()


# =============================================================================
# 6. ESTRUCTURA DE PESTAÑAS (ST.TABS)
# =============================================================================
tab_emojis, tab_emociones, tab_info = st.tabs([
    "😃 Pestaña 1: Análisis de Emojis",
    "🎭 Pestaña 2: Análisis de Emociones & Palabras",
    "📘 Documentación & Metodología"
])


# =============================================================================
# PESTAÑA 1: ANÁLISIS DE EMOJIS (basada en analisis_telegram.py)
# =============================================================================
with tab_emojis:
    st.markdown("### 🔍 Exploración Integral de Emojis")
    st.caption("Extracción y conteo unificado de emojis en texto, stickers y reacciones grupales.")

    # Extracción de frecuencias dinámicas del subconjunto filtrado
    c_total_emojis, c_texto_e, c_sticker_e, c_reaccion_e = extraer_conteo_emojis(df_m_filtrado)
    total_emojis_sum = sum(c_total_emojis.values())
    emojis_unicos = len(c_total_emojis)

    # ---------------------------------------------------------
    # 2. RESUMEN DE EMOJIS: MÉTRICAS Y DONA (Punto 2 del requerimiento)
    # ---------------------------------------------------------
    st.markdown("#### 📌 Resumen General de Uso de Emojis")
    st.caption("Métricas clave y porcentaje de participación de los emojis dominantes.")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    emoji_mas_usado_tuple = c_total_emojis.most_common(1)[0] if c_total_emojis else ("N/A", 0)
    emoji_top_str, emoji_top_cant = emoji_mas_usado_tuple
    pct_top = (emoji_top_cant / total_emojis_sum * 100) if total_emojis_sum > 0 else 0

    col_m1.metric("Total Emojis Registrados", f"{total_emojis_sum:,}")
    col_m2.metric("Variedad (Emojis Únicos)", f"{emojis_unicos:,}")
    col_m3.metric("Emoji Rey / Más Usado", f"{emoji_top_str} ({emoji_top_cant:,})", f"{pct_top:.1f}% del total")
    mensajes_con_emoji = df_m_filtrado[df_m_filtrado["emojis_str"].fillna("") != ""].shape[0]
    pct_msj_emoji = (mensajes_con_emoji / len(df_m_filtrado) * 100) if len(df_m_filtrado) > 0 else 0
    col_m4.metric("Mensajes con Emoji", f"{mensajes_con_emoji:,}", f"{pct_msj_emoji:.1f}% de mensajes")

    # Gráfica de Dona
    if total_emojis_sum > 0:
        top_dona = c_total_emojis.most_common(top_n)
        labels_dona = [f"{e}" for e, _ in top_dona]
        values_dona = [cnt for _, cnt in top_dona]
        otros_sum = total_emojis_sum - sum(values_dona)
        if otros_sum > 0:
            labels_dona.append("Otros")
            values_dona.append(otros_sum)

        fig_dona = go.Figure(data=[
            go.Pie(
                labels=labels_dona,
                values=values_dona,
                hole=0.55,
                marker=dict(
                    colors=PALETA_NEON[:len(labels_dona)],
                    line=dict(color="#000000", width=2)
                ),
                textinfo="label+percent",
                hoverinfo="label+value+percent",
                hovertemplate="<b>Emoji:</b> %{label}<br><b>Frecuencia:</b> %{value:,}<br><b>Proporción:</b> %{percent}<extra></extra>"
            )
        ])
        fig_dona = aplicar_estilo_neon(
            fig_dona,
            titulo="Distribución de Emojis (Top N vs Otros)",
            subtitulo="Proporción sobre el total acumulado de emojis en el período seleccionado.",
            altura=420
        )
        st.plotly_chart(fig_dona, use_container_width=True)
    else:
        st.info("ℹ️ No se detectaron emojis en los mensajes seleccionados.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 1. DICCIONARIO DE EMOJIS (Punto 1 del requerimiento)
    # ---------------------------------------------------------
    st.markdown("#### 📖 1. Diccionario Semántico de Emojis")
    st.caption("Clasificación de los emojis más frecuentes según su categoría funcional y significado contextual en la comunidad.")

    if not df_diccionario.empty:
        # Unir las frecuencias filtradas actuales con la metadata del diccionario
        df_dic_vista = df_diccionario.copy()
        df_dic_vista["conteo_actual"] = df_dic_vista["emoji"].map(lambda e: c_total_emojis.get(e, 0))
        df_dic_vista = df_dic_vista.sort_values("conteo_actual", ascending=False).head(top_n)

        # Gráfica de barras horizontales coloreadas por categoría
        fig_dic = px.bar(
            df_dic_vista[::-1],
            x="conteo_actual",
            y="emoji",
            color="categoria",
            orientation="h",
            color_discrete_sequence=PALETA_NEON,
            labels={"conteo_actual": "Frecuencia en Filtro", "emoji": "Emoji", "categoria": "Categoría Semántica"},
            custom_data=["significado_en_el_grupo", "categoria", "sentimiento", "nombre_oficial", "conteo_actual"]
        )
        fig_dic.update_traces(
            hovertemplate=(
                "<b>Emoji:</b> %{y} (%{customdata[3]})<br>"
                "<b>Categoría:</b> %{customdata[1]}<br>"
                "<b>Significado:</b> %{customdata[0]}<br>"
                "<b>Sentimiento:</b> %{customdata[2]}<br>"
                "<b>Frecuencia actual:</b> %{customdata[4]:,} apariciones<extra></extra>"
            ),
            marker=dict(line=dict(color="#000000", width=1.5))
        )
        fig_dic = aplicar_estilo_neon(
            fig_dic,
            titulo=f"Diccionario Semántico: Top {top_n} Emojis por Categoría",
            subtitulo="Pasa el cursor por cada barra para conocer el significado contextual en el grupo estudiantil.",
            altura=480
        )
        st.plotly_chart(fig_dic, use_container_width=True)

        with st.expander("📋 Ver Tabla Completa del Diccionario de Emojis"):
            st.dataframe(
                df_diccionario[["emoji", "total", "categoria", "sentimiento", "significado_en_el_grupo", "nombre_oficial"]],
                use_container_width=True,
                height=300
            )
    else:
        st.info("ℹ️ Diccionario de emojis no disponible en salida/diccionario_emojis.csv.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 3. EMOJIS MÁS USADOS EN EL PERÍODO (Punto 3 del requerimiento)
    # ---------------------------------------------------------
    st.markdown("#### 🏆 3. Ranking de Emojis Más Populares (Top N)")
    st.caption("Frecuencia absoluta y porcentaje relativo de los emojis más recurrentes en el período filtrado.")

    if total_emojis_sum > 0:
        top_rank = c_total_emojis.most_common(top_n)
        df_rank = pd.DataFrame(top_rank, columns=["emoji", "cantidad"])
        df_rank["porcentaje"] = (df_rank["cantidad"] / total_emojis_sum * 100).round(2)
        # Nombres descriptivos desde el diccionario o unicode
        mapa_nombres = dict(zip(df_diccionario["emoji"], df_diccionario["significado_en_el_grupo"]))
        df_rank["significado"] = df_rank["emoji"].map(mapa_nombres).fillna("Uso contextual")
        df_rank["etiqueta"] = df_rank["emoji"] + "  (" + df_rank["cantidad"].map(lambda x: f"{x:,}") + ")"

        fig_rank = go.Figure(
            go.Bar(
                x=df_rank["cantidad"][::-1],
                y=df_rank["emoji"][::-1],
                orientation="h",
                text=df_rank["etiqueta"][::-1],
                textposition="outside",
                textfont=dict(color="#00F5FF", size=13),
                marker=dict(
                    color=df_rank["cantidad"][::-1],
                    colorscale=[[0, NEON["purple"]], [0.5, NEON["magenta"]], [1, NEON["cyan"]]],
                    line=dict(color="#00F5FF", width=1.2)
                ),
                customdata=np.stack([df_rank["porcentaje"][::-1], df_rank["significado"][::-1]], axis=-1),
                hovertemplate="<b>Emoji:</b> %{y}<br><b>Cantidad exacta:</b> %{x:,}<br><b>Porcentaje:</b> %{customdata[0]}%<br><b>Significado:</b> %{customdata[1]}<extra></extra>"
            )
        )
        fig_rank = aplicar_estilo_neon(
            fig_rank,
            titulo=f"Top {top_n} Emojis Más Frecuentes",
            subtitulo="Total acumulado incluyendo texto, stickers y reacciones.",
            altura=max(420, top_n * 26)
        )
        st.plotly_chart(fig_rank, use_container_width=True)

    st.markdown("---")

    # ---------------------------------------------------------
    # 4. USO DE EMOJIS POR MES + SELECTOR Y HEATMAP (Punto 4 del requerimiento)
    # ---------------------------------------------------------
    st.markdown("#### 📈 4. Evolución Temporal del Uso de Emojis por Mes")
    st.caption("Tendencia temporal mes a mes, desglose por mes específico y mapa de calor interactivo.")

    # Agrupar emojis por mes
    meses_presentes = df_m_filtrado["periodo"].dropna().unique().tolist()
    meses_presentes.sort()

    serie_meses = []
    conteo_por_mes_dict = {}

    for per in meses_presentes:
        sub_df = df_m_filtrado[df_m_filtrado["periodo"] == per]
        c_sub, _, _, _ = extraer_conteo_emojis(sub_df)
        total_sub = sum(c_sub.values())
        conteo_por_mes_dict[per] = c_sub
        serie_meses.append({
            "periodo": per,
            "total_emojis": total_sub,
            "mensajes": len(sub_df)
        })

    df_evo_mes = pd.DataFrame(serie_meses)

    if not df_evo_mes.empty and df_evo_mes["total_emojis"].sum() > 0:
        # Gráfica de línea y barras combinadas
        fig_evo = go.Figure()
        fig_evo.add_trace(go.Bar(
            x=df_evo_mes["periodo"],
            y=df_evo_mes["total_emojis"],
            name="Total Emojis",
            marker=dict(
                color=NEON["cyan"],
                line=dict(color="#00FFFF", width=1.5),
                opacity=0.85
            ),
            hovertemplate="<b>Mes:</b> %{x}<br><b>Emojis emitidos:</b> %{y:,}<extra></extra>"
        ))
        fig_evo.add_trace(go.Scatter(
            x=df_evo_mes["periodo"],
            y=df_evo_mes["total_emojis"],
            name="Tendencia Neón",
            mode="lines+markers",
            line=dict(color=NEON["magenta"], width=3, shape="spline"),
            marker=dict(size=8, color="#FFFFFF", line=dict(color=NEON["magenta"], width=2)),
            hovertemplate="<b>Mes:</b> %{x}<br><b>Tendencia:</b> %{y:,}<extra></extra>"
        ))
        fig_evo = aplicar_estilo_neon(
            fig_evo,
            titulo="Volumen Mensual de Emojis Utilizados",
            subtitulo="Fluctuación del uso de emojis a lo largo de los meses de gestión académica.",
            altura=420
        )
        st.plotly_chart(fig_evo, use_container_width=True)

        # Selector para ver el Top de un mes específico
        col_sel_mes, col_top_mes = st.columns([1, 2])
        with col_sel_mes:
            st.markdown("##### 🎯 Explorar un Mes Específico")
            mes_elegido = st.selectbox(
                "Selecciona un período mensual:",
                options=meses_presentes,
                index=0
            )
            c_mes_elegido = conteo_por_mes_dict.get(mes_elegido, Counter())
            st.metric("Total Emojis en el Mes", f"{sum(c_mes_elegido.values()):,}")
            st.metric("Variedad en el Mes", f"{len(c_mes_elegido):,}")

        with col_top_mes:
            if c_mes_elegido:
                top_mes = c_mes_elegido.most_common(min(top_n, 12))
                df_top_m = pd.DataFrame(top_mes, columns=["emoji", "conteo"])
                fig_sub_mes = go.Figure(go.Bar(
                    x=df_top_m["conteo"][::-1],
                    y=df_top_m["emoji"][::-1],
                    orientation="h",
                    marker=dict(
                        color=NEON["lime"],
                        line=dict(color="#FFFFFF", width=1)
                    ),
                    hovertemplate="<b>Emoji:</b> %{y}<br><b>Cantidad en %{x}:</b> %{x:,}<extra></extra>"
                ))
                fig_sub_mes = aplicar_estilo_neon(
                    fig_sub_mes,
                    titulo=f"Top Emojis en {mes_elegido}",
                    subtitulo=f"Los emojis con mayor actividad registrada durante {mes_elegido}.",
                    altura=320
                )
                st.plotly_chart(fig_sub_mes, use_container_width=True)
            else:
                st.info(f"Sin emojis registrados en {mes_elegido}.")

        # Mapa de Calor (Heatmap) Emojis vs Mes (Opción enriquecida)
        st.markdown("##### 🔥 Mapa de Calor: Emojis vs Mes")
        st.caption("Intensidad de uso de los Top 12 emojis más representativos a través de cada mes.")

        top_emojis_heatmap = [e for e, _ in c_total_emojis.most_common(12)]
        if top_emojis_heatmap and len(meses_presentes) > 1:
            matriz_hm = []
            for e in top_emojis_heatmap:
                fila = [conteo_por_mes_dict[m].get(e, 0) for m in meses_presentes]
                matriz_hm.append(fila)

            fig_hm = go.Figure(data=go.Heatmap(
                z=matriz_hm,
                x=meses_presentes,
                y=top_emojis_heatmap,
                colorscale=[
                    [0.0, "#000000"],
                    [0.2, "#1A0033"],
                    [0.5, "#9D00FF"],
                    [0.8, "#FF007F"],
                    [1.0, "#00F5FF"]
                ],
                hovertemplate="<b>Emoji:</b> %{y}<br><b>Mes:</b> %{x}<br><b>Apariciones:</b> %{z:,}<extra></extra>"
            ))
            fig_hm = aplicar_estilo_neon(
                fig_hm,
                titulo="Matriz de Calor: Top Emojis a lo largo de los Meses",
                subtitulo="Zonas de mayor resplandor indican picos intensos de uso de ese emoji.",
                altura=460
            )
            st.plotly_chart(fig_hm, use_container_width=True)
    else:
        st.info("ℹ️ No hay suficiente dispersión temporal de emojis para graficar la evolución mensual.")


# =============================================================================
# PESTAÑA 2: ANÁLISIS DE EMOCIONES & PALABRAS (basada en analisis_emociones.py)
# =============================================================================
with tab_emociones:
    st.markdown("### 🎭 Detección Léxica de 15 Emociones & Minería de Palabras")
    st.caption("Análisis por oraciones con control de negaciones, comparación estacional (Verano vs Invierno) y perfiles en radar.")

    # Filtrar oraciones con emociones
    df_o_con_emo = df_o_filtrado[df_o_filtrado["n_emociones"] > 0].copy()

    # Expandir emociones para conteos
    if not df_o_con_emo.empty:
        df_exp_emo = (
            df_o_con_emo
            .assign(emocion=df_o_con_emo["emociones"].str.split(";"))
            .explode("emocion")
        )
        conteo_emociones = df_exp_emo["emocion"].value_counts()
    else:
        conteo_emociones = pd.Series(dtype=int)

    # ---------------------------------------------------------
    # 1. EMOCIONES Y SUS CANTIDADES (Punto 1 del requerimiento)
    # ---------------------------------------------------------
    st.markdown("#### 📊 1. Emociones Detectadas y sus Cantidades")
    st.caption("Distribución de las 15 emociones en las oraciones analizadas con colores neón diferenciados.")

    if not conteo_emociones.empty:
        # Asignar un color neón distinto a cada emoción
        emociones_ordenadas = list(LEXICO.keys())
        cantidades = [conteo_emociones.get(e, 0) for e in emociones_ordenadas]

        df_bar_emo = pd.DataFrame({
            "emocion": emociones_ordenadas,
            "cantidad": cantidades,
            "color": [PALETA_NEON[i % len(PALETA_NEON)] for i in range(len(emociones_ordenadas))]
        }).sort_values("cantidad", ascending=True)

        total_detecciones_emo = sum(cantidades)
        df_bar_emo["porcentaje"] = (df_bar_emo["cantidad"] / total_detecciones_emo * 100).round(1) if total_detecciones_emo > 0 else 0

        fig_emo_tot = go.Figure(
            go.Bar(
                x=df_bar_emo["cantidad"],
                y=df_bar_emo["emocion"],
                orientation="h",
                marker=dict(
                    color=df_bar_emo["color"],
                    line=dict(color="#FFFFFF", width=1)
                ),
                text=df_bar_emo["cantidad"].map(lambda x: f"{x:,}"),
                textposition="outside",
                textfont=dict(color="#00F5FF", size=12),
                customdata=df_bar_emo["porcentaje"],
                hovertemplate="<b>Emoción:</b> %{y}<br><b>Oraciones detectadas:</b> %{x:,}<br><b>Proporción:</b> %{customdata}%<extra></extra>"
            )
        )
        fig_emo_tot = aplicar_estilo_neon(
            fig_emo_tot,
            titulo="Frecuencia Global de Emociones Detectadas",
            subtitulo=f"Total de {total_detecciones_emo:,} menciones emocionales detectadas en el filtro activo.",
            altura=520
        )
        st.plotly_chart(fig_emo_tot, use_container_width=True)
    else:
        st.info("ℹ️ No se detectaron emociones en el subconjunto de oraciones seleccionado.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 2. CRONOLOGÍA DE EMOCIONES (Punto 2 del requerimiento)
    # ---------------------------------------------------------
    st.markdown("#### 📅 2. Cronología Temporal de Emociones por Mes")
    st.caption("Evolución mensual del flujo emocional en la comunidad. Permite identificar meses de mayor estrés, gratitud o euforia.")

    if not df_o_con_emo.empty:
        # Conteo mensual por emoción
        crono_df = (
            df_exp_emo
            .groupby(["periodo", "emocion"])
            .size()
            .reset_index(name="conteo")
        )

        periodos_cron = sorted(crono_df["periodo"].unique())

        # Selector de emociones para no saturar si el usuario quiere enfocar
        emociones_disponibles = sorted(crono_df["emocion"].unique())
        top_5_emo = conteo_emociones.head(6).index.tolist()

        emociones_sel_crono = st.multiselect(
            "Selecciona qué emociones graficar en la cronología:",
            options=emociones_disponibles,
            default=[e for e in top_5_emo if e in emociones_disponibles]
        )

        if emociones_sel_crono:
            fig_crono = go.Figure()
            for idx, emo in enumerate(emociones_sel_crono):
                sub_crono = crono_df[crono_df["emocion"] == emo].set_index("periodo")
                y_vals = [sub_crono.loc[p, "conteo"] if p in sub_crono.index else 0 for p in periodos_cron]
                col = PALETA_NEON[idx % len(PALETA_NEON)]

                fig_crono.add_trace(go.Scatter(
                    x=periodos_cron,
                    y=y_vals,
                    name=emo,
                    mode="lines+markers",
                    line=dict(color=col, width=2.8, shape="spline"),
                    marker=dict(size=7, color=col, line=dict(color="#FFFFFF", width=1.5)),
                    hovertemplate=f"<b>Emoción:</b> {emo}<br><b>Mes:</b> %{{x}}<br><b>Menciones:</b> %{{y:,}}<extra></extra>"
                ))

            fig_crono = aplicar_estilo_neon(
                fig_crono,
                titulo="Cronología Mensual de Emociones",
                subtitulo="Líneas fluorescentes con marcadores representando la intensidad de cada emoción mes a mes.",
                altura=480
            )
            st.plotly_chart(fig_crono, use_container_width=True)
        else:
            st.info("Selecciona al menos una emoción en el selector para trazar la cronología.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 3. TOP DE PALABRAS MÁS USADAS (Punto 3 del requerimiento)
    # ---------------------------------------------------------
    st.markdown("#### 💬 3. Ranking de Palabras Más Frecuentes (Top N)")
    st.caption("Términos más recurrentes tras normalización NFC, tokenización léxica y eliminación de stopwords en español.")

    c_palabras = Counter()
    for toks in df_o_filtrado["tokens"].dropna():
        for w in str(toks).split():
            if w not in STOP and len(w) > 2 and w.isalpha():
                c_palabras[w] += 1

    if c_palabras:
        top_words = c_palabras.most_common(top_n)
        df_words = pd.DataFrame(top_words, columns=["palabra", "frecuencia"])

        fig_words = go.Figure(
            go.Bar(
                x=df_words["frecuencia"][::-1],
                y=df_words["palabra"][::-1],
                orientation="h",
                text=df_words["frecuencia"][::-1].map(lambda x: f"{x:,}"),
                textposition="outside",
                textfont=dict(color=NEON["lime"], size=12),
                marker=dict(
                    color=df_words["frecuencia"][::-1],
                    colorscale=[[0, NEON["electric_blue"]], [0.5, NEON["bright_teal"]], [1, NEON["lime"]]],
                    line=dict(color=NEON["lime"], width=1.2)
                ),
                hovertemplate="<b>Palabra:</b> '%{y}'<br><b>Frecuencia exacta:</b> %{x:,} apariciones<extra></extra>"
            )
        )
        fig_words = aplicar_estilo_neon(
            fig_words,
            titulo=f"Top {top_n} Palabras Clave en el Grupo",
            subtitulo="Palabras de mayor relevancia semántica excluyendo pronombres, artículos y conectores habituales.",
            altura=max(420, top_n * 25)
        )
        st.plotly_chart(fig_words, use_container_width=True)
    else:
        st.info("ℹ️ No hay palabras para procesar con los filtros actuales.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 4. VERANO VS INVIERNO (Punto 4 del requerimiento)
    # ---------------------------------------------------------
    st.markdown("#### ☀️❄️ 4. Comparativa Estacional: Verano (Enero) vs Invierno (Julio)")
    st.caption(
        "Comparativa de las cuatro combinaciones requeridas: **Enero 2025, Julio 2025, Enero 2026 y Julio 2026** "
        "(Barras agrupadas por emoción para contraste estacional)."
    )

    # Filtrar el DataFrame de oraciones para las 4 temporadas específicas
    # Respetando la regla de analisis_emociones.py: Enero = Verano, Julio = Invierno
    df_estaciones = df_base_oraciones[df_base_oraciones["temporada"].isin([
        "verano_2025", "invierno_2025", "verano_2026", "invierno_2026"
    ])].copy()

    # Si se seleccionó un remitente específico, también lo filtramos aquí
    if remitente_sel != "Todos los remitentes":
        df_estaciones = df_estaciones[df_estaciones["remitente"] == remitente_sel]

    if not df_estaciones.empty:
        # Total de oraciones por temporada para calcular tasa por 1000
        tot_oraciones_temp = df_estaciones.groupby("temporada").size()

        # Expandir emociones
        exp_temp = (
            df_estaciones[df_estaciones["n_emociones"] > 0]
            .assign(emocion=lambda d: d["emociones"].str.split(";"))
            .explode("emocion")
        )
        cuenta_temp = exp_temp.groupby(["temporada", "emocion"]).size().reset_index(name="n")
        cuenta_temp["total_oraciones"] = cuenta_temp["temporada"].map(tot_oraciones_temp)
        cuenta_temp["tasa_por_1000"] = (cuenta_temp["n"] / cuenta_temp["total_oraciones"] * 1000).round(1)

        # Etiquetas legibles para las cuatro combinaciones
        mapa_nombres_temp = {
            "verano_2025": "☀️ Enero 2025 (Verano)",
            "invierno_2025": "❄️ Julio 2025 (Invierno)",
            "verano_2026": "☀️ Enero 2026 (Verano)",
            "invierno_2026": "❄️ Julio 2026 (Invierno)"
        }
        colores_temporadas = {
            "verano_2025": NEON["yellow"],       # Amarillo neón (calor/inicio 2025)
            "invierno_2025": NEON["cyan"],       # Cian neón frío (invierno 2025)
            "verano_2026": NEON["orange"],      # Naranja neón (verano 2026)
            "invierno_2026": NEON["magenta"]     # Magenta neón (invierno 2026)
        }

        # Toggle para alternar entre Tasa por cada 1,000 oraciones o Conteo Absoluto
        metrica_estacional = st.radio(
            "Selecciona métrica para comparar:",
            options=["Tasa estandarizada (Por cada 1,000 oraciones)", "Cantidad absoluta de oraciones"],
            horizontal=True
        )
        col_valor = "tasa_por_1000" if "Tasa" in metrica_estacional else "n"
        unidad_label = "por 1,000 oraciones" if "Tasa" in metrica_estacional else "oraciones"

        fig_estacional = go.Figure()
        emociones_todas = list(LEXICO.keys())

        for temp_key in ["verano_2025", "invierno_2025", "verano_2026", "invierno_2026"]:
            sub_t = cuenta_temp[cuenta_temp["temporada"] == temp_key].set_index("emocion")
            y_vals = [sub_t.loc[e, col_valor] if e in sub_t.index else 0 for e in emociones_todas]
            n_vals = [sub_t.loc[e, "n"] if e in sub_t.index else 0 for e in emociones_todas]

            fig_estacional.add_trace(go.Bar(
                name=mapa_nombres_temp[temp_key],
                x=emociones_todas,
                y=y_vals,
                marker=dict(
                    color=colores_temporadas[temp_key],
                    line=dict(color="#000000", width=1)
                ),
                customdata=n_vals,
                hovertemplate=(
                    f"<b>Temporada:</b> {mapa_nombres_temp[temp_key]}<br>"
                    "<b>Emoción:</b> %{x}<br>"
                    f"<b>Valor:</b> %{{y:,}} {unidad_label}<br>"
                    "<b>Conteo absoluto:</b> %{customdata:,} oraciones<extra></extra>"
                )
            ))

        fig_estacional.update_layout(barmode="group")
        fig_estacional = aplicar_estilo_neon(
            fig_estacional,
            titulo="Comparativa Estacional: Enero vs Julio (2025 y 2026)",
            subtitulo=f"Visualización de las 4 combinaciones temporales agrupadas por cada una de las 15 emociones.",
            altura=520
        )
        fig_estacional.update_xaxes(tickangle=-40)
        st.plotly_chart(fig_estacional, use_container_width=True)
    else:
        st.warning("⚠️ No se encontraron oraciones para las temporadas de Verano e Invierno con el remitente seleccionado.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 5. GRÁFICA EXTRA: RADAR O BARRAS APILADAS (Punto 5 del requerimiento)
    # ---------------------------------------------------------
    st.markdown("#### 🕸️ 5. Gráfica Extra: Huella Emocional por Temporada")
    st.caption("Perfil multidimensional de cada temporada académica en un diagrama de radar polar fluorescente o barras apiladas.")

    if not df_estaciones.empty:
        col_tipo_extra, _ = st.columns([1, 2])
        tipo_grafica_extra = col_tipo_extra.selectbox(
            "Selecciona el tipo de visualización:",
            options=["Gráfico de Radar Polar (Cyberpunk Radar)", "Barras Apiladas por Temporada (Composición %)"]
        )

        if "Radar" in tipo_grafica_extra:
            fig_radar = go.Figure()
            emociones_radar = list(LEXICO.keys()) + [list(LEXICO.keys())[0]]  # Cerrar el polígono polar

            for temp_key in ["verano_2025", "invierno_2025", "verano_2026", "invierno_2026"]:
                sub_t = cuenta_temp[cuenta_temp["temporada"] == temp_key].set_index("emocion")
                r_vals = [sub_t.loc[e, "tasa_por_1000"] if e in sub_t.index else 0 for e in emociones_radar]
                col_hex = colores_temporadas[temp_key]

                fig_radar.add_trace(go.Scatterpolar(
                    r=r_vals,
                    theta=emociones_radar,
                    name=mapa_nombres_temp[temp_key],
                    fill="toself",
                    fillcolor=f"rgba({int(col_hex[1:3], 16)}, {int(col_hex[3:5], 16)}, {int(col_hex[5:7], 16)}, 0.12)",
                    line=dict(color=col_hex, width=2.5),
                    marker=dict(size=6, color=col_hex),
                    hovertemplate=f"<b>{mapa_nombres_temp[temp_key]}</b><br>Emoción: %{{theta}}<br>Tasa: %{{r}} por 1,000 oraciones<extra></extra>"
                ))

            fig_radar.update_layout(
                template="plotly_dark",
                paper_bgcolor="#000000",
                plot_bgcolor="#000000",
                polar=dict(
                    bgcolor="#050505",
                    radialaxis=dict(
                        visible=True,
                        gridcolor="#222222",
                        linecolor="#333333",
                        tickfont=dict(color="#A0A0A0", size=10)
                    ),
                    angularaxis=dict(
                        gridcolor="#222222",
                        linecolor="#333333",
                        tickfont=dict(color="#FFFFFF", size=11, family="Segoe UI")
                    )
                ),
                font=dict(color="#FFFFFF", family="Segoe UI"),
                title=dict(
                    text="<b style='color:#00F5FF; font-size:17px;'>Radar Emocional: Huella Estacional de 15 Emociones</b><br><span style='color:#888888; font-size:12px;'>Compara la firma y silueta emocional de cada período académico.</span>",
                    x=0.02,
                    y=0.96
                ),
                legend=dict(
                    bgcolor="rgba(8,8,8,0.85)",
                    bordercolor="#222222",
                    borderwidth=1,
                    font=dict(color="#E0E0E0", size=11)
                ),
                margin=dict(l=60, r=60, t=70, b=50),
                height=560
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        else:
            # Barras apiladas (Composición porcentual)
            df_stack = cuenta_temp.copy()
            df_stack["temporada_nombre"] = df_stack["temporada"].map(mapa_nombres_temp)

            fig_stack = px.bar(
                df_stack,
                x="temporada_nombre",
                y="n",
                color="emocion",
                color_discrete_sequence=PALETA_NEON,
                barmode="relative",
                labels={"n": "Cantidad de Oraciones", "temporada_nombre": "Temporada", "emocion": "Emoción"},
                category_orders={"temporada_nombre": [mapa_nombres_temp[k] for k in ["verano_2025", "invierno_2025", "verano_2026", "invierno_2026"]]}
            )
            fig_stack.update_traces(
                hovertemplate="<b>Temporada:</b> %{x}<br><b>Emoción:</b> %{fullData.name}<br><b>Oraciones:</b> %{y:,}<extra></extra>"
            )
            fig_stack = aplicar_estilo_neon(
                fig_stack,
                titulo="Composición Emocional por Temporada (Barras Apiladas)",
                subtitulo="Estructura y distribución de las emociones registradas en cada estación.",
                altura=500
            )
            st.plotly_chart(fig_stack, use_container_width=True)


# =============================================================================
# PESTAÑA 3: METODOLOGÍA & DOCUMENTACIÓN ACADÉMICA
# =============================================================================
with tab_info:
    st.markdown("### 📘 Metodología de Minería de Datos y Procesamiento")
    st.markdown("""
    Este dashboard integra las técnicas aplicadas en los scripts `analisis_telegram.py` y `analisis_emociones.py`
    sobre un archivo exportado de Telegram en formato JSON:

    #### 1. Pipeline de Emojis (`analisis_telegram.py`):
    - **Extracción multicanal**: Se identifican y contabilizan emojis provenientes de:
      1. **Texto**: Emojis insertados directamente en los mensajes de texto.
      2. **Stickers**: Emojis representativos asociados a cada sticker de Telegram.
      3. **Reacciones**: Conteo de reacciones emotivas dejadas por los integrantes a los mensajes.
    - **Normalización**: Tratamiento de secuencias Unicode ZWJ (Zero Width Joiner) y variantes gráficas (`\\ufe0f`).

    #### 2. Detección Léxica de Emociones (`analisis_emociones.py`):
    - **Normalización textual**: Conversión a minúsculas y eliminación de diacríticos/tildes (NFD).
    - **Control de Negación**: Las emociones de polaridad positiva (`Gratitud`, `Alegría`, `Esperanza`, `Alivio`, `Aprobación`)
      incluyen expresiones de búsqueda que previenen falsos positivos tras adverbios negativos (`no`, `ni`, `nunca`, `sin`).
    - **Tokenización por Oración**: Segmentación mediante puntuación terminal y saltos de línea para preservar el contexto emotivo.
    - **Comparación Estacional**: Segmentación de Enero (Verano / Inicio de semestre) contra Julio (Invierno / Mitad de semestre) para los años 2025 y 2026.

    #### 3. Privacidad y Anonimización:
    - **Anonimización completa de remitentes**: Los identificadores de usuario reales y números telefónicos han sido reemplazados
      por etiquetas consistentes de la forma `Persona 1`, `Persona 2`, etc., ordenadas por volumen de participación.
    """)
    st.info("💡 **Tip para la presentación**: Puedes hacer clic en el icono de cámara en la esquina superior derecha de cualquier gráfica interactiva para descargarla como imagen PNG en alta definición.")
