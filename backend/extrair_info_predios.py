import fitz  # PyMuPDF
import json
import os
import re
from pathlib import Path

class ExtratorInfoPredios:
    def __init__(self, pasta_maps="../maps", pasta_saida="dados"):
        self.pasta_maps = pasta_maps
        self.pasta_saida = pasta_saida
        os.makedirs(pasta_saida, exist_ok=True)
    
    def extrair_texto_pdf(self, caminho_pdf):
        """Extrai todo o texto do PDF"""
        try:
            doc = fitz.open(caminho_pdf)
            texto_completo = ""
            
            for pagina_num in range(len(doc)):
                pagina = doc[pagina_num]
                texto_completo += f"\n--- Página {pagina_num + 1} ---\n"
                texto_completo += pagina.get_text()
            
            doc.close()
            return texto_completo
        except Exception as e:
            print(f"Erro ao extrair texto de {caminho_pdf}: {e}")
            return ""
    
    def identificar_salas(self, texto):
        """Identifica salas no texto usando regex"""
        salas = []
        
        # Padrões comuns de salas
        padroes = [
            r'(?:Room|Sala|Office)\s*[:#]?\s*([A-Z0-9\-]+)',
            r'\b([A-Z]\d{3,4}[A-Z]?)\b',  # Ex: A1234, B205A
            r'(?:Lab|Laboratory|Laboratório)\s*[:#]?\s*([A-Z0-9\-]+)',
            r'(?:Classroom|Sala de Aula)\s*[:#]?\s*([A-Z0-9\-]+)',
        ]
        
        for padrao in padroes:
            matches = re.findall(padrao, texto, re.IGNORECASE)
            salas.extend(matches)
        
        # Remover duplicatas e limpar
        salas = list(set([s.strip().upper() for s in salas if s.strip()]))
        return sorted(salas)
    
    def identificar_facilidades(self, texto):
        """Identifica facilidades no prédio"""
        texto_lower = texto.lower()
        facilidades = []
        
        facilidades_map = {
            'Cafeteria': ['cafeteria', 'cafe', 'food court', 'refeitório'],
            'Biblioteca': ['library', 'biblioteca'],
            'Laboratório': ['lab', 'laboratory', 'laboratório'],
            'Auditório': ['auditorium', 'auditório', 'theater', 'theatre'],
            'Ginásio': ['gym', 'gymnasium', 'fitness', 'ginásio'],
            'Banheiro': ['washroom', 'restroom', 'bathroom', 'banheiro'],
            'Elevador': ['elevator', 'elevador', 'lift'],
            'Escadas': ['stairs', 'stairway', 'escada'],
            'Escritórios': ['office', 'escritório'],
            'Sala de Computadores': ['computer lab', 'computer room', 'sala de computadores'],
            'Salas de Aula': ['classroom', 'sala de aula'],
            'Recepção': ['reception', 'front desk', 'recepção'],
        }
        
        for facilidade, keywords in facilidades_map.items():
            if any(keyword in texto_lower for keyword in keywords):
                facilidades.append(facilidade)
        
        return facilidades
    
    def identificar_andares(self, texto):
        """Identifica número de andares"""
        andares = set()
        
        # Padrões para identificar andares
        padroes = [
            r'(?:Floor|Andar|Level)\s*[:#]?\s*(\d+)',
            r'\b([1-9])[º°]?\s*(?:floor|andar)\b',
            r'\b(?:Ground|Main|First|Second|Third|Fourth|Fifth)\s*Floor\b'
        ]
        
        for padrao in padroes:
            matches = re.findall(padrao, texto, re.IGNORECASE)
            andares.update(matches)
        
        # Mapear andares por palavra
        mapa_andares = {
            'ground': '0', 'main': '1', 'first': '1', 'second': '2',
            'third': '3', 'fourth': '4', 'fifth': '5'
        }
        
        texto_lower = texto.lower()
        for palavra, numero in mapa_andares.items():
            if palavra in texto_lower:
                andares.add(numero)
        
        return sorted([int(a) if a.isdigit() else 0 for a in andares])
    
    def processar_predio(self, caminho_pdf, nome_predio):
        """Processa um PDF e extrai todas as informações"""
        print(f"\n📄 Processando: {nome_predio}")
        
        texto = self.extrair_texto_pdf(caminho_pdf)
        
        if not texto:
            return None
        
        info = {
            "nome": nome_predio,
            "ref": nome_predio.split('_')[0],  # Ex: "A_Building" -> "A"
            "salas": self.identificar_salas(texto),
            "facilidades": self.identificar_facilidades(texto),
            "andares": self.identificar_andares(texto),
            "texto_completo": texto[:500] + "..." if len(texto) > 500 else texto  # Preview
        }
        
        print(f"  ✓ Salas encontradas: {len(info['salas'])}")
        print(f"  ✓ Facilidades: {', '.join(info['facilidades']) if info['facilidades'] else 'Nenhuma identificada'}")
        print(f"  ✓ Andares: {info['andares'] if info['andares'] else 'Não identificado'}")
        
        return info
    
    def processar_todos_predios(self):
        """Processa todos os PDFs na pasta maps"""
        print("🏢 Iniciando extração de informações dos prédios...")
        
        pasta_maps = Path(self.pasta_maps)
        pdfs = list(pasta_maps.glob("*.pdf"))
        
        if not pdfs:
            print(f"❌ Nenhum PDF encontrado em {pasta_maps}")
            return
        
        print(f"📚 Encontrados {len(pdfs)} PDFs")
        
        predios_info = {}
        
        for pdf_path in pdfs:
            nome_predio = pdf_path.stem  # Nome sem extensão
            info = self.processar_predio(str(pdf_path), nome_predio)
            
            if info:
                ref = info['ref']
                predios_info[ref] = info
        
        # Salvar em JSON
        arquivo_saida = os.path.join(self.pasta_saida, "predios_detalhes.json")
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(predios_info, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Informações salvas em: {arquivo_saida}")
        print(f"📊 Total de prédios processados: {len(predios_info)}")
        
        return predios_info

if __name__ == "__main__":
    extrator = ExtratorInfoPredios()
    extrator.processar_todos_predios()
