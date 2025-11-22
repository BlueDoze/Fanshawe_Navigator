"""
Campus building navigation system
Creates connection graph between buildings and calculates routes
"""

import json
import math
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class GrafoPredios:
    """
    Campus building navigation graph
    """
    
    def __init__(self):
        self.predios = {}  # {id: {nome, ref, coords, centroide}}
        self.conexoes = []  # [(predio1, predio2, distancia)]
        self.vizinhos = {}  # {predio_id: [connected predio_ids]}
    
    def carregar_geojson(self, caminho_geojson: str):
        """
        Load buildings from GeoJSON and calculate centroids
        """
        with open(caminho_geojson, 'r', encoding='utf-8') as f:
            geojson = json.load(f)
        
        print("🏢 Loading buildings from GeoJSON...")
        
        for feature in geojson.get('features', []):
            props = feature.get('properties', {})
            geom = feature.get('geometry', {})
            
            # Filter only college buildings
            if props.get('building') == 'college':
                nome = props.get('name', 'Sem nome')
                ref = props.get('ref', nome)
                
                # Calculate centroid
                if geom.get('type') == 'Polygon':
                    coords = geom.get('coordinates', [[]])[0]
                    centroide = self._calcular_centroide(coords)
                    
                    predio_id = ref.lower().replace(' ', '_')
                    
                    self.predios[predio_id] = {
                        'id': predio_id,
                        'nome': nome,
                        'ref': ref,
                        'centroide': centroide,
                        'coords_polygon': coords
                    }
                    
                    self.vizinhos[predio_id] = []
        
        print(f"   ✅ {len(self.predios)} buildings loaded")
        
        # List buildings
        for pid, info in sorted(self.predios.items()):
            print(f"      - {info['ref']}: {info['nome']}")
    
    def _calcular_centroide(self, coords: List[List[float]]) -> Tuple[float, float]:
        """
        Calculate the centroid of a polygon
        """
        if not coords:
            return (0, 0)
        
        # Average of coordinates
        lngs = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        
        return (sum(lngs) / len(lngs), sum(lats) / len(lats))
    
    def _distancia_haversine(self, coord1: Tuple[float, float], 
                            coord2: Tuple[float, float]) -> float:
        """
        Calculate distance between two geographic points (in meters)
        Haversine formula
        """
        lon1, lat1 = coord1
        lon2, lat2 = coord2
        
        # Earth radius in meters
        R = 6371000
        
        # Convert to radians
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        # Haversine formula
        a = math.sin(delta_phi/2)**2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def criar_conexoes_automaticas(self, distancia_maxima: float = 200.0):
        """
        Create automatic connections between nearby buildings
        
        Args:
            distancia_maxima: Maximum distance in meters for connection
        """
        print(f"\n🔗 Creating connections between buildings (max distance: {distancia_maxima}m)...")
        
        predios_ids = list(self.predios.keys())
        conexoes_criadas = 0
        
        for i, pid1 in enumerate(predios_ids):
            p1 = self.predios[pid1]
            
            for pid2 in predios_ids[i+1:]:
                p2 = self.predios[pid2]
                
                # Calculate distance between centroids
                dist = self._distancia_haversine(p1['centroide'], p2['centroide'])
                
                # If they are close, create connection
                if dist <= distancia_maxima:
                    self.conexoes.append((pid1, pid2, dist))
                    self.vizinhos[pid1].append(pid2)
                    self.vizinhos[pid2].append(pid1)
                    conexoes_criadas += 1
        
        print(f"   ✅ {conexoes_criadas} connections created")
    
    def adicionar_conexao_manual(self, predio1: str, predio2: str):
        """
        Add manual connection between two buildings
        """
        pid1 = predio1.lower().replace(' ', '_')
        pid2 = predio2.lower().replace(' ', '_')
        
        if pid1 not in self.predios or pid2 not in self.predios:
            print(f"   ⚠️  Building not found: {predio1} or {predio2}")
            return False
        
        p1 = self.predios[pid1]
        p2 = self.predios[pid2]
        
        dist = self._distancia_haversine(p1['centroide'], p2['centroide'])
        
        if pid2 not in self.vizinhos[pid1]:
            self.conexoes.append((pid1, pid2, dist))
            self.vizinhos[pid1].append(pid2)
            self.vizinhos[pid2].append(pid1)
            return True
        
        return False
    
    def calcular_rota(self, origem: str, destino: str) -> Optional[Dict]:
        """
        Calculate route between two buildings using A*
        
        Args:
            origem: Origin building reference (e.g.: "A", "Building A")
            destino: Destination building reference (e.g.: "M", "Building M")
        
        Returns:
            Dictionary with route information or None
        """
        # Normalize IDs
        origem_id = self._normalizar_id_predio(origem)
        destino_id = self._normalizar_id_predio(destino)
        
        if not origem_id or not destino_id:
            return None
        
        if origem_id not in self.predios or destino_id not in self.predios:
            print(f"   ❌ Building not found: {origem} or {destino}")
            return None
        
        print(f"\n🎯 Calculating route: {self.predios[origem_id]['ref']} → {self.predios[destino_id]['ref']}")
        
        # A* pathfinding
        import heapq
        
        def heuristica(pid1, pid2):
            return self._distancia_haversine(
                self.predios[pid1]['centroide'],
                self.predios[pid2]['centroide']
            )
        
        # Priority queue
        contador = 0
        abertos = [(0, contador, origem_id)]
        
        # Costs
        g_score = {origem_id: 0}
        f_score = {origem_id: heuristica(origem_id, destino_id)}
        
        # Tracking
        veio_de = {}
        conjunto_fechados = set()
        
        while abertos:
            _, _, atual = heapq.heappop(abertos)
            
            if atual in conjunto_fechados:
                continue
            
            if atual == destino_id:
                # Reconstruir caminho
                caminho = [atual]
                while atual in veio_de:
                    atual = veio_de[atual]
                    caminho.append(atual)
                caminho.reverse()
                
                # Calcular distância total
                dist_total = g_score[destino_id]
                
                # Criar lista de prédios
                predios_rota = [
                    {
                        'id': pid,
                        'nome': self.predios[pid]['nome'],
                        'ref': self.predios[pid]['ref'],
                        'coords': self.predios[pid]['centroide']
                    }
                    for pid in caminho
                ]
                
                print(f"   ✅ Rota encontrada!")
                print(f"   📏 Distância total: {dist_total:.1f}m")
                print(f"   🏢 Prédios no caminho: {len(predios_rota)}")
                print(f"   🗺️  Rota: {' → '.join([p['ref'] for p in predios_rota])}")
                
                return {
                    'origem': predios_rota[0],
                    'destino': predios_rota[-1],
                    'caminho': predios_rota,
                    'distancia_metros': round(dist_total, 1),
                    'num_predios': len(predios_rota),
                    'coordenadas_rota': [p['coords'] for p in predios_rota]
                }
            
            conjunto_fechados.add(atual)
            
            # Explorar vizinhos
            for vizinho in self.vizinhos[atual]:
                if vizinho in conjunto_fechados:
                    continue
                
                dist = self._distancia_haversine(
                    self.predios[atual]['centroide'],
                    self.predios[vizinho]['centroide']
                )
                
                tentativa_g = g_score[atual] + dist
                
                if vizinho not in g_score or tentativa_g < g_score[vizinho]:
                    veio_de[vizinho] = atual
                    g_score[vizinho] = tentativa_g
                    f_score[vizinho] = tentativa_g + heuristica(vizinho, destino_id)
                    
                    contador += 1
                    heapq.heappush(abertos, (f_score[vizinho], contador, vizinho))
        
        print(f"   ❌ Nenhuma rota encontrada entre {origem} e {destino}")
        return None
    
    def _normalizar_id_predio(self, ref: str) -> Optional[str]:
        """
        Normaliza referência de prédio para ID
        """
        ref_clean = ref.lower().strip()
        
        # Buscar por ID exato
        if ref_clean in self.predios:
            return ref_clean
        
        # Buscar por ref
        for pid, info in self.predios.items():
            if info['ref'].lower() == ref_clean:
                return pid
            if ref_clean in info['nome'].lower():
                return pid
        
        return None
    
    def salvar_grafo(self, caminho_saida: str):
        """
        Salva o grafo em JSON
        """
        grafo_data = {
            'predios': self.predios,
            'conexoes': [
                {
                    'origem': c[0],
                    'destino': c[1],
                    'distancia_metros': round(c[2], 1)
                }
                for c in self.conexoes
            ],
            'estatisticas': {
                'total_predios': len(self.predios),
                'total_conexoes': len(self.conexoes),
                'predios_isolados': len([p for p, v in self.vizinhos.items() if not v])
            }
        }
        
        output_path = Path(caminho_saida)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(grafo_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Grafo salvo em: {output_path}")

def criar_grafo_campus():
    """
    Cria o grafo de navegação do campus
    """
    print("="*60)
    print("🗺️  CRIANDO GRAFO DE NAVEGAÇÃO ENTRE PRÉDIOS")
    print("="*60)
    
    # Criar grafo
    grafo = GrafoPredios()
    
    # Carregar GeoJSON
    geojson_path = Path(__file__).parent / 'dados' / 'campus.geojson'
    grafo.carregar_geojson(str(geojson_path))
    
    # Criar conexões automáticas (prédios a menos de 200m)
    grafo.criar_conexoes_automaticas(distancia_maxima=250.0)
    
    # Salvar grafo
    output_path = Path(__file__).parent / 'dados' / 'grafo_predios.json'
    grafo.salvar_grafo(str(output_path))
    
    # Testes de exemplo
    print(f"\n{'='*60}")
    print("🧪 TESTES DE ROTAS")
    print(f"{'='*60}")
    
    testes = [
        ('A', 'M'),  # Building A → Building M
        ('F', 'J'),  # F Building → Building J
        ('B', 'H'),  # Building B → Building H
    ]
    
    for origem, destino in testes:
        rota = grafo.calcular_rota(origem, destino)
    
    return grafo

if __name__ == '__main__':
    grafo = criar_grafo_campus()
    
    print(f"\n{'='*60}")
    print("✅ GRAFO CRIADO COM SUCESSO")
    print(f"{'='*60}")
    print("\nUse no código:")
    print("  from grafo_predios import GrafoPredios")
    print("  grafo = GrafoPredios()")
    print("  grafo.carregar_geojson('dados/campus.geojson')")
    print("  rota = grafo.calcular_rota('A', 'M')")
