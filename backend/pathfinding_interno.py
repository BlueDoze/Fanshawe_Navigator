"""
Algoritmo A* para pathfinding interno em prédios
Usa o grafo gerado a partir dos SVGs
"""

import heapq
import json
import math
from pathlib import Path
from typing import List, Dict, Optional, Tuple

def calcular_heuristica(no1: Dict, no2: Dict) -> float:
    """
    Calcula distância euclidiana entre dois nós (heurística para A*)
    """
    dx = no1['x'] - no2['x']
    dy = no1['y'] - no2['y']
    return math.sqrt(dx*dx + dy*dy)

def encontrar_porta_mais_proxima(grafo: Dict, sala_id: str, origem_id: str) -> Optional[str]:
    """
    Encontra a porta da sala mais próxima da origem
    
    Args:
        grafo: Dicionário com 'nos' e 'arestas'
        sala_id: ID da sala (ex: "Room_1014")
        origem_id: ID do nó de origem
    
    Returns:
        ID da porta mais próxima ou None
    """
    nos = grafo['nos']
    numero_sala = sala_id.replace('Room_', '').replace('Centro_Room_', '')
    
    # Buscar todas as portas da sala
    portas_sala = [
        nid for nid, no in nos.items()
        if no['tipo'] == 'porta' and no.get('sala') == numero_sala
    ]
    
    if not portas_sala:
        print(f"   ⚠️  Nenhuma porta encontrada para sala {numero_sala}")
        return None
    
    # Se houver apenas uma porta
    if len(portas_sala) == 1:
        return portas_sala[0]
    
    # Encontrar porta mais próxima da origem
    if origem_id not in nos:
        return portas_sala[0]  # Retornar primeira porta
    
    origem = nos[origem_id]
    
    def dist_porta(porta_id: str) -> float:
        porta = nos[porta_id]
        return calcular_heuristica(origem, porta)
    
    porta_mais_proxima = min(portas_sala, key=dist_porta)
    print(f"   ℹ️  Sala {numero_sala} tem {len(portas_sala)} portas, usando {porta_mais_proxima}")
    
    return porta_mais_proxima

def calcular_caminho_a_star(grafo: Dict, origem_id: str, destino_id: str) -> Optional[List[str]]:
    """
    Calcula caminho usando algoritmo A*
    
    Args:
        grafo: Dicionário com 'nos' e 'arestas'
        origem_id: ID do nó de origem
        destino_id: ID do nó de destino
    
    Returns:
        Lista de IDs de nós no caminho, ou None se não houver caminho
    """
    nos = grafo['nos']
    
    # Validar nós
    if origem_id not in nos:
        print(f"   ❌ Origem não encontrada: {origem_id}")
        return None
    
    if destino_id not in nos:
        print(f"   ❌ Destino não encontrado: {destino_id}")
        return None
    
    # Se destino é uma sala, usar a porta mais próxima
    if destino_id.startswith('Room_') or destino_id.startswith('Centro_Room_'):
        nova_destino = encontrar_porta_mais_proxima(grafo, destino_id, origem_id)
        if nova_destino:
            destino_id = nova_destino
        else:
            # Tentar usar centro da sala se não houver portas
            if not destino_id.startswith('Centro_'):
                destino_id = f'Centro_{destino_id}'
                if destino_id not in nos:
                    print(f"   ❌ Nenhuma porta ou centro encontrado para a sala")
                    return None
    
    # Se origem é uma sala, usar a porta mais próxima
    if origem_id.startswith('Room_') or origem_id.startswith('Centro_Room_'):
        nova_origem = encontrar_porta_mais_proxima(grafo, origem_id, destino_id)
        if nova_origem:
            origem_id = nova_origem
        else:
            if not origem_id.startswith('Centro_'):
                origem_id = f'Centro_{origem_id}'
                if origem_id not in nos:
                    print(f"   ❌ Nenhuma porta ou centro encontrado para a sala de origem")
                    return None
    
    print(f"   🎯 Calculando rota: {origem_id} → {destino_id}")
    
    # Implementação A*
    # Fila de prioridade: (f_score, contador, id)
    contador = 0
    abertos = [(0, contador, origem_id)]
    
    # Conjuntos de controle
    conjunto_abertos = {origem_id}
    conjunto_fechados = set()
    
    # Custos
    g_score = {origem_id: 0}
    f_score = {origem_id: calcular_heuristica(nos[origem_id], nos[destino_id])}
    
    # Rastreamento de caminho
    veio_de = {}
    
    while abertos:
        _, _, atual = heapq.heappop(abertos)
        
        if atual in conjunto_fechados:
            continue
        
        # Chegou no destino
        if atual == destino_id:
            # Reconstruir caminho
            caminho = [atual]
            while atual in veio_de:
                atual = veio_de[atual]
                caminho.append(atual)
            caminho.reverse()
            
            # Calcular distância total
            distancia_total = g_score[destino_id]
            
            print(f"   ✅ Caminho encontrado!")
            print(f"   📏 Distância total: {distancia_total:.2f} pixels")
            print(f"   🔢 Nós no caminho: {len(caminho)}")
            
            return caminho
        
        conjunto_fechados.add(atual)
        conjunto_abertos.discard(atual)
        
        # Explorar vizinhos
        for vizinho in nos[atual]['conexoes']:
            if vizinho in conjunto_fechados:
                continue
            
            # Calcular distância
            distancia = calcular_heuristica(nos[atual], nos[vizinho])
            tentativa_g = g_score[atual] + distancia
            
            if vizinho not in g_score or tentativa_g < g_score[vizinho]:
                # Melhor caminho encontrado
                veio_de[vizinho] = atual
                g_score[vizinho] = tentativa_g
                f_score[vizinho] = tentativa_g + calcular_heuristica(nos[vizinho], nos[destino_id])
                
                if vizinho not in conjunto_abertos:
                    contador += 1
                    heapq.heappush(abertos, (f_score[vizinho], contador, vizinho))
                    conjunto_abertos.add(vizinho)
    
    print(f"   ❌ Nenhum caminho encontrado de {origem_id} para {destino_id}")
    return None

def testar_pathfinding():
    """
    Testa o pathfinding com exemplos do Building A
    """
    print("="*60)
    print("🧪 TESTANDO PATHFINDING - BUILDING A")
    print("="*60)
    
    # Carregar grafo do A1
    grafo_path = Path(__file__).parent / 'dados' / 'grafos' / 'building_a_a1_grafo.json'
    
    if not grafo_path.exists():
        print(f"\n❌ Grafo não encontrado: {grafo_path}")
        print("Execute primeiro: python criar_grafo_navegacao.py")
        return
    
    with open(grafo_path, 'r', encoding='utf-8') as f:
        grafo = json.load(f)
    
    print(f"\n✅ Grafo carregado: {len(grafo['nos'])} nós, {len(grafo['arestas'])} arestas")
    
    # Listar alguns nós disponíveis
    print(f"\n📋 Nós disponíveis (primeiros 20):")
    nos_por_tipo = {}
    for nid, no in grafo['nos'].items():
        tipo = no['tipo']
        nos_por_tipo.setdefault(tipo, []).append(nid)
    
    for tipo, nos_ids in nos_por_tipo.items():
        print(f"\n   {tipo.upper()}:")
        for nid in nos_ids[:5]:
            print(f"      - {nid}")
        if len(nos_ids) > 5:
            print(f"      ... e mais {len(nos_ids) - 5}")
    
    # Testes de exemplo
    print(f"\n{'='*60}")
    print("🧪 EXECUTANDO TESTES")
    print(f"{'='*60}")
    
    testes = []
    
    # Teste 1: Entre dois nós de corredor (se existirem)
    nos_corredor = nos_por_tipo.get('corredor', [])
    if len(nos_corredor) >= 2:
        testes.append({
            'nome': 'Corredor para Corredor',
            'origem': nos_corredor[0],
            'destino': nos_corredor[1]
        })
    
    # Teste 2: De corredor para porta (se existirem)
    nos_porta = nos_por_tipo.get('porta', [])
    if nos_corredor and nos_porta:
        testes.append({
            'nome': 'Corredor para Porta',
            'origem': nos_corredor[0],
            'destino': nos_porta[0]
        })
    
    # Teste 3: Entre duas portas
    if len(nos_porta) >= 2:
        testes.append({
            'nome': 'Porta para Porta',
            'origem': nos_porta[0],
            'destino': nos_porta[1]
        })
    
    # Teste 4: De corredor para saída (se existirem)
    nos_saida = nos_por_tipo.get('saida', [])
    if nos_corredor and nos_saida:
        testes.append({
            'nome': 'Corredor para Saída',
            'origem': nos_corredor[0],
            'destino': nos_saida[0]
        })
    
    # Teste 5: Para sala Room_1014 (se existir)
    if nos_corredor and 'Room_1014' in [n.replace('Centro_', '') for n in grafo['nos'].keys()]:
        testes.append({
            'nome': 'Corredor para Sala 1014',
            'origem': nos_corredor[0],
            'destino': 'Room_1014'
        })
    
    # Executar testes
    resultados = []
    for i, teste in enumerate(testes, 1):
        print(f"\n{'─'*60}")
        print(f"Teste {i}: {teste['nome']}")
        print(f"{'─'*60}")
        
        caminho = calcular_caminho_a_star(grafo, teste['origem'], teste['destino'])
        
        resultado = {
            'teste': teste['nome'],
            'origem': teste['origem'],
            'destino': teste['destino'],
            'sucesso': caminho is not None,
            'caminho': caminho
        }
        
        resultados.append(resultado)
        
        if caminho:
            print(f"   📍 Caminho: {' → '.join(caminho[:5])}")
            if len(caminho) > 5:
                print(f"   ... {len(caminho) - 5} nós a mais ...")
                print(f"   ... → {caminho[-1]}")
    
    # Resumo
    print(f"\n{'='*60}")
    print("📊 RESUMO DOS TESTES")
    print(f"{'='*60}")
    
    total = len(resultados)
    sucessos = sum(1 for r in resultados if r['sucesso'])
    
    print(f"\nTotal de testes: {total}")
    print(f"Sucessos.......: {sucessos}")
    print(f"Falhas.........: {total - sucessos}")
    print(f"Taxa de sucesso: {(sucessos/total*100):.1f}%" if total > 0 else "N/A")
    
    # Salvar resultados
    resultados_path = Path(__file__).parent / 'dados' / 'grafos' / 'testes_pathfinding.json'
    with open(resultados_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_testes': total,
            'sucessos': sucessos,
            'falhas': total - sucessos,
            'testes': resultados
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados salvos em: {resultados_path}")

def calcular_rota_completa(origem: str, destino: str, andar: str = 'A1') -> Optional[Dict]:
    """
    Função de alto nível para calcular rota completa
    
    Args:
        origem: ID do local de origem (pode ser sala, porta, nó)
        destino: ID do local de destino (pode ser sala, porta, nó)
        andar: Andar do prédio (default: 'A1')
    
    Returns:
        Dicionário com informações da rota ou None
    """
    # Carregar grafo
    grafo_path = Path(__file__).parent / 'dados' / 'grafos' / f'building_a_{andar.lower()}_grafo.json'
    
    if not grafo_path.exists():
        print(f"❌ Grafo não encontrado: {grafo_path}")
        return None
    
    with open(grafo_path, 'r', encoding='utf-8') as f:
        grafo = json.load(f)
    
    # Calcular caminho
    caminho = calcular_caminho_a_star(grafo, origem, destino)
    
    if not caminho:
        return None
    
    # Calcular informações adicionais
    nos = grafo['nos']
    distancia_total = 0
    
    for i in range(len(caminho) - 1):
        no_atual = nos[caminho[i]]
        no_prox = nos[caminho[i + 1]]
        distancia_total += calcular_heuristica(no_atual, no_prox)
    
    return {
        'origem': origem,
        'destino': destino,
        'andar': andar,
        'caminho': caminho,
        'num_passos': len(caminho),
        'distancia_pixels': round(distancia_total, 2),
        'nos_detalhados': [
            {
                'id': nid,
                'tipo': nos[nid]['tipo'],
                'x': nos[nid]['x'],
                'y': nos[nid]['y']
            }
            for nid in caminho
        ]
    }

if __name__ == '__main__':
    # Executar testes
    testar_pathfinding()
    
    print(f"\n{'='*60}")
    print("✅ TESTES CONCLUÍDOS")
    print(f"{'='*60}")
    print("\nPara usar em produção:")
    print("  from pathfinding_interno import calcular_rota_completa")
    print("  rota = calcular_rota_completa('Node_H1_01', 'Room_1014', 'A1')")
