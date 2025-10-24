import streamlit as st
import base64
from pathlib import Path

st.set_page_config(
    page_title="Barce · Inicio",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ================= CONFIGURACIÓN DE RUTAS CORREGIDA =================
current_dir = Path(__file__).parent if "__file__" in locals() else Path.cwd()

# Lista de posibles ubicaciones y nombres de archivo
possible_paths = [
    current_dir / "data" / "barce.jpeg",      # Nombre que mencionaste
    current_dir / "data" / "barca.jpeg",      # Nombre que usas en el código
    current_dir / "data" / "CUN-1200X1200.png", # El otro archivo que mencionas
    Path("data/barce.jpeg"),                  # Ruta relativa
    Path("data/barca.jpeg"),                  # Ruta relativa alternativa
]

# Encontrar la primera ruta que exista
img_path = None
for path in possible_paths:
    if path.exists():
        img_path = path
        st.success(f"✅ Imagen encontrada en: {img_path}")
        break

# Si no se encuentra ninguna, mostrar ayuda para diagnóstico
if img_path is None:
    st.error("❌ No se pudo encontrar ninguna imagen. Verifica:")
    st.write("**Archivos buscados:**")
    for path in possible_paths:
        st.write(f"- {path} → Existe: {path.exists()}")
    
    # Mostrar estructura de directorios para ayudar
    st.write("**Estructura de directorios actual:**")
    try:
        for item in current_dir.rglob("*"):
            if item.is_file():
                st.write(f"  {item}")
    except:
        st.write("  No se pudo leer la estructura de directorios")
    
    img_path = Path("")  # Ruta vacía para evitar error

def encode_image(path: Path) -> tuple[str, str]:
    if not path or not path.exists():
        return "", "image/png"
    
    try:
        b = path.read_bytes()
        mime = "image/jpeg" if path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
        return base64.b64encode(b).decode(), mime
    except Exception as e:
        st.error(f"⚠️ Error al codificar imagen: {e}")
        return "", "image/png"

encoded_img, img_mime = encode_image(img_path)

# ================= CSS (mantener igual) =================
st.markdown(
    """
    <style>
      html, body { overflow-x:hidden; scroll-behavior:smooth; }
      .stApp > header { display:none !important; }

      .title-container{ width:100%; padding:24px 0 8px 0; margin:0 auto; }
      .main-title{
        font-family: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Arial;
        font-size: clamp(2rem, 6vw, 5rem);
        font-weight:800; color:#31A354; text-align:center; margin:0;
        text-shadow: 2px 2px 12px rgba(0, 255, 0, 0.25);
        letter-spacing:.5px;
      }

      /* === HERO: imagen mitad de pantalla con Efecto Ken Burns === */
      .hero-wrap{
        width:100%;
        height:50vh;
        overflow:hidden;
        border-radius:18px;
        position:relative;
        box-shadow: 0 16px 40px rgba(0,0,0,.18);
        background:#00000010;
        margin: 8px auto 24px auto;
      }
      .hero-img{
        width:100%;
        height:100%;
        display:block;
        object-fit:cover;
        transform-origin:center;
        will-change:transform;
        animation: kenburns 10s ease-in-out infinite alternate both;
      }
      @keyframes kenburns{
        0%   { transform: scale(1.03) translate3d(0, 0, 0); }
        50%  { transform: scale(1.08) translate3d(0, -1.5%, 0); }
        100% { transform: scale(1.12) translate3d(0, -3%, 0); }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ================= Título =================
st.markdown(
    """
    <div class="title-container">
      <p class="main-title">Tablero Control Tratamientos Faciales</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ================= HERO =================
if encoded_img:
    st.markdown(
        f"""
        <figure class="hero-wrap">
          <img src="data:{img_mime};base64,{encoded_img}" class="hero-img" alt="Hero">
        </figure>
        """,
        unsafe_allow_html=True,
    )
else:
    # Placeholder si no hay imagen
    st.markdown(
        """
        <div class="hero-wrap" style="display:flex; align-items:center; justify-content:center; background:#f0f2f6;">
          <p style="color:#666; font-size:1.2rem;">Imagen no disponible</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ================= RUTAS A OTRAS PÁGINAS =================
st.subheader("Rutas del flujo")
st.page_link("pages/ConsentimientoInformado.py", label="📝 ConsentimientoInformado")
st.page_link("pages/DiagnosticoFacial.py", label="🧴 DiagnosticoFacial")

st.divider()
st.write("Bienvenida. Usa las rutas de arriba para continuar con el flujo del cliente.")
