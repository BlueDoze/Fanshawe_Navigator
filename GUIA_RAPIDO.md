# 🚀 Guia Rápido - Campus Guide com GeoJSON + SVG

## ✅ Implementação Completa!

### 📦 O que está funcionando:

1. **GeoJSON**: Polígonos dos prédios renderizados no mapa
2. **SVG Overlay**: Plantas interativas sobre as imagens
3. **Elementos Clicáveis**: Salas e entradas com hover effects
4. **Geração Automática**: Script Python cria elementos SVG do mapas.json

---

## 🎮 Como usar agora:

### **Passo 1: Iniciar o Backend**
```bash
cd backend
uvicorn api:app --reload
```
**URL:** http://localhost:8000

### **Passo 2: Abrir o Frontend**
```bash
cd frontend
python -m http.server 8080
```
**URL:** http://localhost:8080

### **Passo 3: Testar no Navegador**

1. Abra http://localhost:8080
2. Veja o polígono roxo do Prédio 1 no mapa
3. Selecione "Prédio 1" no dropdown
4. Veja a imagem PNG + SVG overlay
5. **Passe o mouse** sobre "Entrada Principal" ou "Sala 101"
   - Borda fica mais grossa
   - Cor fica mais intensa
   - Sombra aparece
6. **Clique** em uma sala
   - Mensagem aparece no chat
   - Sala fica destacada por 2 segundos

---

## 🛠️ Scripts Utilitários:

### **1. Gerar SVG Interativo Automaticamente**
```bash
cd backend
python gerar_svg_interativo.py
```
**O que faz:**
- Lê `mapas.json`
- Cria retângulos SVG para cada local
- Adiciona emojis baseado no tipo (🚪 entrada, 📚 sala, etc.)
- Insere estilos CSS com hover effects
- Atualiza arquivos em `dados/svg/`

### **2. Processar Novos PDFs**
```bash
cd backend
python process_pdf.py
```
**O que faz:**
- Converte PDF → PNG (para imagem de fundo)
- Converte PDF → SVG (para elementos interativos)
- Cria estrutura em `mapas.json`
- Salva em `dados/imagens/` e `dados/svg/`

---

## 📝 Adicionar Mais Locais:

### **Opção 1: Editar mapas.json manualmente**

```json
{
  "locais": [
    {
      "id": "sala_102",
      "nome": "Sala 102",
      "tipo": "sala",
      "coordenadas": {"x": 920, "y": 1056},
      "descricao": "Sala de informática"
    },
    {
      "id": "banheiro_masculino",
      "nome": "Banheiro Masculino",
      "tipo": "banheiro",
      "coordenadas": {"x": 600, "y": 800},
      "descricao": "Banheiro no primeiro andar"
    }
  ]
}
```

Depois execute:
```bash
python gerar_svg_interativo.py
```

### **Opção 2: Editar SVG diretamente no Inkscape**

1. Abra `dados/svg/Prédio 1 - Administração.svg` no Inkscape
2. Use ferramenta Retângulo (R)
3. Desenhe sobre a sala
4. Clique direito → Object Properties
5. Defina ID (ex: "sala_103")
6. Defina Class (ex: "sala")
7. Salve como "Plain SVG"

---

## 🎨 Tipos de Locais e Cores:

| Tipo | Cor | Emoji |
|------|-----|-------|
| `entrada` | Verde #28a745 | 🚪 |
| `sala` | Roxo #667eea | 📚 |
| `banheiro` | Azul #17a2b8 | 🚽 |
| `laboratorio` | Amarelo #ffc107 | 🔬 |
| `biblioteca` | Roxo escuro #6f42c1 | 📖 |
| `auditorio` | Rosa #e83e8c | 🎭 |
| `cantina` | Laranja #fd7e14 | 🍴 |
| `default` | Cinza #6c757d | 📍 |

Para adicionar novo tipo, edite `gerar_svg_interativo.py`:
```python
cores = {
    'secretaria': {'fill': '#ff6b6b', 'emoji': '📋'},
    # ...
}
```

---

## 🔧 Customizações:

### **Mudar Opacidade do SVG:**
`frontend/index.html`, linha ~405:
```javascript
svgOverlay = L.svgOverlay(svgElement, bounds, {
  interactive: true,
  opacity: 0.7  // ← 0 = invisível, 1 = opaco
})
```

### **Mudar Estilo do GeoJSON:**
`frontend/index.html`, linha ~345:
```javascript
style: {
  color: '#667eea',      // Cor da borda
  weight: 3,             // Espessura
  fillOpacity: 0.1,      // Transparência
  fillColor: '#764ba2'   // Cor interna
}
```

### **Mudar Tamanho dos Elementos SVG:**
`gerar_svg_interativo.py`, linha ~42:
```python
tamanho = 80 if local_tipo == 'entrada' else 70
```

---

## 📊 Estrutura de Arquivos Atual:

```
New_Project/
├── backend/
│   ├── api.py                    ✅ API com endpoint /api/geojson
│   ├── process_pdf.py            ✅ Converte PDF → PNG + SVG
│   ├── gerar_svg_interativo.py   ✅ NOVO - Gera elementos SVG
│   └── dados/
│       ├── mapas.json            ✅ Coordenadas dos locais
│       ├── campus.geojson        ✅ NOVO - Polígonos dos prédios
│       ├── imagens/
│       │   └── Prédio 1 - Administração.png  ✅ Imagem de fundo
│       └── svg/
│           └── Prédio 1 - Administração.svg  ✅ NOVO - Elementos interativos
└── frontend/
    └── index.html                ✅ Leaflet com GeoJSON + SVG overlay
```

---

## 🐛 Problemas Comuns:

### **SVG não aparece:**
```bash
# Verificar se SVG existe
ls backend/dados/svg/

# Verificar se API retorna svg_url
curl http://localhost:8000/api/predios/prédio_1_-_administração
```

### **Elementos não são clicáveis:**
Adicione `style="pointer-events: all"` no elemento SVG:
```xml
<rect id="sala_101" style="...; pointer-events: all" />
```

### **Coordenadas erradas:**
Use ferramenta de desenvolvedor do navegador:
1. Abra a imagem PNG
2. Clique com botão direito → Inspecionar
3. Use ferramenta de seleção (Ctrl+Shift+C)
4. Passe mouse sobre a sala
5. Anote coordenadas X, Y

---

## 🎯 Próximos Passos:

### ✅ Já Funciona:
- Visualização de GeoJSON no mapa
- SVG overlay sobre imagens
- Elementos clicáveis e com hover
- Geração automática de SVG

### 🚧 Melhorias Futuras:
- [ ] Adicionar mais prédios (processar mais PDFs)
- [ ] Criar rotas entre salas usando corredores SVG
- [ ] Integrar pathfinding A* com elementos SVG
- [ ] Adicionar diferentes andares (floor switcher)
- [ ] Exportar para coordenadas geográficas reais (lat/lng)

---

## 📚 Comandos Úteis:

```bash
# Processar novo PDF
cd backend
python process_pdf.py

# Gerar elementos SVG
python gerar_svg_interativo.py

# Iniciar backend
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Iniciar frontend
cd ../frontend
python -m http.server 8080

# Ver logs em tempo real
# Abra F12 no navegador → Console
```

---

**Status:** ✅ **PRONTO PARA TESTAR!**

Teste agora abrindo http://localhost:8080 e interagindo com o mapa! 🎉
