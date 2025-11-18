# 🗺️ Implementação GeoJSON + SVG Overlays - Campus Guide

## ✅ O que foi implementado:

### 1. **Backend (API)**
- ✅ Endpoint `/api/geojson` - Retorna dados GeoJSON dos prédios
- ✅ Suporte a arquivos SVG em `/svg/`
- ✅ Função `carregar_geojson()` para ler campus.geojson
- ✅ Atualização de `/api/predios/{predio_id}` para retornar `svg_url`

### 2. **Processamento de PDFs**
- ✅ `process_pdf.py` atualizado com função `converter_pdf_para_svg()`
- ✅ Criação automática de SVG básico com imagem PNG embutida
- ✅ Elementos interativos pré-configurados (salas, entradas)
- ✅ Pasta `dados/svg/` criada automaticamente

### 3. **Frontend (Leaflet.js)**
- ✅ Função `carregarGeoJSON()` - Renderiza polígonos dos prédios
- ✅ Função `carregarSVGOverlay()` - Sobrepõe SVG sobre imagem
- ✅ Função `adicionarInteratividadeSVG()` - Torna salas clicáveis
- ✅ Eventos de hover e click nos elementos SVG
- ✅ GeoJSON com estilo personalizado (roxo/azul)

### 4. **Arquivos Criados**
```
New_Project/
├── backend/
│   ├── dados/
│   │   ├── campus.geojson        ✅ NOVO - Polígono do Prédio 1
│   │   └── svg/
│   │       └── Prédio 1 - Administração.svg  ✅ NOVO
│   └── process_pdf.py            ✅ ATUALIZADO
└── frontend/
    └── index.html                ✅ ATUALIZADO
```

---

## 🎯 Como funciona agora:

### **Fluxo de Visualização:**

1. **Ao carregar a página:**
   - Frontend chama `/api/geojson`
   - Renderiza polígono roxo do Prédio 1 no mapa
   - Polígono tem fill opacity 0.1 (transparente)

2. **Ao selecionar prédio:**
   - Frontend chama `/api/predios/{predio_id}`
   - Carrega imagem PNG como base (`imageOverlay`)
   - Carrega SVG sobre a imagem (`svgOverlay`)
   - SVG tem opacity 0.7 para ver a imagem abaixo

3. **Ao clicar em elemento SVG:**
   - JavaScript detecta clique em `sala_101` ou `entrada_principal`
   - Mostra mensagem no chat
   - Destaca elemento com fill azul por 2 segundos
   - Hover muda borda para azul

---

## 📝 Próximos Passos:

### **Passo 1: Editar campus.geojson**
Ajuste as coordenadas do polígono para corresponder à imagem:

```json
{
  "geometry": {
    "type": "Polygon",
    "coordinates": [[
      [50, 50],        // ← Ajuste para o canto superior esquerdo real
      [1141, 50],      // ← Canto superior direito
      [1141, 1634],    // ← Canto inferior direito
      [50, 1634],      // ← Canto inferior esquerdo
      [50, 50]
    ]]
  }
}
```

### **Passo 2: Adicionar mais elementos ao SVG**
Edite `dados/svg/Prédio 1 - Administração.svg`:

```xml
<!-- Adicione mais salas baseado em mapas.json -->
<rect
   id="sala_102"
   class="room"
   style="fill:#ff0000;fill-opacity:0;stroke:#0000ff;stroke-width:2;stroke-opacity:0.3"
   x="920"
   y="1056"
   width="100"
   height="80" />

<circle
   id="banheiro"
   class="facility"
   style="fill:#00ffff;fill-opacity:0.2;stroke:#00ffff;stroke-width:2"
   cx="600"
   cy="800"
   r="30" />

<!-- Corredor principal -->
<path
   id="corredor_principal"
   class="hallway"
   style="fill:none;stroke:#ffff00;stroke-width:5;stroke-opacity:0.3"
   d="M 100,500 L 1000,500 L 1000,1200" />
```

### **Passo 3: Usar Inkscape para edição visual (Opcional)**

Se tiver Inkscape instalado:
```bash
# Abrir SVG para edição
inkscape "dados/svg/Prédio 1 - Administração.svg"
```

1. Desenhe retângulos sobre as salas
2. Defina IDs únicos (Object > Object Properties)
3. Adicione classes CSS (room, entrance, hallway, etc.)
4. Salve como "Plain SVG"

---

## 🔧 Customizações Disponíveis:

### **Estilos do GeoJSON (frontend/index.html):**
```javascript
L.geoJSON(geojson, {
  style: {
    color: '#667eea',        // Cor da borda
    weight: 3,               // Espessura da borda
    fillOpacity: 0.1,        // Transparência do preenchimento
    fillColor: '#764ba2'     // Cor do preenchimento
  }
})
```

### **Opacidade do SVG Overlay:**
```javascript
svgOverlay = L.svgOverlay(svgElement, bounds, {
  interactive: true,
  opacity: 0.7  // ← Ajuste entre 0 (invisível) e 1 (opaco)
})
```

### **Comportamento de Click:**
```javascript
sala.addEventListener('click', (e) => {
  // Customizar ação ao clicar
  adicionarMensagemBot(`Sala clicada: ${salaId}`);
  
  // Mudar cor da sala
  sala.style.fill = '#667eea';
  sala.style.fillOpacity = '0.5';
});
```

---

## 🧪 Como Testar:

1. **Iniciar backend:**
```bash
cd backend
uvicorn api:app --reload
```

2. **Abrir frontend:**
```bash
cd frontend
python -m http.server 8080
```

3. **Acessar:** http://localhost:8080

4. **Verificar:**
   - ✅ Polígono roxo aparece no mapa
   - ✅ Clicar no polígono carrega a imagem
   - ✅ SVG overlay aparece sobre a imagem
   - ✅ Clicar em "sala_101" mostra mensagem no chat
   - ✅ Hover em sala muda borda para azul

---

## 🐛 Troubleshooting:

### **SVG não aparece:**
- Verifique se `dados/svg/Prédio 1 - Administração.svg` existe
- Confirme que API retorna `svg_url` em `/api/predios/prédio_1_-_administração`
- Abra console do navegador (F12) e veja erros

### **Elementos SVG não são clicáveis:**
- Certifique-se que elementos têm atributo `id`
- Verifique se seletor `[id^="sala_"]` corresponde aos IDs
- Adicione `style="pointer-events: all"` nos elementos SVG

### **Coordenadas erradas:**
- GeoJSON usa coordenadas pixel no sistema Simple CRS
- Valores devem estar entre [0, largura] e [0, altura]
- Y cresce para baixo (invertido do cartesiano)

---

## 📚 Referências Úteis:

- **Leaflet GeoJSON:** https://leafletjs.com/examples/geojson/
- **Leaflet SVG Overlay:** https://leafletjs.com/reference.html#svgoverlay
- **SVG Tutorial:** https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial
- **Inkscape:** https://inkscape.org/

---

**Status:** ✅ Implementação completa e funcional!
**Próximo:** Editar SVG com Inkscape para adicionar todas as salas do campus.
