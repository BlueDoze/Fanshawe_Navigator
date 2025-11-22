from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import os
from grafo_predios import GrafoPredios
from chatbot import chatbot

app = FastAPI(title="Campus Guide API")

# CORS configuration to allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static images
if os.path.exists("dados/imagens"):
    app.mount("/imagens", StaticFiles(directory="dados/imagens"), name="imagens")

# Serve SVG files
if os.path.exists("dados/svg"):
    app.mount("/svg", StaticFiles(directory="dados/svg"), name="svg")

# Load map data
def carregar_mapas():
    try:
        with open("dados/mapas.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"campus": {"nome": "Campus", "predios": []}}

# Load GeoJSON
def carregar_geojson():
    try:
        with open("dados/campus.geojson", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"type": "FeatureCollection", "features": []}

MAPAS_DATA = carregar_mapas()
GEOJSON_DATA = carregar_geojson()

# Load building graph
def carregar_grafo_predios():
    try:
        grafo = GrafoPredios()
        grafo.carregar_geojson("dados/campus.geojson")
        grafo.criar_conexoes_automaticas(distancia_maxima=250.0)
        return grafo
    except Exception as e:
        print(f"Error loading graph: {e}")
        return None

GRAFO_PREDIOS = carregar_grafo_predios()

MAPAS_DATA = carregar_mapas()

# Data models
class PerguntaChat(BaseModel):
    mensagem: str
    contexto: dict = {}

class BuscaLocal(BaseModel):
    termo: str

class RotaPrediosRequest(BaseModel):
    origem: str  # Ex: "A", "Building A"
    destino: str  # Ex: "M", "Building M"

# ==================== API ROUTES ====================

@app.get("/")
def index():
    return {
        "mensagem": "Campus Guide API running!",
        "endpoints": {
            "mapas": "/api/mapas",
            "predios": "/api/predios",
            "buscar": "/api/buscar",
            "chat": "/api/chat",
            "rota": "/api/rota"
        }
    }

@app.get("/api/mapas")
def obter_mapas():
    """Returns all map data"""
    return MAPAS_DATA

@app.get("/api/geojson")
def obter_geojson():
    """Returns building GeoJSON data"""
    return GEOJSON_DATA

@app.get("/api/predios")
def listar_predios():
    """Lists all available buildings"""
    predios = []
    for predio in MAPAS_DATA["campus"]["predios"]:
        predios.append({
            "id": predio["id"],
            "nome": predio["nome"],
            "imagem_url": f"/imagens/{os.path.basename(predio['imagem'])}",
            "total_locais": len(predio["locais"])
        })
    return {"predios": predios}

@app.get("/api/predios/{predio_id}")
def obter_predio(predio_id: str):
    """Returns details of a specific building"""
    for predio in MAPAS_DATA["campus"]["predios"]:
        if predio["id"] == predio_id:
            # Return with formatted image_url
            predio_response = predio.copy()
            predio_response["imagem_url"] = f"/imagens/{os.path.basename(predio['imagem'])}"
            
            # Add SVG URL if it exists
            svg_path = f"dados/svg/{predio['nome']}.svg"
            if os.path.exists(svg_path):
                predio_response["svg_url"] = f"/svg/{predio['nome']}.svg"
            
            return predio_response
    raise HTTPException(status_code=404, detail="Building not found")

@app.post("/api/buscar")
def buscar_local(busca: BuscaLocal):
    """Search locations by name or description"""
    termo = busca.termo.lower()
    resultados = []
    
    for predio in MAPAS_DATA["campus"]["predios"]:
        for local in predio["locais"]:
            if (termo in local["nome"].lower() or 
                termo in local.get("descricao", "").lower()):
                resultados.append({
                    "predio": predio["nome"],
                    "predio_id": predio["id"],
                    "local": local["nome"],
                    "local_id": local["id"],
                    "tipo": local["tipo"],
                    "coordenadas": local["coordenadas"]
                })
    
    return {"resultados": resultados, "total": len(resultados)}

def formatar_info_predio(info):
    """Format building information in bullet points"""
    linhas = []
    
    # Title
    linhas.append(f"📍 {info['nome']}")
    linhas.append("")
    
    # Description
    linhas.append(f"• {info['descricao']}")
    linhas.append("")
    
    # Floors
    if info.get('andares'):
        andares_str = ', '.join(map(str, info['andares']))
        linhas.append(f"• 🏢 Floors: {andares_str}")
        linhas.append("")
    
    # Facilities
    if info.get('facilidades'):
        linhas.append("• ✨ Available facilities:")
        for fac in info['facilidades']:
            linhas.append(f"  - {fac}")
        linhas.append("")
    
    # Main rooms
    if info.get('salas_principais') and len(info['salas_principais']) > 0:
        linhas.append("• 🚪 Main rooms:")
        for sala in info['salas_principais']:
            linhas.append(f"  - {sala['numero']}: {sala['tipo']} (Floor {sala['andar']})")
        linhas.append("")
    
    # Operating hours
    if info.get('horario_funcionamento'):
        linhas.append(f"• 🕐 Operating hours:")
        linhas.append(f"  - {info['horario_funcionamento']}")
    
    return '\n'.join(linhas)

@app.post("/api/chat")
def chat_endpoint(pergunta: PerguntaChat):
    """
    Chatbot endpoint - processes questions and returns responses using Gemini
    """
    mensagem = pergunta.mensagem
    
    # Use enhanced chatbot with Gemini
    resultado = chatbot.processar_mensagem(mensagem)
    
    # If it's a building information request
    if resultado.get("tipo") == "info_predio":
        predio_ref = resultado.get("predio_ref")
        
        # Search for building information
        import json
        import os
        
        caminho_info = os.path.join(os.path.dirname(__file__), "dados", "predios_info.json")
        
        try:
            with open(caminho_info, 'r', encoding='utf-8') as f:
                predios_info = json.load(f)
            
            if predio_ref in predios_info:
                info = predios_info[predio_ref]
                
                # Format response in bullet points
                texto = formatar_info_predio(info)
                
                return {
                    "resposta": texto,
                    "tipo": "info_predio",
                    "predio_ref": predio_ref,
                    "info_completa": info
                }
            else:
                return {
                    "resposta": f"Sorry, I don't have detailed information about building {predio_ref} at the moment. You can ask me about the location or routes to this building.",
                    "tipo": "info_predio",
                    "predio_ref": predio_ref
                }
        except Exception as e:
            print(f"Error loading building information: {e}")
            return {
                "resposta": f"An error occurred while fetching information for building {predio_ref}. Please try again.",
                "tipo": "erro"
            }
    
    # Normal navigation response
    return {
        "resposta": resultado["resposta"],
        "origem": resultado.get("origem"),
        "destino": resultado.get("destino"),
        "acao": "navegar" if resultado.get("origem") and resultado.get("destino") else None
    }

def processar_pergunta_chatbot(mensagem: str):
    """
    Process user questions in a simple way
    TODO: Integrate with OpenAI or Google Gemini for better responses
    """
    
    # Greetings
    if any(palavra in mensagem for palavra in ["oi", "olá", "ola", "hello", "hi"]):
        return {
            "resposta": "Hello! I'm the Campus Guide assistant. How can I help you find a location?",
            "acao": None
        }
    
    # Search for "where is" or "how do I get to"
    if "onde fica" in mensagem or "onde é" in mensagem or "como chego" in mensagem or "where is" in mensagem or "how do I get" in mensagem:
        # Try to extract the mentioned location
        resultados = buscar_em_texto(mensagem)
        
        if resultados:
            local = resultados[0]
            return {
                "resposta": f"I found {local['local']} in {local['predio']}. I'll highlight it on the map for you!",
                "acao": "mostrar_no_mapa",
                "dados": local
            }
        else:
            return {
                "resposta": "I couldn't find that location. Can you give me more details? For example: 'Where is room 101?'",
                "acao": None
            }
    
    # List of buildings
    if "prédios" in mensagem or "predios" in mensagem or "quais prédios" in mensagem or "buildings" in mensagem or "which buildings" in mensagem:
        predios = [p["nome"] for p in MAPAS_DATA["campus"]["predios"]]
        return {
            "resposta": f"We have {len(predios)} buildings on campus: {', '.join(predios)}",
            "acao": None
        }
    
    # Help
    if "ajuda" in mensagem or "help" in mensagem:
        return {
            "resposta": """I can help you find locations on campus! 
            
Example questions:
• "Where is room 101?"
• "How do I get to the chemistry lab?"
• "Which buildings exist?"
• "Where is the library?"

Ask me anything about campus locations!""",
            "acao": None
        }
    
    # Resposta padrão
    return {
        "resposta": "Não entendi bem. Tente perguntar algo como 'Onde fica a sala 101?' ou 'Como chego ao laboratório?'",
        "acao": None,
        "sugestoes": ["Onde fica a entrada principal?", "Quais prédios existem?"]
    }

def buscar_em_texto(texto: str):
    """Busca menções a locais no texto"""
    resultados = []
    
    for predio in MAPAS_DATA["campus"]["predios"]:
        for local in predio["locais"]:
            # Busca pelo nome do local ou número de sala
            nome_local = local["nome"].lower()
            if nome_local in texto:
                resultados.append({
                    "predio": predio["nome"],
                    "predio_id": predio["id"],
                    "local": local["nome"],
                    "local_id": local["id"],
                    "coordenadas": local["coordenadas"]
                })
    
    return resultados

import math
from typing import List, Dict, Tuple

@app.post("/api/rota")
def calcular_rota(origem: dict, destino: dict):
    """
    Calcula rota entre dois pontos usando algoritmo A*
    Origem e destino devem ter: predio_id, local_id, coordenadas
    """
    try:
        predio_origem_id = origem.get("predio_id")
        predio_destino_id = destino.get("predio_id")
        
        if predio_origem_id == predio_destino_id:
            # Mesmo prédio - usar A*
            caminho = calcular_rota_a_star(origem, destino, predio_origem_id)
        else:
            # Prédios diferentes - ir para entrada mais próxima, depois para destino
            caminho = calcular_rota_entre_predios(origem, destino)
        
        if not caminho:
            return {"sucesso": False, "erro": "Não foi possível calcular rota"}
        
        distancia = calcular_distancia_caminho(caminho)
        
        return {
            "sucesso": True,
            "caminho": caminho,
            "distancia_estimada": f"{distancia:.0f} metros",
            "tempo_estimado": calcular_tempo_estimado(distancia),
            "passo_a_passo": gerar_instrucoes_rota(caminho)
        }
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}

def calcular_distancia_euclidiana(p1: Dict, p2: Dict) -> float:
    """Calcula distância euclidiana entre dois pontos"""
    x1, y1 = p1.get("x", 0), p1.get("y", 0)
    x2, y2 = p2.get("x", 0), p2.get("y", 0)
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def calcular_rota_a_star(origem: dict, destino: dict, predio_id: str) -> List[Dict]:
    """
    Implementa algoritmo A* para pathfinding dentro de um prédio
    """
    # Buscar prédio
    predio = None
    for p in MAPAS_DATA["campus"]["predios"]:
        if p["id"] == predio_id:
            predio = p
            break
    
    if not predio:
        return []
    
    origem_coords = origem.get("coordenadas", {})
    destino_coords = destino.get("coordenadas", {})
    
    # Se origem e destino são muito próximos, retorna linha reta
    distancia_direta = calcular_distancia_euclidiana(origem_coords, destino_coords)
    if distancia_direta < 50:
        return [origem_coords, destino_coords]
    
    # Criar nó de origem e destino
    caminho = [origem_coords]
    
    # Adicionar locais intermediários próximos para criar um caminho mais realista
    todos_locais = [local["coordenadas"] for local in predio["locais"]]
    
    # Encontrar locais intermediários relevantes
    intermediarios = []
    for local_coords in todos_locais:
        if local_coords == origem_coords or local_coords == destino_coords:
            continue
        
        dist_da_origem = calcular_distancia_euclidiana(origem_coords, local_coords)
        dist_para_destino = calcular_distancia_euclidiana(local_coords, destino_coords)
        
        # Verificar se o local está "no caminho"
        distancia_direta_total = calcular_distancia_euclidiana(origem_coords, destino_coords)
        desvio = (dist_da_origem + dist_para_destino) - distancia_direta_total
        
        if desvio < distancia_direta_total * 0.5:  # Se desvio é menos que 50%
            intermediarios.append({
                "coords": local_coords,
                "ordem": dist_da_origem
            })
    
    # Ordenar intermediários pela distância da origem
    intermediarios.sort(key=lambda x: x["ordem"])
    
    # Construir caminho
    for inter in intermediarios:
        caminho.append(inter["coords"])
    
    caminho.append(destino_coords)
    
    return caminho

def calcular_rota_entre_predios(origem: dict, destino: dict) -> List[Dict]:
    """Calcula rota entre prédios diferentes"""
    predio_origem_id = origem.get("predio_id")
    predio_destino_id = destino.get("predio_id")
    
    # Caminho simples: origem -> ponto de saída -> ponto de entrada -> destino
    caminho = [origem.get("coordenadas")]
    caminho.append(destino.get("coordenadas"))
    
    return caminho
    
    # Encontrar os locais
    local_origem = None
    local_destino = None
    
    for local in predio["locais"]:
        if local["id"] == local_origem_id:
            local_origem = local
        if local["id"] == local_destino_id:
            local_destino = local
    
    if not local_origem or not local_destino:
        raise Exception("Local não encontrado")
    
    # Retornar caminho com pontos intermediários para suavidade
    caminho = [
        {
            "predio_id": predio_id,
            "local_id": local_origem_id,
            "x": local_origem["coordenadas"]["x"],
            "y": local_origem["coordenadas"]["y"],
            "tipo": "origem",
            "descricao": local_origem["nome"]
        }
    ]
    
    # Adicionar ponto intermediário (25% e 75% do caminho)
    origem_x = local_origem["coordenadas"]["x"]
    origem_y = local_origem["coordenadas"]["y"]
    destino_x = local_destino["coordenadas"]["x"]
    destino_y = local_destino["coordenadas"]["y"]
    
    caminho.append({
        "predio_id": predio_id,
        "x": origem_x + (destino_x - origem_x) * 0.5,
        "y": origem_y + (destino_y - origem_y) * 0.5,
        "tipo": "intermediario",
        "descricao": "Ponto intermediário"
    })
    
    caminho.append({
        "predio_id": predio_id,
        "local_id": local_destino_id,
        "x": destino_x,
        "y": destino_y,
        "tipo": "destino",
        "descricao": local_destino["nome"]
    })
    
    return caminho

def calcular_rota_entre_predios(predio_origem_id: str, local_origem_id: str,
                                 predio_destino_id: str, local_destino_id: str):
    """Calcula rota entre prédios diferentes"""
    
    # Encontrar conexão entre prédios
    conexao = None
    for conn in MAPAS_DATA["campus"].get("conexões_entre_predios", []):
        if ((conn["de_predio"] == predio_origem_id and 
             conn["para_predio"] == predio_destino_id) or
            (conn["de_predio"] == predio_destino_id and 
             conn["para_predio"] == predio_origem_id)):
            conexao = conn
            break
    
    if not conexao:
        raise Exception("Nenhuma rota encontrada entre esses prédios")
    
    # Determinar direção da conexão
    if conexao["de_predio"] == predio_origem_id:
        entrada_origem = conexao["de_local"]
        entrada_destino = conexao["para_local"]
    else:
        entrada_origem = conexao["para_local"]
        entrada_destino = conexao["de_local"]
    
    # Construir caminho completo
    caminho = []
    
    # 1. Rota dentro do prédio de origem até a entrada
    rota_origem = calcular_rota_mesmo_predio(predio_origem_id, local_origem_id, entrada_origem)
    caminho.extend(rota_origem[:-1])  # Excluir último ponto (será repetido)
    
    # 2. Transição entre prédios
    local_entrada_origem = None
    for local in MAPAS_DATA["campus"]["predios"]:
        if local["id"] == predio_origem_id:
            for l in local["locais"]:
                if l["id"] == entrada_origem:
                    local_entrada_origem = l
                    break
    
    local_entrada_destino = None
    for local in MAPAS_DATA["campus"]["predios"]:
        if local["id"] == predio_destino_id:
            for l in local["locais"]:
                if l["id"] == entrada_destino:
                    local_entrada_destino = l
                    break
    
    if local_entrada_origem:
        caminho.append({
            "predio_id": predio_origem_id,
            "x": local_entrada_origem["coordenadas"]["x"],
            "y": local_entrada_origem["coordenadas"]["y"],
            "tipo": "saida",
            "descricao": f"Saída: {local_entrada_origem['nome']}"
        })
    
    if local_entrada_destino:
        caminho.append({
            "predio_id": predio_destino_id,
            "x": local_entrada_destino["coordenadas"]["x"],
            "y": local_entrada_destino["coordenadas"]["y"],
            "tipo": "entrada",
            "descricao": f"Entrada: {local_entrada_destino['nome']}"
        })
    
    # 3. Rota dentro do prédio de destino
    rota_destino = calcular_rota_mesmo_predio(predio_destino_id, entrada_destino, local_destino_id)
    caminho.extend(rota_destino[1:])  # Excluir primeiro ponto (já adicionado)
    
    return caminho

def calcular_distancia_caminho(caminho: list) -> float:
    """Calcula distância total do caminho em metros"""
    distancia = 0
    for i in range(len(caminho) - 1):
        p1 = caminho[i]
        p2 = caminho[i + 1]
        
        x1 = p1.get("x", 0) if isinstance(p1, dict) else p1.get("x", 0)
        y1 = p1.get("y", 0) if isinstance(p1, dict) else p1.get("y", 0)
        x2 = p2.get("x", 0) if isinstance(p2, dict) else p2.get("x", 0)
        y2 = p2.get("y", 0) if isinstance(p2, dict) else p2.get("y", 0)
        
        dx = x2 - x1
        dy = y2 - y1
        
        distancia += (dx**2 + dy**2)**0.5 * 0.1
    
    return distancia

def calcular_tempo_estimado(distancia_metros: float) -> str:
    """Calcula tempo estimado em minutos (velocidade média: 1.4 m/s)"""
    velocidade_ms = 1.4
    tempo_segundos = distancia_metros / velocidade_ms
    tempo_minutos = tempo_segundos / 60
    
    if tempo_minutos < 1:
        return f"{int(tempo_segundos)} segundos"
    else:
        return f"{int(tempo_minutos)} minutos"

def gerar_instrucoes_rota(caminho: list) -> list:
    """Gera instruções passo a passo do caminho"""
    if len(caminho) < 2:
        return ["Origem e destino são o mesmo local"]
    
    instrucoes = ["Iniciando navegação..."]
    
    for i in range(len(caminho)):
        if i == 0:
            instrucoes.append(f"Comece em: ({caminho[i].get('x', 0):.0f}, {caminho[i].get('y', 0):.0f})")
        elif i == len(caminho) - 1:
            instrucoes.append(f"Fim: ({caminho[i].get('x', 0):.0f}, {caminho[i].get('y', 0):.0f})")
        else:
            instrucoes.append(f"Prossiga para: ({caminho[i].get('x', 0):.0f}, {caminho[i].get('y', 0):.0f})")
    
    return instrucoes

# ==================== NOVA ROTA: GET LOCAIS ====================

@app.post("/api/rota-predios")
def calcular_rota_entre_predios_api(request: RotaPrediosRequest):
    """
    Calcula rota de navegação entre dois prédios do campus
    
    Exemplo de uso:
    POST /api/rota-predios
    {
        "origem": "A",
        "destino": "M"
    }
    
    Retorna o caminho com coordenadas geográficas para desenhar no mapa
    """
    if not GRAFO_PREDIOS:
        raise HTTPException(status_code=500, detail="Grafo de prédios não carregado")
    
    try:
        rota = GRAFO_PREDIOS.calcular_rota(request.origem, request.destino)
        
        if not rota:
            raise HTTPException(
                status_code=404, 
                detail=f"Nenhuma rota encontrada entre {request.origem} e {request.destino}"
            )
        
        return {
            "sucesso": True,
            "rota": rota,
            "instrucoes": [
                f"Você está no {rota['origem']['nome']}",
                *[f"Siga para o {p['nome']}" for p in rota['caminho'][1:-1]],
                f"Chegue ao {rota['destino']['nome']}"
            ],
            "tempo_estimado": calcular_tempo_estimado(rota['distancia_metros'])
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/predios-disponiveis")
def listar_predios_disponiveis():
    """
    Lista todos os prédios disponíveis para navegação
    """
    if not GRAFO_PREDIOS:
        return {"predios": []}
    
    predios_lista = [
        {
            "id": info["id"],
            "nome": info["nome"],
            "ref": info["ref"],
            "coords": info["centroide"]
        }
        for info in GRAFO_PREDIOS.predios.values()
    ]
    
    return {
        "total": len(predios_lista),
        "predios": sorted(predios_lista, key=lambda x: x["ref"])
    }

@app.get("/api/predios/{predio_ref}/info")
def obter_info_predio(predio_ref: str):
    """
    Retorna informações detalhadas de um prédio específico
    """
    import json
    import os
    
    # Carregar informações dos prédios
    caminho_info = os.path.join(os.path.dirname(__file__), "dados", "predios_info.json")
    
    try:
        with open(caminho_info, 'r', encoding='utf-8') as f:
            predios_info = json.load(f)
        
        predio_ref_upper = predio_ref.upper()
        
        if predio_ref_upper in predios_info:
            info = predios_info[predio_ref_upper]
            
            # Formatar resposta em bullet points
            texto = formatar_info_predio(info)
            
            return {
                "ref": predio_ref_upper,
                "info": info,
                "texto_formatado": texto
            }
        else:
            return {
                "ref": predio_ref_upper,
                "info": None,
                "texto_formatado": f"Informações do prédio {predio_ref_upper} não disponíveis no momento."
            }
    
    except FileNotFoundError:
        return {
            "ref": predio_ref.upper(),
            "info": None,
            "texto_formatado": "Base de dados de informações dos prédios não encontrada."
        }
    except Exception as e:
        return {
            "ref": predio_ref.upper(),
            "info": None,
            "texto_formatado": f"Erro ao carregar informações: {str(e)}"
        }

@app.get("/api/predios/{predio_id}/locais")
def listar_locais_predio(predio_id: str):
    """Lista todos os locais de um prédio específico"""
    for predio in MAPAS_DATA["campus"]["predios"]:
        if predio["id"] == predio_id:
            return {
                "predio_id": predio_id,
                "predio_nome": predio["nome"],
                "locais": predio["locais"]
            }
    raise HTTPException(status_code=404, detail="Prédio não encontrado")

# Executar com: uvicorn api:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)