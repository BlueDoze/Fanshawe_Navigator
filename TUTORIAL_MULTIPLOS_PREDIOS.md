# 📘 Tutorial: Adicionar Mais Prédios ao Campus Guide

## 🎯 Objetivo
Adicionar novos prédios ao sistema com GeoJSON, imagens e SVG interativos.

---

## 📝 Passo a Passo Completo:

### **Passo 1: Adicionar PDF do Novo Prédio**

Coloque o arquivo PDF em `backend/pdfs_originais/`:
```
backend/
└── pdfs_originais/
    ├── predio_1.pdf  ✅ Já existe
    ├── predio_2.pdf  ← NOVO
    └── predio_3.pdf  ← NOVO
```

---

### **Passo 2: Atualizar process_pdf.py**

Edite `backend/process_pdf.py`, seção `if __name__ == "__main__":`:

```python
# Lista os PDFs que você tem
pdfs = [
    {"arquivo": "pdfs_originais/predio_1.pdf", "nome": "Prédio 1 - Administração"},
    {"arquivo": "pdfs_originais/predio_2.pdf", "nome": "Prédio 2 - Laboratórios"},  # ← NOVO
    {"arquivo": "pdfs_originais/predio_3.pdf", "nome": "Prédio 3 - Biblioteca"},    # ← NOVO
]
```

Execute:
```bash
cd backend
python process_pdf.py
```

**Resultado:**
```
✓ Imagem extraída: dados/imagens/Prédio 2 - Laboratórios.png
✓ SVG básico criado: dados/svg/Prédio 2 - Laboratórios.svg
✓ Imagem extraída: dados/imagens/Prédio 3 - Biblioteca.png
✓ SVG básico criado: dados/svg/Prédio 3 - Biblioteca.svg
```

---

### **Passo 3: Adicionar Coordenadas em mapas.json**

O script criou estrutura básica. Agora edite `backend/dados/mapas.json`:

```json
{
  "campus": {
    "nome": "Minha Universidade",
    "predios": [
      {
        "id": "prédio_1_-_administração",
        "nome": "Prédio 1 - Administração",
        "imagem": "Prédio 1 - Administração.png",
        "dimensoes": {"largura": 1191, "altura": 1684},
        "locais": [
          {
            "id": "entrada_principal",
            "nome": "Entrada Principal",
            "tipo": "entrada",
            "coordenadas": {"x": 832, "y": 738}
          },
          {
            "id": "sala_101",
            "nome": "Sala 101",
            "tipo": "sala",
            "coordenadas": {"x": 825, "y": 1056}
          }
        ]
      },
      {
        "id": "prédio_2_-_laboratórios",
        "nome": "Prédio 2 - Laboratórios",
        "imagem": "Prédio 2 - Laboratórios.png",
        "dimensoes": {"largura": 1000, "altura": 1500},
        "locais": [
          {
            "id": "entrada_lab",
            "nome": "Entrada Principal",
            "tipo": "entrada",
            "coordenadas": {"x": 500, "y": 200}
          },
          {
            "id": "lab_quimica",
            "nome": "Laboratório de Química",
            "tipo": "laboratorio",
            "coordenadas": {"x": 300, "y": 600}
          },
          {
            "id": "lab_biologia",
            "nome": "Laboratório de Biologia",
            "tipo": "laboratorio",
            "coordenadas": {"x": 700, "y": 600}
          }
        ]
      }
    ]
  }
}
```

---

### **Passo 4: Atualizar campus.geojson**

Adicione polígonos para os novos prédios em `backend/dados/campus.geojson`:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "predio_id": "prédio_1_-_administração",
        "nome": "Prédio 1 - Administração",
        "descricao": "Prédio administrativo principal",
        "andares": 1
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [50, 50],
          [1141, 50],
          [1141, 1634],
          [50, 1634],
          [50, 50]
        ]]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "predio_id": "prédio_2_-_laboratórios",
        "nome": "Prédio 2 - Laboratórios",
        "descricao": "Prédio de laboratórios científicos",
        "andares": 2
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [1200, 50],
          [2200, 50],
          [2200, 1550],
          [1200, 1550],
          [1200, 50]
        ]]
      }
    }
  ]
}
```

**Como calcular coordenadas do polígono:**
- Use as dimensões do prédio
- Posicione lado a lado ou em grid
- Deixe espaço entre prédios (~50px)

Exemplo:
```
Prédio 1: largura=1191, altura=1684
  → Polígono: [50, 50] até [1141, 1634]

Prédio 2: largura=1000, altura=1500
  → Começa após Prédio 1 (x=1191 + 50 = 1241)
  → Polígono: [1241, 50] até [2241, 1550]
```

---

### **Passo 5: Gerar Elementos SVG**

Execute o script automático:
```bash
cd backend
python gerar_svg_interativo.py
```

**Saída:**
```
✓ SVG atualizado: dados/svg/Prédio 1 - Administração.svg
  - Adicionados 2 elementos interativos
✓ SVG atualizado: dados/svg/Prédio 2 - Laboratórios.svg
  - Adicionados 3 elementos interativos
```

---

### **Passo 6: Testar no Frontend**

1. **Reinicie o backend:**
```bash
cd backend
uvicorn api:app --reload
```

2. **Abra o frontend:**
```bash
cd frontend
python -m http.server 8080
```

3. **Teste:**
   - ✅ Deve ver 2 polígonos no mapa (Prédio 1 e Prédio 2)
   - ✅ Dropdown deve listar 2 prédios
   - ✅ Clicar em cada polígono carrega seu mapa
   - ✅ Elementos SVG aparecem sobre a imagem

---

## 🎨 Organizar Prédios em Grid:

### **Layout Sugerido:**

```
+---------------+  +---------------+  +---------------+
|   Prédio 1    |  |   Prédio 2    |  |   Prédio 3    |
|  Adm (1191x   |  |  Labs (1000x  |  |  Bib (900x    |
|      1684)    |  |      1500)    |  |     1200)     |
+---------------+  +---------------+  +---------------+
     0-1191           1241-2241          2291-3191

+---------------+  +---------------+
|   Prédio 4    |  |   Prédio 5    |
|  (1100x1600)  |  |  (1050x1400)  |
+---------------+  +---------------+
  0-1100, y:1734    1150-2200, y:1734
```

### **Código GeoJSON para Grid:**

```json
{
  "features": [
    {
      "properties": {"predio_id": "prédio_1", "nome": "Prédio 1"},
      "geometry": {
        "coordinates": [[
          [50, 50], [1191, 50], [1191, 1684], [50, 1684], [50, 50]
        ]]
      }
    },
    {
      "properties": {"predio_id": "prédio_2", "nome": "Prédio 2"},
      "geometry": {
        "coordinates": [[
          [1241, 50], [2241, 50], [2241, 1550], [1241, 1550], [1241, 50]
        ]]
      }
    },
    {
      "properties": {"predio_id": "prédio_3", "nome": "Prédio 3"},
      "geometry": {
        "coordinates": [[
          [2291, 50], [3191, 50], [3191, 1250], [2291, 1250], [2291, 50]
        ]]
      }
    },
    {
      "properties": {"predio_id": "prédio_4", "nome": "Prédio 4"},
      "geometry": {
        "coordinates": [[
          [50, 1734], [1150, 1734], [1150, 3334], [50, 3334], [50, 1734]
        ]]
      }
    },
    {
      "properties": {"predio_id": "prédio_5", "nome": "Prédio 5"},
      "geometry": {
        "coordinates": [[
          [1200, 1734], [2250, 1734], [2250, 3134], [1200, 3134], [1200, 1734]
        ]]
      }
    }
  ]
}
```

---

## 🔧 Automatizar Posicionamento:

Crie script `backend/gerar_geojson_grid.py`:

```python
import json

def gerar_grid_predios(predios_info, espacamento=50):
    """
    Gera GeoJSON com prédios em grid automático
    
    predios_info = [
        {"id": "prédio_1", "nome": "Prédio 1", "largura": 1191, "altura": 1684},
        {"id": "prédio_2", "nome": "Prédio 2", "largura": 1000, "altura": 1500},
    ]
    """
    
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    x_atual = espacamento
    y_atual = espacamento
    max_altura_linha = 0
    largura_total = 0
    predios_por_linha = 3  # Ajuste conforme necessário
    
    for idx, predio in enumerate(predios_info):
        # Nova linha a cada N prédios
        if idx > 0 and idx % predios_por_linha == 0:
            x_atual = espacamento
            y_atual += max_altura_linha + espacamento
            max_altura_linha = 0
        
        # Criar polígono
        x1 = x_atual
        y1 = y_atual
        x2 = x_atual + predio['largura']
        y2 = y_atual + predio['altura']
        
        feature = {
            "type": "Feature",
            "properties": {
                "predio_id": predio['id'],
                "nome": predio['nome'],
                "descricao": predio.get('descricao', ''),
                "andares": predio.get('andares', 1)
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [x1, y1],
                    [x2, y1],
                    [x2, y2],
                    [x1, y2],
                    [x1, y1]
                ]]
            }
        }
        
        geojson['features'].append(feature)
        
        # Atualizar posição
        x_atual += predio['largura'] + espacamento
        max_altura_linha = max(max_altura_linha, predio['altura'])
    
    return geojson

# Exemplo de uso
predios = [
    {"id": "prédio_1", "nome": "Prédio 1 - Administração", "largura": 1191, "altura": 1684},
    {"id": "prédio_2", "nome": "Prédio 2 - Laboratórios", "largura": 1000, "altura": 1500},
    {"id": "prédio_3", "nome": "Prédio 3 - Biblioteca", "largura": 900, "altura": 1200},
]

geojson = gerar_grid_predios(predios)

with open('dados/campus.geojson', 'w', encoding='utf-8') as f:
    json.dump(geojson, f, indent=2, ensure_ascii=False)

print("✓ GeoJSON gerado com sucesso!")
```

Execute:
```bash
python gerar_geojson_grid.py
```

---

## ✅ Checklist Completo:

- [ ] PDF do prédio em `pdfs_originais/`
- [ ] Executar `process_pdf.py`
- [ ] Verificar PNG em `dados/imagens/`
- [ ] Verificar SVG em `dados/svg/`
- [ ] Adicionar coordenadas em `mapas.json`
- [ ] Adicionar polígono em `campus.geojson`
- [ ] Executar `gerar_svg_interativo.py`
- [ ] Reiniciar backend
- [ ] Testar no navegador

---

## 🎯 Resultado Final:

Ao abrir http://localhost:8080 você deve ver:

1. **Visão Geral:**
   - Todos os prédios como polígonos coloridos
   - Organizados em grid

2. **Ao Selecionar Prédio:**
   - Imagem PNG do prédio
   - SVG overlay com elementos interativos
   - Marcadores dos locais

3. **Ao Clicar em Sala:**
   - Mensagem no chat
   - Highlight temporário
   - Informações do local

---

**Pronto!** Agora você pode adicionar quantos prédios quiser seguindo esse processo. 🎉
