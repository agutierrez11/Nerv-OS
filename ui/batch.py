import streamlit as st
import re
from pathlib import Path
from core.batch_processor import run_parallel_tasks
from src.toku_radar.crew import NervCrew
from core.logger import logger

def render_batch_tab(companies_data, output_dir, user_active=None):
    st.subheader("// Procesamiento Masivo Paralelizado")

    total = len(companies_data)
    existing_files = list(output_dir.glob("*.md"))
    existing_names = [f.stem for f in existing_files]
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total", total)
    with col2: st.metric("Generados", len(existing_files))
    with col3: st.metric("Pendientes", total - len(existing_files))

    st.divider()

    # Identificar pendientes
    pending = []
    for row in companies_data:
        safe = re.sub(r'[^\w\-]', '_', row['empresa']).strip('_')
        if safe not in existing_names:
            pending.append(row)

    if not pending:
        st.success("Todos los dossiers han sido generados.")
    else:
        st.info(f"Hay {len(pending)} empresas pendientes de analisis.")
        workers = st.slider("Numero de hilos paralelos (Workers)", 1, 10, 3)
        
        if st.button("LANZAR ENJAMBRE PARALELO (NERV 2.0)", use_container_width=True):
            if not user_active:
                st.error("⚠️ Identificación requerida: Por favor, selecciona tu perfil o regístrate en el panel lateral antes de lanzar el proceso masivo.")
                return

            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Definir las tareas
            def create_task(row):
                def task():
                    try:
                        vendedor_url = user_active.get("vendedor_url", "https://toku.com") if user_active else "https://toku.com"
                        crew = NervCrew(
                            empresa=row["empresa"], 
                            sector=row["sector"], 
                            pitch=row["pitch_principal"],
                            vendedor=vendedor_url,
                            url_cliente=row.get("url", ""),
                            prior_knowledge=row.get("contexto", "")
                        )
                        res = crew.kickoff()
                        # Guardar resultado
                        safe = re.sub(r'[^\w\-]', '_', row['empresa']).strip('_')
                        (output_dir / f"{safe}.md").write_text(res, encoding="utf-8")
                        return f"Success: {row['empresa']}"
                    except Exception as e:
                        logger.error(f"Error procesando {row['empresa']} en batch: {e}")
                        return f"Error: {row['empresa']} -> {e}"
                return task

            tasks = [create_task(row) for row in pending]
            
            # Ejecutar en paralelo
            results = run_parallel_tasks(tasks, max_workers=workers)
            
            st.success("Proceso batch finalizado.")
            st.rerun()

    st.divider()
    
    # Botón para exportar a Word en lotes
    if st.button("📁 CONVERTIR DOSSIERS GENERADOS A WORD (.docx)", use_container_width=True):
        existing_mds = list(output_dir.glob("*.md"))
        if not existing_mds:
            st.error("⚠️ No hay dossiers generados en la caché local para convertir. Por favor, ejecuta primero el análisis batch.")
        else:
            with st.status("📝 Convirtiendo dossiers a documentos Word...", expanded=True) as status:
                from core.docx_exporter import convert_dossier_to_docx
                converted_files = []
                for md_file in existing_mds:
                    try:
                        docx_path = convert_dossier_to_docx(md_file, "/home/antonio/Desktop/Correos_Prospeccion")
                        converted_files.append(docx_path)
                    except Exception as e:
                        logger.error(f"Error convirtiendo {md_file.name} a docx: {e}")
                        st.warning(f"No se pudo convertir {md_file.name}: {e}")
                status.update(label=f"✅ ¡Conversión Completada! Se generaron {len(converted_files)} archivos de Word en el Escritorio del VPS (`/home/antonio/Desktop/Correos_Prospeccion/`).", state="complete")

    st.divider()
    # Listado de empresas con visualización inline y descarga
    for row in companies_data:
        safe = re.sub(r'[^\w\-]', '_', row['empresa']).strip('_')
        exists = (output_dir / f"{safe}.md").exists()
        status = "✅" if exists else "⏳"
        
        if exists:
            content = (output_dir / f"{safe}.md").read_text(encoding="utf-8")
            with st.expander(f"{status} **{row['empresa']}** ({row['sector']})"):
                st.markdown(content)
                st.download_button(
                    "📩 Descargar Dossier",
                    content,
                    file_name=f"{safe}.md",
                    mime="text/markdown",
                    key=f"batch_dl_{safe}",
                    use_container_width=True
                )
        else:
            st.write(f"{status} **{row['empresa']}** ({row['sector']}) — *Pendiente de generar*")
