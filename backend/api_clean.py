from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import os
import math
from typing import List, Dict, Tuple

app = FastAPI(title="Campus Guide API")

# Configuração CORS para permitir frontend acessar o backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir imagens estáticas
if os.path.exists("dados/imagens"):
    app.mount("/imagens", StaticFiles(directory="dados/imagens"), name="imagens")

# Carregar dados dos mapas
def carregar_mapas():
    try:
        with open("dados/mapas.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"campus": {"nome": "Campus", "predios": []}}

MAPAS_DATA = carregar_mapas()

# Modelos de dados
class PerguntaChat(BaseModel):
    mensagem: str
    contexto: dict = {}

class BuscaLocal(BaseModel):
    termo: str

class PontoRota(BaseModel):
    predio_id: str
    local_id: str = None
    coordenadas: dict

# ==================== ROTAS DA API ====================

@app.get("/")
def index():
    return {
        "mensagem": "Campus Guide API funcionando!",
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
    """Retorna todos os dados dos mapas"""
    return MAPAS_DATA

@app.get("/api/predios")
def listar_predios():
    """Lista todos os prédios disponíveis"""
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
    """Retorna detalhes de um prédio específico com URL de imagem formatada"""
    for predio in MAPAS_DATA["campus"]["predios"]:
        if predio["id"] == predio_id:
            predio_response = predio.copy()
            predio_response["imagem_url"] = f"/imagens/{os.path.basename(predio['imagem'])}"
            return predio_response
    raise HTTPException(status_code=404, detail="Prédio não encontrado")

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

@app.post("/api/buscar")
def buscar_local(busca: BuscaLocal):
    """Busca locais por nome ou descrição"""
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

@app.post("/api/chat")
def chat_endpoint(pergunta: PerguntaChat):
    """Endpoint do chatbot - processa perguntas e retorna respostas"""
    mensagem = pergunta.mensagem.lower()
    resposta = processar_pergunta_chatbot(mensagem)
    return resposta

def processar_pergunta_chatbot(mensagem: str):
    """Processa perguntas do usuário de forma simples"""
    
    # Saudações
    if any(palavra in mensagem for palavra in ["oi", "olá", "ola", "hello"]):
        return {
            "resposta": "Olá! Sou o assistente do Campus Guide. Como posso te ajudar a encontrar um local?",
            "acao": None
        }
    
    # Busca por "onde fica" ou "como chego"
    if "onde fica" in mensagem or "onde é" in mensagem or "como chego" in mensagem:
        resultados = buscar_em_texto(mensagem)
        
        if resultados:
            local = resultados[0]
            return {
                "resposta": f"Encontrei {local['local']} no {local['predio']}. Vou destacar no mapa para você!",
                "acao": "mostrar_no_mapa",
                "dados": local
            }
        else:
            return {
                "resposta": "Não encontrei esse local. Pode me dar mais detalhes? Por exemplo: 'Onde fica a sala 101?'",
                "acao": None
            }
    
    # Lista de prédios
    if "prédios" in mensagem or "predios" in mensagem or "quais prédios" in mensagem:
        predios = [p["nome"] for p in MAPAS_DATA["campus"]["predios"]]
        return {
            "resposta": f"Temos {len(predios)} prédios no campus: {', '.join(predios)}",
            "acao": None
        }
    
    # Resposta padrão
    return {
        "resposta": "Não entendi bem. Tente perguntar algo como 'Onde fica a sala 101?' ou 'Como chego ao laboratório?'",
        "acao": None
    }

def buscar_em_texto(texto: str):
    """Busca menções a locais no texto"""
    resultados = []
    
    for predio in MAPAS_DATA["campus"]["predios"]:
        for local in predio["locais"]:
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

# ==================== FUNÇÕES DE PATHFINDING ====================

def calcular_distancia_euclidiana(p1: dict, p2: dict) -> float:
    """Calcula distância euclidiana entre dois pontos"""
    x1 = p1.get("x", 0)
    y1 = p1.get("y", 0)
    x2 = p2.get("x", 0)
    y2 = p2.get("y", 0)
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def calcular_rota_a_star(origem: dict, destino: dict, predio_id: str) -> List[dict]:
    """
    Calcula rota usando algoritmo A* dentro de um prédio
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
    
    # Se origem e destino são muito próximos
    distancia_direta = calcular_distancia_euclidiana(origem_coords, destino_coords)
    if distancia_direta < 50:
        return [origem_coords, destino_coords]
    
    # Criar caminho base
    caminho = [origem_coords]
    
    # Encontrar locais intermediários relevantes
    todos_locais = [local["coordenadas"] for local in predio["locais"]]
    intermediarios = []
    
    for local_coords in todos_locais:
        if local_coords == origem_coords or local_coords == destino_coords:
            continue
        
        dist_da_origem = calcular_distancia_euclidiana(origem_coords, local_coords)
        dist_para_destino = calcular_distancia_euclidiana(local_coords, destino_coords)
        distancia_direta_total = calcular_distancia_euclidiana(origem_coords, destino_coords)
        desvio = (dist_da_origem + dist_para_destino) - distancia_direta_total
        
        # Se o local está "no caminho"
        if desvio < distancia_direta_total * 0.5:
            intermediarios.append({
                "coords": local_coords,
                "ordem": dist_da_origem
            })
    
    # Ordenar e adicionar intermediários
    intermediarios.sort(key=lambda x: x["ordem"])
    for inter in intermediarios:
        caminho.append(inter["coords"])
    
    caminho.append(destino_coords)
    return caminho

@app.post("/api/rota")
def calcular_rota(origem: PontoRota, destino: PontoRota):
    """
    Calcula rota entre dois pontos usando algoritmo A*
    """
    try:
        predio_origem_id = origem.predio_id
        predio_destino_id = destino.predio_id
        
        if predio_origem_id == predio_destino_id:
            # Mesmo prédio - usar A*
            caminho = calcular_rota_a_star(
                {"coordenadas": origem.coordenadas},
                {"coordenadas": destino.coordenadas},
                predio_origem_id
            )
        else:
            # Prédios diferentes - linha reta direta
            caminho = [origem.coordenadas, destino.coordenadas]
        
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

def calcular_distancia_caminho(caminho: list) -> float:
    """Calcula distância total do caminho em metros (1 pixel = 0.1 metro)"""
    distancia = 0
    for i in range(len(caminho) - 1):
        p1 = caminho[i]
        p2 = caminho[i + 1]
        
        distancia += calcular_distancia_euclidiana(p1, p2) * 0.1
    
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

# ==================== EXECUTAR ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
