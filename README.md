# ⚡ Telegram Data Mining Dashboard: Emojis & Emociones (2025 - 2026)

Plataforma interactiva de **minería de datos y procesamiento de lenguaje natural (PLN)** desarrollada con **Streamlit** y **Plotly**, diseñada con una estética *Dark Neon* (fondo negro puro `#000000` y acentos fluorescentes) para la visualización, exploración y análisis de patrones de comunicación en chats exportados de Telegram.

---

## 📋 Tabla de Contenidos
- [Características Principales](#-características-principales)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación y Puesta en Marcha](#-instalación-y-puesta-en-marcha)
- [Pipeline de Procesamiento](#-pipeline-de-procesamiento)
- [Filtros y Métricas Interactivas](#-filtros-y-métricas-interactivas)
- [Privacidad y Anonimización](#-privacidad-y-anonimización)

---

## 🌟 Características Principales

### 😃 Pestaña 1: Análisis de Emojis
1. **Diccionario Semántico**: Gráfica de barras horizontales con el significado contextual, sentimiento y categoría funcional de los 60 emojis más usados.
2. **Resumen de Emojis**: Métricas dinámicas (`Total Emojis`, `Variedad`, `Emoji Rey`, `Mensajes con Emoji`) y **Gráfica de Dona** neón con la distribución porcentual.
3. **Ranking Top N**: Barras horizontales interactivas ordenadas por frecuencia con tooltips detallados.
4. **Evolución Temporal & Mapa de Calor**:
   - Tendencia mensual unificada (barras + líneas con marcadores).
   - Selector de mes individual para inspeccionar su Top N exclusivo.
   - **Mapa de Calor (Heatmap)** cruzando los Top emojis contra cada mes de la gestión académica.

### 🎭 Pestaña 2: Análisis de Emociones y Palabras
1. **Detección de 15 Emociones**: Gráfica de barras con colores fluorescentes diferenciados por emoción (`Gratitud`, `Frustración`, `Humor/Risa`, `Aprobación`, `Tristeza`, `Alegría`, etc.).
2. **Cronología de Emociones**: Líneas temporales con marcadores para evaluar la fluctuación del clima emocional mes a mes.
3. **Top de Palabras Más Frecuentes**: Ranking léxico normalizado (sin tildes, en minúsculas y sin palabras vacías / stopwords en español).
4. **Comparativa Estacional (Verano vs Invierno)**:
   - Contraste de las cuatro combinaciones:
     - ☀️ **Enero 2025** (Verano 2025)
     - ❄️ **Julio 2025** (Invierno 2025)
     - ☀️ **Enero 2026** (Verano 2026)
     - ❄️ **Julio 2026** (Invierno 2026)
   - Selector entre tasa por cada 1,000 oraciones o conteo absoluto.
5. **Huella Emocional Multidimensional**:
   - **Diagrama de Radar Polar (`Scatterpolar`)** neón.
   - **Barras Apiladas** para evaluar la composición porcentual de cada temporada.

---

## 📁 Estructura del Proyecto

```text
├── dashboard.py                  # Aplicación principal del Dashboard interactivo
├── analisis_telegram.py          # Script de extracción, limpieza y conteo de emojis
├── analisis_emociones.py         # Script de tokenización, stopwords y lexico de 15 emociones
├── requirements.txt              # Dependencias y librerías necesarias
├── README.md                     # Guía de instalación y uso del proyecto
├── .streamlit/
│   └── config.toml               # Configuración de tema oscuro nativo (#000000)
├── salida/                       # Datasets procesados y plantillas generadas
│   ├── diccionario_emojis.csv    # Clasificación semántica de emojis con categorías
│   ├── emojis_frecuencia.csv     # Conteo global de emojis (texto, stickers, reacciones)
│   ├── mensajes_completos.csv    # Dataset consolidado de mensajes anonimizados
│   ├── oraciones_2025_2026.csv   # 11,905 oraciones tokenizadas con emociones detectadas
│   └── resumen_emociones.csv     # Resumen estadístico por temporada y estación
└── result.json                   # Exportación en formato JSON del chat de Telegram
```

---

## ⚙️ Requisitos Previos

- **Python 3.10 o superior** (probado y optimizado en Python 3.12).
- Gestor de paquetes **`pip`**.
- (Recomendado) Sistema operativo con soporte UTF-8 (Windows, macOS o Linux).

---

## 🚀 Instalación y Puesta en Marcha

Sigue estos sencillos pasos para clonar y ejecutar el proyecto en tu computadora local:

### 1. Clonar el repositorio
Abre una terminal y clona el proyecto:
```bash
git clone https://github.com/TU-USUARIO/TU-REPOSITORIO.git
cd TU-REPOSITORIO
```

### 2. (Opcional pero Recomendado) Crear un Entorno Virtual
Para mantener tus librerías aisladas y evitar conflictos:

- **En Windows (PowerShell / CMD):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\activate
  ```

- **En macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Instalar las dependencias
Instala todas las librerías necesarias con un solo comando:
```bash
pip install -r requirements.txt
```

Las dependencias principales son:
- `streamlit` (interfaz web interactiva)
- `plotly` (gráficas interactivas con aceleración WebGL y tema oscuro)
- `pandas` (procesamiento y agregación de datasets)
- `emoji` (detección y parsing de secuencias Unicode)
- `numpy` (operaciones vectoriales)

### 4. Ejecutar el Dashboard
Inicia el servidor local de Streamlit ejecutando:
```bash
streamlit run dashboard.py
```

> **Nota para Windows (si tienes varias versiones de Python):**
> ```powershell
> py -3.12 -m streamlit run dashboard.py
> ```

Automáticamente se abrirá una pestaña en tu navegador web en:  
👉 **`http://localhost:8501`**

---

## 🔄 (Opcional) Regenerar los Datos desde Cero

Si deseas actualizar o volver a procesar el archivo `result.json` original con los scripts de consola independientes:

1. **Paso 1: Procesar mensajes y emojis:**
   ```bash
   python analisis_telegram.py result.json
   ```
2. **Paso 2: Procesar oraciones, stopwords y emociones:**
   ```bash
   python analisis_emociones.py
   ```

Ambos scripts conservan compatibilidad como programas de línea de comandos independientes y generan los archivos en la carpeta `salida/`.

---

## 🎛️ Filtros y Controles Interactivos

En la barra lateral izquierda (`st.sidebar`) dispones de:
- **Filtro de Año**: Alterna entre `Ambos (2025 y 2026)`, `2025` o `2026`.
- **Filtro de Mes**: Selector múltiple con los 12 meses (o botón para seleccionar todos con un clic).
- **Remitente**: Selección de un usuario específico o todo el grupo combinado.
- **Top N (Slider)**: Ajuste interactivo del tamaño de los rankings (de 5 a 30 elementos).
- **Descargas**:
  - Botón directo para exportar el dataset filtrado en formato **CSV**.
  - Descarga de cualquier gráfica en alta resolución (**PNG**) mediante el icono de cámara en la barra de herramientas de Plotly.

---

## 🛡️ Privacidad y Anonimización Ética

De acuerdo con las buenas prácticas de minería de datos y protección de la privacidad:
- **No se muestran nombres reales ni números telefónicos**.
- Los remitentes han sido anonimizados de forma determinista mediante identificadores consistentes (`Persona 1`, `Persona 2`, ...), ordenados por su volumen de participación en el chat.
- Las URLs, menciones `@usuario` y números de contacto en el texto de los mensajes fueron depurados mediante expresiones regulares antes de su análisis.

---

## 👥 Créditos y Contacto
Proyecto académico desarrollado para la materia de **Minería de Datos** (2026).
Si tienes dudas o sugerencias sobre el análisis, abre un *Issue* o *Pull Request* en el repositorio.
