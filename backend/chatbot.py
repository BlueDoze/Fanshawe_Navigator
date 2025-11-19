import google.generativeai as genai
import os
import re
import json
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

class ChatbotNavegacao:
    def __init__(self):
        # Configurar Google Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.use_ai = True
            print("✅ Google Gemini AI ativado")
        except Exception as e:
            print(f"⚠️ Erro ao configurar Gemini: {e}")
            print("📝 Usando modo regex simples.")
            self.model = None
            self.use_ai = False
        
        # Prompt para Gemini
        self.system_prompt = """Você é um assistente de navegação do campus Fanshawe College.
Sua tarefa é identificar a ORIGEM e o DESTINO que o usuário menciona.

Prédios disponíveis: A, B, C, D, E, F, G, H, J, K, M, SC (Student Centre), T

Extraia apenas as informações:
- origem: letra do prédio onde o usuário está (ou null)
- destino: letra do prédio para onde o usuário quer ir (ou null)

Responda APENAS no formato JSON:
{"origem": "A", "destino": "M", "resposta": "mensagem amigável"}

Se não conseguir identificar origem ou destino, retorne null para esses campos."""
    
    def processar_mensagem(self, mensagem: str) -> dict:
        """Processa mensagem e extrai intenção de navegação"""
        
        if self.use_ai and self.model:
            try:
                # Usar Gemini para processar
                prompt = f"{self.system_prompt}\n\nUsuário: {mensagem}"
                response = self.model.generate_content(prompt)
                resposta_texto = response.text
                
                # Extrair JSON da resposta
                json_match = re.search(r'\{.*\}', resposta_texto, re.DOTALL)
                if json_match:
                    dados = json.loads(json_match.group())
                    return {
                        "origem": dados.get("origem"),
                        "destino": dados.get("destino"),
                        "resposta": dados.get("resposta", "Entendi sua solicitação!")
                    }
            except Exception as e:
                print(f"Erro ao usar LangChain: {e}")
                # Fallback para regex
        
        # Modo fallback: usar regex simples
        return self._processar_com_regex(mensagem)
    
    def _processar_com_regex(self, mensagem: str) -> dict:
        """Fallback usando regex para extrair origem e destino"""
        msg = mensagem.lower()
        
        # Dicionário de prédios
        predios_validos = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'j', 'k', 'm', 'sc', 't']
        
        origem = None
        destino = None
        
        # Padrão 1: "estou no/na [predio] X" (captura apenas letras de prédios válidos)
        match_origem = re.search(r'(?:estou|tô|to)\s+(?:no|na|em)\s+(?:predio|prédio|building)?\s*([a-z]{1,2})\b', msg)
        if match_origem:
            candidato = match_origem.group(1).lower()
            if candidato in predios_validos:
                origem = candidato.upper()
        
        # Padrão 2: "quero ir no/na/para [predio] X"
        match_destino = re.search(r'(?:ir|quero ir|vou|chegar)\s+(?:no|na|para|ao|à|em)\s+(?:predio|prédio|building)?\s*([a-z]{1,2})\b', msg)
        if match_destino:
            candidato = match_destino.group(1).lower()
            if candidato in predios_validos:
                destino = candidato.upper()
        
        # Padrão 3: "de X para/ate Y" (formato direto)
        match_direto = re.search(r'\b([a-z]{1,2})\s+(?:para|ate|até)\s+(?:o\s+)?([a-z]{1,2})\b', msg)
        if match_direto:
            cand_origem = match_direto.group(1).lower()
            cand_destino = match_direto.group(2).lower()
            if cand_origem in predios_validos:
                origem = cand_origem.upper()
            if cand_destino in predios_validos:
                destino = cand_destino.upper()
        
        # Padrão 4: Procurar letras isoladas com palavras-chave de contexto
        # "estou no A" ou "ir para o B"
        if not origem:
            match_origem_simples = re.search(r'(?:estou|tô)\s+(?:no|na|em)\s+([a-z]{1,2})\b', msg)
            if match_origem_simples:
                candidato = match_origem_simples.group(1).lower()
                if candidato in predios_validos:
                    origem = candidato.upper()
        
        if not destino:
            match_destino_simples = re.search(r'(?:ir|vou)\s+(?:no|na|para|pro|pra)\s+([a-z]{1,2})\b', msg)
            if match_destino_simples:
                candidato = match_destino_simples.group(1).lower()
                if candidato in predios_validos:
                    destino = candidato.upper()
        
        resposta = "Como posso ajudá-lo com a navegação?"
        if origem and destino:
            resposta = f"Entendi! Você está no prédio {origem} e quer ir para o prédio {destino}. Vou calcular a rota!"
        elif destino:
            resposta = f"Você quer ir para o prédio {destino}. De onde você está partindo?"
        elif origem:
            resposta = f"Você está no prédio {origem}. Para onde deseja ir?"
        
        return {
            "origem": origem,
            "destino": destino,
            "resposta": resposta
        }

# Instância global do chatbot
chatbot = ChatbotNavegacao()
