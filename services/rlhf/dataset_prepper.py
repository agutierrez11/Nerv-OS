import json
import os
import glob
from typing import List

def convert_memory_to_rlhf_dataset(memory_dir: str, output_file: str):
    """
    Convierte los logs de feedback de Nerv-OS en un dataset de preferencias para OpenRLHF.
    Formato esperado: (Prompt + Contexto, Chosen (Corregido), Rejected (Original Alucinado))
    """
    rlhf_data = []
    
    # Buscar todos los archivos JSON en la carpeta memory
    json_files = glob.glob(os.path.join(memory_dir, "*.json"))
    
    print(f"Encontrados {len(json_files)} archivos de memoria...")

    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                
                # Buscamos entradas que tengan 'original_response' y 'corrected_response' (Human Feedback)
                # O entradas que tengan objeciones marcadas.
                if isinstance(data, list):
                    for entry in data:
                        if 'human_feedback' in entry and entry['human_feedback']:
                            rlhf_data.append({
                                "prompt": entry.get('original_query', ''),
                                "context": entry.get('source_data', ''),
                                "chosen": entry.get('corrected_response', ''),
                                "rejected": entry.get('original_response', '')
                            })
                elif isinstance(data, dict):
                    # Formato específico si es un solo objeto
                    if 'rejected' in data and 'chosen' in data:
                        rlhf_data.append(data)
            except Exception as e:
                print(f"Error procesando {file_path}: {e}")

    # Guardar en formato JSONL para OpenRLHF
    with open(output_file, 'w', encoding='utf-8') as out:
        for item in rlhf_data:
            out.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    print(f"Dataset generado con {len(rlhf_data)} ejemplos en {output_file}")

if __name__ == "__main__":
    MEMORY_PATH = "c:/Users/Antonio/.gemini/antigravity/scratch/Toku_GTM_Radar/memory"
    OUTPUT_PATH = "c:/Users/Antonio/.gemini/antigravity/scratch/Toku_GTM_Radar/services/rlhf/preference_dataset.jsonl"
    
    # Crear carpeta si no existe
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    convert_memory_to_rlhf_dataset(MEMORY_PATH, OUTPUT_PATH)
