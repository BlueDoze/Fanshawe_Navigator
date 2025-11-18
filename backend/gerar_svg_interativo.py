"""
Script para gerar elementos SVG interativos automaticamente
baseado nas coordenadas do mapas.json
"""

import json
import os

def gerar_elementos_svg_de_mapas():
    """
    Lê mapas.json e gera elementos SVG para cada local
    """
    
    # Carregar mapas.json
    with open('dados/mapas.json', 'r', encoding='utf-8') as f:
        mapas = json.load(f)
    
    for predio in mapas['campus']['predios']:
        predio_nome = predio['nome']
        predio_id = predio['id']
        svg_path = f"dados/svg/{predio_nome}.svg"
        
        if not os.path.exists(svg_path):
            print(f"⚠ SVG não encontrado: {svg_path}")
            continue
        
        # Ler SVG existente
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        # Gerar elementos SVG para cada local
        elementos_svg = []
        
        for local in predio['locais']:
            local_id = local['id']
            local_nome = local['nome']
            local_tipo = local['tipo']
            x = local['coordenadas']['x']
            y = local['coordenadas']['y']
            
            # Definir cores e tamanhos baseado no tipo
            cores = {
                'entrada': {'fill': '#28a745', 'emoji': '🚪'},
                'sala': {'fill': '#667eea', 'emoji': '📚'},
                'banheiro': {'fill': '#17a2b8', 'emoji': '🚽'},
                'laboratorio': {'fill': '#ffc107', 'emoji': '🔬'},
                'biblioteca': {'fill': '#6f42c1', 'emoji': '📖'},
                'auditorio': {'fill': '#e83e8c', 'emoji': '🎭'},
                'cantina': {'fill': '#fd7e14', 'emoji': '🍴'},
                'default': {'fill': '#6c757d', 'emoji': '📍'}
            }
            
            cor_info = cores.get(local_tipo, cores['default'])
            cor = cor_info['fill']
            emoji = cor_info['emoji']
            
            # Tamanho baseado no tipo
            tamanho = 80 if local_tipo == 'entrada' else 70
            
            # Criar elemento SVG
            elemento = f'''
    <!-- {local_nome} -->
    <rect
       id="{local_id}"
       class="{local_tipo}"
       style="fill:{cor};fill-opacity:0.15;stroke:{cor};stroke-width:3;stroke-opacity:0.6;cursor:pointer"
       x="{x - tamanho//2}"
       y="{y - tamanho//2}"
       width="{tamanho}"
       height="{tamanho}"
       rx="5" />
    <text
       x="{x}"
       y="{y - 10}"
       font-family="Arial, sans-serif"
       font-size="18"
       text-anchor="middle"
       style="pointer-events:none"
       fill="{cor}"
       opacity="0.8">
      {emoji}
    </text>
    <text
       x="{x}"
       y="{y + 15}"
       font-family="Arial, sans-serif"
       font-size="11"
       font-weight="bold"
       text-anchor="middle"
       style="pointer-events:none"
       fill="{cor}">
      {local_nome}
    </text>
'''
            elementos_svg.append(elemento)
        
        # Inserir elementos no SVG (antes de </g>)
        elementos_completos = '\n    <!-- Elementos gerados automaticamente -->' + ''.join(elementos_svg)
        
        # Procurar tag </g> e inserir antes dela
        if '</g>' in svg_content:
            # Remove elementos antigos gerados automaticamente
            if '<!-- Elementos gerados automaticamente -->' in svg_content:
                inicio = svg_content.find('<!-- Elementos gerados automaticamente -->')
                fim = svg_content.find('</g>', inicio)
                svg_content = svg_content[:inicio] + svg_content[fim:]
            
            svg_content = svg_content.replace('</g>', elementos_completos + '\n  </g>', 1)
        
        # Adicionar estilos CSS se não existirem
        if '<style' not in svg_content:
            estilos = '''
  <!-- Estilos CSS para hover effects -->
  <style type="text/css">
    <![CDATA[
      rect[class]:hover {
        fill-opacity: 0.4 !important;
        stroke-width: 5 !important;
        filter: drop-shadow(0 0 10px currentColor);
      }
      
      .entrada:hover {
        stroke-width: 6 !important;
      }
      
      .sala:hover {
        stroke-width: 5 !important;
      }
    ]]>
  </style>
</svg>'''
            svg_content = svg_content.replace('</svg>', estilos)
        
        # Salvar SVG atualizado
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        print(f"✓ SVG atualizado: {svg_path}")
        print(f"  - Adicionados {len(elementos_svg)} elementos interativos")

if __name__ == "__main__":
    print("Gerando elementos SVG baseado em mapas.json...\n")
    gerar_elementos_svg_de_mapas()
    print("\n✓ Concluído! Os arquivos SVG foram atualizados com elementos interativos.")
    print("➜ Abra o frontend para ver os elementos clicáveis no mapa.")
