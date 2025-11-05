# pages/DiagnosticoFacial.py
import streamlit as st
import pandas as pd
import openpyxl
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
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
    st.error(f"❌ Error al cargar el Excel: {e}")
    st.stop()

# ================== FILTRO POR FECHA ==================
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
                key="fecha_rango",
            )
            if isinstance(date_range, tuple):
                start_date, end_date = date_range
            else:
                start_date = end_date = date_range
            mask = (df_raw["fecha_valoracion"].dt.date >= start_date) & (df_raw["fecha_valoracion"].dt.date <= end_date)
            df_date = df_raw.loc[mask].copy()

# ---------- CSS para KPIs ----------
KPI_CSS = """
<style>
    /* Cambiar el color de los widgets de Streamlit a azul */
    .st-bb {
        background-color: #B0E0E6;
    }
    .st-at {
        background-color: #4682B4;
    }
    .st-bh {
        background-color: #1E90FF;
    }
    .st-ag {
        background-color: #00BFFF;
    }
    /* Cambiar el color de los checkboxes y multiselect */
    .st-cb {
        background-color: #87CEEB;
    }
    /* Cambiar el color de los sliders */
    .st-dg {
        background-color: #1E90FF;
    }
</style>
"""
st.markdown(KPI_CSS, unsafe_allow_html=True)

# ================== KPIs ==================
col_agente = "esteticista" if "esteticista" in df_date.columns else ("asesor" if "asesor" in df_date.columns else None)
n_agentes = int(df_date[col_agente].nunique()) if col_agente else 0
n_usuarios = int(len(df_date))

k1, k2 = st.columns(2)
with k1:
    st.markdown(f"""<div class="kpi"><h3>Agentes en rango</h3><div class="value">{n_agentes:,}</div></div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""<div class="kpi"><h3>Usuarios en rango</h3><div class="value">{n_usuarios:,}</div></div>""", unsafe_allow_html=True)

# ================== TABLA ==================
st.caption(f"Registros filtrados (por fecha): {len(df_date)}")
st.dataframe(df_date, use_container_width=True, height=500)

# ================== ESCALA DE AZULES PERSONALIZADA ==================
BLUE_COLORSCALE = [
    [0.0, '#B0E0E6'],    # azul pálido
    [0.125, '#ADD8E6'],  # azul claro
    [0.25, '#87CEFA'],   # cielo azul claro
    [0.375, '#87CEEB'],  # cielo azul
    [0.5, '#00BFFF'],    # DeepSkyBlue
    [0.625, '#B0C4DE'],  # azul claro
    [0.75, '#1E90FF'],   # dodgerblue
    [0.875, '#6495ED'],  # azul aciano
    [1.0, '#4682B4']     # azul acero
]

# ================== FUNCIÓN PARA CREAR MAPAS DE CALOR CON USUARIOS ==================
def create_heatmap_with_users(df, main_column, title, second_dimension_candidates=None):
    """Crea un mapa de calor que muestra nombres de usuarios en los tooltips"""
    if main_column not in df.columns or df.empty:
        return None
    
    try:
        # Buscar columna de nombre de usuario
        nombre_col = next((col for col in ["nombre", "cliente", "paciente", "usuario"] if col in df.columns), None)
        
        # Buscar segunda dimensión
        second_dim = None
        if second_dimension_candidates:
            second_dim = next((col for col in second_dimension_candidates if col in df.columns), None)
        
        if second_dim:
            # Agrupar y recolectar nombres de usuarios
            grouped = df.groupby([second_dim, main_column])[nombre_col].agg([
                ('count', 'size'),
                ('users', lambda x: ', '.join(x.astype(str).unique()[:10]) + ('...' if len(x) > 10 else '')
            )]).reset_index()
            
            # Crear matriz para el heatmap
            pivot_data = grouped.pivot(index=second_dim, columns=main_column, values='count').fillna(0)
            
            # Crear matriz de texto con usuarios
            text_data = grouped.pivot(index=second_dim, columns=main_column, values='users').fillna('')
            
            fig = go.Figure(data=go.Heatmap(
                z=pivot_data.values,
                x=pivot_data.columns.tolist(),
                y=pivot_data.index.tolist(),
                text=text_data.values,
                hoverinfo='text',
                hovertemplate=(
                    f"{second_dim}: %{{y}}<br>"
                    f"{main_column}: %{{x}}<br>"
                    "Cantidad: %{z}<br>"
                    "Usuarios: %{text}<br>"
                    "<extra></extra>"
                ),
                colorscale=BLUE_COLORSCALE,
                showscale=True
            ))
            
        else:
            # Mapa de calor simple con usuarios
            if 'fecha_valoracion' in df.columns:
                df_temp = df.copy()
                df_temp['mes'] = df_temp['fecha_valoracion'].dt.to_period('M').astype(str)
                
                # Agrupar por mes y recolectar usuarios
                grouped = df_temp.groupby(['mes', main_column])[nombre_col].agg([
                    ('count', 'size'),
                    ('users', lambda x: ', '.join(x.astype(str).unique()[:8]) + ('...' if len(x) > 8 else '')
                )]).reset_index()
                
                pivot_data = grouped.pivot(index='mes', columns=main_column, values='count').fillna(0)
                text_data = grouped.pivot(index='mes', columns=main_column, values='users').fillna('')
                
                fig = go.Figure(data=go.Heatmap(
                    z=pivot_data.values,
                    x=pivot_data.columns.tolist(),
                    y=pivot_data.index.tolist(),
                    text=text_data.values,
                    hoverinfo='text',
                    hovertemplate=(
                        "Mes: %{y}<br>"
                        f"{main_column}: %{{x}}<br>"
                        "Cantidad: %{z}<br>"
                        "Usuarios: %{text}<br>"
                        "<extra></extra>"
                    ),
                    colorscale=BLUE_COLORSCALE,
                    showscale=True
                ))
                
            else:
                # Mapa de calor básico con usuarios
                user_groups = df.groupby(main_column)[nombre_col].agg([
                    ('count', 'size'),
                    ('users', lambda x: ', '.join(x.astype(str).unique()[:15]) + ('...' if len(x) > 15 else '')
                )]).reset_index()
                
                fig = go.Figure(data=go.Heatmap(
                    z=[user_groups['count'].values],
                    x=user_groups[main_column].tolist(),
                    y=[''],
                    text=[user_groups['users'].values],
                    hoverinfo='text',
                    hovertemplate=(
                        f"{main_column}: %{{x}}<br>"
                        "Cantidad: %{z}<br>"
                        "Usuarios: %{text}<br>"
                        "<extra></extra>"
                    ),
                    colorscale=BLUE_COLORSCALE,
                    showscale=True
                ))
        
        fig.update_layout(
            title=title,
            xaxis_title=main_column,
            yaxis_title=second_dim if second_dim else "",
        )
        return fig
        
    except Exception as e:
        st.error(f"Error al crear mapa de calor para {main_column}: {str(e)}")
        return None

# ================== FUNCIONES AUXILIARES ==================
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

# ================== SECCIÓN HIDRATACIÓN ==================
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
    fig_hid = create_heatmap_with_users(
        df_hid, 
        col_hid, 
        "Distribución de Niveles de Hidratación",
        second_dimension_candidates=["esteticista", "asesor", "genero", "sexo"]
    )
    if fig_hid:
        st.plotly_chart(fig_hid, use_container_width=True)

# ================== SECCIÓN SENSIBILIDAD ==================
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
    fig_sens = create_heatmap_with_users(
        df_sens,
        col_sens,
        "Distribución de Niveles Sebáceos / Sensibilidad",
        second_dimension_candidates=["esteticista", "asesor", "genero", "sexo"]
    )
    if fig_sens:
        st.plotly_chart(fig_sens, use_container_width=True)

# ================== SECCIONES ESPECÍFICAS ==================
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
        fig = create_heatmap_with_users(
            df_filtered,
            col_target,
            f"Distribución de {label}",
            second_dimension_candidates=["esteticista", "asesor", "genero", "sexo"]
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)

