# 🎯 GUIA DE USO: Sistema de Identificação de Salas

## ✅ O Que Foi Feito

Sistema completo criado para identificar salas do Building A e traçar caminhos internos:

### 📄 Arquivos Criados

1. **`SISTEMA_IDENTIFICACAO_SALAS.md`**
   - Documentação técnica completa
   - Explica estrutura dos SVGs
   - Sistema de coordenadas
   - Padrões de ID

2. **`backend/extrair_salas_svg.py`** ✅ TESTADO
   - Extrai salas, portas, saídas e nós dos SVGs
   - Calcula centros e bounding boxes
   - Gera JSON com elementos identificados

3. **`backend/criar_grafo_navegacao.py`**
   - Cria grafo de navegação
   - Conecta nós automaticamente
   - Valida conectividade

4. **`backend/pathfinding_interno.py`**
   - Algoritmo A* para pathfinding
   - Encontra rotas entre salas
   - Testes automatizados

## 📊 Resultado do Teste

```
✅ Building A processado com sucesso!

A1: 1 sala encontrada (Room_1014)
A2: 0 salas encontradas
A3: Arquivo não existe

Sala Room_1014:
  - Centro: (543.56, 492.88) pixels
  - Dimensões: 85.19 x 70.23 pixels
```

## 🚨 Situação Atual

### ⚠️ Problema Identificado

Os SVGs do Building A têm **poucos elementos identificados com IDs**:
- ✅ Apenas **1 sala** (Room_1014) tem ID no A1
- ❌ Nenhuma porta identificada
- ❌ Nenhum nó de corredor
- ❌ Nenhuma saída/entrada marcada

### 📋 O Que Isso Significa

Para fazer o sistema de navegação funcionar completamente, você precisa:

1. **Abrir os SVGs no Inkscape**
2. **Adicionar IDs manualmente** para:
   - Todas as salas (Room_XXXX)
   - Todas as portas (Door_SALA_NUMERO)
   - Nós de corredor (Node_H1_01, Node_H1_02, etc.)
   - Saídas do prédio (Exit_Main, Exit_North, etc.)

## 🎨 Como Adicionar IDs no Inkscape

### Passo a Passo

1. **Abrir SVG no Inkscape**
   ```
   LeafletJS/LeafletJS/Floorplans/Building A/A1.svg
   ```

2. **Selecionar Elemento** (sala, porta, etc.)
   - Clique no elemento desejado

3. **Abrir Propriedades do Objeto**
   - Menu: `Object` → `Object Properties`
   - Ou: `Shift + Ctrl + O`

4. **Definir ID**
   - Campo `ID:` → Digite o ID desejado
   - Exemplos:
     - Sala: `Room_1015`
     - Porta: `Door_1015_1`
     - Nó: `Node_H1_01`
     - Saída: `Exit_Main`

5. **Salvar SVG**

### 🗺️ Estratégia de Marcação

#### 1. Marcar Salas (Prioridade ALTA)
```
Room_1001, Room_1002, Room_1003, ..., Room_1099
```

#### 2. Marcar Portas das Salas
```
Door_1001_1  (primeira porta da sala 1001)
Door_1001_2  (segunda porta da sala 1001)
Door_1002_1  (primeira porta da sala 1002)
```

#### 3. Criar Nós de Corredor

Adicione círculos pequenos nos pontos estratégicos:
- Intersecções de corredores
- Próximo a cada porta (a 20-30 pixels)
- Em curvas de corredores
- Próximo às saídas

```
Node_H1_01, Node_H1_02, Node_H1_03, ...
```

**Como criar nó:**
1. Ferramenta de círculo (F5)
2. Criar círculo pequeno (raio: 5-10 pixels)
3. Definir ID: `Node_H1_XX`
4. Opcional: tornar invisível (opacity: 0)

#### 4. Marcar Saídas/Entradas
```
Exit_Main      (saída principal)
Exit_North     (saída norte)
Entrance_West  (entrada oeste)
```

## 🔄 Fluxo Completo de Uso

### Quando os SVGs Estiverem Marcados

```bash
# 1. Extrair elementos dos SVGs
cd backend
python extrair_salas_svg.py

# 2. Criar grafos de navegação
python criar_grafo_navegacao.py

# 3. Testar pathfinding
python pathfinding_interno.py

# 4. Integrar com API (próximo passo)
```

### Resultado Esperado (com SVGs completos)

```
A1:
  Salas........: 50+
  Portas.......: 80+
  Saídas.......: 5+
  Nós Corredor.: 100+
```

## 🎯 Alternativa: Usar Sistema Existente

### Opção 1: Adaptar do LeafletJS

O projeto LeafletJS já tem um sistema similar em:
```
LeafletJS/LeafletJS/floorPlansScript.js
```

Você pode:
1. Verificar como eles identificam salas
2. Copiar a estrutura de dados
3. Adaptar para o seu sistema

### Opção 2: Sistema Simplificado

Se não quiser marcar todos os SVGs manualmente:

1. **Usar apenas coordenadas** (sem IDs)
2. **Definir pontos manualmente** no `mapas.json`
3. **Criar grafo simplificado** com locais-chave

Exemplo em `mapas.json`:
```json
{
  "id": "building_a",
  "andares": [
    {
      "numero": 1,
      "nos_navegacao": [
        {"id": "n1", "x": 400, "y": 300, "tipo": "corredor"},
        {"id": "n2", "x": 450, "y": 300, "tipo": "corredor"},
        {"id": "sala_1014", "x": 543, "y": 492, "tipo": "sala"}
      ],
      "conexoes": [
        {"de": "n1", "para": "n2"},
        {"de": "n2", "para": "sala_1014"}
      ]
    }
  ]
}
```

## 📝 Próximos Passos Recomendados

### Decisão Necessária

Você precisa escolher uma abordagem:

### ✅ Opção A: Sistema Completo (Recomendado para produção)
1. Marcar SVGs no Inkscape (Room_, Door_, Node_)
2. Executar scripts de extração
3. Gerar grafos automáticos
4. Pathfinding completo e preciso

**Vantagens:**
- ✅ Sistema robusto e escalável
- ✅ Navegação precisa
- ✅ Fácil adicionar novos prédios

**Desvantagens:**
- ⏰ Trabalho manual inicial (marcar SVGs)
- ⏰ ~2-4 horas por andar

### ✅ Opção B: Sistema Simplificado (Rápido para protótipo)
1. Definir pontos-chave manualmente no mapas.json
2. Criar grafo simples com locais principais
3. Pathfinding básico entre pontos

**Vantagens:**
- ⚡ Rápido de implementar
- ✅ Funciona para demo/protótipo

**Desvantagens:**
- ⚠️ Menos preciso
- ⚠️ Mais difícil de manter

## 🎬 Ação Imediata

**O que você gostaria de fazer?**

1. **Opção A**: Começar a marcar os SVGs no Inkscape?
   - Te oriento passo a passo
   - Crio template de IDs

2. **Opção B**: Implementar sistema simplificado?
   - Adapto o código atual
   - Uso apenas coordenadas no mapas.json

3. **Opção C**: Estudar o sistema do LeafletJS primeiro?
   - Analiso mais a fundo o código deles
   - Vejo como eles resolveram isso

---

**Responda qual opção prefere e continuamos!** 🚀
