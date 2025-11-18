# 🚀 Guia Rápido - Campus Guide com Mapa Geográfico Real

## ✅ Implementação Completa - Estilo Google Maps!

### 📦 O que está funcionando:

1. **Mapa Base Real**: OpenStreetMap (como Google Maps) centrado na universidade
2. **GeoJSON Real**: Polígonos dos prédios com coordenadas geográficas (lat/lng)
3. **Plantas Internas**: Sobreposição de imagens sobre prédios ao clicar
4. **SVG Interativo**: Elementos clicáveis nas plantas internas
5. **Navegação**: Zoom, pan, e volta ao mapa geral

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

### **Passo 3: Navegar no Mapa**

#### **Visão Geral (Mapa Geográfico):**
1. Veja todos os prédios da Fanshawe College
2. Prédios acadêmicos em roxo, outros em cinza
3. **Passe o mouse** sobre prédio → destaque
4. **Clique no prédio** → popup com informações
5. **Clique em "Ver Planta Interna"** → muda para modo interno

#### **Modo Planta Interna:**
1. Imagem PNG da planta sobreposta ao prédio
2. Marcadores dos locais (salas, entradas)
3. SVG overlay com elementos clicáveis
4. **Clique em "🗺️ Voltar ao Mapa Geral"** → volta ao mapa

---

## 🗺️ Diferenças: Antes vs Agora

| Aspecto | Antes (Pixel) | Agora (Geográfico) |
|---------|---------------|-------------------|
| **Sistema de Coordenadas** | `L.CRS.Simple` (pixel) | `L.CRS.EPSG3857` (lat/lng) |
| **Mapa Base** | Apenas imagem PNG | OpenStreetMap tiles |
| **Navegação** | Limitada à imagem | Zoom ilimitado, estilo Google |
| **Localização** | Relativa | Coordenadas reais GPS |
| **GeoJSON** | Coordenadas pixel | Coordenadas geográficas |
| **Experiência** | Mapa estático | Mapa interativo dinâmico |

---

## 📍 Coordenadas da Fanshawe College:

- **Centro**: `[43.0125, -81.2002]`
- **Zoom Inicial**: 16 (visão geral do campus)
- **Zoom Mínimo**: 14 (bairro)
- **Zoom Máximo**: 20 (detalhes internos)

---

## 🎨 Funcionalidades do Mapa:

### **1. Visão Geral:**
- ✅ Mapa base OpenStreetMap
- ✅ Polígonos GeoJSON dos prédios
- ✅ Cores diferenciadas por tipo:
  - `building=college` → Roxo (#667eea)
  - Outros → Cinza (#95a5a6)
- ✅ Hover effects (destaque ao passar mouse)
- ✅ Popups informativos com dados do prédio

### **2. Plantas Internas:**
- ✅ ImageOverlay sobreposto ao prédio
- ✅ Conversão automática pixel → lat/lng
- ✅ Marcadores de locais (salas, entradas)
- ✅ SVG overlay com elementos interativos
- ✅ Botão "Voltar ao Mapa Geral"

### **3. Rotas:**
- ✅ Cálculo de rotas entre locais
- ✅ Desenho de polyline no mapa
- ✅ Marcadores de origem (verde) e destino (vermelho)
- ✅ Suporte a coordenadas geográficas e pixel

---

## 🛠️ Arquivos Modificados:

```
frontend/index.html
├── Mudado: L.CRS.Simple → Coordenadas geográficas
├── Adicionado: L.tileLayer (OpenStreetMap)
├── Adicionado: pixelParaLatLng() - conversão de coordenadas
├── Adicionado: voltarMapaGeral() - navegação
├── Atualizado: carregarGeoJSON() - estilos e popups
└── Atualizado: carregarMapaPredio() - overlay geográfico

backend/dados/campus.geojson
└── Substituído: GeoJSON real da Fanshawe College
```

---

## 📚 Como Funciona a Conversão de Coordenadas:

### **Pixel → Lat/Lng:**
```javascript
function pixelParaLatLng(pixelX, pixelY, dimensoes, bounds) {
    // 1. Normalizar coordenadas pixel (0-1)
    const normX = pixelX / dimensoes.largura;
    const normY = pixelY / dimensoes.altura;
    
    // 2. Obter bounds geográficos do prédio
    const latMin = bounds.getSouth();
    const latMax = bounds.getNorth();
    const lngMin = bounds.getWest();
    const lngMax = bounds.getEast();
    
    // 3. Interpolar (Y invertido!)
    const lat = latMax - (normY * (latMax - latMin));
    const lng = lngMin + (normX * (lngMax - lngMin));
    
    return [lat, lng];
}
```
