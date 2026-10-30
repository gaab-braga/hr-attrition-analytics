"""Análises complementares usadas no dashboard: segmentos, sobrevivência simplificada e cenários."""

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')


class PeopleScienceAnalyzer:
    """
    Classe principal para análises avançadas de People Analytics
    Similar ao MarketingScienceAnalyzer do campaign_dashboard
    """
    
    def __init__(self, df):
        self.df = df.copy()
        self.results = {}
        
    def run_all_analyses(self):
        """Executa todas as análises disponíveis"""
        self.results['survival_analysis'] = self.survival_analysis()
        self.results['segmentation'] = self.employee_segmentation()
        self.results['department_analysis'] = self.analyze_by_department()
        self.results['tenure_analysis'] = self.analyze_by_tenure()
        self.results['compensation_analysis'] = self.compensation_analysis()
        self.results['risk_matrix'] = self.create_risk_matrix()
        self.results['scenario_simulations'] = self.run_scenario_simulations()
        return self.results
    
    def survival_analysis(self):
        """
        Análise de Sobrevivência (Kaplan-Meier simplificada)
        Mostra probabilidade de retenção ao longo do tempo
        """
        # Criar curvas de sobrevivência por tenure
        df = self.df.copy()
        
        # Calcular taxas de sobrevivência por ano de empresa
        survival_data = []
        max_tenure = min(int(df['YearsAtCompany'].max()), 20)
        
        for year in range(0, max_tenure + 1):
            at_risk = len(df[df['YearsAtCompany'] >= year])
            churned = len(df[(df['YearsAtCompany'] == year) & (df['Attrition'] == 'Yes')])
            
            if at_risk > 0:
                hazard = churned / at_risk
                survival = 1 - hazard
            else:
                hazard = 0
                survival = 1
                
            survival_data.append({
                'year': year,
                'at_risk': at_risk,
                'churned': churned,
                'hazard_rate': hazard,
                'survival_rate': survival
            })
        
        # Calcular curva cumulativa
        cumulative_survival = 1.0
        for data in survival_data:
            cumulative_survival *= data['survival_rate']
            data['cumulative_survival'] = cumulative_survival
        
        # Análise por segmentos
        segments = {}
        for segment in ['Department', 'JobLevel', 'OverTime']:
            if segment in df.columns:
                seg_analysis = []
                for value in df[segment].unique():
                    seg_df = df[df[segment] == value]
                    total = len(seg_df)
                    churned = len(seg_df[seg_df['Attrition'] == 'Yes'])
                    retained = total - churned
                    
                    # Median tenure
                    median_tenure = seg_df['YearsAtCompany'].median()
                    
                    seg_analysis.append({
                        'segment': str(value),
                        'total': total,
                        'churned': churned,
                        'retained': retained,
                        'attrition_rate': churned / total if total > 0 else 0,
                        'median_tenure': median_tenure
                    })
                segments[segment] = seg_analysis
        
        # Identificar períodos críticos
        critical_periods = []
        for data in survival_data:
            if data['hazard_rate'] > 0.1:  # >10% de risco
                critical_periods.append({
                    'year': data['year'],
                    'hazard_rate': data['hazard_rate'],
                    'recommendation': f"Alto risco de saída no ano {data['year']} - Implementar programa de retenção"
                })
        
        return {
            'survival_curve': survival_data,
            'segment_analysis': segments,
            'critical_periods': critical_periods,
            'median_tenure': df[df['Attrition'] == 'No']['YearsAtCompany'].median(),
            'avg_tenure_churned': df[df['Attrition'] == 'Yes']['YearsAtCompany'].mean()
        }
    
    def employee_segmentation(self, n_clusters=4):
        """
        Segmentação de colaboradores usando clustering
        """
        df = self.df.copy()
        
        # Features para clustering
        cluster_features = [
            'Age', 'MonthlyIncome', 'YearsAtCompany', 'JobSatisfaction',
            'EnvironmentSatisfaction', 'WorkLifeBalance', 'JobLevel',
            'Flight_Risk_Score', 'Engagement_Index'
        ]
        cluster_features = [f for f in cluster_features if f in df.columns]
        
        X = df[cluster_features].fillna(df[cluster_features].median())
        
        # Normalizar
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df['Cluster'] = kmeans.fit_predict(X_scaled)
        
        # Analisar clusters
        cluster_profiles = []
        cluster_names = {
            0: 'Estáveis',
            1: 'Alto Potencial',
            2: 'Em Risco',
            3: 'Veteranos'
        }
        
        for cluster in range(n_clusters):
            cluster_df = df[df['Cluster'] == cluster]
            
            profile = {
                'cluster_id': cluster,
                'cluster_name': cluster_names.get(cluster, f'Cluster {cluster}'),
                'count': len(cluster_df),
                'pct_total': len(cluster_df) / len(df) * 100,
                'avg_age': cluster_df['Age'].mean(),
                'avg_tenure': cluster_df['YearsAtCompany'].mean(),
                'avg_income': cluster_df['MonthlyIncome'].mean(),
                'avg_satisfaction': cluster_df['JobSatisfaction'].mean(),
                'avg_flight_risk': cluster_df['Flight_Risk_Score'].mean() if 'Flight_Risk_Score' in cluster_df else 0,
                'avg_engagement': cluster_df['Engagement_Index'].mean() if 'Engagement_Index' in cluster_df else 0,
                'attrition_rate': cluster_df['Attrition_Binary'].mean() * 100 if 'Attrition_Binary' in cluster_df else 0,
                'departments': cluster_df['Department'].value_counts().head(3).to_dict(),
                'job_levels': cluster_df['JobLevel'].value_counts().to_dict()
            }
            
            # Definir nome baseado nas características
            if profile['avg_flight_risk'] > 60:
                profile['cluster_name'] = 'Em Risco'
            elif profile['avg_tenure'] > 10:
                profile['cluster_name'] = 'Veteranos'
            elif profile['avg_engagement'] > 70 and profile['attrition_rate'] < 10:
                profile['cluster_name'] = 'Alto Potencial'
            else:
                profile['cluster_name'] = 'Estáveis'
            
            cluster_profiles.append(profile)
        
        return {
            'n_clusters': n_clusters,
            'profiles': cluster_profiles,
            'features_used': cluster_features
        }
    
    def analyze_by_department(self):
        """
        Análise detalhada por departamento
        """
        df = self.df.copy()
        
        department_metrics = []
        for dept in df['Department'].unique():
            dept_df = df[df['Department'] == dept]
            
            metrics = {
                'department': dept,
                'headcount': len(dept_df),
                'pct_total': len(dept_df) / len(df) * 100,
                'avg_age': dept_df['Age'].mean(),
                'avg_tenure': dept_df['YearsAtCompany'].mean(),
                'avg_income': dept_df['MonthlyIncome'].mean(),
                'avg_satisfaction': dept_df['JobSatisfaction'].mean(),
                'attrition_rate': dept_df['Attrition_Binary'].mean() * 100,
                'overtime_rate': len(dept_df[dept_df['OverTime'] == 'Yes']) / len(dept_df) * 100,
                'avg_flight_risk': dept_df['Flight_Risk_Score'].mean() if 'Flight_Risk_Score' in dept_df else 0,
                'high_risk_count': len(dept_df[dept_df['Flight_Risk_Score'] > 70]) if 'Flight_Risk_Score' in dept_df else 0,
                'avg_engagement': dept_df['Engagement_Index'].mean() if 'Engagement_Index' in dept_df else 0,
                'promotion_rate': len(dept_df[dept_df['YearsSinceLastPromotion'] == 0]) / len(dept_df) * 100,
                'avg_training': dept_df['TrainingTimesLastYear'].mean(),
                'gender_distribution': dept_df['Gender'].value_counts(normalize=True).to_dict(),
                'top_roles': dept_df['JobRole'].value_counts().head(3).to_dict()
            }
            
            department_metrics.append(metrics)
        
        # Ranking de departamentos por risco
        department_metrics = sorted(department_metrics, key=lambda x: x['attrition_rate'], reverse=True)
        
        # Identificar department com maior problema
        worst_dept = department_metrics[0]
        best_dept = department_metrics[-1]
        
        return {
            'department_details': department_metrics,
            'highest_risk': worst_dept['department'],
            'lowest_risk': best_dept['department'],
            'risk_spread': worst_dept['attrition_rate'] - best_dept['attrition_rate']
        }
    
    def analyze_by_tenure(self):
        """
        Análise por faixa de tempo de empresa
        """
        df = self.df.copy()
        
        # Criar faixas se não existirem
        if 'Tenure_Band' not in df.columns:
            df['Tenure_Band'] = pd.cut(
                df['YearsAtCompany'],
                bins=[0, 1, 2, 5, 10, 40],
                labels=['<1 ano', '1-2 anos', '2-5 anos', '5-10 anos', '10+ anos'],
                include_lowest=True
            )
        
        tenure_metrics = []
        for band in df['Tenure_Band'].cat.categories:
            band_df = df[df['Tenure_Band'] == band]
            
            if len(band_df) == 0:
                continue
                
            metrics = {
                'tenure_band': str(band),
                'headcount': len(band_df),
                'pct_total': len(band_df) / len(df) * 100,
                'avg_age': band_df['Age'].mean(),
                'avg_income': band_df['MonthlyIncome'].mean(),
                'avg_satisfaction': band_df['JobSatisfaction'].mean(),
                'attrition_rate': band_df['Attrition_Binary'].mean() * 100,
                'avg_flight_risk': band_df['Flight_Risk_Score'].mean() if 'Flight_Risk_Score' in band_df else 0,
                'avg_engagement': band_df['Engagement_Index'].mean() if 'Engagement_Index' in band_df else 0,
                'overtime_pct': len(band_df[band_df['OverTime'] == 'Yes']) / len(band_df) * 100,
                'promotion_waiting': band_df['YearsSinceLastPromotion'].mean()
            }
            
            tenure_metrics.append(metrics)
        
        return {
            'tenure_details': tenure_metrics,
            'highest_risk_band': max(tenure_metrics, key=lambda x: x['attrition_rate'])['tenure_band'] if tenure_metrics else None,
            'key_insight': self._generate_tenure_insight(tenure_metrics)
        }
    
    def _generate_tenure_insight(self, tenure_metrics):
        """Gera insight sobre tenure"""
        if not tenure_metrics:
            return "Dados insuficientes para análise"
        
        high_risk_bands = [t for t in tenure_metrics if t['attrition_rate'] > 20]
        if high_risk_bands:
            bands = [t['tenure_band'] for t in high_risk_bands]
            return f"Atenção especial às faixas {', '.join(bands)} com turnover acima de 20%"
        return "Turnover distribuído uniformemente entre as faixas de tenure"
    
    def compensation_analysis(self):
        """
        Análise de compensação e equidade salarial
        """
        df = self.df.copy()
        
        # Análise por Job Level
        level_analysis = []
        for level in sorted(df['JobLevel'].unique()):
            level_df = df[df['JobLevel'] == level]
            
            analysis = {
                'job_level': level,
                'headcount': len(level_df),
                'avg_salary': level_df['MonthlyIncome'].mean(),
                'median_salary': level_df['MonthlyIncome'].median(),
                'min_salary': level_df['MonthlyIncome'].min(),
                'max_salary': level_df['MonthlyIncome'].max(),
                'salary_spread': level_df['MonthlyIncome'].max() - level_df['MonthlyIncome'].min(),
                'std_salary': level_df['MonthlyIncome'].std(),
                'cv': level_df['MonthlyIncome'].std() / level_df['MonthlyIncome'].mean() * 100,
                'attrition_rate': level_df['Attrition_Binary'].mean() * 100
            }
            level_analysis.append(analysis)
        
        # Análise de equidade de gênero
        gender_pay = {}
        for dept in df['Department'].unique():
            dept_df = df[df['Department'] == dept]
            male_avg = dept_df[dept_df['Gender'] == 'Male']['MonthlyIncome'].mean()
            female_avg = dept_df[dept_df['Gender'] == 'Female']['MonthlyIncome'].mean()
            
            if male_avg > 0 and female_avg > 0:
                gap = (male_avg - female_avg) / male_avg * 100
                gender_pay[dept] = {
                    'male_avg': male_avg,
                    'female_avg': female_avg,
                    'gap_pct': gap,
                    'gap_status': 'Equitativo' if abs(gap) < 5 else 'Atenção' if abs(gap) < 10 else 'Crítico'
                }
        
        # Compa-Ratio analysis
        compa_analysis = {}
        if 'Compa_Ratio' in df.columns:
            compa_analysis = {
                'below_market': len(df[df['Compa_Ratio'] < 0.9]),
                'at_market': len(df[(df['Compa_Ratio'] >= 0.9) & (df['Compa_Ratio'] <= 1.1)]),
                'above_market': len(df[df['Compa_Ratio'] > 1.1]),
                'avg_compa_ratio': df['Compa_Ratio'].mean(),
                'below_market_attrition': df[df['Compa_Ratio'] < 0.9]['Attrition_Binary'].mean() * 100 if len(df[df['Compa_Ratio'] < 0.9]) > 0 else 0,
                'at_market_attrition': df[(df['Compa_Ratio'] >= 0.9) & (df['Compa_Ratio'] <= 1.1)]['Attrition_Binary'].mean() * 100
            }
        
        return {
            'level_analysis': level_analysis,
            'gender_pay_analysis': gender_pay,
            'compa_analysis': compa_analysis,
            'overall_median': df['MonthlyIncome'].median(),
            'overall_mean': df['MonthlyIncome'].mean()
        }
    
    def create_risk_matrix(self):
        """
        Matriz de risco: Flight Risk vs Critical Talent Score
        """
        df = self.df.copy()
        
        if 'Flight_Risk_Score' not in df.columns or 'Critical_Talent_Score' not in df.columns:
            return {'error': 'Scores não calculados'}
        
        # Criar quadrantes
        high_risk = df['Flight_Risk_Score'] > 50
        high_value = df['Critical_Talent_Score'] > 60
        
        quadrants = {
            'stars_at_risk': {
                'count': len(df[high_risk & high_value]),
                'pct': len(df[high_risk & high_value]) / len(df) * 100,
                'description': 'Alto valor e alto risco - Prioridade máxima de retenção',
                'action': 'Intervenção imediata com plano de retenção personalizado',
                'employees': df[high_risk & high_value][['EmployeeNumber', 'JobRole', 'Department', 'Flight_Risk_Score', 'Critical_Talent_Score']].head(10).to_dict('records') if len(df[high_risk & high_value]) > 0 else []
            },
            'stars_secure': {
                'count': len(df[~high_risk & high_value]),
                'pct': len(df[~high_risk & high_value]) / len(df) * 100,
                'description': 'Alto valor e engajado - Desenvolver e reter',
                'action': 'Programas de desenvolvimento e sucessão',
                'employees': []
            },
            'low_value_at_risk': {
                'count': len(df[high_risk & ~high_value]),
                'pct': len(df[high_risk & ~high_value]) / len(df) * 100,
                'description': 'Baixo valor e alto risco - Avaliar custo-benefício',
                'action': 'Analisar se vale investir em retenção',
                'employees': []
            },
            'solid_performers': {
                'count': len(df[~high_risk & ~high_value]),
                'pct': len(df[~high_risk & ~high_value]) / len(df) * 100,
                'description': 'Base sólida - Manter engajamento',
                'action': 'Manter políticas de engajamento padrão',
                'employees': []
            }
        }
        
        # Custo total em risco (Stars at Risk)
        stars_at_risk_df = df[high_risk & high_value]
        if len(stars_at_risk_df) > 0:
            cost_at_risk = (stars_at_risk_df['MonthlyIncome'] * 6).sum()
        else:
            cost_at_risk = 0
        
        return {
            'quadrants': quadrants,
            'total_high_risk': len(df[high_risk]),
            'total_high_value': len(df[high_value]),
            'cost_at_risk': cost_at_risk,
            'priority_count': len(df[high_risk & high_value])
        }
    
    def run_scenario_simulations(self):
        """
        Executa simulações de cenários what-if
        """
        df = self.df.copy()
        
        scenarios = {}
        
        # Cenário 1: Eliminar overtime
        overtime_group = df[df['OverTime'] == 'Yes']
        no_overtime_group = df[df['OverTime'] == 'No']
        
        overtime_attrition = overtime_group['Attrition_Binary'].mean()
        no_overtime_attrition = no_overtime_group['Attrition_Binary'].mean()
        
        potential_saved = int(len(overtime_group) * (overtime_attrition - no_overtime_attrition))
        avg_salary = df['MonthlyIncome'].mean()
        
        scenarios['eliminate_overtime'] = {
            'name': 'Eliminar Hora Extra',
            'current_overtime_employees': len(overtime_group),
            'current_overtime_attrition': overtime_attrition * 100,
            'target_attrition': no_overtime_attrition * 100,
            'potential_employees_retained': potential_saved,
            'potential_savings': potential_saved * avg_salary * 6,
            'implementation': 'Contratar staff adicional ou redistribuir carga',
            'estimated_investment': len(overtime_group) * avg_salary * 0.3 * 12
        }
        
        # Cenário 2: Programa de promoções
        stagnated = df[(df['YearsSinceLastPromotion'] > 3) & (df['Attrition'] == 'No')]
        stagnated_attrition_rate = df[df['YearsSinceLastPromotion'] > 3]['Attrition_Binary'].mean()
        normal_attrition_rate = df[df['YearsSinceLastPromotion'] <= 3]['Attrition_Binary'].mean()
        
        # Promover 20% dos elegíveis
        to_promote = int(len(stagnated) * 0.2)
        promotion_cost = to_promote * avg_salary * 0.15 * 12
        expected_retention = int(to_promote * (stagnated_attrition_rate - normal_attrition_rate))
        
        scenarios['promotion_program'] = {
            'name': 'Programa de Promoções',
            'stagnated_employees': len(stagnated),
            'employees_to_promote': to_promote,
            'promotion_cost_annual': promotion_cost,
            'expected_retention': expected_retention,
            'expected_savings': expected_retention * avg_salary * 6,
            'roi': (expected_retention * avg_salary * 6) / promotion_cost if promotion_cost > 0 else 0
        }
        
        # Cenário 3: Ajuste salarial
        if 'Compa_Ratio' in df.columns:
            underpaid = df[(df['Compa_Ratio'] < 0.9) & (df['Attrition'] == 'No')]
            adjustment_needed = underpaid.apply(
                lambda row: max(0, (0.95 - row['Compa_Ratio']) * row['MonthlyIncome'] * 12),
                axis=1
            )
            total_adjustment = adjustment_needed.sum()
            
            underpaid_attrition = df[df['Compa_Ratio'] < 0.9]['Attrition_Binary'].mean()
            market_attrition = df[df['Compa_Ratio'] >= 0.95]['Attrition_Binary'].mean()
            
            retained = int(len(underpaid) * (underpaid_attrition - market_attrition))
            
            scenarios['salary_adjustment'] = {
                'name': 'Ajuste Salarial para Mercado',
                'underpaid_employees': len(underpaid),
                'total_adjustment_annual': total_adjustment,
                'avg_adjustment_per_employee': total_adjustment / len(underpaid) if len(underpaid) > 0 else 0,
                'expected_retention': retained,
                'expected_savings': retained * avg_salary * 6,
                'roi': (retained * avg_salary * 6) / total_adjustment if total_adjustment > 0 else 0
            }
        
        # Cenário 4: Programa de engajamento
        low_engagement = df[(df['Engagement_Index'] < 50) & (df['Attrition'] == 'No')] if 'Engagement_Index' in df.columns else pd.DataFrame()
        
        if len(low_engagement) > 0:
            engagement_cost = len(low_engagement) * 500 * 12  # $500/mês por funcionário
            low_engagement_attrition = df[df['Engagement_Index'] < 50]['Attrition_Binary'].mean() if 'Engagement_Index' in df.columns else 0
            high_engagement_attrition = df[df['Engagement_Index'] >= 70]['Attrition_Binary'].mean() if 'Engagement_Index' in df.columns else 0
            
            retained = int(len(low_engagement) * (low_engagement_attrition - high_engagement_attrition) * 0.5)  # 50% de efetividade
            
            scenarios['engagement_program'] = {
                'name': 'Programa de Engajamento',
                'low_engagement_employees': len(low_engagement),
                'program_cost_annual': engagement_cost,
                'expected_retention': retained,
                'expected_savings': retained * avg_salary * 6,
                'roi': (retained * avg_salary * 6) / engagement_cost if engagement_cost > 0 else 0
            }
        
        return scenarios
    
    def generate_executive_summary(self):
        """
        Gera resumo executivo de todas as análises
        """
        if not self.results:
            self.run_all_analyses()
        
        summary = {
            'critical_findings': [],
            'top_recommendations': [],
            'key_metrics': {},
            'immediate_actions': []
        }
        
        # Finding 1: Período crítico de sobrevivência
        if 'survival_analysis' in self.results:
            surv = self.results['survival_analysis']
            if surv.get('critical_periods'):
                summary['critical_findings'].append({
                    'title': 'Períodos Críticos de Retenção',
                    'finding': f"Identificados {len(surv['critical_periods'])} períodos com hazard rate >10%",
                    'details': surv['critical_periods'][:3]
                })
        
        # Finding 2: Departamento mais crítico
        if 'department_analysis' in self.results:
            dept = self.results['department_analysis']
            summary['critical_findings'].append({
                'title': 'Departamento de Maior Risco',
                'finding': f"{dept['highest_risk']} tem o maior índice de turnover",
                'spread': f"Diferença de {dept['risk_spread']:.1f}pp entre melhor e pior departamento"
            })
        
        # Finding 3: Stars at Risk
        if 'risk_matrix' in self.results:
            matrix = self.results['risk_matrix']
            if 'quadrants' in matrix:
                stars = matrix['quadrants']['stars_at_risk']
                summary['critical_findings'].append({
                    'title': 'Talentos em Risco',
                    'finding': f"{stars['count']} colaboradores de alto valor com alto risco de saída",
                    'cost_at_risk': f"R$ {matrix.get('cost_at_risk', 0):,.0f} em custos potenciais"
                })
        
        # Top Recommendations baseadas em ROI
        if 'scenario_simulations' in self.results:
            scenarios = self.results['scenario_simulations']
            sorted_scenarios = sorted(
                [(k, v) for k, v in scenarios.items() if 'roi' in v],
                key=lambda x: x[1].get('roi', 0),
                reverse=True
            )
            
            for scenario_key, scenario in sorted_scenarios[:3]:
                summary['top_recommendations'].append({
                    'initiative': scenario['name'],
                    'roi': scenario.get('roi', 0),
                    'expected_retention': scenario.get('expected_retention', 0),
                    'investment': scenario.get('promotion_cost_annual', scenario.get('total_adjustment_annual', scenario.get('program_cost_annual', 0)))
                })
        
        # Key Metrics
        summary['key_metrics'] = {
            'total_headcount': len(self.df),
            'overall_attrition': self.df['Attrition_Binary'].mean() * 100,
            'avg_tenure': self.df['YearsAtCompany'].mean(),
            'avg_satisfaction': self.df['JobSatisfaction'].mean(),
            'high_risk_count': len(self.df[self.df['Flight_Risk_Score'] > 70]) if 'Flight_Risk_Score' in self.df.columns else 0
        }
        
        # Immediate Actions
        summary['immediate_actions'] = [
            "Revisar colaboradores no quadrante 'Stars at Risk' para planos individuais",
            f"Investigar causas de turnover no departamento {self.results.get('department_analysis', {}).get('highest_risk', 'N/A')}",
            "Implementar programa piloto de redução de overtime",
            "Avaliar competitividade salarial para colaboradores com Compa-Ratio < 0.9"
        ]
        
        return summary


def run_complete_analysis(df):
    """
    Função helper para executar análise completa
    """
    analyzer = PeopleScienceAnalyzer(df)
    results = analyzer.run_all_analyses()
    summary = analyzer.generate_executive_summary()
    
    return {
        'detailed_results': results,
        'executive_summary': summary,
        'analyzer': analyzer
    }
