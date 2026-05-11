import streamlit as st
import re
from pathlib import Path
from core.batch_processor import run_parallel_tasks
from src.toku_radar.crew import TokuCrew
from core.logger import logger

def render_batch_tab(companies_data, output_dir):
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
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Definir las tareas
            def create_task(row):
                def task():
                    try:
                        crew = TokuCrew(row["empresa"], row["sector"], row["pitch_principal"])
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
    # Listado de empresas con descarga
    for row in companies_data:
        safe = re.sub(r'[^\w\-]', '_', row['empresa']).strip('_')
        exists = (output_dir / f"{safe}.md").exists()
        status = "✅" if exists else "⏳"
        col_a, col_b = st.columns([0.9, 0.1])
        col_a.write(f"{status} **{row['empresa']}** ({row['sector']})")
        if exists:
            content = (output_dir / f"{safe}.md").read_text(encoding="utf-8")
            col_b.download_button("⬇️", content, file_name=f"{safe}.md", key=f"batch_dl_{safe}")
