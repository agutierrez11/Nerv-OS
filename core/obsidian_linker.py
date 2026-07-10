import os
import re
from pathlib import Path

# Static list of common fintech and enterprise sales concepts to link automatically
COMMON_CONCEPTS = {
    "CFO": "CFO",
    "COO": "COO",
    "CEO": "CEO",
    "SPEI": "SPEI",
    "Toku": "Toku",
    "reconciliación": "Conciliación",
    "reconciliaciones": "Conciliación",
    "conciliación": "Conciliación",
    "conciliaciones": "Conciliación",
    "cobro recurrente": "Cobro Recurrente",
    "cobros recurrentes": "Cobro Recurrente",
    "recurrencia": "Cobro Recurrente",
    "suscripciones": "Suscripciones",
    "suscripción": "Suscripciones",
    "pasarela de pagos": "Pasarela de Pagos",
    "pasarelas de pago": "Pasarela de Pagos",
    "adquirente": "Adquirente",
    "adquirentes": "Adquirente",
    "fraude": "Prevención de Fraude",
    "phishing": "Phishing",
    "contracargos": "Contracargos",
    "contracargo": "Contracargos",
    "tasa de aceptación": "Tasa de Aceptación",
    "reembolsos": "Reembolsos",
    "reembolso": "Reembolsos",
    "cartera vencida": "Cartera Vencida",
    "México": "México",
    "Brasil": "Brasil",
    "Colombia": "Colombia",
    "Chile": "Chile",
    "Perú": "Perú",
    "Argentina": "Argentina",
    # Payment Gateways (Pasarelas de Pago)
    "PayPal": "PayPal",
    "PayU": "PayU",
    "Stripe": "Stripe",
    "Mercado Pago": "Mercado Pago",
    "Mercadopago": "Mercado Pago",
    "Adyen": "Adyen",
    "dLocal": "dLocal",
    "Kushki": "Kushki",
    "Conekta": "Conekta",
    "Openpay": "Openpay",
    "Webpay": "Webpay",
    # E-commerce & Tech Platforms
    "Salesforce Commerce Cloud": "Salesforce Commerce Cloud",
    "Salesforce": "Salesforce",
    "VTEX": "VTEX",
    "Shopify": "Shopify",
    "Magento": "Magento",
    "WooCommerce": "WooCommerce",
    "Wappalyzer": "Wappalyzer"
}

def link_text_safe(text, term, target_note):
    """
    Safely replaces occurrences of 'term' with a wikilink to 'target_note',
    ignoring segments that are already inside [[...]], [...](...), or <...>.
    """
    if not term or not text:
        return text
        
    # Split text by markdown links, wikilinks, and HTML tags
    pattern = r'(\[\[[^\]]*\]\]|\[[^\]]*\]\([^\)]*\)|<[^>]*>)'
    segments = re.split(pattern, text)
    
    # Compile whole word pattern for the search term
    # Match term case-insensitively with boundary assertions
    term_pat = re.compile(r'(?<!\w)(' + re.escape(term) + r')(?!\w)', re.IGNORECASE)
    
    for i in range(len(segments)):
        # Even indices represent normal plain text (not links or HTML tags)
        if i % 2 == 0:
            def replace_fn(match):
                matched_text = match.group(1)
                # Normalize the matched text to see if it matches target_note case-insensitively
                # If they are essentially the same word, link as [[Target]]
                # Otherwise, link as [[Target|MatchedText]] to keep original casing/conjugation
                norm_matched = matched_text.strip().replace('_', ' ').lower()
                norm_target = target_note.replace('_', ' ').lower()
                if norm_matched == norm_target:
                    return f"[[{target_note}]]"
                else:
                    return f"[[{target_note}|{matched_text}]]"
            segments[i] = term_pat.sub(replace_fn, segments[i])
            
    return "".join(segments)

def link_dossier(dossier_text, vault_path):
    """
    Scans the Obsidian vault to identify existing company notes, builds a dynamic
    search-term map, and links companies and common concepts in the dossier text.
    """
    if not dossier_text:
        return dossier_text
        
    vault_dir = Path(vault_path)
    if not vault_dir.exists():
        # If vault doesn't exist, just link the static common concepts
        result = dossier_text
        for concept, target in COMMON_CONCEPTS.items():
            result = link_text_safe(result, concept, target)
        return result
        
    # Build dynamic map of existing company notes
    company_links = {}
    
    for item in vault_dir.glob("*.md"):
        filename = item.stem  # e.g., "Adidas_Mexico_Reporte" or "Estafeta_Simulacion"
        
        # Add the full note title as a search term
        company_links[filename.replace('_', ' ')] = filename
        company_links[filename] = filename
        
        # Try to extract the base company name
        # e.g., "Adidas_Mexico_Reporte" -> "Adidas Mexico"
        # "Estafeta_Simulacion" -> "Estafeta"
        base_name = filename
        if base_name.endswith("_Reporte"):
            base_name = base_name[:-8]
        elif base_name.endswith("_Simulacion"):
            base_name = base_name[:-11]
            
        clean_base = base_name.replace('_', ' ')
        company_links[clean_base] = filename
        
        # If it has location words, add the very core word as well
        # e.g., "UPS México" -> "UPS"
        core_words = clean_base.split()
        if len(core_words) > 1:
            core_name = core_words[0]
            # Avoid single-character or overly generic words
            if len(core_name) > 2 and core_name.lower() not in ["del", "los", "las", "san"]:
                # If it's not already mapped to a shorter file, map it
                if core_name not in company_links:
                    company_links[core_name] = filename

    # Perform linking:
    # 1. Link companies (sort terms by length descending to match longer phrases first, e.g., "UPS México" before "UPS")
    sorted_companies = sorted(company_links.keys(), key=len, reverse=True)
    
    result = dossier_text
    for term in sorted_companies:
        target_note = company_links[term]
        result = link_text_safe(result, term, target_note)
        
    # 2. Link common concepts
    sorted_concepts = sorted(COMMON_CONCEPTS.keys(), key=len, reverse=True)
    for concept in sorted_concepts:
        target_note = COMMON_CONCEPTS[concept]
        result = link_text_safe(result, concept, target_note)
        
    return result

if __name__ == "__main__":
    # Small local test
    test_text = "Estafeta es competidor de UPS México y de Luuna en México. El CFO de Luuna quiere automatizar la conciliación de cobros recurrentes de SPEI con Toku."
    print("Original:\n", test_text)
    
    # Simulate a vault path
    fake_vault = "./fake_vault"
    os.makedirs(fake_vault, exist_ok=True)
    Path(fake_vault + "/Estafeta_Reporte.md").write_text("# Estafeta")
    Path(fake_vault + "/UPS_México_Reporte.md").write_text("# UPS México")
    Path(fake_vault + "/Luuna_Simulacion.md").write_text("# Luuna")
    
    linked = link_dossier(test_text, fake_vault)
    print("\nLinked:\n", linked)
    
    # Cleanup fake vault
    import shutil
    shutil.rmtree(fake_vault)
