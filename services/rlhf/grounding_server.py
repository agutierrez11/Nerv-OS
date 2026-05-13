from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

app = FastAPI(title="Nerv-OS Grounding Reward Server")

# Cargar modelo NLI (Natural Language Inference) para verificar "Hallucinations"
# Usamos DeBERTa-v3-large ya que es el estándar de la industria para NLI fáctico
MODEL_NAME = "microsoft/deberta-v3-large-mnli"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

class RewardRequest(BaseModel):
    query: str
    response: str
    context: str  # Los datos reales de OSINT/JSON

@app.post("/reward")
async def calculate_reward(request: RewardRequest):
    """
    Calcula una recompensa basada en la veracidad (Grounding).
    Este endpoint es llamado por OpenRLHF durante el entrenamiento o inferencia.
    """
    # 1. Separar la respuesta en afirmaciones (sentences)
    sentences = [s.strip() for s in request.response.split('.') if len(s.strip()) > 10]
    
    total_score = 0
    verification_details = []

    for sentence in sentences:
        # 2. Formatear para NLI: [Premisa: Contexto] [Hipótesis: Afirmación del Agente]
        inputs = tokenizer(request.context, sentence, return_tensors="pt", truncation=True, max_length=512)
        
        with torch.no_grad():
            logits = model(**inputs).logits
            
        # DeBERTa MNLI labels: 0: entailment, 1: neutral, 2: contradiction
        probs = torch.softmax(logits, dim=1)
        entailment_prob = probs[0][0].item()
        neutral_prob = probs[0][1].item()
        contradiction_prob = probs[0][2].item()

        # Lógica de Recompensa:
        if entailment_prob > 0.7:
            sentence_score = 1.0  # Dato verificado
            status = "Verified"
        elif contradiction_prob > 0.5:
            sentence_score = -5.0  # ¡ALUCINACIÓN/ERROR!
            status = "Contradiction"
        else:
            sentence_score = -1.0  # Dato no rastreable (Invento probable)
            status = "Unverifiable"
        
        total_score += sentence_score
        verification_details.append({
            "sentence": sentence,
            "score": sentence_score,
            "status": status,
            "probs": {"E": entailment_prob, "N": neutral_prob, "C": contradiction_prob}
        })

    # Normalizar score por número de afirmaciones
    final_reward = total_score / max(len(sentences), 1)
    
    return {
        "reward": final_reward,
        "details": verification_details
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
