import google.generativeai as genai
import os
import re
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ChatbotNavegacao:
    def __init__(self):
        # Configure Google Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.use_ai = True
            print("✅ Google Gemini AI activated")
        except Exception as e:
            print(f"⚠️ Error configuring Gemini: {e}")
            print("📝 Using simple regex mode.")
            self.model = None
            self.use_ai = False
        
        # Prompt for Gemini
        self.system_prompt = """You are a navigation assistant for Fanshawe College campus.
Your task is to identify the ORIGIN and DESTINATION that the user mentions.

Available buildings: A, B, C, D, E, F, G, H, J, K, M, SC (Student Centre), T

Extract only the information:
- origem: letter of the building where the user is (or null)
- destino: letter of the building where the user wants to go (or null)

Respond ONLY in JSON format:
{"origem": "A", "destino": "M", "resposta": "friendly message"}

If you can't identify origin or destination, return null for those fields."""
    
    def processar_mensagem(self, mensagem: str) -> dict:
        """Process message and extract navigation intent"""
        
        print(f"🔍 Processing message: {mensagem}")
        
        # First check if it's a question about building information
        info_predio = self._verificar_info_predio(mensagem)
        if info_predio:
            print(f"✓ Detected building information request: {info_predio}")
            return info_predio
        
        if self.use_ai and self.model:
            try:
                # Use Gemini to process
                prompt = f"{self.system_prompt}\n\nUser: {mensagem}"
                response = self.model.generate_content(prompt)
                resposta_texto = response.text
                
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', resposta_texto, re.DOTALL)
                if json_match:
                    dados = json.loads(json_match.group())
                    return {
                        "origem": dados.get("origem"),
                        "destino": dados.get("destino"),
                        "resposta": dados.get("resposta", "I understood your request!")
                    }
            except Exception as e:
                print(f"Error using Gemini: {e}")
                # Fallback to regex
        
        # Fallback mode: use simple regex
        print("📝 Using simple regex mode")
        return self._processar_com_regex(mensagem)
    
    def _verificar_info_predio(self, mensagem: str) -> dict:
        """Verifica se usuário está perguntando sobre informações de um prédio"""
        msg = mensagem.lower()
        
        # Padrões de pergunta sobre prédio - mais flexíveis
        padroes_info = [
            r'(?:o que|que|quais)\s+(?:tem|há|existe|existem)\s+(?:no|na)\s+(?:predio|prédio|building)?\s*([a-z]{1,2})\b',
            r'(?:info|informa[çc][õo]es?|sobre|fale sobre|me fale|fale)\s+(?:do|da|sobre|o)?\s*(?:predio|prédio|building)\s*([a-z]{1,2})\b',
            r'(?:predio|prédio|building)\s*([a-z]{1,2})\s+(?:tem|possui|oferece|o que tem)',
            r'(?:me mostre|mostre|exiba)\s+(?:info|informações|dados)?\s*(?:do|da|sobre|o)?\s*(?:predio|prédio|building)?\s*([a-z]{1,2})\b',
        ]
        
        predios_validos = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'j', 'k', 'm', 'sc', 't']
        
        for padrao in padroes_info:
            match = re.search(padrao, msg)
            if match:
                predio_ref = match.group(1).lower()
                if predio_ref in predios_validos:
                    print(f"✓ Detectada pergunta sobre prédio {predio_ref.upper()}")
                    return {
                        "tipo": "info_predio",
                        "predio_ref": predio_ref.upper(),
                        "resposta": f"Buscando informações sobre o prédio {predio_ref.upper()}..."
                    }
        
        return None
    
    def _processar_com_regex(self, mensagem: str) -> dict:
        """Fallback using regex to extract origin and destination"""
        msg = mensagem.lower()
        
        # Dictionary of buildings
        predios_validos = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'j', 'k', 'm', 'sc', 't']
        
        origem = None
        destino = None
        
        # Pattern 1: "I am at/in [building] X" (captures only valid building letters)
        match_origem = re.search(r'(?:estou|tô|to|i am|i\'m at|at)\s+(?:no|na|em|in|at)?\s+(?:predio|prédio|building)?\s*([a-z]{1,2})\b', msg)
        if match_origem:
            candidato = match_origem.group(1).lower()
            if candidato in predios_validos:
                origem = candidato.upper()
        
        # Pattern 2: "I want to go to/to [building] X"
        match_destino = re.search(r'(?:ir|quero ir|vou|chegar|go|going|want to go|get to)\s+(?:no|na|para|ao|à|em|to)?\s+(?:predio|prédio|building)?\s*([a-z]{1,2})\b', msg)
        if match_destino:
            candidato = match_destino.group(1).lower()
            if candidato in predios_validos:
                destino = candidato.upper()
        
        # Pattern 3: "from X to Y" (direct format)
        match_direto = re.search(r'\b([a-z]{1,2})\s+(?:para|ate|até|to)\s+(?:o\s+)?([a-z]{1,2})\b', msg)
        if match_direto:
            cand_origem = match_direto.group(1).lower()
            cand_destino = match_direto.group(2).lower()
            if cand_origem in predios_validos:
                origem = cand_origem.upper()
            if cand_destino in predios_validos:
                destino = cand_destino.upper()
        
        # Pattern 4: Look for isolated letters with context keywords
        # "I am at A" or "go to B"
        if not origem:
            match_origem_simples = re.search(r'(?:estou|tô|i am|i\'m|at)\s+(?:no|na|em|at)?\s+([a-z]{1,2})\b', msg)
            if match_origem_simples:
                candidato = match_origem_simples.group(1).lower()
                if candidato in predios_validos:
                    origem = candidato.upper()
        
        if not destino:
            match_destino_simples = re.search(r'(?:ir|vou|go|going to)\s+(?:no|na|para|pro|pra|to)?\s+([a-z]{1,2})\b', msg)
            if match_destino_simples:
                candidato = match_destino_simples.group(1).lower()
                if candidato in predios_validos:
                    destino = candidato.upper()
        
        resposta = "How can I help you with navigation?"
        if origem and destino:
            resposta = f"✅ Done! Showing the path from building {origem} to building {destino} on the map."
        elif destino:
            resposta = f"📍 Destination: building {destino}. Which building are you leaving from?"
        elif origem:
            resposta = f"📍 Origin: building {origem}. Which building would you like to go to?"
        
        return {
            "origem": origem,
            "destino": destino,
            "resposta": resposta
        }

# Global chatbot instance
chatbot = ChatbotNavegacao()
