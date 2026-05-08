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

---

## 5. Architectural Roadmap (In Progress)

Para alinear el desarrollo con las mejores prácticas de Data Engineering y Machine Learning, NERV OS se rige por las siguientes premisas estructurales:

### 5.1. Feedback Loop Activo (Memoria RAG)
**Estado:** `Implementado en feature/nerv-upgrade-rag`
No realizamos *fine-tuning* (modificación de pesos). En su lugar, aplicamos **In-Context Learning**. Se guardan las objeciones reales de los comerciales en `memory/feedback_loop/objections_library.json` y se inyectan dinámicamente en el prompt del agente. El sistema "aprende" sin el costo computacional de re-entrenar un LLM, permitiendo trazabilidad total y eliminando el entrenamiento de "caja negra".

### 5.2. Capa de Validación de Datos (Pydantic)
**Estado:** `En Roadmap (src/toku_radar/validators/)`
La entrada del sistema será blindada usando esquemas de validación estrictos con `Pydantic`. Si los datos de entrada carecen de URL, Sector o contexto válido, la ejecución se aborta. Esto evita el efecto GIGO (Garbage In, Garbage Out) y reduce llamadas inútiles a la API.

### 5.3. Orquestación de "Agentes de Control" (Galileo Logic)
**Estado:** `En Roadmap (agents.yaml)`
Migración de la lógica de auditoría hacia un agente independiente ("The Auditor"). Su misión será recibir el dossier final, validarlo contra los datos crudos y, si detecta una alucinación (ej. inventar métricas), **rechazar la generación y disparar una re-evaluación automática**.

### 5.4. Abstracción de Modelos y Enrutamiento (GroqRotator Avanzado)
**Estado:** `En Roadmap (groq_rotator.py)`
Implementación de lógica de ruteo inteligente de LLMs:
- `Llama-3.3-70B`: Exclusivo para simulación de agentes complejos (Estratega, Psicólogo).
- `Llama-3.1-8B`: Tareas deterministas y ligeras (Formateo Markdown, Resumen Crudo).
Optimización de costos y latencia sin sacrificar la calidad del resultado final.
