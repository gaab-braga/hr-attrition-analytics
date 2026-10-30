"""
What-If Simulator para People Analytics
Simulações de cenários e projeções de impacto de intervenções de RH
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from sklearn.ensemble import GradientBoostingClassifier
import warnings
warnings.filterwarnings('ignore')


@dataclass
class ScenarioResult:
    """Resultado de uma simulação de cenário"""
    nome: str
    descricao: str
    colaboradores_impactados: int
    reducao_turnover_estimada: float  # percentual
    economia_gerada: float  # R$
    custo_investimento: float  # R$
    roi_estimado: float
    payback_meses: float
    detalhes: Dict


class WhatIfSimulator:
    """
    Simulador What-If para análise de impacto de intervenções de RH
    """
    
    # Custos padrão (podem ser customizados)
    CUSTO_MEDIO_TURNOVER = 35000  # R$ custo médio por saída
    CUSTO_PROMOCAO = 8000  # R$ custo médio de promoção (aumento salarial anual)
    CUSTO_TREINAMENTO = 3000  # R$ custo médio por treinamento
    CUSTO_AJUSTE_OVERTIME = 2000  # R$ custo médio de ajuste por pessoa
    
    def __init__(self, df: pd.DataFrame, modelo=None):
        """
        Inicializa o simulador
        
        Args:
            df: DataFrame com dados dos colaboradores
            modelo: Modelo treinado para prever attrition (opcional)
        """
        self.df = df.copy()
        self.modelo = modelo
        self._preparar_dados()
        
        if self.modelo is None:
            self._treinar_modelo_interno()
    
    def _preparar_dados(self):
        """Prepara dados para simulação"""
        # Garantir que Attrition seja numérico
        if 'Attrition' in self.df.columns:
            if self.df['Attrition'].dtype == 'object':
                self.df['Attrition_Num'] = (self.df['Attrition'] == 'Yes').astype(int)
            else:
                self.df['Attrition_Num'] = self.df['Attrition']
        
        # Criar Flight Risk Score se não existir
        if 'Flight_Risk_Score' not in self.df.columns:
            self._calcular_flight_risk()
    
    def _calcular_flight_risk(self):
        """Calcula score de risco de saída"""
        risk_score = np.zeros(len(self.df))
        
        # Fatores de risco
        if 'OverTime' in self.df.columns:
            risk_score += (self.df['OverTime'] == 'Yes').astype(float) * 0.2
        
        if 'JobSatisfaction' in self.df.columns:
            risk_score += (4 - self.df['JobSatisfaction']) / 4 * 0.15
        
        if 'YearsSinceLastPromotion' in self.df.columns:
            risk_score += np.minimum(self.df['YearsSinceLastPromotion'] / 10, 1) * 0.15
        
        if 'WorkLifeBalance' in self.df.columns:
            risk_score += (4 - self.df['WorkLifeBalance']) / 4 * 0.1
        
        if 'EnvironmentSatisfaction' in self.df.columns:
            risk_score += (4 - self.df['EnvironmentSatisfaction']) / 4 * 0.1
        
        if 'MonthlyIncome' in self.df.columns:
            median_income = self.df['MonthlyIncome'].median()
            risk_score += (self.df['MonthlyIncome'] < median_income * 0.8).astype(float) * 0.15
        
        if 'YearsAtCompany' in self.df.columns:
            # Maior risco entre 1-3 anos
            risk_score += ((self.df['YearsAtCompany'] >= 1) & 
                          (self.df['YearsAtCompany'] <= 3)).astype(float) * 0.15
        
        self.df['Flight_Risk_Score'] = np.clip(risk_score, 0, 1)
    
    def _treinar_modelo_interno(self):
        """Treina modelo interno de previsão"""
        features_numericas = [
            'Age', 'DailyRate', 'DistanceFromHome', 'Education',
            'EnvironmentSatisfaction', 'HourlyRate', 'JobInvolvement',
            'JobLevel', 'JobSatisfaction', 'MonthlyIncome', 'MonthlyRate',
            'NumCompaniesWorked', 'PercentSalaryHike', 'PerformanceRating',
            'RelationshipSatisfaction', 'StockOptionLevel', 'TotalWorkingYears',
            'TrainingTimesLastYear', 'WorkLifeBalance', 'YearsAtCompany',
            'YearsInCurrentRole', 'YearsSinceLastPromotion', 'YearsWithCurrManager'
        ]
        
        # Adicionar features categóricas codificadas
        if 'OverTime' in self.df.columns:
            self.df['OverTime_Num'] = (self.df['OverTime'] == 'Yes').astype(int)
            features_numericas.append('OverTime_Num')
        
        # Filtrar features disponíveis
        features_disponiveis = [f for f in features_numericas if f in self.df.columns]
        
        if 'Attrition_Num' not in self.df.columns:
            return
        
        X = self.df[features_disponiveis].copy()
        y = self.df['Attrition_Num']
        
        # Preencher valores faltantes
        X = X.fillna(X.median())
        
        self.modelo = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            random_state=42
        )
        self.modelo.fit(X, y)
        self.features_modelo = features_disponiveis
    
    def _prever_probabilidades(self, df_modificado: pd.DataFrame) -> np.ndarray:
        """Calcula probabilidades de saída para dados modificados"""
        if self.modelo is None:
            # Usar Flight Risk Score como proxy
            return df_modificado['Flight_Risk_Score'].values
        
        X = df_modificado[self.features_modelo].copy()
        X = X.fillna(X.median())
        return self.modelo.predict_proba(X)[:, 1]
    
    def simular_aumento_promocoes(self, 
                                   taxa_aumento: float = 0.2,
                                   anos_sem_promocao_threshold: int = 3) -> ScenarioResult:
        """
        Simula impacto de aumentar taxa de promoções
        
        Args:
            taxa_aumento: Percentual de aumento na taxa de promoção (0.2 = 20%)
            anos_sem_promocao_threshold: Anos sem promoção para priorizar
        
        Returns:
            ScenarioResult com detalhes do cenário
        """
        # Identificar colaboradores elegíveis (muitos anos sem promoção)
        if 'YearsSinceLastPromotion' not in self.df.columns:
            return self._criar_resultado_vazio("Aumento de Promoções")
        
        elegiveis = self.df[self.df['YearsSinceLastPromotion'] >= anos_sem_promocao_threshold].copy()
        n_promover = int(len(elegiveis) * taxa_aumento)
        
        if n_promover == 0:
            return self._criar_resultado_vazio("Aumento de Promoções")
        
        # Priorizar por performance e risco
        if 'PerformanceRating' in elegiveis.columns:
            elegiveis = elegiveis.sort_values(
                ['PerformanceRating', 'Flight_Risk_Score'], 
                ascending=[False, False]
            )
        
        promovidos_idx = elegiveis.head(n_promover).index
        
        # Criar cenário modificado
        df_cenario = self.df.copy()
        df_cenario.loc[promovidos_idx, 'YearsSinceLastPromotion'] = 0
        
        if 'JobLevel' in df_cenario.columns:
            df_cenario.loc[promovidos_idx, 'JobLevel'] = np.minimum(
                df_cenario.loc[promovidos_idx, 'JobLevel'] + 1, 5
            )
        
        if 'MonthlyIncome' in df_cenario.columns:
            df_cenario.loc[promovidos_idx, 'MonthlyIncome'] *= 1.15  # 15% aumento médio
        
        # Recalcular Flight Risk
        prob_original = self.df['Flight_Risk_Score'].mean()
        
        # Simular redução de risco para promovidos
        df_cenario.loc[promovidos_idx, 'Flight_Risk_Score'] *= 0.6  # 40% redução
        prob_novo = df_cenario['Flight_Risk_Score'].mean()
        
        reducao_percentual = (prob_original - prob_novo) / prob_original * 100
        
        # Calcular impacto financeiro
        turnover_evitado = int(n_promover * 0.4)  # 40% seriam retidos
        economia = turnover_evitado * self.CUSTO_MEDIO_TURNOVER
        custo = n_promover * self.CUSTO_PROMOCAO
        roi = (economia - custo) / custo * 100 if custo > 0 else 0
        payback = custo / (economia / 12) if economia > 0 else float('inf')
        
        return ScenarioResult(
            nome="Aumento de Promoções",
            descricao=f"Promover {taxa_aumento*100:.0f}% dos colaboradores com {anos_sem_promocao_threshold}+ anos sem promoção",
            colaboradores_impactados=n_promover,
            reducao_turnover_estimada=reducao_percentual,
            economia_gerada=economia,
            custo_investimento=custo,
            roi_estimado=roi,
            payback_meses=payback,
            detalhes={
                'elegiveis_total': len(elegiveis),
                'promovidos': n_promover,
                'turnover_evitado': turnover_evitado,
                'departamentos': elegiveis.head(n_promover)['Department'].value_counts().to_dict() if 'Department' in elegiveis.columns else {}
            }
        )
    
    def simular_politica_anti_overtime(self, 
                                        limite_overtime: float = 0.1) -> ScenarioResult:
        """
        Simula impacto de limitar horas extras
        
        Args:
            limite_overtime: Percentual máximo do time fazendo overtime
        
        Returns:
            ScenarioResult com detalhes do cenário
        """
        if 'OverTime' not in self.df.columns:
            return self._criar_resultado_vazio("Política Anti-Overtime")
        
        # Identificar quem faz overtime
        overtime_atual = self.df[self.df['OverTime'] == 'Yes'].copy()
        n_overtime_atual = len(overtime_atual)
        n_limite = int(len(self.df) * limite_overtime)
        n_remover_overtime = max(0, n_overtime_atual - n_limite)
        
        if n_remover_overtime == 0:
            return self._criar_resultado_vazio("Política Anti-Overtime")
        
        # Priorizar remoção por risco de saída
        overtime_ordenado = overtime_atual.sort_values('Flight_Risk_Score', ascending=False)
        remover_idx = overtime_ordenado.head(n_remover_overtime).index
        
        # Simular impacto
        df_cenario = self.df.copy()
        df_cenario.loc[remover_idx, 'OverTime'] = 'No'
        df_cenario.loc[remover_idx, 'Flight_Risk_Score'] *= 0.7  # 30% redução risco
        
        prob_original = self.df['Flight_Risk_Score'].mean()
        prob_novo = df_cenario['Flight_Risk_Score'].mean()
        reducao_percentual = (prob_original - prob_novo) / prob_original * 100
        
        # Calcular impacto
        turnover_evitado = int(n_remover_overtime * 0.3)
        economia = turnover_evitado * self.CUSTO_MEDIO_TURNOVER
        custo = n_remover_overtime * self.CUSTO_AJUSTE_OVERTIME
        roi = (economia - custo) / custo * 100 if custo > 0 else 0
        payback = custo / (economia / 12) if economia > 0 else float('inf')
        
        return ScenarioResult(
            nome="Política Anti-Overtime",
            descricao=f"Limitar overtime a {limite_overtime*100:.0f}% do time",
            colaboradores_impactados=n_remover_overtime,
            reducao_turnover_estimada=reducao_percentual,
            economia_gerada=economia,
            custo_investimento=custo,
            roi_estimado=roi,
            payback_meses=payback,
            detalhes={
                'overtime_atual': n_overtime_atual,
                'overtime_apos': n_limite,
                'colaboradores_beneficiados': n_remover_overtime,
                'percentual_atual': n_overtime_atual / len(self.df) * 100
            }
        )
    
    def simular_ajuste_salarial(self,
                                 compa_ratio_minimo: float = 0.95,
                                 compa_ratio_atual_threshold: float = 0.9) -> ScenarioResult:
        """
        Simula impacto de ajuste salarial para colaboradores abaixo do mercado
        
        Args:
            compa_ratio_minimo: Compa-ratio mínimo desejado
            compa_ratio_atual_threshold: Threshold para identificar quem precisa ajuste
        
        Returns:
            ScenarioResult com detalhes do cenário
        """
        if 'MonthlyIncome' not in self.df.columns or 'JobLevel' not in self.df.columns:
            return self._criar_resultado_vazio("Ajuste Salarial")
        
        # Calcular compa-ratio se não existir
        if 'Compa_Ratio' not in self.df.columns:
            # Usar mediana por JobLevel como referência
            mediana_por_nivel = self.df.groupby('JobLevel')['MonthlyIncome'].median()
            self.df['Compa_Ratio'] = self.df.apply(
                lambda x: x['MonthlyIncome'] / mediana_por_nivel.get(x['JobLevel'], x['MonthlyIncome']),
                axis=1
            )
        
        # Identificar colaboradores elegíveis
        elegiveis = self.df[self.df['Compa_Ratio'] < compa_ratio_atual_threshold].copy()
        
        if len(elegiveis) == 0:
            return self._criar_resultado_vazio("Ajuste Salarial")
        
        # Calcular ajuste necessário
        ajuste_necessario = elegiveis.apply(
            lambda x: (compa_ratio_minimo - x['Compa_Ratio']) * x['MonthlyIncome'],
            axis=1
        )
        ajuste_necessario = np.maximum(ajuste_necessario, 0)
        
        custo_mensal = ajuste_necessario.sum()
        custo_anual = custo_mensal * 12
        
        # Simular impacto
        df_cenario = self.df.copy()
        df_cenario.loc[elegiveis.index, 'Compa_Ratio'] = compa_ratio_minimo
        df_cenario.loc[elegiveis.index, 'MonthlyIncome'] *= (compa_ratio_minimo / elegiveis['Compa_Ratio'])
        df_cenario.loc[elegiveis.index, 'Flight_Risk_Score'] *= 0.65  # 35% redução
        
        prob_original = self.df['Flight_Risk_Score'].mean()
        prob_novo = df_cenario['Flight_Risk_Score'].mean()
        reducao_percentual = (prob_original - prob_novo) / prob_original * 100
        
        turnover_evitado = int(len(elegiveis) * 0.35)
        economia = turnover_evitado * self.CUSTO_MEDIO_TURNOVER
        roi = (economia - custo_anual) / custo_anual * 100 if custo_anual > 0 else 0
        payback = custo_anual / (economia / 12) if economia > 0 else float('inf')
        
        return ScenarioResult(
            nome="Ajuste Salarial",
            descricao=f"Elevar Compa-Ratio de colaboradores abaixo de {compa_ratio_atual_threshold:.0%} para {compa_ratio_minimo:.0%}",
            colaboradores_impactados=len(elegiveis),
            reducao_turnover_estimada=reducao_percentual,
            economia_gerada=economia,
            custo_investimento=custo_anual,
            roi_estimado=roi,
            payback_meses=payback,
            detalhes={
                'ajuste_mensal_total': custo_mensal,
                'ajuste_medio_por_pessoa': custo_mensal / len(elegiveis),
                'compa_ratio_medio_atual': elegiveis['Compa_Ratio'].mean(),
                'departamentos': elegiveis['Department'].value_counts().to_dict() if 'Department' in elegiveis.columns else {}
            }
        )
    
    def simular_programa_treinamento(self,
                                      treinamentos_adicionais: int = 2) -> ScenarioResult:
        """
        Simula impacto de programa de treinamento intensificado
        
        Args:
            treinamentos_adicionais: Número de treinamentos adicionais por pessoa
        
        Returns:
            ScenarioResult com detalhes do cenário
        """
        if 'TrainingTimesLastYear' not in self.df.columns:
            return self._criar_resultado_vazio("Programa de Treinamento")
        
        # Focar em quem tem poucos treinamentos e alto risco
        elegiveis = self.df[
            (self.df['TrainingTimesLastYear'] <= 2) & 
            (self.df['Flight_Risk_Score'] > 0.3)
        ].copy()
        
        if len(elegiveis) == 0:
            # Expandir critérios
            elegiveis = self.df[self.df['TrainingTimesLastYear'] <= 2].copy()
        
        if len(elegiveis) == 0:
            return self._criar_resultado_vazio("Programa de Treinamento")
        
        # Simular impacto
        df_cenario = self.df.copy()
        df_cenario.loc[elegiveis.index, 'TrainingTimesLastYear'] += treinamentos_adicionais
        df_cenario.loc[elegiveis.index, 'Flight_Risk_Score'] *= 0.85  # 15% redução
        
        prob_original = self.df['Flight_Risk_Score'].mean()
        prob_novo = df_cenario['Flight_Risk_Score'].mean()
        reducao_percentual = (prob_original - prob_novo) / prob_original * 100
        
        custo = len(elegiveis) * treinamentos_adicionais * self.CUSTO_TREINAMENTO
        turnover_evitado = int(len(elegiveis) * 0.15)
        economia = turnover_evitado * self.CUSTO_MEDIO_TURNOVER
        roi = (economia - custo) / custo * 100 if custo > 0 else 0
        payback = custo / (economia / 12) if economia > 0 else float('inf')
        
        return ScenarioResult(
            nome="Programa de Treinamento",
            descricao=f"Adicionar {treinamentos_adicionais} treinamentos para colaboradores com poucos treinamentos",
            colaboradores_impactados=len(elegiveis),
            reducao_turnover_estimada=reducao_percentual,
            economia_gerada=economia,
            custo_investimento=custo,
            roi_estimado=roi,
            payback_meses=payback,
            detalhes={
                'treinamentos_totais': len(elegiveis) * treinamentos_adicionais,
                'media_treinamentos_atual': elegiveis['TrainingTimesLastYear'].mean(),
                'departamentos': elegiveis['Department'].value_counts().to_dict() if 'Department' in elegiveis.columns else {}
            }
        )
    
    def simular_programa_work_life_balance(self) -> ScenarioResult:
        """
        Simula impacto de programa de melhoria de work-life balance
        
        Returns:
            ScenarioResult com detalhes do cenário
        """
        if 'WorkLifeBalance' not in self.df.columns:
            return self._criar_resultado_vazio("Programa Work-Life Balance")
        
        # Focar em quem tem baixo WLB
        elegiveis = self.df[self.df['WorkLifeBalance'] <= 2].copy()
        
        if len(elegiveis) == 0:
            return self._criar_resultado_vazio("Programa Work-Life Balance")
        
        # Simular melhoria de 1 ponto no WLB
        df_cenario = self.df.copy()
        df_cenario.loc[elegiveis.index, 'WorkLifeBalance'] = np.minimum(
            df_cenario.loc[elegiveis.index, 'WorkLifeBalance'] + 1, 4
        )
        df_cenario.loc[elegiveis.index, 'Flight_Risk_Score'] *= 0.75  # 25% redução
        
        prob_original = self.df['Flight_Risk_Score'].mean()
        prob_novo = df_cenario['Flight_Risk_Score'].mean()
        reducao_percentual = (prob_original - prob_novo) / prob_original * 100
        
        # Custos de programa de flexibilidade
        custo_por_pessoa = 1500  # Home office, flexibilidade, etc.
        custo = len(elegiveis) * custo_por_pessoa
        
        turnover_evitado = int(len(elegiveis) * 0.25)
        economia = turnover_evitado * self.CUSTO_MEDIO_TURNOVER
        roi = (economia - custo) / custo * 100 if custo > 0 else 0
        payback = custo / (economia / 12) if economia > 0 else float('inf')
        
        return ScenarioResult(
            nome="Programa Work-Life Balance",
            descricao="Implementar políticas de flexibilidade para colaboradores com baixo equilíbrio",
            colaboradores_impactados=len(elegiveis),
            reducao_turnover_estimada=reducao_percentual,
            economia_gerada=economia,
            custo_investimento=custo,
            roi_estimado=roi,
            payback_meses=payback,
            detalhes={
                'wlb_medio_atual': elegiveis['WorkLifeBalance'].mean(),
                'percentual_empresa': len(elegiveis) / len(self.df) * 100,
                'departamentos': elegiveis['Department'].value_counts().to_dict() if 'Department' in elegiveis.columns else {}
            }
        )
    
    def executar_todos_cenarios(self) -> List[ScenarioResult]:
        """
        Executa todos os cenários de simulação
        
        Returns:
            Lista de ScenarioResult ordenados por ROI
        """
        cenarios = [
            self.simular_aumento_promocoes(),
            self.simular_politica_anti_overtime(),
            self.simular_ajuste_salarial(),
            self.simular_programa_treinamento(),
            self.simular_programa_work_life_balance()
        ]
        
        # Ordenar por ROI
        cenarios_validos = [c for c in cenarios if c.colaboradores_impactados > 0]
        cenarios_validos.sort(key=lambda x: x.roi_estimado, reverse=True)
        
        return cenarios_validos
    
    def gerar_matriz_decisao(self) -> pd.DataFrame:
        """
        Gera matriz de decisão estratégica por colaborador
        
        Returns:
            DataFrame com classificação e ação recomendada
        """
        df = self.df.copy()
        
        # Definir critérios
        high_performance = df['PerformanceRating'] >= 3 if 'PerformanceRating' in df.columns else pd.Series([False]*len(df))
        high_risk = df['Flight_Risk_Score'] >= 0.4
        low_engagement = df['JobSatisfaction'] <= 2 if 'JobSatisfaction' in df.columns else pd.Series([False]*len(df))
        
        # Calcular Compa_Ratio se não existir
        if 'Compa_Ratio' not in df.columns and 'MonthlyIncome' in df.columns:
            if 'JobLevel' in df.columns:
                mediana_por_nivel = df.groupby('JobLevel')['MonthlyIncome'].median()
                df['Compa_Ratio'] = df.apply(
                    lambda x: x['MonthlyIncome'] / mediana_por_nivel.get(x['JobLevel'], x['MonthlyIncome']),
                    axis=1
                )
            else:
                df['Compa_Ratio'] = df['MonthlyIncome'] / df['MonthlyIncome'].median()
        
        high_salary = df['Compa_Ratio'] >= 1.1 if 'Compa_Ratio' in df.columns else pd.Series([False]*len(df))
        low_performance = df['PerformanceRating'] <= 2 if 'PerformanceRating' in df.columns else pd.Series([False]*len(df))
        
        # Classificar
        def classificar(row_idx):
            hp = high_performance.iloc[row_idx] if len(high_performance) > row_idx else False
            hr = high_risk.iloc[row_idx] if len(high_risk) > row_idx else False
            le = low_engagement.iloc[row_idx] if len(low_engagement) > row_idx else False
            hs = high_salary.iloc[row_idx] if len(high_salary) > row_idx else False
            lp = low_performance.iloc[row_idx] if len(low_performance) > row_idx else False
            
            if hp and hr:
                return ('🔴 Reter a Todo Custo', 'One-on-one, Promoção Acelerada, Retenção', 'Imediata (7 dias)')
            elif not hp and le:
                return ('🟠 Desenvolver', 'PDI, Mentoria, Novos Desafios', '30 dias')
            elif lp and hs:
                return ('🟡 Monitorar', 'PIP, Realocação, Avaliação', '60 dias')
            elif hp and not hr:
                return ('🟢 Celebrar', 'Reconhecimento, Carreira, Retenção', 'Ongoing')
            elif lp and hr:
                return ('⚪ Investigar', 'Diagnóstico, Fit Cultural', '15 dias')
            else:
                return ('🔵 Acompanhar', 'Monitoramento Regular', '90 dias')
        
        resultados = [classificar(i) for i in range(len(df))]
        
        df['Quadrante'] = [r[0] for r in resultados]
        df['Acao_Recomendada'] = [r[1] for r in resultados]
        df['Urgencia'] = [r[2] for r in resultados]
        
        # Selecionar colunas relevantes
        colunas_base = ['EmployeeNumber'] if 'EmployeeNumber' in df.columns else []
        colunas_extras = ['Department', 'JobRole', 'PerformanceRating', 'Flight_Risk_Score', 
                         'Quadrante', 'Acao_Recomendada', 'Urgencia']
        colunas_finais = colunas_base + [c for c in colunas_extras if c in df.columns]
        
        return df[colunas_finais]
    
    def gerar_resumo_cenarios(self) -> Dict:
        """
        Gera resumo consolidado de todos os cenários
        
        Returns:
            Dicionário com resumo dos cenários
        """
        cenarios = self.executar_todos_cenarios()
        
        if not cenarios:
            return {'erro': 'Nenhum cenário válido encontrado'}
        
        total_investimento = sum(c.custo_investimento for c in cenarios)
        total_economia = sum(c.economia_gerada for c in cenarios)
        total_impactados = sum(c.colaboradores_impactados for c in cenarios)
        
        return {
            'cenarios': [
                {
                    'nome': c.nome,
                    'descricao': c.descricao,
                    'colaboradores_impactados': c.colaboradores_impactados,
                    'reducao_turnover': f'{c.reducao_turnover_estimada:.1f}%',
                    'economia': f'R$ {c.economia_gerada:,.0f}',
                    'investimento': f'R$ {c.custo_investimento:,.0f}',
                    'roi': f'{c.roi_estimado:.0f}%',
                    'payback': f'{c.payback_meses:.1f} meses' if c.payback_meses < 100 else 'N/A',
                    'detalhes': c.detalhes
                }
                for c in cenarios
            ],
            'resumo': {
                'total_investimento': f'R$ {total_investimento:,.0f}',
                'total_economia_potencial': f'R$ {total_economia:,.0f}',
                'roi_consolidado': f'{(total_economia - total_investimento) / total_investimento * 100:.0f}%' if total_investimento > 0 else 'N/A',
                'colaboradores_totais_impactados': total_impactados,
                'melhor_roi': cenarios[0].nome if cenarios else 'N/A'
            }
        }
    
    def _criar_resultado_vazio(self, nome: str) -> ScenarioResult:
        """Cria resultado vazio para cenário não aplicável"""
        return ScenarioResult(
            nome=nome,
            descricao="Cenário não aplicável aos dados disponíveis",
            colaboradores_impactados=0,
            reducao_turnover_estimada=0,
            economia_gerada=0,
            custo_investimento=0,
            roi_estimado=0,
            payback_meses=0,
            detalhes={}
        )


# Teste do módulo
if __name__ == "__main__":
    # Carregar dados
    df = pd.read_csv('WA_Fn-UseC_-HR-Employee-Attrition.csv')
    
    print("="*60)
    print("WHAT-IF SIMULATOR - PEOPLE ANALYTICS")
    print("="*60)
    
    # Criar simulador
    simulator = WhatIfSimulator(df)
    
    # Executar todos os cenários
    resumo = simulator.gerar_resumo_cenarios()
    
    print("\n📊 CENÁRIOS DE SIMULAÇÃO:")
    print("-"*60)
    
    for cenario in resumo['cenarios']:
        print(f"\n🎯 {cenario['nome']}")
        print(f"   Descrição: {cenario['descricao']}")
        print(f"   Colaboradores impactados: {cenario['colaboradores_impactados']}")
        print(f"   Redução de Turnover: {cenario['reducao_turnover']}")
        print(f"   Economia potencial: {cenario['economia']}")
        print(f"   Investimento: {cenario['investimento']}")
        print(f"   ROI: {cenario['roi']}")
        print(f"   Payback: {cenario['payback']}")
    
    print("\n" + "="*60)
    print("📈 RESUMO CONSOLIDADO:")
    print("-"*60)
    print(f"   Total Investimento: {resumo['resumo']['total_investimento']}")
    print(f"   Total Economia Potencial: {resumo['resumo']['total_economia_potencial']}")
    print(f"   ROI Consolidado: {resumo['resumo']['roi_consolidado']}")
    print(f"   Colaboradores Impactados: {resumo['resumo']['colaboradores_totais_impactados']}")
    print(f"   Melhor ROI: {resumo['resumo']['melhor_roi']}")
    
    # Gerar matriz de decisão
    print("\n" + "="*60)
    print("📋 MATRIZ DE DECISÃO (amostra):")
    print("-"*60)
    matriz = simulator.gerar_matriz_decisao()
    print(matriz.groupby('Quadrante').size().sort_values(ascending=False))
