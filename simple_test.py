import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Cargar variables de entorno
load_dotenv()

def test_simple():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ API Key no encontrada")
        return
    
    print("✅ API Key encontrada")
    
    # Crear LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        openai_api_key=api_key
    )
    
    # Prompt simple
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Analiza el CV y responde SOLO con un JSON válido: {\"name\": \"Nombre\", \"email\": \"email@ejemplo.com\"}"),
        ("human", "CV: CARLOS RODRÍGUEZ\nEmail: juan2645@gmail.com\nTeléfono: +54 11 5555-1234")
    ])
    
    try:
        messages = prompt.format_messages()
        response = llm.invoke(messages)
        print("🔍 Respuesta:")
        print(response.content)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simple()
