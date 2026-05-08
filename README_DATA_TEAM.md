# 🧠 NERV OS: Toku GTM Radar - Technical Documentation
**Target Audience:** Data Engineering & Data Science Teams
**Version:** 2.0 (Swarm Intelligence & Consensus Architecture)

---

## 1. Executive Summary
El proyecto **Toku GTM Radar** es una herramienta de prospección automatizada B2B. A diferencia de los wrappers tradicionales de LLMs, NERV OS implementa una **Arquitectura de Enjambre (Swarm Architecture)**. Utiliza agentes especializados que operan bajo un paradigma de "Role-Playing Adversarial" y resolución por consenso.

## 2. Swarm Architecture (Multi-Agent System)
El sistema instancia 6 entidades distintas impulsadas por `Llama-3.3-70B-Versatile` (via Groq API para inferencia ultra-rápida y cost-efficient):

### 🛠️ Capa Táctica (Ejecución)
1. **Investigador Forense:** Responsable de OSINT. Extrae datos crudos de la web y noticias recientes usando herramientas de búsqueda y scraping (`Serper API`, `Firecrawl`).
2. **Psicólogo de Ventas:** Emulador de la API de Crystal. Infiriendo a partir de perfiles de LinkedIn, clasifica a los decisores bajo la matriz DISC y extrae su influencia (Favikon).
3. **Estratega GTM:** Sintetiza el dolor operativo en un ángulo de ventas (Schwerpunkt).

### ⚔️ Capa Adversarial (Self-Correction)
4. **Gemelo Digital (Digital Twin):** Asume la personalidad DISC del decisor detectado. Su *System Prompt* le ordena ser escéptico y criticar el pitch del Estratega, forzando un bucle de auto-corrección antes de la generación del output.

### ⚖️ Capa de Consenso (Observancia y Calidad)
5. **MiroFish (Heuristic Scorer):** Evalúa semánticamente el debate de los agentes y calcula un **Puntaje de Alineación (Alignment Score)** basado en el encaje entre el dolor financiero de la empresa y la propuesta de valor de Toku. No es un modelo predictivo tradicional, sino una función de evaluación por consenso.
6. **Galileo (Auditor de Verdad):** Realiza un *Cross-Reference* con Temperature=0.0 entre el dossier final y la data cruda original. Genera un **Hallucination Score (0-10)** para garantizar el *grounding* de la información.

---

## 3. Persistent Memory (RAG Paradigm)
El sistema no es "Stateless". Implementa un motor incipiente de **Memoria Colectiva** (`TokuMemory`):
- **Almacenamiento Local:** Indexado en `memory/index.json`.
- **Estructura:** Grafos de conocimiento en formato JSON que almacenan el resumen de la táctica y la empresa.
- **Retrieval:** Antes de iniciar la investigación de una nueva empresa, el sistema consulta el `index.json` filtrando por el mismo `sector`. Esto permite inyectar contexto histórico en el prompt, logrando que el LLM reutilice ángulos de venta que fueron exitosos en empresas similares, optimizando el uso de tokens y mejorando el *Success Rate* progresivamente.

---

## 4. Verification & Reproducibility
Para la auditoría del equipo de Data, todos los artefactos se persisten localmente para validación humana:
*   **Resultados Finales:** `output/*.md` (Dossier limpio para el comercial).
*   **Razonamiento y Prompts (Trace Logs):** `output/trace_*.md` (Registro detallado de los *tool calls*, debates y justificaciones de consenso).
*   **Batch Engine:** `batch.py` permite la ejecución asíncrona de listas de empresas en formato CSV respetando rate-limits.

---
*Propietario de la Arquitectura: Antonio (NERV / Toku Project)*
