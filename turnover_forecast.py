"""
Turnover Forecast - People Analytics
Modelo de previsão temporal de turnover com projeções mensais
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings('ignore')


@dataclass
class ForecastResult:
    """Resultado de previsão de turnover"""
    periodo: str
    turnover_projetado: float
    intervalo_confianca_inferior: float
    intervalo_confianca_superior: float
    saidas_estimadas: int
    custo_projetado: float
    departamentos_criticos: Dict[str, int]


class TurnoverForecaster:
    """
    Modelo de previsão de turnover com projeções temporais
    """
    
    CUSTO_MEDIO_TURNOVER = 35000  # R$ por saída
    
    def __init__(self, df: pd.DataFrame):
        """
        Inicializa o forecaster
        
        Args:
            df: DataFrame com dados dos colaboradores
        """
        self.df = df.copy()
        self.modelo = None
        self.features = None
        self._preparar_dados()
        self._treinar_modelo()
    
    def _preparar_dados(self):
        """Prepara dados para modelagem"""
        # Garantir Attrition numérico
        if 'Attrition' in self.df.columns:
            if self.df['Attrition'].dtype == 'object':
                self.df['Attrition_Num'] = (self.df['Attrition'] == 'Yes').astype(int)
            else:
                self.df['Attrition_Num'] = self.df['Attrition']
        
        # Codificar variáveis categóricas
        if 'OverTime' in self.df.columns:
            self.df['OverTime_Num'] = (self.df['OverTime'] == 'Yes').astype(int)
        
        if 'Gender' in self.df.columns:
            self.df['Gender_Num'] = (self.df['Gender'] == 'Male').astype(int)
        
        if 'MaritalStatus' in self.df.columns:
            self.df['MaritalStatus_Single'] = (self.df['MaritalStatus'] == 'Single').astype(int)
    
    def _treinar_modelo(self):
        """Treina modelo de previsão de attrition"""
        features_candidatas = [
            'Age', 'DistanceFromHome', 'Education', 'EnvironmentSatisfaction',
            'JobInvolvement', 'JobLevel', 'JobSatisfaction', 'MonthlyIncome',
            'NumCompaniesWorked', 'PercentSalaryHike', 'PerformanceRating',
            'RelationshipSatisfaction', 'StockOptionLevel', 'TotalWorkingYears',
            'TrainingTimesLastYear', 'WorkLifeBalance', 'YearsAtCompany',
            'YearsInCurrentRole', 'YearsSinceLastPromotion', 'YearsWithCurrManager',
            'OverTime_Num', 'Gender_Num', 'MaritalStatus_Single'
        ]
        
        self.features = [f for f in features_candidatas if f in self.df.columns]
        
        if 'Attrition_Num' not in self.df.columns or len(self.features) == 0:
            return
        
        X = self.df[self.features].fillna(self.df[self.features].median())
        y = self.df['Attrition_Num']
        
        self.modelo = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42
        )
        self.modelo.fit(X, y)
        
        # Calcular performance do modelo
        self.cv_scores = cross_val_score(self.modelo, X, y, cv=5, scoring='roc_auc')
    
    def calcular_probabilidades_individuais(self) -> pd.DataFrame:
        """
        Calcula probabilidade de saída para cada colaborador
        
        Returns:
            DataFrame com probabilidades individuais
        """
        if self.modelo is None:
            return pd.DataFrame()
        
        X = self.df[self.features].fillna(self.df[self.features].median())
        probabilidades = self.modelo.predict_proba(X)[:, 1]
        
        resultado = self.df.copy()
        resultado['Probabilidade_Saida'] = probabilidades
        resultado['Risco_Categoria'] = pd.cut(
            probabilidades,
            bins=[0, 0.15, 0.35, 0.6, 1.0],
            labels=['Baixo', 'Moderado', 'Alto', 'Crítico']
        )
        
        return resultado
    
    def projetar_turnover(self, meses: int = 12) -> List[ForecastResult]:
        """
        Projeta turnover para os próximos meses
        
        Args:
            meses: Número de meses para projeção
        
        Returns:
            Lista de ForecastResult por período
        """
        if self.modelo is None:
            return []
        
        # Obter probabilidades individuais
        df_prob = self.calcular_probabilidades_individuais()
        
        resultados = []
        colaboradores_restantes = len(df_prob)
        prob_media = df_prob['Probabilidade_Saida'].mean()
        
        # Simular saídas ao longo do tempo
        for mes in range(1, meses + 1):
            # Ajustar probabilidade mensal (baseado em probabilidade anual)
            prob_mensal = 1 - (1 - prob_media) ** (1/12)
            
            # Variação sazonal (mais saídas no início do ano e após bônus)
            fator_sazonal = 1.0
            if mes in [1, 2, 7]:  # Janeiro, Fevereiro, Julho
                fator_sazonal = 1.3
            elif mes in [11, 12]:  # Novembro, Dezembro
                fator_sazonal = 0.7
            
            prob_ajustada = prob_mensal * fator_sazonal
            
            # Calcular saídas estimadas
            saidas = int(colaboradores_restantes * prob_ajustada)
            saidas = max(1, min(saidas, int(colaboradores_restantes * 0.15)))  # Limites razoáveis
            
            # Intervalo de confiança (80%)
            std = np.sqrt(colaboradores_restantes * prob_ajustada * (1 - prob_ajustada))
            ic_inferior = max(0, saidas - 1.28 * std)
            ic_superior = saidas + 1.28 * std
            
            # Identificar departamentos críticos
            dept_prob = df_prob.groupby('Department')['Probabilidade_Saida'].mean() if 'Department' in df_prob.columns else pd.Series()
            dept_count = df_prob.groupby('Department').size() if 'Department' in df_prob.columns else pd.Series()
            
            departamentos_criticos = {}
            for dept in dept_prob.index:
                saidas_dept = int(dept_count[dept] * prob_ajustada * (dept_prob[dept] / prob_media))
                if saidas_dept > 0:
                    departamentos_criticos[dept] = saidas_dept
            
            # Turnover rate projetado
            turnover_projetado = saidas / colaboradores_restantes * 100
            
            resultados.append(ForecastResult(
                periodo=f"Mês {mes}",
                turnover_projetado=turnover_projetado,
                intervalo_confianca_inferior=ic_inferior / colaboradores_restantes * 100,
                intervalo_confianca_superior=ic_superior / colaboradores_restantes * 100,
                saidas_estimadas=saidas,
                custo_projetado=saidas * self.CUSTO_MEDIO_TURNOVER,
                departamentos_criticos=departamentos_criticos
            ))
            
            colaboradores_restantes -= saidas
        
        return resultados
    
    def identificar_proximas_saidas(self, top_n: int = 10) -> pd.DataFrame:
        """
        Identifica os colaboradores com maior probabilidade de saída
        
        Args:
            top_n: Número de colaboradores a retornar
        
        Returns:
            DataFrame com top colaboradores em risco
        """
        df_prob = self.calcular_probabilidades_individuais()
        
        if df_prob.empty:
            return pd.DataFrame()
        
        # Ordenar por probabilidade
        df_prob = df_prob.sort_values('Probabilidade_Saida', ascending=False)
        
        # Selecionar colunas relevantes
        colunas = ['EmployeeNumber'] if 'EmployeeNumber' in df_prob.columns else []
        colunas += ['Department', 'JobRole', 'JobLevel', 'YearsAtCompany', 
                   'PerformanceRating', 'Probabilidade_Saida', 'Risco_Categoria']
        colunas = [c for c in colunas if c in df_prob.columns]
        
        # Filtrar apenas ativos (se tiver dados)
        if 'Attrition' in df_prob.columns:
            df_prob = df_prob[df_prob['Attrition'] == 'No']
        
        return df_prob[colunas].head(top_n)
    
    def gerar_projecao_trimestral(self) -> Dict:
        """
        Gera projeção consolidada por trimestre
        
        Returns:
            Dicionário com projeções trimestrais
        """
        projecoes_mensais = self.projetar_turnover(12)
        
        if not projecoes_mensais:
            return {}
        
        trimestres = {
            'Q1': projecoes_mensais[0:3],
            'Q2': projecoes_mensais[3:6],
            'Q3': projecoes_mensais[6:9],
            'Q4': projecoes_mensais[9:12]
        }
        
        resultado = {}
        for trim, meses in trimestres.items():
            saidas_total = sum(m.saidas_estimadas for m in meses)
            custo_total = sum(m.custo_projetado for m in meses)
            
            # Agregar departamentos
            dept_agregado = {}
            for m in meses:
                for dept, count in m.departamentos_criticos.items():
                    dept_agregado[dept] = dept_agregado.get(dept, 0) + count
            
            resultado[trim] = {
                'saidas_estimadas': saidas_total,
                'custo_projetado': f'R$ {custo_total:,.0f}',
                'departamentos_criticos': dict(sorted(
                    dept_agregado.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:3])  # Top 3 departamentos
            }
        
        return resultado
    
    def calcular_metricas_modelo(self) -> Dict:
        """
        Calcula métricas de qualidade do modelo
        
        Returns:
            Dicionário com métricas do modelo
        """
        if self.modelo is None:
            return {'erro': 'Modelo não treinado'}
        
        return {
            'auc_medio': f'{self.cv_scores.mean():.3f}',
            'auc_std': f'{self.cv_scores.std():.3f}',
            'features_utilizadas': len(self.features),
            'confianca': 'Alta' if self.cv_scores.mean() > 0.75 else 'Moderada' if self.cv_scores.mean() > 0.65 else 'Baixa',
            'top_features': self._get_top_features(5)
        }
    
    def _get_top_features(self, n: int = 5) -> List[str]:
        """Retorna as features mais importantes"""
        if self.modelo is None:
            return []
        
        importances = self.modelo.feature_importances_
        indices = np.argsort(importances)[-n:][::-1]
        return [self.features[i] for i in indices]
    
    def gerar_resumo_previsao(self) -> Dict:
        """
        Gera resumo completo das previsões
        
        Returns:
            Dicionário com resumo das previsões
        """
        projecoes = self.projetar_turnover(12)
        proximas_saidas = self.identificar_proximas_saidas(10)
        metricas = self.calcular_metricas_modelo()
        trimestral = self.gerar_projecao_trimestral()
        
        # Calcular totais anuais
        total_saidas = sum(p.saidas_estimadas for p in projecoes)
        total_custo = sum(p.custo_projetado for p in projecoes)
        
        # Taxa de turnover anual projetada
        taxa_turnover_anual = total_saidas / len(self.df) * 100 if len(self.df) > 0 else 0
        
        # Benchmark (mercado brasileiro)
        benchmark_mercado = 38.0  # % turnover médio Brasil
        
        return {
            'resumo_anual': {
                'turnover_projetado': f'{taxa_turnover_anual:.1f}%',
                'saidas_estimadas': total_saidas,
                'custo_total_projetado': f'R$ {total_custo:,.0f}',
                'comparacao_benchmark': 'Abaixo da média' if taxa_turnover_anual < benchmark_mercado else 'Acima da média',
                'benchmark_mercado': f'{benchmark_mercado}%'
            },
            'projecao_trimestral': trimestral,
            'proximas_saidas': proximas_saidas.to_dict('records') if not proximas_saidas.empty else [],
            'metricas_modelo': metricas,
            'projecao_mensal': [
                {
                    'periodo': p.periodo,
                    'turnover': f'{p.turnover_projetado:.2f}%',
                    'saidas': p.saidas_estimadas,
                    'custo': f'R$ {p.custo_projetado:,.0f}',
                    'intervalo_confianca': f'{p.intervalo_confianca_inferior:.2f}% - {p.intervalo_confianca_superior:.2f}%'
                }
                for p in projecoes
            ]
        }
    
    def projetar_cenario_com_intervencao(self, 
                                          reducao_risco: float = 0.2) -> Dict:
        """
        Projeta cenário após intervenções de retenção
        
        Args:
            reducao_risco: Percentual de redução no risco (0.2 = 20%)
        
        Returns:
            Comparação entre cenário atual e com intervenção
        """
        # Cenário atual
        projecoes_atual = self.projetar_turnover(12)
        total_saidas_atual = sum(p.saidas_estimadas for p in projecoes_atual)
        custo_atual = sum(p.custo_projetado for p in projecoes_atual)
        
        # Cenário com intervenção (reduz probabilidades)
        df_backup = self.df.copy()
        
        # Simular redução de risco
        self.df['Probabilidade_Saida_Ajustada'] = self.df.get('Probabilidade_Saida', 0.1) * (1 - reducao_risco)
        
        # Recalcular projeções com fator de redução
        total_saidas_intervencao = int(total_saidas_atual * (1 - reducao_risco))
        custo_intervencao = total_saidas_intervencao * self.CUSTO_MEDIO_TURNOVER
        
        self.df = df_backup  # Restaurar
        
        economia = custo_atual - custo_intervencao
        saidas_evitadas = total_saidas_atual - total_saidas_intervencao
        
        return {
            'cenario_atual': {
                'saidas_anuais': total_saidas_atual,
                'custo_anual': f'R$ {custo_atual:,.0f}'
            },
            'cenario_com_intervencao': {
                'reducao_risco_aplicada': f'{reducao_risco*100:.0f}%',
                'saidas_anuais': total_saidas_intervencao,
                'custo_anual': f'R$ {custo_intervencao:,.0f}'
            },
            'impacto': {
                'saidas_evitadas': saidas_evitadas,
                'economia_gerada': f'R$ {economia:,.0f}',
                'reducao_percentual': f'{(saidas_evitadas/total_saidas_atual*100):.1f}%' if total_saidas_atual > 0 else '0%'
            }
        }


# Teste do módulo
if __name__ == "__main__":
    # Carregar dados
    df = pd.read_csv('WA_Fn-UseC_-HR-Employee-Attrition.csv')
    
    print("="*60)
    print("TURNOVER FORECASTER - PEOPLE ANALYTICS")
    print("="*60)
    
    # Criar forecaster
    forecaster = TurnoverForecaster(df)
    
    # Gerar resumo
    resumo = forecaster.gerar_resumo_previsao()
    
    print("\n📊 PROJEÇÃO ANUAL:")
    print("-"*60)
    for k, v in resumo['resumo_anual'].items():
        print(f"   {k}: {v}")
    
    print("\n📅 PROJEÇÃO TRIMESTRAL:")
    print("-"*60)
    for trim, dados in resumo['projecao_trimestral'].items():
        print(f"\n   {trim}:")
        print(f"      Saídas estimadas: {dados['saidas_estimadas']}")
        print(f"      Custo projetado: {dados['custo_projetado']}")
        print(f"      Departamentos críticos: {dados['departamentos_criticos']}")
    
    print("\n🎯 TOP 10 PRÓXIMAS SAÍDAS PROVÁVEIS:")
    print("-"*60)
    proximas = forecaster.identificar_proximas_saidas(10)
    if not proximas.empty:
        print(proximas.to_string())
    
    print("\n📈 MÉTRICAS DO MODELO:")
    print("-"*60)
    for k, v in resumo['metricas_modelo'].items():
        print(f"   {k}: {v}")
    
    # Cenário com intervenção
    print("\n🔮 CENÁRIO COM INTERVENÇÃO (20% redução de risco):")
    print("-"*60)
    cenario = forecaster.projetar_cenario_com_intervencao(0.2)
    print(f"   Cenário Atual: {cenario['cenario_atual']['saidas_anuais']} saídas ({cenario['cenario_atual']['custo_anual']})")
    print(f"   Com Intervenção: {cenario['cenario_com_intervencao']['saidas_anuais']} saídas ({cenario['cenario_com_intervencao']['custo_anual']})")
    print(f"   Economia Potencial: {cenario['impacto']['economia_gerada']}")
    print(f"   Saídas Evitadas: {cenario['impacto']['saidas_evitadas']}")
