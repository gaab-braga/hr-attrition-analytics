# People Analytics: turnover na base IBM HR

Dashboard em Dash e um conjunto de análises para entender por que as pessoas saem de uma empresa e quem tem mais risco de sair.

Usei a base pública IBM HR Analytics Employee Attrition (dados fictícios criados pela IBM): 1.470 colaboradores, 35 colunas, 16,1% de turnover.

## O que tem

- `people_science.py`: três classificadores (regressão logística, random forest e gradient boosting) para os fatores de risco, e a probabilidade de saída de cada colaborador ativo.
- `statistical_analysis.py`: regressão logística para explicar o turnover, com odds ratio, intervalo de confiança e p-valor de cada variável.
- `survival_analysis.py`: curvas de Kaplan-Meier por tempo de casa e por segmento.
- `cluster_analysis.py`: K-Means, com o k escolhido pelo silhouette, e o perfil de cada grupo.
- `what_if_simulator.py`: muda uma variável (promoção, hora extra, salário, treinamento) e recalcula a probabilidade de saída.
- `dashboard/`: o painel com seis abas (principal, watchlist, people science, insights, plano de ação e perfil ideal).
- `scripts/`: dois relatórios em HTML, o estatístico e o executivo.

## Como validei

- AUC em validação cruzada estratificada de 5 dobras. A padronização fica dentro de um `Pipeline`, então ela é ajustada só nas dobras de treino.
- Os colaboradores ativos também estão no treino. Para dar a probabilidade de saída de cada um, uso `cross_val_predict`: cada pessoa recebe a nota do modelo da dobra em que ficou de fora.
- A regressão logística explicativa (odds ratios) é ajustada na base inteira, porque ali o objetivo é interpretar e não prever. A AUC dela também vem da validação cruzada.
- A acurácia aparece ao lado do baseline: quem chuta "ninguém sai" acerta 83,9%.

Antes dessa revisão, o scaler era ajustado na base inteira antes da validação cruzada, e a probabilidade dos ativos vinha de um modelo que já tinha visto essas pessoas no treino. Com isso, os 1.233 ativos apareciam todos como risco baixo. Com a previsão fora da dobra, 101 aparecem como risco médio, alto ou crítico. Há um teste que reprova se a previsão voltar a ser feita dentro da amostra.

## Resultados (validação cruzada, 5 dobras)

| Modelo | AUC |
|---|---|
| Regressão logística (fatores de risco) | 0,816 |
| Random forest | 0,817 |
| Gradient boosting | 0,794 |
| Regressão logística explicativa | 0,828 ± 0,015 |
| Gradient boosting da probabilidade de saída | 0,778 |

A acurácia da regressão explicativa é 87,3%, contra 83,9% do baseline. Por isso a comparação entre modelos é feita pela AUC.

Os fatores que mais pesam: salário, hora extra, idade e tempo de carreira. Quem faz hora extra tem 30,5% de turnover, contra 10,4% de quem não faz.

## Limitações

- Os dados são fictícios e não têm data de saída. A projeção mês a mês divide a probabilidade anual por mês e aplica fatores sazonais fixos no código (janeiro, fevereiro e julho mais altos; novembro e dezembro mais baixos). Esses fatores são suposição, não vêm dos dados.
- Na análise de fatores de risco, cargo, departamento e estado civil entram com `LabelEncoder`, o que cria uma ordem que não existe. One-hot seria o certo para a regressão logística.
- O simulador mostra associação, não causa. Ele muda uma variável e lê o que o modelo responde.
- A regressão explicativa usa gênero como variável. Serve para descrever a base, mas não deveria entrar numa decisão sobre pessoas.

## Como rodar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run_dashboard.py --open
```

O painel abre em `http://127.0.0.1:8050`. Para os relatórios e os testes:

```bash
python scripts/generate_analysis_report.py
python scripts/generate_final_report.py
pytest
```

## Estrutura

```
data/raw/             base IBM HR Attrition (CSV)
src/rh_analytics/     análises e modelos
src/rh_analytics/dashboard/   app Dash, componentes e CSS
scripts/              geradores dos relatórios HTML
reports/              saída dos relatórios (fora do git)
tests/                testes do app e da validação
run_dashboard.py      sobe o painel
```
