# pages/DiagnosticoFacial.py
import streamlit as st
import pandas as pd
import openpyxl  # requiere estar instalado en el venv
from pathlib import Path
import plotly.express as px
import unicodedata

st.set_page_config(page_title="DiagnósticoFacial", page_icon="🧴", layout="wide")

# ---------- Rutas y carga ----------
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "diagnostico_facial_ejemplo.xlsx"

@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    return pd.read_excel(path, engine="openpyxl")

st.title("🧴 Diagnóstico Facial — DataFrame")
st.caption(f"Fuente: {DATA_PATH}")

# ---------- Carga base ----------
try:
    df_raw = load_data(DATA_PATH)
except FileNotFoundError:
    st.error(f"❌ No se encontró el archivo: {DATA_PATH}")
    st.stop()
except Exception as e:
    st.error(f"❌ Error al cargar el Excel: {e}  (prueba: pip install --upgrade openpyxl pandas)")
    st.stop()

# ================== FILTRO POR FECHA (BARRA LATERAL) ==================
with st.sidebar:
    st.header("Filtros")
    if "fecha_valoracion" not in df_raw.columns:
        st.error("La columna 'fecha_valoracion' no existe en el DataFrame.")
        df_date = df_raw.copy()
    else:
        df_raw = df_raw.copy()
        df_raw["fecha_valoracion"] = pd.to_datetime(df_raw["fecha_valoracion"], errors="coerce")
        min_dt = df_raw["fecha_valoracion"].min()
        max_dt = df_raw["fecha_valoracion"].max()

        if pd.isna(min_dt) or pd.isna(max_dt):
            st.warning("No hay fechas válidas en 'fecha_valoracion'.")
            df_date = df_raw.copy()
        else:
            start_default = min_dt.date()
            end_default = max_dt.date()
            date_range = st.date_input(
                "Rango de fechas (fecha_valoracion)",
                value=(start_default, end_default),
                min_value=start_default,
                max_value=end_default,
                help="Filtra por la columna 'fecha_valoracion' (rango inclusivo).",
                key="fecha_rango",
            )
            if isinstance(date_range, tuple):
                start_date, end_date = date_range
            else:
                start_date = end_date = date_range
            mask = (df_raw["fecha_valoracion"].dt.date >= start_date) & (df_raw["fecha_valoracion"].dt.date <= end_date)
            df_date = df_raw.loc[mask].copy()

# ---------- CSS simple para KPIs ----------
KPI_CSS = """
<style>
.kpi { background: white; border-radius: 14px; padding: 14px 16px;
       box-shadow: 0 2px 10px rgba(0,0,0,0.08); border: 1px solid rgba(0,0,0,0.05); }
.kpi h3 { font-size: 14px; margin: 0 0 6px 0; color: #666; font-weight: 600; }
.kpi .value { font-size: 26px; font-weight: 800; margin-top: 2px; }
</style>
"""
st.markdown(KPI_CSS, unsafe_allow_html=True)

# ================== KPIs (sobre df filtrado por fecha) ==================
col_agente = "esteticista" if "esteticista" in df_date.columns else ("asesor" if "asesor" in df_date.columns else None)
n_agentes = int(df_date[col_agente].nunique()) if col_agente else 0
n_usuarios = int(len(df_date))

k1, k2 = st.columns(2)
with k1:
    st.markdown(
        f"""
        <div class="kpi">
          <h3>Agentes en rango</h3>
          <div class="value">{n_agentes:,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        f"""
        <div class="kpi">
          <h3>Usuarios en rango</h3>
          <div class="value">{n_usuarios:,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ================== TABLA (sobre df filtrado por fecha) ==================
st.caption(f"Registros filtrados (por fecha): {len(df_date)}")
st.dataframe(df_date, use_container_width=True, height=500)

# ================== FUNCIÓN PARA CREAR MAPAS DE CALOR ==================
def create_heatmap(df, main_column, title, second_dimension_candidates=None):
    """Crea un mapa de calor para una columna principal, opcionalmente contra una segunda dimensión"""
    if main_column not in df.columns or df.empty:
        return None
    
    try:
        # Buscar segunda dimensión si se proporcionan candidatos
        second_dim = None
        if second_dimension_candidates:
            second_dim = next((col for col in second_dimension_candidates if col in df.columns), None)
        
        if second_dim:
            # Mapa de calor con dos dimensiones
            heatmap_data = df.groupby([second_dim, main_column]).size().unstack(fill_value=0)
            fig = px.imshow(
                heatmap_data,
                title=f"{title} vs {second_dim}",
                labels=dict(x=main_column, y=second_dim, color="Cantidad"),
                aspect="auto",
                color_continuous_scale="Viridis"
            )
        else:
            # Mapa de calor simple - buscar dimensión temporal
            if 'fecha_valoracion' in df.columns:
                df_temp = df.copy()
                df_temp['mes'] = df_temp['fecha_valoracion'].dt.to_period('M').astype(str)
                heatmap_data = df_temp.groupby(['mes', main_column]).size().unstack(fill_value=0)
                fig = px.imshow(
                    heatmap_data.T,
                    title=f"{title} por Mes",
                    labels=dict(x="Mes", y=main_column, color="Cantidad"),
                    aspect="auto",
                    color_continuous_scale="Blues"
                )
            else:
                # Mapa de calor básico de frecuencias
                value_counts = df[main_column].value_counts()
                heatmap_data = value_counts.to_frame().T
                fig = px.imshow(
                    heatmap_data,
                    title=title,
                    labels=dict(x=main_column, color="Cantidad"),
                    color_continuous_scale="Viridis"
                )
                fig.update_layout(yaxis=dict(showticklabels=False))
        
        fig.update_layout(
            xaxis_title=main_column,
            yaxis_title=second_dim if second_dim else "",
        )
        return fig
        
    except Exception as e:
        st.error(f"Error al crear mapa de calor para {main_column}: {str(e)}")
        return None

# ================== FILTRO + MAPA DE CALOR: NIVEL DE HIDRATACIÓN ==================
posibles_hid = ["nivel_hidratacion", "nivel_hidratación", "Nivel de hidratación"]
col_hid = next((c for c in posibles_hid if c in df_date.columns), None)

with st.sidebar:
    st.subheader("Filtro: Nivel de hidratación")
    if col_hid is None:
        st.error("No encuentro la columna de nivel de hidratación.")
        selected_hid_levels = []
    else:
        niveles_hid = sorted(df_date[col_hid].dropna().unique().tolist())
        selected_hid_levels = st.multiselect(
            "Selecciona nivel(es) de hidratación",
            options=niveles_hid,
            default=niveles_hid,
            key="hid_multiselect",
        )

df_hid = df_date.copy()
if col_hid and selected_hid_levels:
    df_hid = df_hid[df_hid[col_hid].isin(selected_hid_levels)].copy()

if col_hid and selected_hid_levels and not df_hid.empty:
    st.subheader("🧴 Mapa de Calor: Nivel de Hidratación")
    fig_hid = create_heatmap(
        df_hid, 
        col_hid, 
        "Distribución de Niveles de Hidratación",
        second_dimension_candidates=["esteticista", "asesor", "genero", "sexo"]
    )
    if fig_hid:
        st.plotly_chart(fig_hid, use_container_width=True)
        
        # Mostrar datos en tabla
        with st.expander("Ver datos detallados de hidratación"):
            st.dataframe(df_hid[col_hid].value_counts().reset_index().rename(
                columns={'index': 'Nivel de Hidratación', col_hid: 'Cantidad'}
            ))

# ================== FILTRO + MAPA DE CALOR: NIVEL SEBÁCEO / SENSIBILIDAD ==================
posibles_sens = ["nivel_sebaceo", "grado_sensibilidad", "sensibilidad"]
col_sens = next((c for c in posibles_sens if c in df_date.columns), None)

with st.sidebar:
    st.subheader("Filtro: Nivel sebáceo / sensibilidad")
    if col_sens is None:
        st.error("No encuentro la columna de nivel sebáceo/sensibilidad.")
        selected_sens_levels = []
    else:
        niveles_sens = sorted(df_date[col_sens].dropna().unique().tolist())
        selected_sens_levels = st.multiselect(
            "Selecciona nivel(es) sebáceo/sensibilidad",
            options=niveles_sens,
            default=niveles_sens,
            key="sens_multiselect",
        )

df_sens = df_date.copy()
if col_sens and selected_sens_levels:
    df_sens = df_sens[df_sens[col_sens].isin(selected_sens_levels)].copy()

if col_sens and selected_sens_levels and not df_sens.empty:
    st.subheader("🔍 Mapa de Calor: Nivel Sebáceo / Sensibilidad")
    fig_sens = create_heatmap(
        df_sens,
        col_sens,
        "Distribución de Niveles Sebáceos / Sensibilidad",
        second_dimension_candidates=["esteticista", "asesor", "genero", "sexo"]
    )
    if fig_sens:
        st.plotly_chart(fig_sens, use_container_width=True)

# ================== UTILIDADES PARA SECCIONES GENÉRICAS ==================
def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode("ascii")
    return "".join(ch for ch in s.lower() if ch.isalnum() or ch in "_ ")

def find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    norm_cols = { _norm(c): c for c in df.columns }
    for cand in candidates:
        key = _norm(cand)
        if key in norm_cols:
            return norm_cols[key]
    for cand in candidates:
        key = _norm(cand)
        for k, orig in norm_cols.items():
            if key in k:
                return orig
    return None

def render_heatmap_section(df_base: pd.DataFrame, label: str, candidates: list[str], key_prefix: str):
    """Renderiza una sección con mapa de calor para variables categóricas"""
    col_target = find_col(df_base, candidates)
    
    with st.sidebar:
        st.subheader(f"Filtro: {label}")
        if col_target is None:
            st.error(f"No encuentro la columna para: {label}")
            return None, None
        niveles = sorted(df_base[col_target].dropna().unique().tolist())
        if not niveles:
            st.warning(f"Sin niveles válidos para: {label}")
            return None, None
        selected_levels = st.multiselect(
            f"Selecciona nivel(es) — {label}",
            options=niveles,
            default=niveles,
            key=f"{key_prefix}_multiselect",
        )
    
    df_filtered = df_base.copy()
    if selected_levels:
        df_filtered = df_filtered[df_filtered[col_target].isin(selected_levels)].copy()
    
    return df_filtered, col_target

# ================== SECCIONES ESPECÍFICAS CON MAPAS DE CALOR ==================
sections = [
    ("Pigmentación", ["pigementacion", "pigmentacion", "pigmentación"], "pigmentacion"),
    ("Tratamiento médico", ["tratamiento medico", "tratamiento_medico", "tratamiento_médico"], "trat_medico"),
    ("Tratamiento médico — ¿Cuál?", ["tratamiento_medico_cual", "tratamiento medico cual", "tratamiento_médico_cuál"], "trat_medico_cual"),
    ("Firmeza / líneas de expresión", ["firmeza lineas_expresion_zon", "firmeza_lineas_expresion_zon", "firmeza lineas expresion zon"], "firmeza_lineas"),
    ("Nutrición", ["nutricion", "nutrición"], "nutricion"),
    ("Fotosensibilidad", ["fotosnesibilidad", "fotosensibilidad", "foto_sensibilidad"], "fotosensibilidad"),
    ("Tratamiento para reducir enfermedades", ["tratamiento_para reducir enfermedades_importantes", "tratamiento_para_reducir_enfermedades_importantes", "tratamiento para reducir enfermedades importantes"], "trat_enf_importantes"),
    ("Toma medicamentos", ["toma_medicamentos", "toma medicamentos"], "toma_meds"),
]

for label, candidates, key_prefix in sections:
    df_filtered, col_target = render_heatmap_section(df_date, label, candidates, key_prefix)
    
    if df_filtered is not None and col_target and not df_filtered.empty:
        st.subheader(f"📊 Mapa de Calor: {label}")
        fig = create_heatmap(
            df_filtered,
            col_target,
            f"Distribución de {label}",
            second_dimension_candidates=["esteticista", "asesor", "genero", "sexo", "fecha_valoracion"]
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar datos en tabla
            with st.expander(f"Ver datos detallados de {label}"):
                st.dataframe(df_filtered[col_target].value_counts().reset_index().rename(
                    columns={'index': label, col_target: 'Cantidad'}
                ))

# ================== MAPA DE CALOR GENERAL DE CORRELACIONES ==================
st.subheader("🔥 Mapa de Calor General de Correlaciones")

# Seleccionar columnas numéricas para correlación
numeric_columns = df_date.select_dtypes(include=['number']).columns.tolist()

if len(numeric_columns) > 1:
    correlation_matrix = df_date[numeric_columns].corr()
    
    fig_corr = px.imshow(
        correlation_matrix,
        title="Correlación entre Variables Numéricas",
        color_continuous_scale="RdBu_r",
        aspect="auto",
        zmin=-1,
        zmax=1
    )
    fig_corr.update_layout(
        xaxis_title="Variables",
        yaxis_title="Variables",
    )
    st.plotly_chart(fig_corr, use_container_width=True)
else:
    st.info("No hay suficientes columnas numéricas para calcular correlaciones.")
