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

# ================== FILTRO + GRÁFICO: NIVEL DE HIDRATACIÓN ==================
posibles_hid = ["nivel_hidratacion", "nivel_hidratación", "Nivel de hidratación"]
col_hid = next((c for c in posibles_hid if c in df_date.columns), None)

with st.sidebar:
    st.subheader("Filtro: Nivel de hidratación")
    if col_hid is None:
        st.error("No encuentro la columna de nivel de hidratación.")
        selected_hid_levels = []
        top_n_hid = 20
    else:
        niveles_hid = sorted(df_date[col_hid].dropna().unique().tolist())
        selected_hid_levels = st.multiselect(
            "Selecciona nivel(es) de hidratación",
            options=niveles_hid,
            default=niveles_hid,
            key="hid_multiselect",
        )
        top_n_hid = st.slider(
            "Top clientes (hidratación)",
            min_value=5, max_value=50, value=20, step=1,
            key="hid_topn",
        )

df_hid = df_date.copy()
if col_hid and selected_hid_levels:
    df_hid = df_hid[df_hid[col_hid].isin(selected_hid_levels)].copy()

if col_hid and selected_hid_levels:
    if "nombre" not in df_hid.columns:
        st.error("No encuentro la columna 'nombre' para identificar al cliente (hidratación).")
    elif df_hid.empty:
        st.warning("No hay datos tras aplicar el filtro de hidratación.")
    else:
        agg_hid = df_hid.groupby(["nombre", col_hid]).size().reset_index(name="n")
        top_hid = (
            agg_hid.groupby("nombre", as_index=False)["n"]
                   .sum()
                   .sort_values("n", ascending=False)
                   .head(top_n_hid)
        )
        agg_hid_top = agg_hid[agg_hid["nombre"].isin(top_hid["nombre"])]
        if not agg_hid_top.empty:
            fig_hid = px.bar(
                agg_hid_top, x="nombre", y="n", color=col_hid, barmode="group",
                title="Distribución de nivel de hidratación por cliente",
                hover_data={"nombre": True, col_hid: True, "n": True},
            )
            fig_hid.update_layout(xaxis_title="Cliente", yaxis_title="# registros")
            st.plotly_chart(fig_hid, use_container_width=True)

# ================== FILTRO + GRÁFICO: NIVEL SEBÁCEO / SENSIBILIDAD ==================
posibles_sens = ["nivel_sebaceo", "grado_sensibilidad", "sensibilidad"]
col_sens = next((c for c in posibles_sens if c in df_date.columns), None)

with st.sidebar:
    st.subheader("Filtro: Nivel sebáceo / sensibilidad")
    if col_sens is None:
        st.error("No encuentro la columna de nivel sebáceo/sensibilidad.")
        selected_sens_levels = []
        top_n_sens = 20
    else:
        niveles_sens = sorted(df_date[col_sens].dropna().unique().tolist())
        selected_sens_levels = st.multiselect(
            "Selecciona nivel(es) sebáceo/sensibilidad",
            options=niveles_sens,
            default=niveles_sens,
            key="sens_multiselect",
        )
        top_n_sens = st.slider(
            "Top clientes (sebáceo/sensibilidad)",
            min_value=5, max_value=50, value=20, step=1,
            key="sens_topn",
        )

df_sens = df_date.copy()
if col_sens and selected_sens_levels:
    df_sens = df_sens[df_sens[col_sens].isin(selected_sens_levels)].copy()

if col_sens and selected_sens_levels:
    if "nombre" not in df_sens.columns:
        st.error("No encuentro la columna 'nombre' para identificar al cliente (sebáceo/sensibilidad).")
    elif df_sens.empty:
        st.warning("No hay datos tras aplicar el filtro de sebáceo/sensibilidad.")
    else:
        agg_sens = df_sens.groupby(["nombre", col_sens]).size().reset_index(name="n")
        top_sens = (
            agg_sens.groupby("nombre", as_index=False)["n"]
                    .sum()
                    .sort_values("n", ascending=False)
                    .head(top_n_sens)
        )
        agg_sens_top = agg_sens[agg_sens["nombre"].isin(top_sens["nombre"])]
        if not agg_sens_top.empty:
            fig_sens = px.bar(
                agg_sens_top, x="nombre", y="n", color=col_sens, barmode="group",
                title="Distribución por nivel sebáceo / sensibilidad",
                hover_data={"nombre": True, col_sens: True, "n": True},
            )
            fig_sens.update_layout(xaxis_title="Cliente", yaxis_title="# registros")
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

def find_client_col(df: pd.DataFrame) -> str | None:
    return find_col(df, ["nombre", "cliente", "paciente", "usuario"])

def render_categorical_section(df_base: pd.DataFrame, label: str, candidates: list[str], key_prefix: str):
    col_target = find_col(df_base, candidates)
    with st.sidebar:
        st.subheader(label)
        if col_target is None:
            st.error(f"No encuentro la columna para: {label}")
            return
        niveles = sorted(df_base[col_target].dropna().unique().tolist())
        if not niveles:
            st.warning(f"Sin niveles válidos para: {label}")
            return
        sel = st.multiselect(
            f"Selecciona nivel(es) — {label}",
            options=niveles,
            default=niveles,
            key=f"{key_prefix}_multiselect",
        )
        topn = st.slider(
            f"Top clientes — {label}",
            min_value=5, max_value=50, value=20, step=1,
            key=f"{key_prefix}_topn",
        )

    df_f = df_base.copy()
    if sel:
        df_f = df_f[df_f[col_target].isin(sel)].copy()

    cliente_col = find_client_col(df_f)
    if cliente_col is None:
        st.error(f"No encuentro la columna de cliente (nombre/cliente/usuario) para: {label}")
        return
    if df_f.empty:
        st.warning(f"No hay datos tras aplicar filtros para: {label}")
        return

    agg = df_f.groupby([cliente_col, col_target]).size().reset_index(name="n")
    top = (
        agg.groupby(cliente_col, as_index=False)["n"]
           .sum()
           .sort_values("n", ascending=False)
           .head(topn)
    )
    agg_top = agg[agg[cliente_col].isin(top[cliente_col])]
    if agg_top.empty:
        st.warning(f"No hay datos para graficar con los filtros en: {label}")
        return

    fig = px.bar(
        agg_top, x=cliente_col, y="n", color=col_target, barmode="group",
        title=f"Distribución por {label} (por cliente)",
        hover_data={cliente_col: True, col_target: True, "n": True},
    )
    fig.update_layout(xaxis_title="Cliente", yaxis_title="# registros")
    st.plotly_chart(fig, use_container_width=True)

# ================== SECCIONES ESPECÍFICAS QUE PEDISTE (sobre df_date) ==================
render_categorical_section(
    df_base=df_date,
    label="Pigmentación",
    candidates=["pigementacion", "pigmentacion", "pigmentación"],
    key_prefix="pigmentacion",
)
render_categorical_section(
    df_base=df_date,
    label="Tratamiento médico",
    candidates=["tratamiento medico", "tratamiento_medico", "tratamiento_médico"],
    key_prefix="trat_medico",
)
render_categorical_section(
    df_base=df_date,
    label="Tratamiento médico — ¿Cuál?",
    candidates=["tratamiento_medico_cual", "tratamiento medico cual", "tratamiento_médico_cuál"],
    key_prefix="trat_medico_cual",
)
render_categorical_section(
    df_base=df_date,
    label="Firmeza / líneas de expresión (zona)",
    candidates=["firmeza lineas_expresion_zon", "firmeza_lineas_expresion_zon", "firmeza lineas expresion zon"],
    key_prefix="firmeza_lineas",
)
render_categorical_section(
    df_base=df_date,
    label="Nutrición",
    candidates=["nutricion", "nutrición"],
    key_prefix="nutricion",
)
render_categorical_section(
    df_base=df_date,
    label="Fotosensibilidad",
    candidates=["fotosnesibilidad", "fotosensibilidad", "foto_sensibilidad"],
    key_prefix="fotosensibilidad",
)
render_categorical_section(
    df_base=df_date,
    label="Tratamiento para reducir enfermedades importantes",
    candidates=[
        "tratamiento_para reducir enfermedades_importantes",
        "tratamiento_para_reducir_enfermedades_importantes",
        "tratamiento para reducir enfermedades importantes",
    ],
    key_prefix="trat_enf_importantes",
)
render_categorical_section(
    df_base=df_date,
    label="Toma medicamentos",
    candidates=["toma_medicamentos", "toma medicamentos"],
    key_prefix="toma_meds",
)
