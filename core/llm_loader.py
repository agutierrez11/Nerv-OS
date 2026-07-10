import os
from dotenv import load_dotenv

load_dotenv()

def get_llm(temperature=0.2):
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    
    if provider == "ollama":
        model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        print(f"[LLM LOADER] Initializing local Ollama ChatOpenAI client with model: {model_name}...")
        
        # We can use ChatOpenAI because Ollama exposes a standard OpenAI compatible API on /v1
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            base_url=base_url,
            temperature=temperature,
            api_key="ollama" # dummy key
        )
    else:
        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        api_key = os.getenv("GROQ_API_KEY")
        print(f"[LLM LOADER] Initializing cloud ChatGroq client with model: {model_name}...")
        
        from langchain_groq import ChatGroq
        return ChatGroq(
            temperature=temperature,
            model_name=model_name,
            api_key=api_key
        )
