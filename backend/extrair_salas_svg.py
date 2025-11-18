"""
Script para extrair elementos identificáveis de arquivos SVG
Identifica salas, portas, saídas e nós de corredor
"""

import xml.etree.ElementTree as ET
import json
import os
import re
from pathlib import Path

def extrair_bbox_de_path(path_data):
    """
    Extrai coordenadas aproximadas de um elemento path SVG
    Parse simplificado - apenas pega as coordenadas
    """
    # Regex para encontrar números em formato M x,y ou L x,y
    coords = re.findall(r'[\d.]+', path_data)
    
    if len(coords) < 4:
        return None
    
    # Converter para float
    nums = [float(c) for c in coords]
    
    # Pegar min/max para X e Y
    xs = nums[0::2]  # índices pares (X)
    ys = nums[1::2]  # índices ímpares (Y)
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    return {
        'x': min_x,
        'y': min_y,
        'width': max_x - min_x,
        'height': max_y - min_y
    }

def extrair_bbox_de_elemento(elemento):
    """
    Extrai bounding box do elemento SVG
    """
    tag = elemento.tag.split('}')[-1] if '}' in elemento.tag else elemento.tag
    
    # Para elementos path
    if tag == 'path':
        path_data = elemento.get('d')
        if path_data:
            return extrair_bbox_de_path(path_data)
    
    # Para elementos rect
    elif tag == 'rect':
        x = elemento.get('x')
        y = elemento.get('y')
        w = elemento.get('width')
        h = elemento.get('height')
        
        if all([x, y, w, h]):
            return {
                'x': float(x),
                'y': float(y),
                'width': float(w),
                'height': float(h)
            }
    
    # Para elementos circle
    elif tag == 'circle':
        cx = elemento.get('cx')
        cy = elemento.get('cy')
        r = elemento.get('r')
        
        if all([cx, cy, r]):
            r_val = float(r)
            return {
                'x': float(cx) - r_val,
                'y': float(cy) - r_val,
                'width': r_val * 2,
                'height': r_val * 2
            }
    
    # Para elementos polygon
    elif tag == 'polygon':
        points = elemento.get('points')
        if points:
            coords = re.findall(r'[\d.]+', points)
            if len(coords) >= 4:
                nums = [float(c) for c in coords]
                xs = nums[0::2]
                ys = nums[1::2]
                
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                
                return {
                    'x': min_x,
                    'y': min_y,
                    'width': max_x - min_x,
                    'height': max_y - min_y
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

def extrair_elementos_svg(caminho_svg):
    """
    Extrai todos os elementos identificáveis do SVG
    """
    print(f"\n📖 Lendo {caminho_svg}...")
    
    tree = ET.parse(caminho_svg)
    root = tree.getroot()
    
    elementos = {
        'salas': [],
        'portas': [],
        'saidas': [],
        'nos_corredor': [],
        'outros': []
    }
    
    # Buscar todos os elementos com ID
    elementos_processados = 0
    
    for elem in root.iter():
        elem_id = elem.get('id')
        if elem_id:
            elementos_processados += 1
            
            # Salas (Room_XXXX)
            if elem_id.startswith('Room_'):
                bbox = extrair_bbox_de_elemento(elem)
                centro = calcular_centro(bbox)
                
                elementos['salas'].append({
                    'id': elem_id,
                    'numero': elem_id.replace('Room_', ''),
                    'bbox': bbox,
                    'centro': centro,
                    'tipo_elemento': elem.tag.split('}')[-1]
                })
            
            # Portas (Door_SALA_NUMERO)
            elif elem_id.startswith('Door_'):
                bbox = extrair_bbox_de_elemento(elem)
                centro = calcular_centro(bbox)
                
                # Extrair sala relacionada
                partes = elem_id.split('_')
                sala_relacionada = partes[1] if len(partes) >= 2 else None
                
                elementos['portas'].append({
                    'id': elem_id,
                    'sala_relacionada': sala_relacionada,
                    'bbox': bbox,
                    'centro': centro,
                    'tipo_elemento': elem.tag.split('}')[-1]
                })
            
            # Saídas/Entradas (Exit_, Entrance_)
            elif elem_id.startswith('Exit_') or elem_id.startswith('Entrance_'):
                bbox = extrair_bbox_de_elemento(elem)
                centro = calcular_centro(bbox)
                
                elementos['saidas'].append({
                    'id': elem_id,
                    'tipo': 'saida' if elem_id.startswith('Exit_') else 'entrada',
                    'bbox': bbox,
                    'centro': centro,
                    'tipo_elemento': elem.tag.split('}')[-1]
                })
            
            # Nós de corredor (Node_)
            elif elem_id.startswith('Node_'):
                tag = elem.tag.split('}')[-1]
                
                # Para círculos
                if tag == 'circle':
                    cx = elem.get('cx')
                    cy = elem.get('cy')
                    if cx and cy:
                        elementos['nos_corredor'].append({
                            'id': elem_id,
                            'x': float(cx),
                            'y': float(cy),
                            'tipo_elemento': 'circle'
                        })
                else:
                    # Para outros tipos, usar centro do bbox
                    bbox = extrair_bbox_de_elemento(elem)
                    centro = calcular_centro(bbox)
                    if centro:
                        elementos['nos_corredor'].append({
                            'id': elem_id,
                            'x': centro['x'],
                            'y': centro['y'],
                            'tipo_elemento': tag
                        })
            
            # Outros elementos interessantes
            elif any(palavra in elem_id.lower() for palavra in ['hallway', 'corridor', 'stair', 'elevator']):
                bbox = extrair_bbox_de_elemento(elem)
                centro = calcular_centro(bbox)
                
                elementos['outros'].append({
                    'id': elem_id,
                    'bbox': bbox,
                    'centro': centro,
                    'tipo_elemento': elem.tag.split('}')[-1]
                })
    
    print(f"   ✓ {elementos_processados} elementos com ID processados")
    print(f"   ✓ {len(elementos['salas'])} salas encontradas")
    print(f"   ✓ {len(elementos['portas'])} portas encontradas")
    print(f"   ✓ {len(elementos['saidas'])} saídas encontradas")
    print(f"   ✓ {len(elementos['nos_corredor'])} nós de corredor encontrados")
    print(f"   ✓ {len(elementos['outros'])} outros elementos encontrados")
    
    return elementos

def processar_building_a():
    """
    Processa todos os andares do Building A
    """
    print("🏢 Processando Building A...")
    
    # Caminho base para os SVGs
    base_path = Path(__file__).parent.parent.parent / 'LeafletJS' / 'LeafletJS' / 'Floorplans' / 'Building A'
    
    # Criar diretório de saída
    output_dir = Path(__file__).parent / 'dados' / 'building_elements'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    resultados = {}
    
    # Processar cada andar
    for andar in ['A1', 'A2', 'A3']:
        svg_path = base_path / f'{andar}.svg'
        
        if svg_path.exists():
            elementos = extrair_elementos_svg(str(svg_path))
            
            # Salvar JSON
            output_path = output_dir / f'building_a_{andar.lower()}_elementos.json'
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(elementos, f, indent=2, ensure_ascii=False)
            
            print(f"   💾 Salvo em: {output_path}")
            
            resultados[andar] = {
                'elementos': elementos,
                'arquivo': str(output_path)
            }
        else:
            print(f"   ⚠️  Arquivo não encontrado: {svg_path}")
    
    # Criar resumo geral
    resumo_path = output_dir / 'building_a_resumo.json'
    resumo = {
        'predio': 'Building A',
        'andares_processados': list(resultados.keys()),
        'estatisticas': {
            andar: {
                'salas': len(dados['elementos']['salas']),
                'portas': len(dados['elementos']['portas']),
                'saidas': len(dados['elementos']['saidas']),
                'nos_corredor': len(dados['elementos']['nos_corredor'])
            }
            for andar, dados in resultados.items()
        },
        'arquivos_gerados': [dados['arquivo'] for dados in resultados.values()]
    }
    
    with open(resumo_path, 'w', encoding='utf-8') as f:
        json.dump(resumo, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Resumo geral salvo em: {resumo_path}")
    print("\n✅ Processamento completo!")
    
    return resumo

def listar_todos_ids(caminho_svg, mostrar_primeiros=20):
    """
    Lista todos os IDs encontrados no SVG (útil para debug)
    """
    tree = ET.parse(caminho_svg)
    root = tree.getroot()
    
    ids = []
    for elem in root.iter():
        elem_id = elem.get('id')
        if elem_id:
            tag = elem.tag.split('}')[-1]
            ids.append({'id': elem_id, 'tag': tag})
    
    print(f"\n📋 Total de IDs encontrados: {len(ids)}")
    print(f"\n📝 Primeiros {mostrar_primeiros} IDs:")
    for item in ids[:mostrar_primeiros]:
        print(f"   - {item['id']} ({item['tag']})")
    
    return ids

if __name__ == '__main__':
    # Executar processamento
    resumo = processar_building_a()
    
    print("\n" + "="*60)
    print("📈 ESTATÍSTICAS GERAIS")
    print("="*60)
    
    for andar, stats in resumo['estatisticas'].items():
        print(f"\n{andar}:")
        print(f"  Salas........: {stats['salas']}")
        print(f"  Portas.......: {stats['portas']}")
        print(f"  Saídas.......: {stats['saidas']}")
        print(f"  Nós Corredor.: {stats['nos_corredor']}")
