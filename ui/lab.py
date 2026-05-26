import streamlit as st
import urllib.parse
import json
import datetime
from pathlib import Path
from src.toku_radar.tools.miro_predictor import ComiteSimulation

def log_objections_vault(
    user_active, empresa, url_cliente, modo, contexto,
    objeciones_lista, sim_result, vendedor_url, dpo_feedback=None
):
    """Registra en la bóveda con campos estructurados para DPO/RLHF."""
    vault_file = Path("objections_vault.jsonl")
    record = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "user_name": user_active.get("name", "Desconocido") if user_active else "Desconocido",
        "user_email": user_active.get("email", "") if user_active else "",
        "user_role": user_active.get("role", "Otro") if user_active else "Otro",
        "user_industry": user_active.get("industry", "General") if user_active else "General",
        # Flag DPO: registros admin = tests, NO incluir en entrenamiento
        "is_admin": user_active.get("is_admin", False) if user_active else False,
        "source": "admin_test" if (user_active and user_active.get("is_admin")) else "production",
        "empresa_target": empresa,
        "url_cliente": url_cliente,
        "vendedor_url": vendedor_url,
        "modo": modo,
        # Contexto libre (narración del vendedor)
        "contexto_libre": contexto,
        # Lista estructurada de objeciones (anticipadas en pre / reales en post)
        "objeciones_lista": objeciones_lista,
        # Señal DPO: qué predicciones del modelo fueron correctas
        "dpo_feedback": dpo_feedback or {},
        "comite_simulado": [
            {
                "name": p.get("name", ""),
                "role": p.get("role", ""),
                "disc": p.get("disc", ""),
                "stance": p.get("stance", "")
            }
            for p in sim_result.get("personas", [])
        ]
    }
    try:
        with open(vault_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        from core.logger import logger
        logger.error(f"Error escribiendo en objections_vault.jsonl: {e}")

def render_lab_tab(companies_data=None, user_active=None):
    st.markdown("""
        <div style='background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); padding: 20px; border-radius: 10px; margin-bottom: 25px;'>
            <h2 style='color: white; margin: 0;'>🧪 NERV Lab</h2>
            <p style='color: #d1d5db; margin: 5px 0 0 0;'>
                Simula el comité de compras de tu prospecto. Llega preparado o debriefa lo que pasó.
            </p>
        </div>
    """, unsafe_allow_html=True)

    def_url_cliente = ""
    def_producto = "ej: Software de Ciberseguridad / Tu Producto"
    def_contexto = ""
    use_toku_demo = False

    # ── PASO 1: Inputs mínimos ────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🚀 Tu Empresa")
        default_url_vendedor = "https://mi-empresa.com"
        url_vendedor = st.text_input("URL de tu Empresa", value=default_url_vendedor)
        producto = st.text_input("¿Qué vendes?", value=def_producto)
    with col2:
        st.subheader("🎯 Tu Prospecto")
        if companies_data:
            # Admin / Toku: selector desplegable con la lista de prospectos
            opciones = ["(Nueva Empresa / Ingreso Manual)"] + sorted([c["empresa"] for c in companies_data])
            seleccion = st.selectbox("Selecciona el prospecto", options=opciones)
            use_toku_demo = st.checkbox(
                "🔌 Usar propuesta de valor Demo (Toku)",
                value=False,
                help="Carga el pitch predefinido de Toku para cobros y recurrencia."
            )
            if seleccion != "(Nueva Empresa / Ingreso Manual)":
                empresa_data = next(c for c in companies_data if c["empresa"] == seleccion)
                def_url_cliente = empresa_data.get("url", "")
                def_contexto = empresa_data.get("contexto", "")
                if use_toku_demo:
                    def_producto = empresa_data.get("pitch_principal", def_producto)
                    url_vendedor = "https://toku.com"
            # Campo de texto siempre visible (muestra la URL o permite editarla)
            url_cliente = st.text_input("URL de la Empresa Cliente", value=def_url_cliente, placeholder="https://empresa-cliente.com")
        else:
            # Demo / Agnóstico: el usuario escribe la URL manualmente
            url_cliente = st.text_input("URL de la Empresa Cliente", value="", placeholder="https://empresa-cliente.com")
        icp_linkedin = st.text_input(
            "🔗 LinkedIn del Tomador de Decisión (Opcional)",
            placeholder="https://linkedin.com/in/usuario",
            help="Si lo ingresas, NERV garantizará que esta persona sea parte del comité y buscará su correo verificado.",
            key="icp_linkedin"
        )

    st.divider()

    # ── PASO 2: Modo PRE o POST ───────────────────────────────────────────────
    st.markdown("#### ¿En qué momento estás?")
    modo_opcion = st.radio(
        label="modo_selector",
        options=[
            "📋 Pre-Reunión — Me preparo para una junta que aún no ocurre",
            "🎙️ Post-Reunión — Acabo de salir de una junta y necesito debriefear",
        ],
        horizontal=True,
        label_visibility="collapsed",
        key="modo_selector"
    )
    modo = "pre" if "Pre" in modo_opcion else "post"

    # ── PASO 3: Contexto libre + Objeciones estructuradas ──────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if modo == "pre":
        contexto = st.text_area(
            "🧠 ¿Qué sabes de este prospecto y qué quieres lograr?",
            value=def_contexto,
            placeholder=(
                "Cuéntamelo todo como si le contaras a un colega:\n"
                "¿Quién es la empresa? ¿Quién va a estar en la junta? "
                "¿Qué te han dicho antes? ¿Qué quieres conseguir?"
            ),
            height=130,
            key="contexto_pre"
        )
        st.markdown(
            "**🚧 ¿Qué objeciones anticipas?** "
            "<span style='color:#94a3b8;font-size:0.85em;'>Una por línea — esto alimenta el DPO</span>",
            unsafe_allow_html=True
        )
        objeciones_raw = st.text_area(
            "objeciones_pre",
            placeholder=(
                "Ej:\nEl precio es muy alto\n"
                "Ya tienen un proveedor\n"
                "No es prioridad ahora"
            ),
            height=110,
            label_visibility="collapsed",
            key="objeciones_pre"
        )
    else:
        contexto = st.text_area(
            "📝 ¿Qué pasó en la junta?",
            value=def_contexto,
            placeholder=(
                "Ej: Presenté la solución. El CFO preguntó por precio, "
                "el líder de IT por integración con su ERP."
            ),
            height=130,
            key="contexto_post"
        )
        st.markdown(
            "**⚠️ ¿Qué objeciones te pusieron?** "
            "<span style='color:#94a3b8;font-size:0.85em;'>Una por línea — señal directa para DPO</span>",
            unsafe_allow_html=True
        )
        objeciones_raw = st.text_area(
            "objeciones_post",
            placeholder=(
                "Ej:\nEl precio está fuera de nuestro presupuesto\n"
                "Necesitamos aprobación del board\n"
                "Ya tenemos una solución similar"
            ),
            height=110,
            label_visibility="collapsed",
            key="objeciones_post"
        )
    # ── Botón único ───────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🧬 Activar NERV", use_container_width=True, type="primary"):
        if not user_active:
            st.error("⚠️ Identificación requerida: Por favor, selecciona tu perfil o regístrate en el panel lateral antes de activar NERV.")
            return

        faltantes = []
        if not url_vendedor:                     faltantes.append("URL de tu Empresa")
        if not producto:                          faltantes.append("¿Qué vendes?")
        if not url_cliente:                       faltantes.append("URL del Cliente")
        if not contexto or not contexto.strip(): faltantes.append("Contexto")

        if faltantes:
            st.warning(f"⚠️ Por favor completa: {', '.join(faltantes)}")
            return

        # Parsear objeciones estructuradas (lista limpia sin vacíos)
        objeciones_lista = [
            line.strip() for line in objeciones_raw.splitlines()
            if line.strip()
        ]
        st.session_state["nerv_objeciones_lista"] = objeciones_lista
        st.session_state["nerv_modo"] = modo
        st.session_state["nerv_contexto"] = contexto
        st.session_state["nerv_url_cliente"] = url_cliente
        st.session_state["nerv_url_vendedor"] = url_vendedor

        domain = urllib.parse.urlparse(
            url_cliente if "//" in url_cliente else f"http://{url_cliente}"
        ).netloc
        parts = domain.replace("www.", "").split(".")
        empresa_nombre = parts[0].capitalize() if parts else "Empresa"
        
        st.session_state["nerv_empresa"] = empresa_nombre

        with st.status(f"🧬 Iniciando Protocolos NERV para {empresa_nombre}...", expanded=True) as sim_status:
            log_container = st.empty()

            def sim_logger(msg):
                from core.logger import logger
                logger.info(msg)
                log_container.markdown(f"`{msg}`")

            # 1. Extraer Inteligencia Automáticamente
            try:
                from src.toku_radar.crew import TokuCrew
                import re
                crew = TokuCrew(
                    empresa=empresa_nombre,
                    sector="General", 
                    pitch=producto,
                    vendedor=url_vendedor,
                    url_cliente=url_cliente,
                    prior_knowledge=contexto,
                    log_callback=sim_logger
                )
                raw_dossier = crew.kickoff()
                dossier_final = re.sub(r'<thought>.*?</thought>', '', raw_dossier, flags=re.DOTALL).strip()
            except Exception as e:
                sim_logger(f"⚠️ Error extrayendo inteligencia web. Usando contexto manual. {e}")
                dossier_final = (
                    f"Vendedor: {url_vendedor}\n"
                    f"Producto: {producto}\n"
                    f"Cliente: {url_cliente}\n\n"
                    f"Contexto: {contexto}"
                )

            # 2. Simular Comité
            try:
                sim = ComiteSimulation(log_callback=sim_logger)
                sim_result = sim.run_simulation(
                    product=producto,
                    sector="General",
                    dossier=dossier_final,
                    objeciones=contexto,
                    vendor_notes=contexto if modo == "post" else None,
                    company_url=url_cliente,
                    empresa=empresa_nombre,
                    icp_linkedin=icp_linkedin,
                )
                st.session_state["nerv_sim_result"] = sim_result
                sim_status.update(label="✅ Análisis y Simulación Completados", state="complete")
                
                # Registrar en la Bóveda de Objeciones (sin dpo_feedback aún — llega después)
                objeciones_lista_saved = st.session_state.get("nerv_objeciones_lista", [])
                log_objections_vault(
                    user_active=user_active,
                    empresa=empresa_nombre,
                    url_cliente=st.session_state.get("nerv_url_cliente", url_cliente),
                    modo=modo,
                    contexto=contexto,
                    objeciones_lista=objeciones_lista_saved,
                    sim_result=sim_result,
                    vendedor_url=st.session_state.get("nerv_url_vendedor", url_vendedor),
                    dpo_feedback=None  # se actualiza cuando el user valida abajo
                )
            except Exception as e:
                st.error(f"Error crítico en la simulación: {e}")
                sim_status.update(label="❌ Error en la Simulación", state="error")

    # ── OUTPUT ────────────────────────────────────────────────────────────────
    if "nerv_sim_result" not in st.session_state:
        return

    sim_result = st.session_state["nerv_sim_result"]
    empresa_nombre = st.session_state.get("nerv_empresa", "Empresa")
    mode = sim_result.get("mode", "pre")

    st.divider()

    # Disclaimer modo simulación
    st.markdown("""
<div style='background: linear-gradient(90deg, #7c3aed 0%, #a855f7 100%);
            padding: 14px 20px; border-radius: 8px; margin: 10px 0 18px 0;'>
    <b style='color: white; font-size: 1em;'>⚠️ MODO SIMULACIÓN ACTIVO</b><br>
    <span style='color: #e9d5ff; font-size: 0.85em;'>
    Los perfiles y argumentos son inferencias del LLM basadas en tu contexto.
    Verifica estadísticas marcadas con ⚠️ antes de usarlas en una reunión real.
    </span>
</div>
""", unsafe_allow_html=True)

    mode_label = "📋 Pre-Reunión" if mode == "pre" else "🎙️ Post-Reunión"
    st.markdown(f"### 👥 Comité de Compras — **{empresa_nombre}** · {mode_label}")

    # ── Tarjetas del comité ───────────────────────────────────────────────────
    personas = sim_result.get("personas", [])
    if personas:
        cols = st.columns(len(personas))
        disc_colors = {"D": "#ef4444", "I": "#f59e0b", "S": "#22c55e", "C": "#3b82f6"}
        disc_labels = {"D": "Dominante", "I": "Influyente", "S": "Estable", "C": "Consciente"}

        for idx, p in enumerate(personas):
            disc = p.get("disc", "?")
            color = disc_colors.get(disc, "#94a3b8")
            label = disc_labels.get(disc, disc)
            email_html = (
                f"<p style='margin:5px 0 0 0;font-size:0.85em;color:#10b981;'>"
                f"<b>Email:</b> {p['email']} ✅</p>"
            ) if p.get("email") else ""
            linkedin_html = (
                f"<p style='margin:2px 0 5px 0;font-size:0.85em;'>"
                f"<a href='{p['linkedin_url']}' target='_blank' style='color:#3b82f6;'>🔗 Perfil LinkedIn</a></p>"
            ) if p.get("linkedin_url") else ""

            with cols[idx]:
                html_content = f"""
<div style='background:#1e293b;border-left:5px solid {color};
            padding:15px;border-radius:5px;min-height:220px;
            overflow-y:auto;color:#f8fafc;margin-bottom:15px;'>
    <h4 style='margin:0;color:{color};font-size:1.1em;'>{p['name']}</h4>
    <p style='margin:5px 0 0 0;font-size:0.85em;'><b>Rol:</b> {p['role']}</p>
    {email_html}
    {linkedin_html}
    <span style='background:{color};color:white;font-size:0.75em;
                 padding:2px 8px;border-radius:10px;font-weight:bold;
                 display:inline-block;margin-top:6px;'>
        DISC: {disc} — {label}
    </span>
    <p style='margin:6px 0 0 0;font-size:0.78em;color:#cbd5e1;'>
        {p.get('disc_description','')}
    </p>
    <p style='margin:8px 0 0 0;font-size:0.8em;color:#94a3b8;line-height:1.3;'>
        {p.get('stance','')}
    </p>
</div>
"""
                st.markdown(html_content, unsafe_allow_html=True)

    # ── Tabs de simulación ────────────────────────────────────────────────────
    phase2_label = "📌 Criterios de Entrada" if mode == "pre" else "⚖️ Veredicto y Negociación"

    tab1, tab2 = st.tabs([phase2_label, "🎯 Plan de Ataque GTM"])
    with tab1:
        st.markdown(sim_result.get("phase_2", sim_result.get("round_2", "")))
    with tab2:
        st.markdown(sim_result.get("battle_plan", ""))

    # ── DPO Feedback: Validación humana de predicciones ──────────────────────
    st.divider()
    st.markdown("### 🧠 Human-in-the-Loop · Señal DPO")
    st.caption("Valida qué tan bien predijo NERV. Esta información entrena el modelo.")

    objeciones_lista = st.session_state.get("nerv_objeciones_lista", [])
    modo_guardado = st.session_state.get("nerv_modo", mode)

    dpo_col1, dpo_col2 = st.columns(2)

    with dpo_col1:
        label_obj = "🚧 Objeciones anticipadas" if modo_guardado == "pre" else "⚠️ Objeciones reportadas"
        st.markdown(f"**{label_obj}**")
        if objeciones_lista:
            for obj in objeciones_lista:
                st.markdown(f"- {obj}")
        else:
            st.caption("No ingresaste objeciones estructuradas en este análisis.")

        # Para modo post: marcar cuáles predijo bien NERV
        if modo_guardado == "post" and objeciones_lista:
            st.markdown("**¿Cuáles predijo NERV correctamente?**")
            predicciones_correctas = st.multiselect(
                "predicciones_ok",
                options=objeciones_lista,
                label_visibility="collapsed",
                key="dpo_pred_ok"
            )
        else:
            predicciones_correctas = []

    with dpo_col2:
        st.markdown("**⭐ Calidad general de la simulación**")
        sim_rating = st.select_slider(
            "Rating",
            options=["Inútil", "Pobre", "Útil", "Genial", "🎯 Perfecto"],
            value="Útil",
            key="sim_rating"
        )
        objecion_nueva = st.text_input(
            "➕ Objeción real no anticipada (opcional)",
            placeholder="Ej: Nos pidieron referencias de clientes similares",
            key="dpo_nueva_objecion"
        )

    if st.button("💾 Guardar Feedback DPO", key="save_dpo_feedback", use_container_width=True, type="secondary"):
        try:
            from src.toku_radar.tools.miro_predictor import ROLEPLAY_LOG
            dpo_record = {
                "ts": datetime.datetime.utcnow().isoformat() + "Z",
                "empresa": empresa_nombre,
                "mode": mode,
                "rating": sim_rating,
                "objeciones_ingresadas": objeciones_lista,
                "predicciones_correctas": predicciones_correctas,
                "objecion_nueva": objecion_nueva.strip() if objecion_nueva else "",
                "user_role": st.session_state.get("user_active", {}).get("role", "Otro"),
                "user_industry": st.session_state.get("user_active", {}).get("industry", "General"),
                "type": "dpo_feedback"
            }
            with open(ROLEPLAY_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(dpo_record, ensure_ascii=False) + "\n")
            # También actualizar vault
            vault_file = Path("objections_vault.jsonl")
            with open(vault_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({**dpo_record, "type": "dpo_feedback_vault"}, ensure_ascii=False) + "\n")
            st.toast(f"✅ Feedback DPO guardado. Rating: '{sim_rating}'")
            if predicciones_correctas:
                st.success(f"📌 {len(predicciones_correctas)} objeción(es) confirmadas como correctas.")
            if objecion_nueva.strip():
                st.info(f"➕ Objeción nueva registrada: *{objecion_nueva.strip()}*")
        except Exception as e:
            st.error(f"Error guardando feedback DPO: {e}")

    full_sim_report = (
        f"# 🔬 Simulación NERV: {empresa_nombre}\n\n"
        f"## 👥 Comité de Compras\n"
        + "\n".join([
            f"- **{p['name']} ({p['role']})** — DISC: {p.get('disc','?')} "
            f"({p.get('disc_description','')})\n  Postura: {p.get('stance','')}"
            for p in personas
        ])
        + f"\n\n## ⚖️ Veredicto y Negociación\n{sim_result.get('phase_2','')}"
        + f"\n\n## 🎯 Plan de Ataque GTM\n{sim_result.get('battle_plan','')}"
    )

    st.download_button(
        "📩 Descargar Reporte Completo",
        full_sim_report,
        file_name=f"NERV_{empresa_nombre}.md",
        use_container_width=True
    )
