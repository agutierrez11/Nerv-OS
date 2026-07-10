import streamlit as st
import pandas as pd
import re
import unicodedata
from pathlib import Path
from core.lookalike_engine import LookalikeCrew
from core.icp_store import icp_store
from src.toku_radar.crew import NervCrew
from core.database import db
from core.telegram_logger import send_telegram_notification
from core.logger import logger

def clean_filename(text):
    if not text:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', text)
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
    return re.sub(r'[^\w\-]', '_', only_ascii).strip('_')

def render_lookalike_tab(user_active=None):
    st.subheader("// Motor de Prospectos y Lookalikes (NERV Lookalike)")
    st.write(
        "Identifica prospectos que encajan con tu Perfil de Cliente Ideal (ICP) "
        "o extrae clientes de tus competidores para interceptarlos en tiempo real."
    )

    # 1. Indicadores / Stats del pipeline desde Supabase
    st.markdown("### 📊 Pipeline de Prospectación")
    try:
        stats = icp_store.get_stats()
        col_st1, col_st2, col_st3 = st.columns(3)
        with col_st1:
            st.metric("Total Prospectos", stats.get("total", 0))
        with col_st2:
            st.metric("Nuevos (Sin contactar)", stats.get("nuevos", 0))
        with col_st3:
            st.metric("Contactados / Calificados", stats.get("contactados", 0))
    except Exception as e:
        st.warning("No se pudieron cargar estadísticas en tiempo real de Supabase (Base de datos desconectada o pausada).")

    st.divider()

    # 2. Selección de Vector de Búsqueda
    col_config, col_results = st.columns([1, 2])

    # Inicializar estado para los resultados de la sesión si no existe
    if "lookalike_results" not in st.session_state:
        st.session_state["lookalike_results"] = []

    is_toku = user_active.get("is_toku", False) if user_active else False

    with col_config:
        st.markdown("### 🛠️ Configurar Vector de Búsqueda")
        vector_type = st.radio(
            "Selecciona el vector estratégico:",
            ["🎯 Vector 1: Lookalike Directo", "⚔️ Vector 2: Competitor Intercept"]
        )

        if vector_type == "🎯 Vector 1: Lookalike Directo":
            empresa_base = st.text_input(
                "Empresa de Referencia (Éxito Base)", 
                value="Mary Kay México" if is_toku else "Clip",
                help="Empresa que ya es tu cliente o representa tu ICP perfecto."
            )
            sector = st.text_input(
                "Sector / Vertical", 
                value="Catalog / Venta por catálogo" if is_toku else "Fintech",
                help="Sector de la empresa base."
            )
            pitch = st.text_area(
                "Propuesta de Valor (Pitch de Venta)",
                value="Automatización de Cobranza a Consultoras con Domiciliación y AI Agent" if is_toku else "Terminales de pago y cobros recurrentes",
                help="Propuesta de valor que deseas calibrar contra el prospecto."
            )
            extra_context = st.text_area(
                "Contexto Adicional (Opcional)",
                placeholder="Evitar competidores directos, enfocar en empresas con facturación de +10M USD..."
            )
            max_results = st.slider("Resultados Máximos", min_value=3, max_value=20, value=8)

            if st.button("Buscar Prospectos Lookalike 🧠", type="primary", use_container_width=True):
                if not empresa_base:
                    st.error("Especifica la empresa de referencia.")
                else:
                    with st.status("Generando lookalikes directos...", expanded=True) as status:
                        try:
                            crew = LookalikeCrew(
                                mode="direct",
                                empresa_base=empresa_base,
                                sector=sector,
                                pitch=pitch,
                                extra_context=extra_context,
                                max_results=max_results,
                                vendor=user_active.get("vendedor_name") if user_active else None
                            )
                            results = crew.run()
                            st.session_state["lookalike_results"] = results
                            status.update(label=f"✅ Búsqueda completada: {len(results)} prospectos evaluados", state="complete")
                            
                            # Notificación a Telegram si está configurado
                            vendedor_name = user_active.get("name", "Invitado") if user_active else "Invitado"
                            modo_str = "Modo Toku 🟢" if is_toku else "Modo Agnóstico 🔵"
                            send_telegram_notification(
                                f"🧠 *Lookalike Generado* ({modo_str})\nBase: {empresa_base}\nSector: {sector}\nProspectos: {len(results)}\nUsuario: {vendedor_name}"
                            )
                        except Exception as e:
                            status.update(label="❌ Error durante la generación", state="error")
                            st.error(str(e))

        else:  # Competitor Intercept
            competitor_url = st.text_input(
                "URL del Competidor",
                value="https://gtmagent.getswan.com",
                help="URL del sitio web del competidor (se buscarán sus secciones de clientes/casos de éxito)."
            )
            empresa_base = st.text_input(
                "Tu Empresa Base (Opcional)",
                value="Toku" if is_toku else "Mi Empresa",
                help="Tu empresa para calcular fit."
            )
            sector = st.text_input(
                "Sector / Vertical",
                value="Fintech / Pagos" if is_toku else "SaaS",
            )
            pitch = st.text_area(
                "Tu Propuesta de Valor (Pitch)",
                value="Automatización y orquestación inteligente de cobranza B2B" if is_toku else "Solución comercial B2B",
            )
            max_results = st.slider("Resultados Máximos", min_value=3, max_value=20, value=8)

            if st.button("Interceptar Competidor ⚔️", type="primary", use_container_width=True):
                if not competitor_url:
                    st.error("Especifica la URL del competidor.")
                else:
                    with st.status(f"Escaneando competidor: {competitor_url}...", expanded=True) as status:
                        try:
                            crew = LookalikeCrew(
                                mode="competitor",
                                competitor_url=competitor_url,
                                empresa_base=empresa_base,
                                sector=sector,
                                pitch=pitch,
                                max_results=max_results,
                                vendor=user_active.get("vendedor_name") if user_active else None
                            )
                            results = crew.run()
                            st.session_state["lookalike_results"] = results
                            status.update(label=f"✅ Interceptación completada: {len(results)} prospectos detectados", state="complete")

                            vendedor_name = user_active.get("name", "Invitado") if user_active else "Invitado"
                            modo_str = "Modo Toku 🟢" if is_toku else "Modo Agnóstico 🔵"
                            send_telegram_notification(
                                f"⚔️ *Competitor Intercept* ({modo_str})\nCompetidor: {competitor_url}\nProspectos: {len(results)}\nUsuario: {vendedor_name}"
                            )
                        except Exception as e:
                            status.update(label="❌ Error al interceptar competidor", state="error")
                            st.error(str(e))

    with col_results:
        st.markdown("### 🎯 Prospectos Calibrados")
        results = st.session_state.get("lookalike_results", [])

        if not results:
            st.info("Configura los parámetros en el panel izquierdo y ejecuta la búsqueda para ver resultados.")
        else:
            # Filtrar errores
            clean_results = [r for r in results if r.get("empresa") != "ERROR"]
            if not clean_results:
                st.warning("No se encontraron prospectos válidos en la última ejecución.")
            else:
                # Mostrar en formato DataFrame interactivo
                df_data = []
                for r in clean_results:
                    df_data.append({
                        "Empresa": r.get("empresa", ""),
                        "Fit Score": r.get("score", 50),
                        "Señal Clave": r.get("señal_principal", ""),
                        "Decisor Sugerido": r.get("decision_maker_sugerido", ""),
                        "Razón del Fit": r.get("razon", ""),
                        "URL / Snippet": r.get("url") or r.get("snippet", "")
                    })
                
                df = pd.DataFrame(df_data)
                # Ordenar por score descendente
                df = df.sort_values(by="Fit Score", ascending=False)
                
                st.dataframe(df, use_container_width=True, hide_index=True)

                st.divider()

                # Acción: Generar Dossier para un prospecto de la tabla
                st.markdown("### 🚀 Generar Inteligencia GTM")
                
                selected_prospect = st.selectbox(
                    "Selecciona una empresa para iniciar un Dossier Forense completo:",
                    options=df["Empresa"].tolist()
                )

                if selected_prospect:
                    # Encontrar los datos de la fila seleccionada
                    row_data = next((r for r in clean_results if r["empresa"] == selected_prospect), None)
                    
                    if row_data:
                        # Recuperar valores para NervCrew
                        custom_pitch = st.text_input("Pitch de Venta Final para Dossier", value=pitch if 'pitch' in locals() else "Automatización")
                        custom_reason = row_data.get("razon", "")
                        
                        if st.button(f"GENERAR DOSSIER FORENSE PARA {selected_prospect.upper()} 🚀", type="primary", use_container_width=True):
                            output_dir = Path("output")
                            output_dir.mkdir(exist_ok=True)
                            
                            with st.status(f"🧠 Lanzando enjambre GTM para {selected_prospect}...", expanded=True) as status:
                                try:
                                    log_placeholder = st.empty()
                                    st.session_state.full_log = ""
                                    def update_ui_log(msg):
                                        st.session_state.full_log += msg + "\n\n"
                                        log_placeholder.markdown(f"```text\n{st.session_state.full_log}\n```")

                                    vendedor_url = user_active.get("vendedor_url", "https://toku.com") if user_active else "https://toku.com"
                                    
                                    # Ejecutar NervCrew
                                    crew = NervCrew(
                                        empresa=selected_prospect,
                                        sector=sector if 'sector' in locals() else "General",
                                        pitch=custom_pitch,
                                        vendedor=vendedor_url,
                                        url_cliente=row_data.get("url", ""),
                                        prior_knowledge=f"Prospecto calificado por NERV Lookalike. Razón: {custom_reason}",
                                        log_callback=update_ui_log
                                    )
                                    dossier = crew.kickoff()
                                    
                                    # Limpiar thoughts
                                    dossier_limpio = re.sub(r'<thought>.*?</thought>', '', dossier, flags=re.DOTALL).strip()
                                    st.session_state[f"dossier_{selected_prospect}"] = dossier_limpio
                                    
                                    # Guardar en local
                                    safe_name = clean_filename(selected_prospect)
                                    (output_dir / f"{safe_name}.md").write_text(dossier_limpio, encoding="utf-8")
                                    
                                    # Guardar automáticamente en la bóveda de Obsidian
                                    vault_path = Path("/home/antonio/Desktop/Toku_WarRoom_Vault")
                                    if vault_path.exists():
                                        try:
                                            from core.obsidian_linker import link_dossier
                                            dossier_linked = link_dossier(dossier_limpio, str(vault_path))
                                        except Exception as le:
                                            logger.error(f"Error running obsidian linker during lookalike auto-save: {le}")
                                            dossier_linked = dossier_limpio
                                        try:
                                            (vault_path / f"{safe_name}.md").write_text(dossier_linked, encoding="utf-8")
                                            st.toast(f"📂 Dossier auto-guardado en Obsidian.")
                                        except Exception as ve:
                                            logger.error(f"Error guardando automático desde lookalike en bóveda Obsidian: {ve}")
                                    
                                    status.update(label="✅ Dossier Generado Exitosamente", state="complete")
                                    st.toast("El Dossier se ha guardado en la carpeta output / Obsidian.")
                                    st.rerun()
                                except Exception as e:
                                    logger.error(f"Error generando dossier desde Lookalike: {e}")
                                    st.error(f"Error crítico: {e}")

    # 3. Base de Datos Histórica y Cambio de Status
    st.divider()
    st.markdown("### 📂 Repositorio Histórico de Prospectos (Supabase)")
    
    col_filters, col_table = st.columns([1, 3])
    
    with col_filters:
        st.markdown("**Filtros de Base de Datos**")
        db_vector = st.selectbox("Filtrar por origen (Vector)", ["Todos", "Lookalike Directo", "Competitor Intercept"])
        db_status = st.selectbox("Filtrar por estado (Status)", ["Todos", "nuevo", "contactado", "descartado"])
        db_min_score = st.slider("Mínimo Score de Fit", 0, 100, 40)
        
        vector_val = None
        if db_vector == "Lookalike Directo":
            vector_val = "direct"
        elif db_vector == "Competitor Intercept":
            vector_val = "competitor"
            
        status_val = None if db_status == "Todos" else db_status

    with col_table:
        try:
            db_prospects = icp_store.get_prospects(vector=vector_val, status=status_val, min_score=db_min_score, limit=50)
            
            if not db_prospects:
                st.info("No se encontraron prospectos históricos con los filtros seleccionados.")
            else:
                hist_data = []
                for p in db_prospects:
                    sen = p.get("senales", {})
                    hist_data.append({
                        "ID": p.get("id"),
                        "Empresa": p.get("empresa"),
                        "Fit Score": p.get("score"),
                        "Vector": "Lookalike Directo" if p.get("vector") == "direct" else "Competitor Intercept",
                        "Origen / Fuente": p.get("source"),
                        "Decisor": p.get("decision_maker"),
                        "Estado": p.get("status"),
                        "Razón Fit": sen.get("razon", "")
                    })
                
                df_hist = pd.DataFrame(hist_data)
                st.dataframe(df_hist, use_container_width=True, hide_index=True)
                
                # Modificación de estado inline
                st.markdown("**Actualizar Estado de Prospecto**")
                col_update1, col_update2 = st.columns(2)
                with col_update1:
                    to_update_company = st.selectbox("Selecciona empresa para actualizar:", options=df_hist["Empresa"].tolist(), key="db_update_company")
                with col_update2:
                    new_status = st.selectbox("Nuevo Estado:", options=["nuevo", "contactado", "descartado"], key="db_update_status")
                    
                if st.button("Actualizar Estado en Supabase 💾", use_container_width=True):
                    row_to_update = next((p for p in db_prospects if p["empresa"] == to_update_company), None)
                    if row_to_update:
                        res = icp_store.update_status(row_to_update["id"], new_status)
                        if res:
                            st.success(f"¡Estado de {to_update_company} cambiado a '{new_status}' exitosamente!")
                            st.rerun()
                        else:
                            st.error("Error al actualizar estado en Supabase.")
        except Exception as e:
            st.error(f"Error consultando base de datos histórica: {e}")
