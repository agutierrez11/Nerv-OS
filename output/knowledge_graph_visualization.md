# 🧠 Grafo de Conocimiento: Memoria NERV OS

Este es el esquema visual de cómo la arquitectura NERV implementa Retrieval-Augmented Generation (RAG) usando su `index.json` local.

```mermaid
graph TD
    %% Definición de Nodos Centrales (Sectores)
    SECTOR[Sector: Ecommerce]:::sectorNode

    %% Entidades Previas Analizadas (Memoria)
    N1(Nike)
    N2(Under Armour)
    
    %% Tácticas Aplicadas y Scores
    T1[Táctica: Recurrencia]
    T2[Táctica: Orquestación Plug&Play]
    
    S1((Score: 65%)):::lowScore
    S2((Score: 82%)):::highScore

    %% Conexiones de Memoria Pasada
    SECTOR -->|Pertenece a| N1
    SECTOR -->|Pertenece a| N2
    
    N1 -.->|Pitch Estratégico| T1
    N2 -.->|Pitch Estratégico| T2
    
    T1 -.->|MiroFish Alignment Scorer| S1
    T2 -.->|MiroFish Alignment Scorer| S2

    %% Nuevo Objetivo (Inyección de Prompt)
    NEW_TARGET{Nuevo Prospecto:\nADIDAS}:::targetNode
    AGENT_INV[Agente Investigador]:::agentNode
    
    NEW_TARGET -->|1. Sector Detectado| SECTOR
    SECTOR ==>|2. RAG Retrieval| AGENT_INV
    
    AGENT_INV ==>|3. Inyección de Prompt\n'Usa la táctica de mayor éxito'| S2
    S2 ==>|4. Aprendizaje| T2
    
    %% Output
    T2 ===>|5. Nueva Estrategia Optimizada| NEW_TARGET

    %% Estilos
    classDef sectorNode fill:#2d3436,stroke:#74b9ff,stroke-width:2px,color:#fff;
    classDef targetNode fill:#d63031,stroke:#ff7675,stroke-width:4px,color:#fff;
    classDef agentNode fill:#6c5ce7,stroke:#a29bfe,stroke-width:2px,color:#fff;
    classDef lowScore fill:#fdcb6e,color:#2d3436;
    classDef highScore fill:#00b894,color:#fff;
```

### Explicación del Flujo de RAG (Para los Data Scientists):
1. **Detección**: Cuando metes a `Adidas` en el batch, el sistema detecta que es del nodo `Sector: Ecommerce`.
2. **Retrieval (Extracción)**: El Agente Investigador consulta el `index.json` filtrando por ese nodo. Descubre que ya existen `Nike` y `Under Armour` en ese clúster.
3. **Análisis de Consenso Pasado**: Observa que la táctica de "Recurrencia" con Nike solo tuvo un **65%** de éxito, pero la táctica de "Orquestación Plug&Play" con Under Armour tuvo un **82%** (MiroFish Score).
4. **Prompt Injection**: El Investigador se inyecta esta premisa en su Prompt antes de hablar con el Gemelo Digital: *"En nuestro histórico, el ángulo de Plug&Play convierte mejor en este sector. Prioriza esa narrativa."*
5. **Evolución**: El nuevo dossier de Adidas nace siendo estadísticamente superior al de Nike porque heredó la memoria colectiva del enjambre.
