# Sistema de Identificação de Salas e Traçado de Caminhos

## 📋 Visão Geral

Para traçar caminhos corretos no Building A (e outros prédios), precisamos entender como as salas, portas e corredores são identificados nos arquivos SVG.

## 🏗️ Estrutura dos Arquivos SVG

### Análise do Building A

Os arquivos SVG do Building A estão localizados em:
```
LeafletJS/LeafletJS/Floorplans/Building A/
├── A1.svg  (Andar 1)
├── A2.svg  (Andar 2)
└── A3.svg  (Andar 3)
```

### Sistema de Camadas (Layers) no Inkscape

Os SVGs usam **camadas do Inkscape** para organizar elementos:

```xml
<g inkscape:groupmode="layer" 
   id="layer1" 
   inkscape:label="Rooms">
   <!-- Salas ficam aqui -->
</g>
```

### Identificação de Elementos

#### 1. **Salas (Rooms)**
```xml
<path
   style="opacity:0.405634;fill:#808080;stroke:#000000;stroke-width:3.77953"
   d="M 500.96232,483.59549 516.77681,528 586.15652,501.47246 569.32174,457.76883 Z"
   id="Room_1014" />
```

**Padrão de ID**: `Room_XXXX`
- Exemplo: `Room_1014`, `Room_2103`, `Room_3205`
- Número XXXX geralmente indica: `[Andar][Número da sala]`

#### 2. **Portas (Doors)**
```xml
<rect id="Door_1014_1" x="520" y="490" width="10" height="20" />
<rect id="Door_1014_2" x="540" y="495" width="10" height="20" />
```

**Padrão de ID**: `Door_SALA_NUMERO`
- Exemplo: `Door_1014_1` = Porta 1 da sala 1014
- Exemplo: `Door_1014_2` = Porta 2 da sala 1014
- Uma sala pode ter múltiplas portas

#### 3. **Saídas/Entradas do Prédio (Exits/Entrances)**
```xml
<polygon id="Exit_Main" points="..." />
<polygon id="Exit_North" points="..." />
```

**Padrão de ID**: `Exit_NOME` ou `Entrance_NUMERO`

#### 4. **Nós de Corredor (Hallway Nodes)**
```xml
<circle id="Node_H1_01" cx="400" cy="300" r="5" />
<circle id="Node_H1_02" cx="450" cy="300" r="5" />
```

**Padrão de ID**: `Node_H[Andar]_[Sequência]`
- Exemplo: `Node_H1_01` = Nó 01 do corredor do 1º andar
- Estes nós criam o "grafo" para pathfinding

## 🗺️ Sistema de Coordenadas

### Coordenadas SVG vs Coordenadas Geográficas

```javascript
// Coordenadas no SVG (pixels)
{
  x: 500.96,  // Posição X no SVG
  y: 483.59   // Posição Y no SVG
}

// Convertido para coordenadas geográficas
{
  lat: 43.0137,   // Latitude
  lng: -81.1998   // Longitude
}
```

### Função de Conversão (já implementada no frontend)

```javascript
function pixelParaLatLng(pixelX, pixelY, dimensoes, bounds) {
    // Normalizar coordenadas (0-1)
    const normX = pixelX / dimensoes.width;
    const normY = pixelY / dimensoes.height;
    
    // Interpolar para coordenadas geográficas
    const lat = bounds.getSouth() + (1 - normY) * (bounds.getNorth() - bounds.getSouth());
    const lng = bounds.getWest() + normX * (bounds.getEast() - bounds.getWest());
    
    return [lat, lng];
}
```

## 📊 Estrutura de Dados do Sistema LeafletJS

### floorPlansScript.js

```javascript
const floorPlans = {
    "Building A": {
        "path": "Floorplans/Building A",
        "floors": {
            "floor1": {
                "plan": "A1.svg",
                "objects": {
                    "rooms": {
                        "Room_1003": ["Door_1003_1", "Door_1003_2"],
                        "Room_1014": ["Door_1014_1"]
                    },
                    "entrances": {
                        "Exit_Main": []
                    }
                }
            }
        }
    }
}
```

## 🎯 Como Implementar Sistema de Identificação de Salas

### Passo 1: Extrair IDs dos SVGs

```python
# backend/extrair_salas_svg.py
import xml.etree.ElementTree as ET
import json
import os

def extrair_elementos_svg(caminho_svg):
    """
    Extrai todos os elementos identificáveis do SVG
    """
    tree = ET.parse(caminho_svg)
    root = tree.getroot()
    
    # Namespace do SVG
    ns = {'svg': 'http://www.w3.org/2000/svg',
          'inkscape': 'http://www.inkscape.org/namespaces/inkscape'}
    
    elementos = {
        'salas': [],
        'portas': [],
        'saidas': [],
        'nos_corredor': []
    }
    
    # Buscar todos os elementos com ID
    for elem in root.iter():
        elem_id = elem.get('id')
        if elem_id:
            # Salas
            if elem_id.startswith('Room_'):
                bbox = extrair_bbox(elem)
                elementos['salas'].append({
                    'id': elem_id,
                    'numero': elem_id.replace('Room_', ''),
                    'bbox': bbox,
                    'centro': calcular_centro(bbox)
                })
            
            # Portas
            elif elem_id.startswith('Door_'):
                bbox = extrair_bbox(elem)
                elementos['portas'].append({
                    'id': elem_id,
                    'sala_relacionada': elem_id.split('_')[1],
                    'bbox': bbox,
                    'centro': calcular_centro(bbox)
                })
            
            # Saídas
            elif elem_id.startswith('Exit_') or elem_id.startswith('Entrance_'):
                bbox = extrair_bbox(elem)
                elementos['saidas'].append({
                    'id': elem_id,
                    'bbox': bbox,
                    'centro': calcular_centro(bbox)
                })
            
            # Nós de corredor
            elif elem_id.startswith('Node_'):
                # Para círculos
                if elem.tag.endswith('circle'):
                    elementos['nos_corredor'].append({
                        'id': elem_id,
                        'x': float(elem.get('cx', 0)),
                        'y': float(elem.get('cy', 0))
                    })
    
    return elementos

def extrair_bbox(elemento):
    """
    Extrai bounding box do elemento
    """
    # Para path elements
    if elemento.get('d'):
        # Parse path data (simplificado)
        return {'x': 0, 'y': 0, 'width': 0, 'height': 0}
    
    # Para rect elements
    elif elemento.get('x'):
        return {
            'x': float(elemento.get('x', 0)),
            'y': float(elemento.get('y', 0)),
            'width': float(elemento.get('width', 0)),
            'height': float(elemento.get('height', 0))
        }
    
    return None

def calcular_centro(bbox):
    """
    Calcula o centro do bounding box
    """
    if not bbox:
        return None
    
    return {
        'x': bbox['x'] + bbox['width'] / 2,
        'y': bbox['y'] + bbox['height'] / 2
    }

# Processar todos os andares do Building A
for andar in ['A1', 'A2', 'A3']:
    caminho = f'../LeafletJS/LeafletJS/Floorplans/Building A/{andar}.svg'
    if os.path.exists(caminho):
        elementos = extrair_elementos_svg(caminho)
        
        # Salvar JSON
        output_path = f'dados/building_a_{andar.lower()}_elementos.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(elementos, f, indent=2, ensure_ascii=False)
        
        print(f"✅ {andar}: {len(elementos['salas'])} salas, {len(elementos['portas'])} portas")
```

### Passo 2: Criar Grafo de Navegação

```python
# backend/criar_grafo_navegacao.py
import json
import math

class GrafoNavegacao:
    def __init__(self):
        self.nos = {}  # {id: {x, y, tipo, conexoes}}
        self.arestas = []  # [(id1, id2, distancia)]
    
    def adicionar_elementos_svg(self, elementos):
        """
        Adiciona elementos extraídos do SVG ao grafo
        """
        # Adicionar nós de corredor
        for no in elementos['nos_corredor']:
            self.nos[no['id']] = {
                'x': no['x'],
                'y': no['y'],
                'tipo': 'corredor',
                'conexoes': []
            }
        
        # Adicionar portas como nós
        for porta in elementos['portas']:
            if porta['centro']:
                self.nos[porta['id']] = {
                    'x': porta['centro']['x'],
                    'y': porta['centro']['y'],
                    'tipo': 'porta',
                    'sala': porta['sala_relacionada'],
                    'conexoes': []
                }
        
        # Adicionar saídas como nós
        for saida in elementos['saidas']:
            if saida['centro']:
                self.nos[saida['id']] = {
                    'x': saida['centro']['x'],
                    'y': saida['centro']['y'],
                    'tipo': 'saida',
                    'conexoes': []
                }
    
    def conectar_nos_proximos(self, distancia_maxima=100):
        """
        Conecta nós que estão próximos uns dos outros
        """
        ids = list(self.nos.keys())
        
        for i, id1 in enumerate(ids):
            no1 = self.nos[id1]
            
            for id2 in ids[i+1:]:
                no2 = self.nos[id2]
                
                # Calcular distância euclidiana
                dist = math.sqrt(
                    (no1['x'] - no2['x'])**2 + 
                    (no1['y'] - no2['y'])**2
                )
                
                # Se estiverem próximos, criar conexão
                if dist <= distancia_maxima:
                    self.arestas.append((id1, id2, dist))
                    no1['conexoes'].append(id2)
                    no2['conexoes'].append(id1)
    
    def salvar_grafo(self, caminho_saida):
        """
        Salva o grafo em JSON
        """
        grafo_data = {
            'nos': self.nos,
            'arestas': [
                {
                    'origem': a[0],
                    'destino': a[1],
                    'distancia': a[2]
                }
                for a in self.arestas
            ]
        }
        
        with open(caminho_saida, 'w', encoding='utf-8') as f:
            json.dump(grafo_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Grafo salvo: {len(self.nos)} nós, {len(self.arestas)} arestas")

# Processar Building A - Andar 1
elementos = json.load(open('dados/building_a_a1_elementos.json'))
grafo = GrafoNavegacao()
grafo.adicionar_elementos_svg(elementos)
grafo.conectar_nos_proximos(distancia_maxima=150)
grafo.salvar_grafo('dados/building_a_a1_grafo.json')
```

### Passo 3: Atualizar mapas.json

```json
{
  "campus": {
    "nome": "Fanshawe College",
    "predios": [
      {
        "id": "building_a",
        "nome": "A Building",
        "geojson_id": "A Building",
        "andares": [
          {
            "numero": 1,
            "svg_url": "/svg/building_a_floor1.svg",
            "grafo_url": "/dados/building_a_a1_grafo.json",
            "dimensoes": {"width": 816, "height": 1056}
          }
        ],
        "locais": [
          {
            "id": "sala_1014",
            "nome": "Sala 1014",
            "tipo": "sala",
            "andar": 1,
            "svg_id": "Room_1014",
            "portas": ["Door_1014_1"],
            "coordenadas": {"x": 543, "y": 470},
            "descricao": "Sala de aula"
          }
        ]
      }
    ]
  }
}
```

## 🚀 Algoritmo de Pathfinding com Salas

### A* Modificado para Navegação Interna

```python
# backend/pathfinding_interno.py
import heapq
import math

def calcular_caminho_interno(grafo, origem_id, destino_id):
    """
    A* pathfinding dentro do prédio usando o grafo extraído do SVG
    
    Args:
        grafo: Dicionário com 'nos' e 'arestas'
        origem_id: ID do nó de origem (ex: "Door_1014_1")
        destino_id: ID do nó de destino (ex: "Room_2103")
    
    Returns:
        Lista de IDs de nós no caminho
    """
    nos = grafo['nos']
    
    # Se destino é uma sala, usar a porta mais próxima
    if destino_id.startswith('Room_'):
        destino_id = encontrar_porta_mais_proxima(grafo, destino_id, origem_id)
    
    # Implementação A*
    def heuristica(id1, id2):
        n1 = nos[id1]
        n2 = nos[id2]
        return math.sqrt((n1['x'] - n2['x'])**2 + (n1['y'] - n2['y'])**2)
    
    # Fila de prioridade: (f_score, id)
    abertos = [(0, origem_id)]
    
    # Custos
    g_score = {origem_id: 0}
    f_score = {origem_id: heuristica(origem_id, destino_id)}
    
    # Rastreamento de caminho
    veio_de = {}
    
    while abertos:
        _, atual = heapq.heappop(abertos)
        
        if atual == destino_id:
            # Reconstruir caminho
            caminho = [atual]
            while atual in veio_de:
                atual = veio_de[atual]
                caminho.append(atual)
            return list(reversed(caminho))
        
        # Explorar vizinhos
        for vizinho in nos[atual]['conexoes']:
            distancia = calcular_distancia(nos[atual], nos[vizinho])
            tentativa_g = g_score[atual] + distancia
            
            if vizinho not in g_score or tentativa_g < g_score[vizinho]:
                veio_de[vizinho] = atual
                g_score[vizinho] = tentativa_g
                f_score[vizinho] = tentativa_g + heuristica(vizinho, destino_id)
                
                if not any(v[1] == vizinho for v in abertos):
                    heapq.heappush(abertos, (f_score[vizinho], vizinho))
    
    return None  # Sem caminho

def encontrar_porta_mais_proxima(grafo, sala_id, origem_id):
    """
    Encontra a porta da sala mais próxima da origem
    """
    numero_sala = sala_id.replace('Room_', '')
    portas_sala = [
        nid for nid, no in grafo['nos'].items()
        if no['tipo'] == 'porta' and no.get('sala') == numero_sala
    ]
    
    if not portas_sala:
        return sala_id
    
    # Retornar porta mais próxima
    origem = grafo['nos'][origem_id]
    
    def dist_porta(porta_id):
        porta = grafo['nos'][porta_id]
        return math.sqrt(
            (origem['x'] - porta['x'])**2 + 
            (origem['y'] - porta['y'])**2
        )
    
    return min(portas_sala, key=dist_porta)

def calcular_distancia(no1, no2):
    return math.sqrt((no1['x'] - no2['x'])**2 + (no1['y'] - no2['y'])**2)
```

## 📍 Integração com Frontend

### Exemplo de Uso Completo

```javascript
// frontend/index.html

async function tracarCaminhoParaSala(salaDestino) {
    try {
        // 1. Carregar grafo do andar
        const response = await fetch('/dados/building_a_a1_grafo.json');
        const grafo = await response.json();
        
        // 2. Determinar posição atual do usuário
        const origem = 'Node_H1_01'; // ou posição GPS convertida
        
        // 3. Encontrar porta da sala
        const destino = `Room_${salaDestino}`;
        
        // 4. Calcular caminho no backend
        const rotaResponse = await fetch('/api/rota-interna', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                grafo: grafo,
                origem: origem,
                destino: destino
            })
        });
        
        const rota = await rotaResponse.json();
        
        // 5. Desenhar caminho no SVG
        desenharCaminhoSVG(rota.caminho, grafo);
        
    } catch (error) {
        console.error('Erro ao traçar caminho:', error);
    }
}

function desenharCaminhoSVG(caminho, grafo) {
    // Obter o elemento SVG carregado
    const svgElement = document.querySelector('svg');
    if (!svgElement) return;
    
    // Criar grupo para linhas do caminho
    let pathGroup = svgElement.getElementById('caminho-rota');
    if (!pathGroup) {
        pathGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        pathGroup.setAttribute('id', 'caminho-rota');
        svgElement.appendChild(pathGroup);
    } else {
        pathGroup.innerHTML = ''; // Limpar caminho anterior
    }
    
    // Desenhar linhas entre nós consecutivos
    for (let i = 0; i < caminho.length - 1; i++) {
        const no1 = grafo.nos[caminho[i]];
        const no2 = grafo.nos[caminho[i + 1]];
        
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', no1.x);
        line.setAttribute('y1', no1.y);
        line.setAttribute('x2', no2.x);
        line.setAttribute('y2', no2.y);
        line.setAttribute('stroke', '#FF0000');
        line.setAttribute('stroke-width', '5');
        line.setAttribute('stroke-dasharray', '10,5');
        line.setAttribute('opacity', '0.8');
        
        pathGroup.appendChild(line);
    }
    
    // Destacar nós do caminho
    caminho.forEach((nodeId, index) => {
        const no = grafo.nos[nodeId];
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', no.x);
        circle.setAttribute('cy', no.y);
        circle.setAttribute('r', '8');
        circle.setAttribute('fill', index === 0 ? '#00FF00' : 
                                     index === caminho.length - 1 ? '#FF0000' : 
                                     '#FFA500');
        circle.setAttribute('opacity', '0.9');
        
        pathGroup.appendChild(circle);
    });
}
```

## 🎨 Melhorias Recomendadas para os SVGs

### 1. Adicionar Nós de Corredor Manualmente no Inkscape

1. Abrir `A1.svg` no Inkscape
2. Criar nova camada: "Hallway Nodes"
3. Usar ferramenta de círculo para criar nós
4. Nomear cada nó: `Node_H1_01`, `Node_H1_02`, etc.
5. Colocar nós em:
   - Intersecções de corredores
   - Próximo a cada porta
   - Próximo a cada saída
   - Curvas de corredores

### 2. Adicionar IDs às Portas

Para cada sala no SVG:
```xml
<!-- Sala 1014 com 1 porta -->
<path id="Room_1014" d="..." />
<rect id="Door_1014_1" x="..." y="..." />

<!-- Sala 2103 com 2 portas -->
<path id="Room_2103" d="..." />
<rect id="Door_2103_1" x="..." y="..." />
<rect id="Door_2103_2" x="..." y="..." />
```

## ✅ Checklist de Implementação

- [ ] Extrair elementos SVG do Building A
- [ ] Criar grafo de navegação com nós de corredor
- [ ] Implementar pathfinding A* para navegação interna
- [ ] Atualizar mapas.json com dados das salas
- [ ] Adicionar endpoint `/api/rota-interna` no backend
- [ ] Implementar visualização de caminho no SVG
- [ ] Testar navegação de sala para sala
- [ ] Adicionar suporte para múltiplos andares
- [ ] Implementar transições entre andares (escadas/elevadores)

## 🔍 Próximos Passos

1. **Executar script de extração** para mapear todas as salas do Building A
2. **Criar nós de corredor** manualmente no Inkscape ou automaticamente
3. **Gerar grafo de navegação** para cada andar
4. **Implementar pathfinding interno** no backend
5. **Testar roteamento** de uma sala para outra

---

**Nota**: Este documento fornece a base completa para implementar navegação precisa dentro dos prédios usando os SVGs existentes.
