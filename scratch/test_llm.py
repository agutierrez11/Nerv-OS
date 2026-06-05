import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

def test_groq():
    api_key = os.getenv("GROQ_API_KEY")
    print(f"API Key exists: {bool(api_key)}")
    if api_key:
        print(f"API Key starts with: {api_key[:10]}...")
        
    try:
        llm = ChatGroq(
            temperature=0.1,
            model_name="llama-3.3-70b-versatile",
            api_key=api_key
        )
        print("Invoking Groq LLM...")
        resp = llm.invoke("Hola, responde con la palabra 'OK'")
        print(f"Response: {resp.content}")
    except Exception as e:
        print(f"ERROR calling Groq: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_groq()
