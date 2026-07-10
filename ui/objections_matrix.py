import streamlit as st
import json
import os
from pathlib import Path
from core.logger import logger

# --- BASE DE DATOS SEMILLA (ACADEMIC SEED) ---
# Objeciones comerciales y contra-argumentos (Battle Cards) enfocados en el ecosistema de pagos y Toku
SEEDED_OBJECTIONS = [
    {
        "objection": "Ya tenemos un contrato regional y las decisiones se toman en corporativo (fuera de México).",
        "prospect_role": "CFO",
        "industry": "Retail",
        "seller_role": "Account Executive (AE)",
        "context": "El cliente tiene un acuerdo global con procesadores como Adyen o Stripe y siente que no puede usar soluciones locales.",
        "battlecard": "Toku puede operar de manera complementaria sobre su pasarela de pagos actual. No requerimos que cancelen su acuerdo regional. Nos conectamos vía API para gestionar la lógica de cobros recurrentes y conciliación local en México, resolviendo el dolor operativo del equipo local sin interferir en los contratos globales.",
        "source": "Semilla"
    },
    {
        "objection": "Nuestra pasarela de pagos ya ofrece cobros con tarjeta y no vemos la necesidad de agregar otro proveedor.",
        "prospect_role": "CFO",
        "industry": "E-commerce",
        "seller_role": "SDR",
        "context": "El tomador de decisiones ve a Toku como 'otra pasarela de cobros' más y no entiende la diferencia con su procesador de adquirencia actual.",
        "battlecard": "Las pasarelas tradicionales cobran pero no gestionan la recurrencia inteligente ni la conciliación. Toku ofrece reintentos automáticos inteligentes basados en el emisor de la tarjeta, ruteo dinámico y enlaces de pago con recordatorios por WhatsApp. Aumentamos la tasa de recaudación hasta en un 5% adicional en comparación con cobros recurrentes tradicionales de pasarelas estándar.",
        "source": "Semilla"
    },
    {
        "objection": "Integrar otra plataforma de cobros requiere desarrollo de APIs y el equipo de IT está saturado con el ERP actual.",
        "prospect_role": "CTO / IT",
        "industry": "SaaS / Software",
        "seller_role": "Sales Engineer / Pre-Sales",
        "context": "El equipo técnico teme retrasar sus entregables clave por integrar otra API de pagos.",
        "battlecard": "Toku ofrece opciones de integración 'No-Code' (enlaces de pago autogenerados y portales de clientes preconstruidos) y soporte técnico dedicado en Slack para su equipo de desarrollo. La integración estándar de nuestra API se realiza en menos de dos semanas con documentación interactiva y SDKs listos en múltiples lenguajes.",
        "source": "Semilla"
    },
    {
        "objection": "La conciliación de pagos de SPEI y transferencias la hacemos manual y es costosa, pero no confiamos en automatizarla.",
        "prospect_role": "COO / Operaciones",
        "industry": "Venta por Catálogo / Direct Selling",
        "seller_role": "Key Account Manager (KAM)",
        "context": "El equipo de administración y finanzas teme que la automatización de conciliación falle y genere descuadres contables o falsos positivos.",
        "battlecard": "Toku genera CLABEs interbancarias personalizadas y únicas para cada cliente. Cuando el cliente paga vía SPEI, el sistema detecta de forma inmediata a quién corresponde el abono y concilia el 100% de las transacciones automáticamente en tiempo real. Reducimos el error humano a cero y liberamos al equipo administrativo de tareas repetitivas.",
        "source": "Semilla"
    },
    {
        "objection": "No queremos almacenar datos bancarios de los clientes por riesgo de hackeo o cumplimiento de normas de seguridad.",
        "prospect_role": "Legal / Compliance",
        "industry": "General",
        "seller_role": "Account Executive (AE)",
        "context": "El departamento legal busca evitar a toda costa la responsabilidad de almacenar datos de tarjetas de crédito o cuentas (PCI-DSS).",
        "battlecard": "Toku cuenta con certificación PCI-DSS Nivel 1. Los datos sensibles de pago nunca tocan los servidores del cliente; se tokenizan de manera segura en la infraestructura de Toku. Además, cumplimos estrictamente con la Ley de Protección de Datos Personales en Posesión de Particulares de México (LFPDPPP) y normativas de la CNBV.",
        "source": "Semilla"
    },
    {
        "objection": "Nuestros clientes son tradicionales y prefieren pagar en efectivo o en tiendas de conveniencia (OXXO), no por internet.",
        "prospect_role": "CFO",
        "industry": "Logística / Supply Chain",
        "seller_role": "Inside Sales",
        "context": "Clientes B2B o B2C con baja bancarización o preferencia de pago físico.",
        "battlecard": "Toku permite generar órdenes de pago con códigos de barra únicos que el cliente puede pagar en efectivo en miles de corresponsales físicos en México (como OXXO, 7-Eleven, etc.), manteniendo el pago conciliado automáticamente sin que el cliente tenga que usar tarjeta en línea.",
        "source": "Semilla"
    },
    {
        "objection": "La comisión por cobro recurrente es más alta que lo que nos cobra el banco directamente por domiciliación bancaria.",
        "prospect_role": "CFO",
        "industry": "Venta por Catálogo / Direct Selling",
        "seller_role": "Head of Sales / VP Sales",
        "context": "Comparación directa del costo transaccional con esquemas tradicionales de cobros bancarios (domiciliaciones).",
        "battlecard": "La domiciliación bancaria tradicional tiene una tasa de rechazo de hasta el 40% debido a problemas de comunicación o falta de fondos, sin reportar motivos de falla en tiempo real. Toku combina domiciliación, SPEI referenciado y tarjetas en un solo flujo, ofreciendo reintentos automáticos y notificaciones preventivas que reducen el rechazo en más de un 60%, lo que compensa con creces la comisión.",
        "source": "Semilla"
    },
    {
        "objection": "Ya tenemos implementado un portal de pagos propio en nuestro sitio web.",
        "prospect_role": "CTO / IT",
        "industry": "Retail",
        "seller_role": "BDR Manager",
        "context": "El equipo de ingeniería siente orgullo por el portal que construyeron y no quieren reemplazarlo por un tercero.",
        "battlecard": "No es necesario reemplazar su portal actual. Toku funciona en el 'back-end' como el motor de cobros recurrentes y comunicación. Pueden embeber nuestros flujos de pago mediante widgets o usar la API de forma transparente para el usuario final, manteniendo la marca de su empresa pero con la tecnología de reintentos e inteligencia de cobro de Toku.",
        "source": "Semilla"
    }
]

def load_dynamic_objections():
    """Lee objeciones del archivo objections_vault.jsonl del VPS y las devuelve estructuradas."""
    dynamic_list = []
    vault_file = Path("objections_vault.jsonl")
    if not vault_file.exists():
        return dynamic_list

    try:
        with open(vault_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    empresa = record.get("empresa_target", "Desconocida")
                    industry = record.get("user_industry", "General")
                    seller_role = record.get("user_role", "BDR")
                    
                    # 1. Extraer objeciones explícitas de la lista
                    objeciones_lista = record.get("objeciones_lista", [])
                    for obj in objeciones_lista:
                        if obj.strip():
                            dynamic_list.append({
                                "objection": obj.strip(),
                                "prospect_role": "General / Mixto",
                                "industry": industry,
                                "seller_role": seller_role,
                                "context": f"Objeción reportada en simulación real para la empresa {empresa}.",
                                "battlecard": "Analiza las características de esta empresa y usa el Plan de Ataque GTM en NERV Lab para estructurar tu respuesta de forma personalizada.",
                                "source": f"Real ({empresa})"
                            })
                            
                    # 2. Extraer objeciones asociadas a posturas del comité simulado
                    comite = record.get("comite_simulado", [])
                    for persona in comite:
                        stance = persona.get("stance", "")
                        role = persona.get("role", "Decisor")
                        if stance.strip() and len(stance) > 20: # Filtrar textos muy cortos
                            dynamic_list.append({
                                "objection": stance.strip(),
                                "prospect_role": role,
                                "industry": industry,
                                "seller_role": seller_role,
                                "context": f"Postura adoptada por {persona.get('name', 'Decisor')} en simulación para {empresa}.",
                                "battlecard": "Personaliza tu pitch enfocándote en aliviar este dolor específico de este perfil directivo.",
                                "source": f"Simulado ({empresa})"
                            })
                except Exception as je:
                    logger.debug(f"Error parseando línea de objections_vault.jsonl: {je}")
    except Exception as e:
        logger.error(f"Error leyendo objections_vault.jsonl: {e}")
        
    return dynamic_list

def render_objections_matrix_tab(user_active):
    st.markdown("""
        <div style='background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); padding: 20px; border-radius: 10px; margin-bottom: 25px;'>
            <h2 style='color: white; margin: 0;'>🎯 Matriz de Objeciones</h2>
            <p style='color: #d1d5db; margin: 5px 0 0 0;'>
                Consulta y filtra los principales obstáculos en la venta y cómo rebatirlos usando la propuesta de valor de Toku.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Cargar todas las objeciones (Semilla + Dinámicas)
    dynamic_objections = load_dynamic_objections()
    all_objections = SEEDED_OBJECTIONS + dynamic_objections

    # 2. Extraer opciones únicas para los filtros
    industrias_disponibles = sorted(list(set(o["industry"] for o in all_objections)))
    roles_prospecto_disponibles = sorted(list(set(o["prospect_role"] for o in all_objections)))
    roles_vendedor_disponibles = sorted(list(set(o["seller_role"] for o in all_objections)))
    sources_disponibles = sorted(list(set(o["source"].split(" (")[0] for o in all_objections)))

    # 3. Interfaz de Filtros
    st.subheader("🔍 Filtros de Búsqueda")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ind_filtro = st.multiselect(
            "Vertical o Industria del Prospecto", 
            options=industrias_disponibles,
            placeholder="Todas las industrias"
        )
    with col2:
        decisor_filtro = st.multiselect(
            "Rol del Prospecto (Decisor)", 
            options=roles_prospecto_disponibles,
            placeholder="Todos los roles directivos"
        )
    with col3:
        origen_filtro = st.multiselect(
            "Origen de la Objeción", 
            options=sources_disponibles,
            placeholder="Todos los orígenes"
        )

    # 4. Aplicar los filtros
    filtered_objections = []
    for o in all_objections:
        # Filtro de Industria
        if ind_filtro and o["industry"] not in ind_filtro:
            continue
        # Filtro de Rol del Prospecto
        if decisor_filtro and o["prospect_role"] not in decisor_filtro:
            continue
        # Filtro de Origen
        src_base = o["source"].split(" (")[0]
        if origen_filtro and src_base not in origen_filtro:
            continue
            
        filtered_objections.append(o)

    st.divider()

    # 5. Visualizar Resultados
    st.write(f"Se encontraron **{len(filtered_objections)}** objeciones que coinciden con tus filtros.")
    st.markdown("<br>", unsafe_allow_html=True)

    if not filtered_objections:
        st.info("No hay objeciones registradas para esta combinación de filtros. ¡Prueba a expandir tu búsqueda!")
        return

    # Renderizar cada objeción en una tarjeta
    for idx, o in enumerate(filtered_objections):
        source_color = "#3b82f6" if o["source"] == "Semilla" else ("#10b981" if "Real" in o["source"] else "#7c3aed")
        
        # HTML para los badges informativos
        badges_html = f"""
        <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px;">
            <span style="background: #1e293b; color: #f8fafc; font-size: 0.75em; padding: 3px 10px; border-radius: 12px; font-weight: bold;">🏢 Industria: {o['industry']}</span>
            <span style="background: #1e293b; color: #f8fafc; font-size: 0.75em; padding: 3px 10px; border-radius: 12px; font-weight: bold;">👤 Decisor: {o['prospect_role']}</span>
            <span style="background: #1e293b; color: #f8fafc; font-size: 0.75em; padding: 3px 10px; border-radius: 12px; font-weight: bold;">💼 Rol Comercial: {o['seller_role']}</span>
            <span style="background: {source_color}; color: white; font-size: 0.75em; padding: 3px 10px; border-radius: 12px; font-weight: bold;">📍 Origen: {o['source']}</span>
        </div>
        """
        
        with st.container():
            st.markdown(f"""
            <div style="background: #ffffff; border-left: 6px solid #1e3a8a; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06); margin-bottom: 20px;">
                <h4 style="color: #1e3a8a; margin-top: 0; margin-bottom: 10px; font-size: 1.15em;">⚠️ Objeción: "{o['objection']}"</h4>
                {badges_html}
                <p style="color: #475569; font-size: 0.9em; line-height: 1.5; margin-bottom: 15px;"><b>Contexto y Dolor:</b> {o['context']}</p>
                <div style="background: #f1f5f9; padding: 15px; border-radius: 6px; border: 1px solid #cbd5e1;">
                    <b style="color: #0f172a; font-size: 0.95em;">🛡️ Contra-argumento (Battle Card):</b>
                    <p style="color: #1e293b; font-size: 0.9em; line-height: 1.5; margin: 5px 0 0 0;">{o['battlecard']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
