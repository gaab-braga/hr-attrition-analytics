# 🎯 PEOPLE ANALYTICS & TALENT INTELLIGENCE DASHBOARD
## Sistema Completo de Análise de Performance e Retenção de Talentos
### 📌 Projeto desenvolvido para entrevista na BB Previdência

---

## 🏢 SOBRE A BB PREVIDÊNCIA (Contexto para Entrevista)

A **BB Previdência** é uma **Entidade Fechada de Previdência Complementar (EFPC)**, sem fins lucrativos, vinculada ao **Banco do Brasil**. Diferente da Previ (fundo de pensão dos funcionários do BB), a BB Previdência administra planos de previdência complementar para:

- **Empresas privadas**
- **Sociedades de economia mista**
- **Empresas públicas**
- **Cooperativas, fundações e sindicatos**
- **Entidades de classe**

### Números da BB Previdência (Referência 2016):
| Indicador | Valor |
|-----------|-------|
| Participantes Ativos | +107.000 |
| Assistidos | 2.504 |
| Pensionistas | 198 |
| Planos de Benefícios | 46 |
| Patrocinadores | 55 |
| Instituidores | 2 |
| Recursos Administrados | ~R$ 5 bilhões |

### Valores do Grupo BB relevantes para People Analytics:
- **Sustentabilidade:** BB foi eleito instituição financeira mais sustentável do mundo (2019)
- **Governança Corporativa:** Alto padrão regulatório (PREVIC)
- **Foco em longo prazo:** Natureza previdenciária exige visão de retenção de talentos
- **Ambiente regulado:** Compliance e gestão de riscos são prioridades

### Como conectar o projeto à BB Previdência:
1. **Retenção de talentos** é crítico em EFPC (conhecimento especializado, certificações)
2. **Custo de turnover** alto em ambiente regulado (treinamento regulatório)
3. **Longevidade dos funcionários** alinha com a missão previdenciária
4. **Governança de pessoas** como pilar de sustentabilidade ESG

---

**Contexto do Dashboard:** Aja como um Head de People Analytics & Strategy com expertise em Data Science aplicada a RH. Crie um sistema completo de análise de performance e retenção de talentos (Dashboard) usando o arquivo CSV (IBM HR Analytics - WA_Fn-UseC_-HR-Employee-Attrition.csv).

Este projeto demonstra capacidade analítica para apoiar decisões estratégicas de gestão de pessoas em uma entidade como a BB Previdência.

Siga rigorosamente as instruções abaixo e produza um dashboard totalmente funcional, focado em Business Impact, organizado e pronto para apresentação executiva.

---

## 📊 PROMPT 1 – CONSTRUÇÃO DO DASHBOARD

### 1. BASE DE DADOS E ENGENHARIA DE ATRIBUTOS (Feature Engineering)

Use o CSV enviado contendo os seguintes campos:
- **Demográficos:** Age, Gender, MaritalStatus, Education, EducationField
- **Organizacionais:** Department, JobRole, JobLevel, YearsAtCompany, YearsInCurrentRole
- **Performance:** PerformanceRating, JobInvolvement, TrainingTimesLastYear
- **Compensação:** MonthlyIncome, DailyRate, HourlyRate, MonthlyRate, PercentSalaryHike, StockOptionLevel
- **Satisfação:** EnvironmentSatisfaction, JobSatisfaction, RelationshipSatisfaction, WorkLifeBalance
- **Carreira:** NumCompaniesWorked, TotalWorkingYears, YearsSinceLastPromotion, YearsWithCurrManager
- **Outros:** Attrition, OverTime, BusinessTravel, DistanceFromHome

**Calcule automaticamente as seguintes métricas avançadas:**

| Métrica | Fórmula | Propósito |
|---------|---------|-----------|
| **Turnover Rate** | (Attrition = "Yes" / Total) * 100 | Taxa global de saída |
| **Promotion Velocity** | YearsAtCompany / (YearsSinceLastPromotion + 1) | Velocidade de progressão (quanto maior, mais estagnado) |
| **Compa-Ratio** | MonthlyIncome / AVG(MonthlyIncome por JobRole) | Posicionamento salarial vs. mercado interno |
| **Tenure Band** | Categorizar: "Onboarding (<1 ano)", "Ramping (1-2 anos)", "Core (2-5 anos)", "Veterano (>5 anos)" | Ciclo de vida do colaborador |
| **Flight Risk Score (0-100)** | Algoritmo ponderado (ver detalhes abaixo) | Probabilidade de saída |
| **Cost of Attrition** | Se Attrition = "Yes": MonthlyIncome * 6 | Custo estimado por perda |
| **Engagement Index** | (JobSatisfaction + EnvironmentSatisfaction + RelationshipSatisfaction + WorkLifeBalance) / 16 * 100 | Índice de engajamento |
| **High Potential Flag** | PerformanceRating >= 3 AND JobInvolvement >= 3 | Identificação de talentos |
| **Burnout Risk** | OverTime = "Yes" AND WorkLifeBalance <= 2 | Risco de esgotamento |
| **Salary Competitiveness** | Compa-Ratio < 0.9 = "Abaixo", 0.9-1.1 = "Adequado", > 1.1 = "Acima" | Análise de competitividade |

**Fórmula do Flight Risk Score:**
```
Flight Risk = (
    (5 - JobSatisfaction) * 15 +           # Insatisfação (0-60 pts)
    (Overtime = "Yes" ? 15 : 0) +           # Sobrecarga (0-15 pts)
    min(YearsSinceLastPromotion * 3, 15) +  # Estagnação (0-15 pts)
    (Compa-Ratio < 0.9 ? 10 : 0)            # Salário baixo (0-10 pts)
) 
Normalizar para escala 0-100
```

---

### 2. DASHBOARD PRINCIPAL (VISÃO DO DIRETOR)

Construa um dashboard visual, moderno e limpo com as seguintes seções:

#### **Indicadores de Topo (KPI Cards):**

| KPI | Descrição | Visual |
|-----|-----------|--------|
| Headcount Total | Número total de colaboradores ativos | Card com variação % |
| Taxa de Turnover | (Attrition / Total) * 100, anualizada | Card com trend indicator |
| Custo Total de Attrition | Soma de Cost of Attrition para saídas | Card em R$ com impacto |
| eNPS Estimado | Baseado em JobSatisfaction (Promotores - Detratores) | Gauge chart |
| Avg Time to Promote | Média de YearsSinceLastPromotion | Card com benchmark |
| Engagement Score | Média do Engagement Index | Card com status |

#### **Gráficos Estratégicos:**

1. **Matriz de Risco vs. Performance**
   - Eixo X: PerformanceRating (1-4)
   - Eixo Y: Flight Risk Score (0-100)
   - Tamanho: MonthlyIncome
   - Cor: Department
   - Quadrantes: "Reter a Todo Custo", "Desenvolver", "Monitorar", "Investigar"

2. **Curva de Sobrevivência (Survival Analysis)**
   - Gráfico de linha mostrando probabilidade de permanência por YearsAtCompany
   - Identificar "momento crítico" de maior evasão
   - Overlay com média do mercado

3. **Drivers de Attrition (Waterfall Chart)**
   - Impacto de cada variável na probabilidade de saída
   - Ordenado por importância (baseado em modelo)

4. **Impacto Financeiro por Departamento**
   - Gráfico de barras: Custo de Attrition por Department
   - Sublinha: Taxa de Turnover de cada área

5. **Distribuição de Flight Risk**
   - Histogram ou box plot por Department/JobRole
   - Highlighting de outliers

6. **Heatmap de Satisfação**
   - Matriz: JobRole vs. Métricas de Satisfação
   - Identificar "bolsões de insatisfação"

#### **Filtros Interativos:**
- Department & JobRole
- Tenure Band
- Gender & Education Field
- Performance Rating (1-4)
- Flight Risk Range (Baixo/Médio/Alto/Crítico)
- High Potential (Yes/No)
- OverTime (Yes/No)

---

### 3. MÓDULO: WATCHLIST DE RETENÇÃO (Talentos Críticos)

Crie um módulo automático que identifica funcionários que requerem atenção imediata:

#### **Critérios de Alerta (Score composto):**
```
Critical Talent Score = (
    (PerformanceRating == 4 ? 30 : PerformanceRating == 3 ? 20 : 0) +
    (Flight Risk Score > 70 ? 30 : Flight Risk Score > 50 ? 15 : 0) +
    (Compa-Ratio < 0.9 ? 20 : 0) +
    (OverTime = "Yes" ? 10 : 0) +
    (YearsSinceLastPromotion > 3 ? 10 : 0)
)
```

#### **Exibir:**

1. **Ranking dos Top 10 Talentos Críticos**
   - EmployeeNumber, JobRole, Department
   - Flight Risk Score, Performance Rating
   - Motivos do Risco (em bullet points)
   - Tempo de empresa e última promoção
   - Recomendação de ação

2. **Padrões Identificados (Pattern Recognition)**
   - "70% dos colaboradores em risco são de R&D com mais de 3 anos sem promoção"
   - "Gestores de Vendas com OverTime têm 3x mais chance de sair"
   - Clustering automático de perfis de risco

3. **Recomendações Automáticas por Colaborador:**
   | Situação | Ação Recomendada |
   |----------|------------------|
   | Compa-Ratio < 0.9 | "Revisão Salarial Urgente" |
   | YearsSinceLastPromotion > 4 | "Plano de Carreira / Promoção" |
   | OverTime + Low WLB | "Rebalanceamento de Carga" |
   | Low EnvironmentSat | "Check-in com Gestor / Cultura" |

---

### 4. MODELOS DE PEOPLE SCIENCE (Análise Avançada)

Implemente modelos estatísticos para explicar o "Porquê":

#### **4.1 Driver Analysis (Impacto Real dos Fatores)**

**Modelo 1: Regressão Logística**
- Target: Attrition (Yes/No)
- Features: Todas as variáveis relevantes
- Output: Odds Ratio de cada variável
- Interpretação: "Overtime aumenta a chance de saída em X%"

**Modelo 2: Random Forest / Gradient Boosting**
- Feature Importance ranking
- Permutation Importance para validação
- SHAP values para interpretabilidade

**Visualização:**
- Gráfico de barras horizontais com Feature Importance
- Percentual de impacto normalizado
- Direção do impacto (positivo/negativo para retenção)

#### **4.2 Análise de Causalidade**

**Difference-in-Differences:**
- Comparar grupos: OverTime = Yes vs. No
- Métricas: Attrition Rate, Satisfaction, Performance
- Calcular uplift/impacto isolado

**Análise de Correlação:**
- YearsSinceLastPromotion × JobSatisfaction
- MonthlyIncome × Attrition
- DistanceFromHome × Attrition
- WorkLifeBalance × Engagement

**Matriz de Correlação Interativa:**
- Heatmap com valores de correlação
- Highlight de correlações significativas (p < 0.05)

#### **4.3 Predictive Analytics**

**Previsão de Turnover (6 meses):**
```
- Modelo: Gradient Boosting Classifier
- Output: Probabilidade individual de saída
- Agregação: Taxa de Turnover projetada
- Intervalo de confiança: 95%
```

**Outputs:**
1. Lista dos próximos 10 prováveis a pedir demissão
2. Taxa de Turnover projetada para próximo trimestre
3. Custo projetado se nenhuma ação for tomada
4. Cenário com intervenções vs. sem intervenções

---

### 5. ABAS ADICIONAIS

#### **Aba: "Insights do Analista"**

Gerar insights automáticos em linguagem natural baseados nos dados:

**Estrutura dos Insights:**
1. **Narrativa Geral** (numerada)
   - Visão macro do cenário de retenção
   - Comparação entre departamentos
   - Tendências identificadas

2. **Insights de Eficiência de Pessoas**
   - Custo por colaborador por departamento
   - ROI de treinamento vs. retenção
   - Produtividade (proxy) por tenure band

**Exemplo de Insights Automáticos:**
```
1. "O departamento de Sales concentra 45% do custo de turnover, 
    apesar de representar apenas 30% do headcount."

2. "Colaboradores com WorkLifeBalance = 1 têm probabilidade de 
    saída 2.5x maior que a média."

3. "A faixa de 2-3 anos de empresa é o momento crítico: 
    60% das saídas ocorrem nesse período."

4. "Cada ponto adicional em JobSatisfaction reduz a probabilidade 
    de saída em 23%."
```

#### **Aba: "Plano de Ação"**

Lista de ações priorizadas por impacto financeiro:

| Prioridade | Ação | Público-Alvo | Investimento Est. | ROI Esperado |
|------------|------|--------------|-------------------|--------------|
| 🔴 Crítica | Revisão salarial para Compa-Ratio < 0.85 | 45 pessoas | R$ 150k/ano | 3.2x |
| 🟠 Alta | Programa de Career Path para R&D | 120 pessoas | R$ 80k | 2.8x |
| 🟡 Média | Política de flexibilidade para OverTime | 200 pessoas | R$ 30k | 2.1x |
| 🟢 Monitorar | Mentoria para Onboarding | 50 pessoas | R$ 20k | 1.8x |

**Cálculo de ROI:**
```
ROI = (Custo Evitado de Turnover) / (Investimento na Ação)
Custo Evitado = Probabilidade de Saída Reduzida × Custo Médio de Attrition × N pessoas
```

#### **Aba: "Perfil do Colaborador Ideal"**

Análise das características comuns entre colaboradores com:
- YearsAtCompany > 5
- PerformanceRating >= 3
- Attrition = "No"

**Outputs:**
1. **Perfil Demográfico Médio**
   - Idade, Estado Civil, Educação

2. **Perfil Comportamental**
   - Média de satisfações
   - WorkLifeBalance típico
   - Padrão de viagem

3. **Perfil de Carreira**
   - Tempo médio para promoção
   - Número de empresas anteriores
   - Training frequency

4. **Insights Acionáveis:**
   - "O colaborador ideal típico teve 1 promoção a cada 3 anos"
   - "92% não fazem hora extra regularmente"
   - "Média de 3+ treinamentos por ano"

---

### 6. VISUAL E EXPERIÊNCIA

- **Cores:** Azul Corporativo (#1e40af), Cinza (#64748b), Alertas em Laranja (#f59e0b) e Vermelho (#ef4444)
- **Tema:** Moderno, limpo, profissional (similar a Tableau/Power BI premium)
- **Cards:** Bordas suaves, sombras sutis, ícones contextuais
- **Tooltips:** Explicativas ao passar o mouse sobre KPIs técnicos
- **Responsivo:** Adaptável para telas diferentes
- **Navegação:** Tabs claras, filtros persistentes, estado salvo

---

## ⚙️ PROMPT 2 – ANÁLISE ESTRATÉGICA DE PEOPLE SCIENCE

*(Executar após criar o Dashboard)*

Com base nos dados processados e no dashboard criado, execute uma análise completa usando metodologias de People Science:

### 1. ISOLAMENTO DE VARIÁVEIS DE IMPACTO

**Análise Ceteris Paribus:**
```
Para cada variável chave (OverTime, WorkLifeBalance, YearsSinceLastPromotion, 
MonthlyIncome, DistanceFromHome):
- Calcular impacto isolado na probabilidade de Attrition
- Manter outras variáveis constantes (propensity score matching ou regressão)
- Reportar: Odds Ratio, Intervalo de Confiança, p-value
```

**Outputs Esperados:**
- "OverTime = Yes aumenta a probabilidade de saída em 154% (IC 95%: 120-195%)"
- "Cada ano sem promoção aumenta o risco em 12%"
- "Cada R$1.000 adicional no salário reduz o risco em 8%"

### 2. MATRIZ DE DECISÃO ESTRATÉGICA

Criar matriz automática de ação por colaborador:

| Quadrante | Critério | Ação | Urgência |
|-----------|----------|------|----------|
| 🔴 **Reter a Todo Custo** | High Performance + High Risk | One-on-one, Promoção Acelerada, Retenção Salarial | Imediata (7 dias) |
| 🟠 **Desenvolver** | Medium Performance + Low Engagement | PDI, Mentoria, Novos Desafios | 30 dias |
| 🟡 **Monitorar** | Low Performance + High Salary | PIP, Realocação, Avaliação | 60 dias |
| 🟢 **Celebrar** | High Performance + Low Risk | Reconhecimento, Carreira, Retenção | Ongoing |
| ⚪ **Investigar** | Low Performance + High Risk | Diagnóstico, Fit Cultural | 15 dias |

### 3. SIMULAÇÃO DE CENÁRIOS (What-If Analysis)

**Cenário 1: Aumento de Promoções**
```
Input: Aumentar taxa de promoção em 20%
Output: 
- Redução estimada no Turnover: X%
- Economia gerada: R$ Y
- Número de colaboradores impactados: Z
```

**Cenário 2: Política Anti-Overtime**
```
Input: Limitar OverTime a 10% do time
Output:
- Impacto no Flight Risk Score médio
- Redução de custos de saúde/afastamento
- Impacto em produtividade
```

**Cenário 3: Ajuste Salarial**
```
Input: Elevar todos os Compa-Ratio < 0.9 para 0.95
Output:
- Custo do ajuste: R$ X
- Redução estimada de saídas: Y pessoas
- Payback period: Z meses
```

### 4. PREVISÃO DE CURTO PRAZO

**Projeção para 30/60/90 dias:**
- Volume de vagas que precisaremos abrir
- Custo projetado de recrutamento
- Impacto na produtividade da equipe
- Áreas mais afetadas

**Modelo de Previsão:**
```
- Baseado em probabilidades individuais do modelo
- Agregação por departamento e job role
- Intervalo de confiança: 80% e 95%
```

---

## 📑 PROMPT 3 – RELATÓRIO EXECUTIVO FINAL

*(Gerar após análises completas)*

Transforme toda a análise em um relatório executivo contendo:

### ESTRUTURA DO RELATÓRIO:

1. **Resumo Executivo (1 página)**
   - 3 números mais importantes
   - Situação geral em 1 parágrafo
   - Top 3 ações prioritárias

2. **10 Descobertas Principais**
   - Insights numerados com dados de suporte
   - Gráfico ou visualização para cada um
   - Implicação de negócio

3. **5 Oportunidades de Retenção**
   - Quick wins vs. Investimentos de longo prazo
   - Custo vs. Impacto estimado
   - Responsável sugerido

4. **3 Descobertas Contraintuitivas (Quebrando Mitos de RH)**
   - Ex: "Salário não é o principal driver de saída em R&D"
   - Ex: "Colaboradores que viajam frequentemente têm menor turnover"
   - Dados que contradizem senso comum

5. **3 Recomendações de Alto Impacto**
   - Ação específica e mensurável
   - Timeline sugerido
   - KPI de sucesso
   - ROI estimado

6. **Projeção de ROI do Programa de Retenção**
   ```
   Investimento Total: R$ X
   Redução Estimada de Turnover: Y%
   Economia Anual Projetada: R$ Z
   Payback Period: N meses
   ROI 12 meses: X%
   ```

7. **Anexos**
   - Metodologia dos modelos
   - Lista completa de talentos críticos
   - Plano de ação detalhado por departamento

---

## 🛠️ ESPECIFICAÇÕES TÉCNICAS

### Stack Recomendado:
- **Backend:** Python (Pandas, Scikit-learn, Scipy, Statsmodels)
- **Dashboard:** Dash + Plotly ou Streamlit
- **Estilização:** CSS customizado com tema corporativo
- **Relatórios:** HTML/PDF export capability

### Estrutura de Arquivos:
```
rh_dashboard/
├── data_processor.py      # Carregamento e feature engineering
├── people_science.py      # Modelos estatísticos e ML
├── advanced_analysis.py   # Análises avançadas (DiD, Survival, etc.)
├── dashboard.py           # Interface principal do dashboard
├── generate_report.py     # Geração de relatórios
├── assets/
│   └── style.css          # Estilização customizada
├── WA_Fn-UseC_-HR-Employee-Attrition.csv
├── requirements.txt
└── README.md
```

### Bibliotecas Necessárias:
```
pandas>=1.5.0
numpy>=1.23.0
scikit-learn>=1.1.0
scipy>=1.9.0
statsmodels>=0.13.0
plotly>=5.11.0
dash>=2.7.0
dash-bootstrap-components>=1.2.0
lifelines>=0.27.0  # Para Survival Analysis
shap>=0.41.0       # Para interpretabilidade
```

---

## 📋 CHECKLIST DE ENTREGA

- [ ] Dashboard funcional com todos os KPIs
- [ ] Filtros interativos funcionando
- [ ] Módulo de Watchlist populado
- [ ] Modelos de ML treinados e validados
- [ ] Insights gerados automaticamente
- [ ] Plano de ação priorizado
- [ ] Relatório executivo exportável
- [ ] Código limpo e documentado
- [ ] Visual profissional e responsivo

---

**Nota Final:** Este dashboard deve ser tão sofisticado e acionável quanto um produto de People Analytics enterprise, permitindo que o Head de RH tome decisões baseadas em dados com confiança e precisão.

---

## 🎤 GUIA PARA APRESENTAÇÃO NA ENTREVISTA BB PREVIDÊNCIA

### Pontos de Conexão com o Negócio da BB Previdência:

1. **Retenção de Talentos em Ambiente Regulado**
   - "Em uma EFPC como a BB Previdência, o custo de perder um colaborador sênior vai além do financeiro - há perda de conhecimento regulatório, certificações e relacionamento com patrocinadores"
   - Demonstrar: Flight Risk Score aplicado a certificados e conhecimento crítico

2. **Governança e Compliance**
   - "O modelo de People Analytics que desenvolvi considera variáveis de compliance, garantindo que decisões de gestão de pessoas estejam alinhadas com as exigências da PREVIC"
   - Demonstrar: Matriz de risco com sobreposição de funções críticas regulatórias

3. **Visão de Longo Prazo (DNA Previdenciário)**
   - "Assim como a BB Previdência planeja benefícios para décadas, este dashboard projeta cenários de workforce planning de 6-12 meses"
   - Demonstrar: Survival Analysis e Previsão de Turnover

4. **ESG e Sustentabilidade Corporativa**
   - "O BB foi eleito a instituição financeira mais sustentável do mundo. People Analytics conecta-se ao 'S' de ESG através de métricas de bem-estar e equidade"
   - Demonstrar: Engagement Index e análise de equidade salarial (Compa-Ratio)

5. **ROI Quantificável**
   - "Para cada R$1 investido em programa de retenção baseado nesta análise, estimamos retorno de X vezes em economia de turnover"
   - Demonstrar: Cálculo de Cost of Attrition e ROI de ações

### Perguntas que você pode antecipar:

| Pergunta Provável | Como Responder |
|-------------------|----------------|
| "Como isso se aplica à nossa realidade?" | "O modelo é adaptável. Podemos incluir variáveis específicas como certificações ANBIMA, tempo de CPA, ou exposição a patrocinadores estratégicos" |
| "Temos poucos dados históricos" | "Comecei com dados sintéticos do IBM HR. Na BB Previdência, podemos começar com análise descritiva e evoluir para preditiva conforme coletamos dados" |
| "Qual o prazo de implementação?" | "MVP em 30 dias com indicadores básicos. Dashboard completo em 90 dias. Modelos preditivos calibrados em 6 meses" |
| "Quem vai usar isso?" | "Diretoria para decisões estratégicas, gestores para ações táticas, e BP de RH para intervenções individuais" |

### Vocabulário-chave para usar na entrevista:
- ✅ "Previdência complementar fechada"
- ✅ "PREVIC", "Resolução CNPC"
- ✅ "Patrocinadores e instituidores"
- ✅ "Governança corporativa"
- ✅ "Gestão de riscos de pessoas"
- ✅ "Sustentabilidade e ESG"
- ✅ "Planejamento de sucessão"
- ✅ "Retenção de conhecimento crítico"

### O que NÃO fazer:
- ❌ Falar apenas de tecnologia sem conectar ao negócio
- ❌ Ignorar o contexto regulatório
- ❌ Apresentar métricas sem traduzir em impacto financeiro
- ❌ Usar jargões de tech sem explicar o valor para gestão

---

## 📊 MÉTRICAS ESPECÍFICAS PARA CONTEXTO BB PREVIDÊNCIA

Considere adicionar estas métricas personalizadas:

| Métrica | Fórmula | Relevância BB Previdência |
|---------|---------|---------------------------|
| **Índice de Concentração de Conhecimento** | Nº de processos críticos dependentes de 1 pessoa | Risco operacional em ambiente regulado |
| **Cobertura de Sucessão** | % de posições-chave com sucessor identificado | Continuidade de negócio |
| **Tempo de Adaptação Regulatória** | Dias até certificação/capacitação completa | Custo de onboarding em EFPC |
| **Índice de Relacionamento com Patrocinadores** | Score de exposição a clientes estratégicos | Risco de perda de relacionamento |
| **Taxa de Renovação de Certificações** | % certificações válidas vs. total | Compliance regulatório |

---

**Boa sorte na entrevista! 🍀**
