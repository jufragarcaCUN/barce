import streamlit as st
import base64
from pathlib import Path

st.set_page_config(
    page_title="Barce · Inicio",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="expanded",
)

current_dir = Path(__file__).parent
logo_folder_name = "data"

# Ruta ABSOLUTA (con fallback relativo)
logo_win_path = Path(r"C:\Users\juan_garnicac\Documents\escuchaSocial\barce\data\barce.jpeg")
logo_rel_path = current_dir / logo_folder_name / "CUN-1200X1200.png"
img_path = logo_win_path if logo_win_path.exists() else logo_rel_path

def encode_image(path: Path) -> tuple[str, str]:
    try:
        b = path.read_bytes()
        mime = "image/jpeg" if path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
        return base64.b64encode(b).decode(), mime
    except Exception as e:
        st.info(f"⚠️ Imagen no disponible ({e}).")
        return "", "image/png"

encoded_img, img_mime = encode_image(img_path)

# ================= CSS (incluye el efecto y estilos mínimos) =================
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
        height:50vh;             /* mitad de la pantalla */
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

# ================= HERO (AQUÍ SE PINTA LA IMAGEN CON EL EFECTO) =================
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
    st.warning("No se pudo cargar la imagen del hero. Revisa la ruta en 'img_path'.")

# ================= RUTAS A OTRAS PÁGINAS =================
st.subheader("Rutas del flujo")
# <<< AQUI SE LLAMA A LA PAGINA CONSENTIMIENTO INFORMADO >>>
st.page_link("pages/ConsentimientoInformado.py", label="📝 ConsentimientoInformado")

# <<< AQUI SE LLAMA A LA PAGINA DIAGNOSTICO FACIAL (SIN TILDE EN EL NOMBRE DEL ARCHIVO) >>>
st.page_link("pages/DiagnosticoFacial.py", label="🧴 DiagnosticoFacial")

st.divider()
st.write("Bienvenida. Usa las rutas de arriba para continuar con el flujo del cliente.")
