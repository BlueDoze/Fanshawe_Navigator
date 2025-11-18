import fitz  # PyMuPDF
from PIL import Image
import json
import os
import subprocess
import sys

class ProcessadorMapas:
    def __init__(self, pasta_pdfs="pdfs_originais", pasta_saida="dados/imagens"):
        self.pasta_pdfs = pasta_pdfs
        self.pasta_saida = pasta_saida
        os.makedirs(pasta_saida, exist_ok=True)
        os.makedirs("dados/svg", exist_ok=True)
    
    def extrair_imagem_pdf(self, caminho_pdf, nome_predio):
        """
        Converte PDF em imagem PNG para usar no mapa interativo
        """
        try:
            doc = fitz.open(caminho_pdf)
            pagina = doc[0]  # Primeira página
            
            # Aumenta a resolução para melhor qualidade
            zoom = 2
            mat = fitz.Matrix(zoom, zoom)
            pix = pagina.get_pixmap(matrix=mat)
            
            # Salva como PNG
            caminho_saida = f"{self.pasta_saida}/{nome_predio}.png"
            pix.save(caminho_saida)
            
            print(f"✓ Imagem extraída: {caminho_saida}")
            
            # Retorna dimensões para configurar coordenadas
            return {
                "nome": nome_predio,
                "imagem": caminho_saida,
                "largura": pix.width,
                "altura": pix.height
            }
        
        except Exception as e:
            print(f"✗ Erro ao processar {caminho_pdf}: {e}")
            return None
    
    def converter_pdf_para_svg(self, caminho_pdf, nome_predio):
        """
        Converte PDF em SVG para criar plantas interativas
        Requer: pip install pdf2svg ou Inkscape instalado
        """
        try:
            caminho_saida = f"dados/svg/{nome_predio}.svg"
            
            # Tenta usar Inkscape (mais comum no Windows)
            inkscape_paths = [
                r"C:\Program Files\Inkscape\bin\inkscape.exe",
                r"C:\Program Files (x86)\Inkscape\bin\inkscape.exe",
                "inkscape"  # Se estiver no PATH
            ]
            
            for inkscape in inkscape_paths:
                try:
                    subprocess.run([
                        inkscape,
                        caminho_pdf,
                        "--export-type=svg",
                        f"--export-filename={caminho_saida}"
                    ], check=True, capture_output=True)
                    print(f"✓ SVG criado: {caminho_saida}")
                    return caminho_saida
                except (FileNotFoundError, subprocess.CalledProcessError):
                    continue
            
            # Se Inkscape não estiver disponível, cria SVG básico com imagem embutida
            print(f"⚠ Inkscape não encontrado. Criando SVG básico com imagem PNG...")
            return self._criar_svg_basico(caminho_pdf, nome_predio)
            
        except Exception as e:
            print(f"✗ Erro ao converter para SVG: {e}")
            return None
    
    def _criar_svg_basico(self, caminho_pdf, nome_predio):
        """
        Cria um SVG básico com a imagem PNG embutida
        """
        try:
            # Primeiro extrai a imagem
            info = self.extrair_imagem_pdf(caminho_pdf, nome_predio)
            if not info:
                return None
            
            # Cria SVG básico
            caminho_saida = f"dados/svg/{nome_predio}.svg"
            svg_content = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   width="{info['largura']}px"
   height="{info['altura']}px"
   viewBox="0 0 {info['largura']} {info['altura']}"
   version="1.1"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:xlink="http://www.w3.org/1999/xlink">
  <defs id="defs1" />
  <g id="layer1">
    <!-- Imagem de fundo -->
    <image
       width="{info['largura']}"
       height="{info['altura']}"
       preserveAspectRatio="none"
       xlink:href="../imagens/{nome_predio}.png"
       id="background-image"
       x="0"
       y="0" />
    
    <!-- Elementos interativos - adicione aqui -->
    <!-- Exemplo de sala clicável -->
    <rect
       id="sala_101"
       class="room"
       style="fill:#ff0000;fill-opacity:0;stroke:#0000ff;stroke-width:2;stroke-opacity:0.3"
       x="825"
       y="1056"
       width="100"
       height="80" />
    
    <rect
       id="entrada_principal"
       class="entrance"
       style="fill:#00ff00;fill-opacity:0;stroke:#00ff00;stroke-width:3;stroke-opacity:0.3"
       x="832"
       y="738"
       width="80"
       height="60" />
  </g>
</svg>'''
            
            with open(caminho_saida, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            print(f"✓ SVG básico criado: {caminho_saida}")
            print(f"➜ Edite o SVG para adicionar mais elementos interativos (salas, portas, etc.)")
            return caminho_saida
            
        except Exception as e:
            print(f"✗ Erro ao criar SVG básico: {e}")
            return None
    
    def criar_estrutura_dados(self, info_predios):
        """
        Cria arquivo JSON com estrutura dos prédios
        Você vai preencher manualmente as coordenadas depois
        """
        estrutura = {
            "campus": {
                "nome": "Minha Universidade",
                "predios": []
            }
        }
        
        for predio in info_predios:
            estrutura["campus"]["predios"].append({
                "id": predio["nome"].lower().replace(" ", "_"),
                "nome": predio["nome"],
                "imagem": predio["imagem"],
                "dimensoes": {
                    "largura": predio["largura"],
                    "altura": predio["altura"]
                },
                "locais": [
                    # EXEMPLO - Você vai adicionar os locais reais depois
                    {
                        "id": "entrada_principal",
                        "nome": "Entrada Principal",
                        "tipo": "entrada",
                        "coordenadas": {"x": 100, "y": 50},  # pixels na imagem
                        "descricao": "Porta principal do prédio"
                    },
                    {
                        "id": "sala_101",
                        "nome": "Sala 101",
                        "tipo": "sala",
                        "coordenadas": {"x": 200, "y": 150},
                        "descricao": "Sala de aula no primeiro andar"
                    }
                    # Adicione mais locais aqui
                ]
            })
        
        # Salva JSON
        with open("dados/mapas.json", "w", encoding="utf-8") as f:
            json.dump(estrutura, f, indent=2, ensure_ascii=False)
        
        print("✓ Arquivo mapas.json criado!")
        return estrutura


# COMO USAR:
if __name__ == "__main__":
    processador = ProcessadorMapas()
    
    # Lista os PDFs que você tem
    pdfs = [
        {"arquivo": "pdfs_originais/predio_1.pdf", "nome": "Prédio 1 - Administração"}
        # Adicione mais prédios conforme necessário
    ]
    
    # Processa todos os PDFs
    info_predios = []
    for pdf in pdfs:
        if os.path.exists(pdf["arquivo"]):
            info = processador.extrair_imagem_pdf(pdf["arquivo"], pdf["nome"])
            if info:
                info_predios.append(info)
                # Também criar SVG
                svg_path = processador.converter_pdf_para_svg(pdf["arquivo"], pdf["nome"])
                if svg_path:
                    info['svg'] = svg_path
        else:
            print(f"⚠ Arquivo não encontrado: {pdf['arquivo']}")
    
    # Cria estrutura de dados
    if info_predios:
        processador.criar_estrutura_dados(info_predios)
        print(f"\n✓ Processados {len(info_predios)} prédios!")
        print("➜ Próximo passo: edite dados/mapas.json e adicione as coordenadas dos locais")
        print("➜ Edite os arquivos SVG em dados/svg/ para adicionar elementos interativos")
    else:
        print("\n✗ Nenhum PDF foi processado. Verifique os caminhos dos arquivos.")