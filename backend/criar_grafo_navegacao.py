"""
Script para criar grafo de navegação a partir dos elementos SVG extraídos
Conecta nós de corredor, portas e saídas para permitir pathfinding
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Tuple

class GrafoNavegacao:
    """
    Representa um grafo de navegação para pathfinding interno em um prédio
    """
    
    def __init__(self, andar: str):
        self.andar = andar
        self.nos = {}  # {id: {x, y, tipo, conexoes, metadata}}
        self.arestas = []  # [(id1, id2, distancia)]
    
    def adicionar_elementos_svg(self, elementos: Dict):
        """
        Adiciona elementos extraídos do SVG ao grafo
        
        Args:
            elementos: Dicionário com salas, portas, saídas, nos_corredor
        """
        print(f"\n🔧 Construindo grafo para {self.andar}...")
        
        # 1. Adicionar nós de corredor
        for no in elementos['nos_corredor']:
            self.nos[no['id']] = {
                'x': no['x'],
                'y': no['y'],
                'tipo': 'corredor',
                'conexoes': [],
                'metadata': {
                    'tipo_elemento': no.get('tipo_elemento', 'unknown')
                }
            }
        
        print(f"   ✓ {len(elementos['nos_corredor'])} nós de corredor adicionados")
        
        # 2. Adicionar portas como nós
        for porta in elementos['portas']:
            if porta['centro']:
                self.nos[porta['id']] = {
                    'x': porta['centro']['x'],
                    'y': porta['centro']['y'],
                    'tipo': 'porta',
                    'sala': porta['sala_relacionada'],
                    'conexoes': [],
                    'metadata': {
                        'tipo_elemento': porta.get('tipo_elemento', 'unknown'),
                        'bbox': porta.get('bbox')
                    }
                }
        
        print(f"   ✓ {len(elementos['portas'])} portas adicionadas")
        
        # 3. Adicionar saídas como nós
        for saida in elementos['saidas']:
            if saida['centro']:
                self.nos[saida['id']] = {
                    'x': saida['centro']['x'],
                    'y': saida['centro']['y'],
                    'tipo': 'saida',
                    'conexoes': [],
                    'metadata': {
                        'tipo_elemento': saida.get('tipo_elemento', 'unknown'),
                        'bbox': saida.get('bbox'),
                        'tipo_saida': saida.get('tipo', 'saida')
                    }
                }
        
        print(f"   ✓ {len(elementos['saidas'])} saídas adicionadas")
        
        # 4. Adicionar centros de salas (para referência)
        for sala in elementos['salas']:
            if sala['centro']:
                sala_id = f"Centro_{sala['id']}"
                self.nos[sala_id] = {
                    'x': sala['centro']['x'],
                    'y': sala['centro']['y'],
                    'tipo': 'sala_centro',
                    'sala': sala['numero'],
                    'conexoes': [],
                    'metadata': {
                        'nome_sala': sala['id'],
                        'bbox': sala.get('bbox')
                    }
                }
        
        print(f"   ✓ {len(elementos['salas'])} centros de sala adicionados")
        print(f"   📊 Total de nós: {len(self.nos)}")
    
    def calcular_distancia(self, id1: str, id2: str) -> float:
        """
        Calcula distância euclidiana entre dois nós
        """
        no1 = self.nos[id1]
        no2 = self.nos[id2]
        
        dx = no1['x'] - no2['x']
        dy = no1['y'] - no2['y']
        
        return math.sqrt(dx*dx + dy*dy)
    
    def conectar_nos_proximos(self, distancia_maxima: float = 150.0, 
                             conectar_portas_a_salas: bool = True):
        """
        Conecta nós que estão próximos uns dos outros
        
        Args:
            distancia_maxima: Distância máxima para criar conexão
            conectar_portas_a_salas: Se deve conectar portas aos centros das salas
        """
        print(f"\n🔗 Conectando nós (distância máxima: {distancia_maxima}px)...")
        
        ids = list(self.nos.keys())
        conexoes_criadas = 0
        
        for i, id1 in enumerate(ids):
            no1 = self.nos[id1]
            
            for id2 in ids[i+1:]:
                no2 = self.nos[id2]
                
                # Calcular distância
                dist = self.calcular_distancia(id1, id2)
                
                # Regras de conexão
                deve_conectar = False
                
                # Caso 1: Nós de corredor entre si
                if no1['tipo'] == 'corredor' and no2['tipo'] == 'corredor':
                    if dist <= distancia_maxima:
                        deve_conectar = True
                
                # Caso 2: Nós de corredor com portas
                elif (no1['tipo'] == 'corredor' and no2['tipo'] == 'porta') or \
                     (no1['tipo'] == 'porta' and no2['tipo'] == 'corredor'):
                    if dist <= distancia_maxima * 0.8:  # Distância menor para portas
                        deve_conectar = True
                
                # Caso 3: Nós de corredor com saídas
                elif (no1['tipo'] == 'corredor' and no2['tipo'] == 'saida') or \
                     (no1['tipo'] == 'saida' and no2['tipo'] == 'corredor'):
                    if dist <= distancia_maxima:
                        deve_conectar = True
                
                # Caso 4: Portas com centros de suas próprias salas
                elif conectar_portas_a_salas:
                    if no1['tipo'] == 'porta' and no2['tipo'] == 'sala_centro':
                        if no1.get('sala') == no2.get('sala'):
                            deve_conectar = True
                    elif no2['tipo'] == 'porta' and no1['tipo'] == 'sala_centro':
                        if no2.get('sala') == no1.get('sala'):
                            deve_conectar = True
                
                # Criar conexão se aplicável
                if deve_conectar:
                    self.arestas.append((id1, id2, dist))
                    no1['conexoes'].append(id2)
                    no2['conexoes'].append(id1)
                    conexoes_criadas += 1
        
        print(f"   ✓ {conexoes_criadas} conexões criadas")
    
    def adicionar_conexao_manual(self, id1: str, id2: str):
        """
        Adiciona uma conexão manual entre dois nós
        """
        if id1 not in self.nos or id2 not in self.nos:
            print(f"   ⚠️  Nó não encontrado: {id1} ou {id2}")
            return False
        
        dist = self.calcular_distancia(id1, id2)
        
        if id2 not in self.nos[id1]['conexoes']:
            self.arestas.append((id1, id2, dist))
            self.nos[id1]['conexoes'].append(id2)
            self.nos[id2]['conexoes'].append(id1)
            return True
        
        return False
    
    def validar_grafo(self) -> Dict:
        """
        Valida o grafo e retorna estatísticas
        """
        print(f"\n🔍 Validando grafo...")
        
        # Contar nós sem conexões
        nos_isolados = [nid for nid, no in self.nos.items() if len(no['conexoes']) == 0]
        
        # Estatísticas por tipo
        tipos = {}
        for no in self.nos.values():
            tipo = no['tipo']
            tipos[tipo] = tipos.get(tipo, 0) + 1
        
        # Estatísticas de conexões
        total_conexoes = len(self.arestas)
        media_conexoes = sum(len(no['conexoes']) for no in self.nos.values()) / len(self.nos) if self.nos else 0
        
        validacao = {
            'total_nos': len(self.nos),
            'total_arestas': total_conexoes,
            'nos_isolados': len(nos_isolados),
            'lista_nos_isolados': nos_isolados,
            'nos_por_tipo': tipos,
            'media_conexoes_por_no': round(media_conexoes, 2)
        }
        
        print(f"   📊 Total de nós: {validacao['total_nos']}")
        print(f"   📊 Total de arestas: {validacao['total_arestas']}")
        print(f"   📊 Nós isolados: {validacao['nos_isolados']}")
        print(f"   📊 Média de conexões por nó: {validacao['media_conexoes_por_no']}")
        
        if validacao['nos_isolados'] > 0:
            print(f"   ⚠️  ATENÇÃO: {validacao['nos_isolados']} nós sem conexões!")
            print(f"      Primeiros 10: {nos_isolados[:10]}")
        
        return validacao
    
    def salvar_grafo(self, caminho_saida: str):
        """
        Salva o grafo em formato JSON
        """
        print(f"\n💾 Salvando grafo...")
        
        grafo_data = {
            'andar': self.andar,
            'nos': self.nos,
            'arestas': [
                {
                    'origem': a[0],
                    'destino': a[1],
                    'distancia': round(a[2], 2)
                }
                for a in self.arestas
            ],
            'validacao': self.validar_grafo()
        }
        
        output_path = Path(caminho_saida)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(grafo_data, f, indent=2, ensure_ascii=False)
        
        print(f"   ✓ Grafo salvo em: {output_path}")
        
        return str(output_path)
    
    def exportar_para_visualizacao(self, caminho_saida: str):
        """
        Exporta dados do grafo em formato para visualização
        """
        # Formato compatível com bibliotecas de visualização de grafos
        vis_data = {
            'nodes': [
                {
                    'id': nid,
                    'label': nid,
                    'x': no['x'],
                    'y': no['y'],
                    'type': no['tipo'],
                    'connections': len(no['conexoes'])
                }
                for nid, no in self.nos.items()
            ],
            'edges': [
                {
                    'from': a[0],
                    'to': a[1],
                    'weight': round(a[2], 2)
                }
                for a in self.arestas
            ]
        }
        
        output_path = Path(caminho_saida)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(vis_data, f, indent=2, ensure_ascii=False)
        
        print(f"   ✓ Dados de visualização salvos em: {output_path}")

def processar_building_a_grafos():
    """
    Processa grafos para todos os andares do Building A
    """
    print("="*60)
    print("🏗️  CRIANDO GRAFOS DE NAVEGAÇÃO - BUILDING A")
    print("="*60)
    
    # Diretórios
    elements_dir = Path(__file__).parent / 'dados' / 'building_elements'
    grafos_dir = Path(__file__).parent / 'dados' / 'grafos'
    grafos_dir.mkdir(parents=True, exist_ok=True)
    
    resultados = {}
    
    # Processar cada andar
    for andar in ['A1', 'A2', 'A3']:
        print(f"\n{'='*60}")
        print(f"Processando {andar}")
        print(f"{'='*60}")
        
        # Carregar elementos
        elementos_path = elements_dir / f'building_a_{andar.lower()}_elementos.json'
        
        if not elementos_path.exists():
            print(f"⚠️  Arquivo de elementos não encontrado: {elementos_path}")
            print(f"   Execute primeiro: python extrair_salas_svg.py")
            continue
        
        with open(elementos_path, 'r', encoding='utf-8') as f:
            elementos = json.load(f)
        
        # Criar grafo
        grafo = GrafoNavegacao(andar)
        grafo.adicionar_elementos_svg(elementos)
        
        # Conectar nós
        # Para Building A, usar distância um pouco maior devido ao tamanho
        distancia_maxima = 200.0 if andar == 'A1' else 150.0
        grafo.conectar_nos_proximos(distancia_maxima=distancia_maxima)
        
        # Salvar grafo
        grafo_path = grafos_dir / f'building_a_{andar.lower()}_grafo.json'
        grafo.salvar_grafo(str(grafo_path))
        
        # Exportar para visualização
        vis_path = grafos_dir / f'building_a_{andar.lower()}_vis.json'
        grafo.exportar_para_visualizacao(str(vis_path))
        
        resultados[andar] = {
            'grafo_path': str(grafo_path),
            'vis_path': str(vis_path),
            'total_nos': len(grafo.nos),
            'total_arestas': len(grafo.arestas)
        }
    
    # Resumo final
    print(f"\n{'='*60}")
    print("✅ PROCESSAMENTO COMPLETO")
    print(f"{'='*60}")
    
    for andar, info in resultados.items():
        print(f"\n{andar}:")
        print(f"  Nós.........: {info['total_nos']}")
        print(f"  Arestas.....: {info['total_arestas']}")
        print(f"  Grafo.......: {info['grafo_path']}")
        print(f"  Visualização: {info['vis_path']}")
    
    return resultados

if __name__ == '__main__':
    # Processar Building A
    resultados = processar_building_a_grafos()
    
    print(f"\n{'='*60}")
    print("📝 PRÓXIMOS PASSOS")
    print(f"{'='*60}")
    print("1. Revisar grafos gerados em: backend/dados/grafos/")
    print("2. Se houver nós isolados, adicionar mais nós de corredor no SVG")
    print("3. Testar pathfinding com: python pathfinding_interno.py")
    print("4. Integrar com API: adicionar endpoint /api/rota-interna")
