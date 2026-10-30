"""
Análise de Sobrevivência - PROMPT 2
Kaplan-Meier, Hazard Rates, Curvas de Retenção por Segmento
People Analytics Dashboard - BB Previdência
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


class SurvivalAnalyzer:
    """
    Análise de Sobrevivência para People Analytics
    Implementação de Kaplan-Meier sem dependências externas
    """
    
    def __init__(self, df):
        self.df = df.copy()
        self.results = {}
        
    def calculate_kaplan_meier(self, time_col='YearsAtCompany', event_col='Attrition_Binary', 
                                group_col=None, max_time=None):
        """
        Calcula curva de Kaplan-Meier
        
        Args:
            time_col: Coluna de tempo (tenure)
            event_col: Coluna de evento (attrition = 1)
            group_col: Coluna para estratificação (opcional)
            max_time: Tempo máximo para análise
        """
        df = self.df.copy()
        
        if max_time is None:
            max_time = int(df[time_col].max())
        
        if group_col:
            # Análise estratificada
            groups = df[group_col].unique()
            results = {}
            
            for group in groups:
                group_df = df[df[group_col] == group]
                results[str(group)] = self._compute_km_curve(
                    group_df, time_col, event_col, max_time
                )
            
            return results
        else:
            # Análise geral
            return self._compute_km_curve(df, time_col, event_col, max_time)
    
    def _compute_km_curve(self, df, time_col, event_col, max_time):
        """
        Computa curva KM para um grupo
        """
        survival_table = []
        cumulative_survival = 1.0
        
        for t in range(0, max_time + 1):
            # At risk: todos com tempo >= t
            at_risk = len(df[df[time_col] >= t])
            
            # Events: attrition no tempo t
            events = len(df[(df[time_col] == t) & (df[event_col] == 1)])
            
            # Censored: ainda ativos no tempo t (sem evento)
            censored = len(df[(df[time_col] == t) & (df[event_col] == 0)])
            
            # Hazard rate
            hazard = events / at_risk if at_risk > 0 else 0
            
            # Survival rate
            survival = 1 - hazard
            cumulative_survival *= survival
            
            # Confidence interval (Greenwood's formula)
            if at_risk > 0 and at_risk > events:
                variance = (cumulative_survival ** 2) * (events / (at_risk * (at_risk - events)))
            else:
                variance = 0
            
            std_error = np.sqrt(variance) if variance > 0 else 0
            ci_lower = max(0, cumulative_survival - 1.96 * std_error)
            ci_upper = min(1, cumulative_survival + 1.96 * std_error)
            
            survival_table.append({
                'time': t,
                'at_risk': at_risk,
                'events': events,
                'censored': censored,
                'hazard_rate': hazard,
                'survival_rate': survival,
                'cumulative_survival': cumulative_survival,
                'std_error': std_error,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper
            })
        
        # Métricas sumárias
        median_survival = None
        for row in survival_table:
            if row['cumulative_survival'] <= 0.5:
                median_survival = row['time']
                break
        
        # Restricted Mean Survival Time (RMST)
        rmst = sum([row['cumulative_survival'] for row in survival_table])
        
        return {
            'survival_table': survival_table,
            'median_survival': median_survival,
            'rmst': rmst,
            'final_survival': survival_table[-1]['cumulative_survival'] if survival_table else 0,
            'total_events': sum([row['events'] for row in survival_table]),
            'total_at_risk_start': survival_table[0]['at_risk'] if survival_table else 0
        }
    
    def log_rank_test(self, group_col):
        """
        Teste Log-Rank para comparar curvas de sobrevivência entre grupos
        """
        df = self.df.copy()
        
        groups = df[group_col].unique()
        if len(groups) != 2:
            return {'error': 'Log-rank test requer exatamente 2 grupos'}
        
        group1_name, group2_name = groups[0], groups[1]
        group1 = df[df[group_col] == group1_name]
        group2 = df[df[group_col] == group2_name]
        
        # Calcular estatística log-rank
        max_time = int(df['YearsAtCompany'].max())
        
        observed_1 = 0
        expected_1 = 0
        variance = 0
        
        for t in range(0, max_time + 1):
            # At risk em cada grupo
            n1 = len(group1[group1['YearsAtCompany'] >= t])
            n2 = len(group2[group2['YearsAtCompany'] >= t])
            n_total = n1 + n2
            
            if n_total == 0:
                continue
            
            # Eventos em cada grupo
            d1 = len(group1[(group1['YearsAtCompany'] == t) & (group1['Attrition_Binary'] == 1)])
            d2 = len(group2[(group2['YearsAtCompany'] == t) & (group2['Attrition_Binary'] == 1)])
            d_total = d1 + d2
            
            if d_total == 0 or n_total <= 1:
                continue
            
            # Eventos esperados no grupo 1
            e1 = n1 * d_total / n_total
            
            observed_1 += d1
            expected_1 += e1
            
            # Variância
            if n_total > 1:
                v = (n1 * n2 * d_total * (n_total - d_total)) / (n_total ** 2 * (n_total - 1))
                variance += v
        
        # Estatística chi-quadrado
        if variance > 0:
            chi2 = (observed_1 - expected_1) ** 2 / variance
            p_value = 1 - stats.chi2.cdf(chi2, df=1)
        else:
            chi2 = 0
            p_value = 1.0
        
        return {
            'group1': str(group1_name),
            'group2': str(group2_name),
            'observed_1': observed_1,
            'expected_1': expected_1,
            'observed_2': int(df[df[group_col] == group2_name]['Attrition_Binary'].sum()),
            'chi2_statistic': chi2,
            'p_value': p_value,
            'is_significant': p_value < 0.05,
            'interpretation': f"Diferença significativa entre grupos (p={p_value:.4f})" if p_value < 0.05 
                             else f"Sem diferença significativa (p={p_value:.4f})"
        }
    
    def identify_critical_periods(self, threshold=0.1):
        """
        Identifica períodos críticos de alto risco de saída
        """
        km_results = self.calculate_kaplan_meier()
        survival_table = km_results['survival_table']
        
        critical_periods = []
        
        for row in survival_table:
            if row['hazard_rate'] >= threshold:
                critical_periods.append({
                    'year': row['time'],
                    'hazard_rate': row['hazard_rate'],
                    'at_risk': row['at_risk'],
                    'events': row['events'],
                    'cumulative_survival': row['cumulative_survival'],
                    'risk_level': 'Crítico' if row['hazard_rate'] >= 0.2 else 'Alto',
                    'recommendation': self._get_period_recommendation(row['time'])
                })
        
        return critical_periods
    
    def _get_period_recommendation(self, year):
        """
        Retorna recomendação baseada no período crítico
        """
        recommendations = {
            0: "Fortalecer onboarding e integração cultural",
            1: "Aumentar acompanhamento no primeiro ano, mentoria",
            2: "Revisar expectativas de carreira, desenvolvimento",
            3: "Avaliar promoção ou movimentação lateral",
            4: "Plano de retenção, projeto especial",
            5: "Discussão de longo prazo, liderança"
        }
        return recommendations.get(year, "Monitorar e avaliar caso a caso")
    
    def analyze_by_segment(self):
        """
        Análise de sobrevivência por múltiplos segmentos
        """
        df = self.df.copy()
        
        segments = {
            'OverTime': 'Hora Extra',
            'Department': 'Departamento',
            'JobLevel': 'Nível do Cargo',
            'MaritalStatus': 'Estado Civil'
        }
        
        segment_analysis = {}
        
        for col, label in segments.items():
            if col not in df.columns:
                continue
            
            # Curvas por grupo
            km_by_group = self.calculate_kaplan_meier(group_col=col)
            
            # Log-rank test se binário
            if len(df[col].unique()) == 2:
                log_rank = self.log_rank_test(col)
            else:
                log_rank = None
            
            # Resumo por grupo
            group_summary = []
            for group_name, group_data in km_by_group.items():
                group_summary.append({
                    'group': group_name,
                    'median_survival': group_data['median_survival'],
                    'rmst': group_data['rmst'],
                    'final_survival': group_data['final_survival'],
                    'total_events': group_data['total_events'],
                    'event_rate': group_data['total_events'] / group_data['total_at_risk_start'] 
                                  if group_data['total_at_risk_start'] > 0 else 0
                })
            
            segment_analysis[col] = {
                'label': label,
                'km_curves': km_by_group,
                'log_rank_test': log_rank,
                'group_summary': group_summary
            }
        
        self.results['segment_analysis'] = segment_analysis
        return segment_analysis
    
    def calculate_tenure_milestones(self):
        """
        Calcula taxa de retenção em marcos importantes
        """
        km_results = self.calculate_kaplan_meier()
        survival_table = km_results['survival_table']
        
        milestones = {
            1: '1 ano',
            2: '2 anos',
            3: '3 anos',
            5: '5 anos',
            10: '10 anos'
        }
        
        milestone_data = []
        
        for year, label in milestones.items():
            if year < len(survival_table):
                row = survival_table[year]
                milestone_data.append({
                    'year': year,
                    'label': label,
                    'retention_rate': row['cumulative_survival'] * 100,
                    'attrition_rate': (1 - row['cumulative_survival']) * 100,
                    'ci_lower': row['ci_lower'] * 100,
                    'ci_upper': row['ci_upper'] * 100,
                    'at_risk': row['at_risk']
                })
        
        return milestone_data
    
    def run_all_analyses(self):
        """
        Executa todas as análises de sobrevivência
        """
        print("Calculando curva Kaplan-Meier geral...")
        self.results['overall_km'] = self.calculate_kaplan_meier()
        
        print("Identificando períodos críticos...")
        self.results['critical_periods'] = self.identify_critical_periods()
        
        print("Analisando por segmentos...")
        self.results['segments'] = self.analyze_by_segment()
        
        print("Calculando milestones de tenure...")
        self.results['milestones'] = self.calculate_tenure_milestones()
        
        # Resumo executivo
        self.results['summary'] = self._generate_summary()
        
        return self.results
    
    def _generate_summary(self):
        """
        Gera resumo executivo da análise de sobrevivência
        """
        overall = self.results.get('overall_km', {})
        critical = self.results.get('critical_periods', [])
        milestones = self.results.get('milestones', [])
        
        summary = {
            'median_tenure': overall.get('median_survival'),
            'rmst': overall.get('rmst'),
            'final_retention': overall.get('final_survival', 0) * 100,
            'critical_periods_count': len(critical),
            'highest_risk_year': critical[0]['year'] if critical else None,
            'highest_risk_rate': critical[0]['hazard_rate'] if critical else None,
            'key_milestones': milestones[:3],
            'key_findings': []
        }
        
        # Finding 1: Taxa de retenção no primeiro ano
        if milestones:
            year1 = next((m for m in milestones if m['year'] == 1), None)
            if year1:
                summary['key_findings'].append({
                    'title': 'Retenção no Primeiro Ano',
                    'finding': f"{year1['retention_rate']:.1f}% dos colaboradores permanecem após 1 ano"
                })
        
        # Finding 2: Período mais crítico
        if critical:
            summary['key_findings'].append({
                'title': 'Período de Maior Risco',
                'finding': f"Ano {critical[0]['year']} apresenta hazard rate de {critical[0]['hazard_rate']:.1%}"
            })
        
        # Finding 3: Comparação Overtime
        segments = self.results.get('segments', {})
        if 'OverTime' in segments and segments['OverTime'].get('log_rank_test'):
            lr = segments['OverTime']['log_rank_test']
            if lr.get('is_significant'):
                summary['key_findings'].append({
                    'title': 'Impacto de Hora Extra',
                    'finding': f"Diferença significativa na sobrevivência entre quem faz e não faz hora extra (p={lr['p_value']:.4f})"
                })
        
        return summary


def run_survival_analysis(df):
    """
    Função helper para executar análise completa
    """
    analyzer = SurvivalAnalyzer(df)
    results = analyzer.run_all_analyses()
    
    return {
        'results': results,
        'analyzer': analyzer
    }
