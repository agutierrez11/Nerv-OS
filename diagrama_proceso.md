# Proceso de Generación de Dossier NERV OS (Flujo 1x1 con Toku)

Este diagrama ilustra exactamente qué ocurre en las entrañas del sistema (motor `crew.py` con DeepSeek) en los 2 minutos que transcurren desde que haces clic en "Generar" hasta que obtienes el dossier final.

```mermaid
graph TD
    %% Estilos de los nodos
    classDef user fill:#2d3436,stroke:#00cec9,stroke-width:2px,color:white;
    classDef core fill:#0984e3,stroke:#74b9ff,stroke-width:2px,color:white;
    classDef api fill:#6c5ce7,stroke:#a29bfe,stroke-width:2px,color:white;
    classDef agent fill:#e84393,stroke:#fd79a8,stroke-width:2px,color:white;
    classDef auditor fill:#d63031,stroke:#ff7675,stroke-width:2px,color:white;
    classDef success fill:#00b894,stroke:#55efc4,stroke-width:2px,color:white;

    %% Flujo Inicial
    A[Usuario: Ingresa 'Empresa' en Streamlit] :::user --> B(Auto-Descubrimiento de URL Oficial) :::core
    
    %% Ingesta de Datos y Web Scraping
    B -->|Busca en Google| C{¿Tiene Web?} :::api
    C -->|Sí| D[Web Scraper: Extrae texto de la Home y Subpáginas] :::api
    C -->|No| E[Búsqueda en Noticias y LinkedIn] :::api
    D --> F[Consolidación de Contexto de la Empresa] :::core
    E --> F
    
    %% Inyección del Cerebro Toku
    F --> G{¿Es el Vendedor 'Toku'?} :::core
    G -->|Sí| H[Carga de Inteligencia Toku] :::core
    
    subgraph El Cerebro Toku
        H --> I1[Asigna Presentación de Vertical Ej. Retail/Educación]
        H --> I2[Inyecta Toku_Global_KB.md Ej. Productos y Casos de uso]
    end
    
    I1 --> J
    I2 --> J
    
    G -->|No| K[Carga Descripción Genérica Agnóstica] :::core
    K --> J[Contexto Base Preparado] :::core
    
    %% Enjambre de Agentes (DeepSeek)
    J --> L[INICIO DEL ENJAMBRE DE AGENTES - DeepSeek] :::agent
    
    subgraph NERV Crew - Razonamiento Profundo
        L --> M1[1. Investigador: Rastrea Finanzas, Competidores y Noticias]
        M1 --> M2[2. Psicólogo: Crea Gemelos Digitales y perfiles DISC]
        M2 --> M3[3. Estratega: Cruza dolores de la empresa con los productos Toku]
        M3 --> M4[4. Prospector: Extrae correos exactos vía Prospeo/LinkedIn]
    end
    
    %% Auditoría
    M4 --> N[Auditor de Calidad] :::auditor
    N -->|Evalúa contra la verdad| O{¿Cumple el Estándar?} :::auditor
    
    O -->|Alucinaciones / Falso| P[Marca como RECHAZADO o exije reescritura] :::auditor
    O -->|Datos reales y estratégicos| Q[Marca como APROBADO] :::success
    
    %% Entrega Final
    Q --> R[Se muestra Dossier Markdown en Streamlit] :::user
```

### Explicación de Etapas Críticas

1. **Auto-Descubrimiento y Scraping:** El sistema no asume nada. Lo primero que hace es leer la página oficial del prospecto para entender a qué se dedica hoy, no hace un año.
2. **El Cerebro Toku:** Aquí entra en juego la actualización que acabamos de subir. El motor identifica en qué industria opera el prospecto e inyecta la presentación específica (Ej. *Bienes de Consumo*), además del catálogo *Global* completo, obligando al sistema a pensar como un vendedor experto de Toku.
3. **Razonamiento DeepSeek:** En lugar de lanzar una respuesta de un solo golpe, los 4 agentes se pasan la información como en una cadena de montaje. El psicólogo no trabaja hasta que el investigador termina.
4. **Auditoría Final:** El paso que te garantiza no perder el tiempo. DeepSeek verifica que no haya inventado datos antes de mostrarte la pantalla final.
