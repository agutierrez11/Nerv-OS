# Nerv-OS: Sistema de Alineación Fáctica (RLHF/GRPO)

Este módulo implementa una capa de **Reinforcement Learning from Human Feedback (RLHF)** diseñada para eliminar alucinaciones en los reportes de ventas y garantizar que cada descubrimiento presentado sea 100% rastreable a los datos de origen.

## 🛠 Arquitectura para el Data Engineer

El sistema utiliza **OpenRLHF** sobre una arquitectura distribuida (Ray) para optimizar el modelo no por "estilo", sino por "veracidad".

1.  **Ingesta de Datos (`dataset_prepper.py`):** Convierte los logs de interacción y correcciones humanas en `memory/` a un dataset de preferencias.
    *   **Chosen:** Respuesta corregida por el experto en ventas.
    *   **Rejected:** Respuesta original del LLM con posibles alucinaciones.
2.  **Servidor de Recompensas (`grounding_server.py`):**
    *   Expone un endpoint `/reward` que utiliza un modelo de **NLI (Natural Language Inference)**.
    *   Calcula matemáticamente si una afirmación se deriva lógicamente del contexto OSINT.
    *   Penaliza con un score negativo pesado (-5.0) cualquier contradicción detectada.

## 📊 Métricas para el Data Scientist

Para validar el éxito del entrenamiento, nos enfocaremos en estas métricas:

*   **Hallucination Rate (HR):** Porcentaje de oraciones clasificadas como "Neutral" o "Contradiction" por el modelo NLI.
*   **Grounding Density:** Ratio de afirmaciones verificadas por token generado.
*   **GRPO Divergence:** Control de que el modelo no pierda su capacidad de razonamiento mientras se alinea con los datos fácticos.

## 🚀 Cómo ejecutarlo

1.  **Instalar dependencias:**
    ```bash
    pip install fastapi uvicorn transformers torch
    ```
2.  **Iniciar el Servidor de Verificación:**
    ```bash
    python grounding_server.py
    ```
3.  **Configurar OpenRLHF:**
    Al lanzar el entrenamiento de PPO/GRPO en OpenRLHF, utiliza el flag de recompensa remota apuntando a este servidor:
    ```bash
    --reward_model_path http://localhost:8001/reward
    ```

## Hallazgos Clave
- El uso de **GRPO** permite que el modelo "razone" antes de contestar (CoT), lo que reduce las alucinaciones por "presión de respuesta".
- La integración de **NLI como recompensa** es más robusta que el simple RAG, ya que mide la relación semántica de verdad, no solo la similitud de palabras.
