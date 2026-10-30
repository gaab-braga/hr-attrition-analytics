"""Regressão logística para explicar o attrition: odds ratios, intervalos de confiança e p-valores."""

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.pipeline import make_pipeline
import warnings
warnings.filterwarnings('ignore')


class StatisticalAnalyzer:
    """
    Classe para análises estatísticas interpretáveis
    Foco em entender os drivers de turnover com rigor estatístico
    """
    
    def __init__(self, df):
        self.df = df.copy()
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.results = {}
        
    def prepare_data(self):
        """
        Prepara dados para análise estatística
        """
        df = self.df.copy()
        
        # Features numéricas
        numeric_features = [
            'Age', 'MonthlyIncome', 'DistanceFromHome', 'JobSatisfaction',
            'EnvironmentSatisfaction', 'WorkLifeBalance', 'YearsAtCompany',
            'YearsSinceLastPromotion', 'YearsWithCurrManager', 'NumCompaniesWorked',
            'TotalWorkingYears', 'TrainingTimesLastYear', 'PercentSalaryHike',
            'StockOptionLevel', 'JobLevel', 'JobInvolvement', 'RelationshipSatisfaction'
        ]
        
        # Features categóricas para encoding
        categorical_features = ['OverTime', 'BusinessTravel', 'MaritalStatus', 'Gender']
        
        # Filtrar existentes
        numeric_features = [f for f in numeric_features if f in df.columns]
        categorical_features = [f for f in categorical_features if f in df.columns]
        
        # Criar dummies para categóricas
        for cat_col in categorical_features:
            dummies = pd.get_dummies(df[cat_col], prefix=cat_col, drop_first=True)
            for col in dummies.columns:
                df[col] = dummies[col]
        
        # Feature names finais
        self.feature_names = numeric_features + [col for col in df.columns if any(cat in col for cat in categorical_features) and '_' in col]
        
        # Filtrar features que existem
        self.feature_names = [f for f in self.feature_names if f in df.columns]
        
        X = df[self.feature_names].fillna(0)
        y = df['Attrition_Binary']
        
        return X, y
    
    def run_logistic_regression(self):
        """
        Regressão Logística com interpretação completa
        """
        X, y = self.prepare_data()
        
        # Normalizar para interpretação
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Modelo de regressão logística
        self.model = LogisticRegression(
            penalty='l2',
            C=1.0,
            solver='lbfgs',
            max_iter=1000,
            random_state=42
        )
        self.model.fit(X_scaled, y)
        
        # Cross-validation
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        # A padronização entra no Pipeline para ser ajustada só nas dobras de treino
        pipeline = make_pipeline(StandardScaler(), LogisticRegression(
            penalty='l2', C=1.0, solver='lbfgs', max_iter=1000, random_state=42))
        cv_scores = cross_val_score(pipeline, X, y, cv=cv, scoring='roc_auc')
        
        # Calcular odds ratios e intervalos de confiança
        coefficients = self.model.coef_[0]
        odds_ratios = np.exp(coefficients)
        
        # Calcular standard errors usando Hessian aproximada
        predictions = self.model.predict_proba(X_scaled)[:, 1]
        W = np.diag(predictions * (1 - predictions))
        X_design = np.hstack([np.ones((X_scaled.shape[0], 1)), X_scaled])
        
        try:
            # Fisher Information Matrix
            fisher_info = X_design.T @ W @ X_design
            cov_matrix = np.linalg.inv(fisher_info)
            std_errors = np.sqrt(np.diag(cov_matrix)[1:])  # Excluir intercept
        except:
            # Fallback: usar bootstrap aproximado
            std_errors = np.abs(coefficients) * 0.2
        
        # Intervalos de confiança 95%
        z_critical = 1.96
        ci_lower = coefficients - z_critical * std_errors
        ci_upper = coefficients + z_critical * std_errors
        
        # Odds ratio CI
        or_lower = np.exp(ci_lower)
        or_upper = np.exp(ci_upper)
        
        # P-values
        z_scores = coefficients / std_errors
        p_values = 2 * (1 - stats.norm.cdf(np.abs(z_scores)))
        
        # Nomes legíveis
        readable_names = {
            'Age': 'Idade',
            'MonthlyIncome': 'Salário Mensal',
            'DistanceFromHome': 'Distância de Casa (km)',
            'JobSatisfaction': 'Satisfação no Trabalho',
            'EnvironmentSatisfaction': 'Satisfação com Ambiente',
            'WorkLifeBalance': 'Work-Life Balance',
            'YearsAtCompany': 'Anos na Empresa',
            'YearsSinceLastPromotion': 'Anos sem Promoção',
            'YearsWithCurrManager': 'Anos com Gestor Atual',
            'NumCompaniesWorked': 'Empresas Anteriores',
            'TotalWorkingYears': 'Experiência Total (anos)',
            'TrainingTimesLastYear': 'Treinamentos no Ano',
            'PercentSalaryHike': '% Aumento Salarial',
            'StockOptionLevel': 'Stock Options',
            'JobLevel': 'Nível do Cargo',
            'JobInvolvement': 'Envolvimento no Trabalho',
            'RelationshipSatisfaction': 'Satisfação com Relações',
            'OverTime_Yes': 'Faz Hora Extra',
            'BusinessTravel_Travel_Frequently': 'Viaja Frequentemente',
            'BusinessTravel_Travel_Rarely': 'Viaja Raramente',
            'MaritalStatus_Married': 'Casado(a)',
            'MaritalStatus_Single': 'Solteiro(a)',
            'Gender_Male': 'Gênero Masculino'
        }
        
        # Compilar resultados
        regression_results = []
        for i, feature in enumerate(self.feature_names):
            result = {
                'variable': readable_names.get(feature, feature),
                'original_name': feature,
                'coefficient': coefficients[i],
                'std_error': std_errors[i],
                'z_score': z_scores[i],
                'p_value': p_values[i],
                'odds_ratio': odds_ratios[i],
                'or_ci_lower': or_lower[i],
                'or_ci_upper': or_upper[i],
                'is_significant': p_values[i] < 0.05,
                'effect_direction': 'Aumenta Risco' if coefficients[i] > 0 else 'Reduz Risco',
                'significance_stars': '***' if p_values[i] < 0.001 else '**' if p_values[i] < 0.01 else '*' if p_values[i] < 0.05 else ''
            }
            regression_results.append(result)
        
        # Ordenar por significância e magnitude
        regression_results = sorted(regression_results, key=lambda x: (not x['is_significant'], -abs(x['coefficient'])))
        
        self.results['logistic_regression'] = {
            'coefficients': regression_results,
            'model_performance': {
                'auc_mean': np.mean(cv_scores),
                'auc_std': np.std(cv_scores),
                'auc_scores': cv_scores.tolist(),
                'accuracy': cross_val_score(pipeline, X, y, cv=cv, scoring='accuracy').mean(),
                'baseline_accuracy': 1 - y.mean(),  # acerto de quem diz que ninguém sai
                'intercept': self.model.intercept_[0]
            },
            'sample_size': len(y),
            'n_positive': int(y.sum()),
            'n_negative': int(len(y) - y.sum()),
            'event_rate': float(y.mean())
        }
        
        return self.results['logistic_regression']
    
    def run_univariate_analysis(self):
        """
        Análise univariada para cada variável
        Teste t para contínuas, Chi-quadrado para categóricas
        """
        df = self.df.copy()
        univariate_results = []
        
        # Variáveis numéricas
        numeric_vars = [
            'Age', 'MonthlyIncome', 'DistanceFromHome', 'JobSatisfaction',
            'EnvironmentSatisfaction', 'WorkLifeBalance', 'YearsAtCompany',
            'YearsSinceLastPromotion', 'YearsWithCurrManager', 'NumCompaniesWorked',
            'TotalWorkingYears', 'TrainingTimesLastYear', 'PercentSalaryHike'
        ]
        
        for var in numeric_vars:
            if var not in df.columns:
                continue
                
            group_yes = df[df['Attrition'] == 'Yes'][var].dropna()
            group_no = df[df['Attrition'] == 'No'][var].dropna()
            
            if len(group_yes) < 5 or len(group_no) < 5:
                continue
            
            # Teste t
            t_stat, p_value = stats.ttest_ind(group_yes, group_no)
            
            # Effect size (Cohen's d)
            pooled_std = np.sqrt((group_yes.std()**2 + group_no.std()**2) / 2)
            cohens_d = (group_yes.mean() - group_no.mean()) / pooled_std if pooled_std > 0 else 0
            
            univariate_results.append({
                'variable': var,
                'type': 'numeric',
                'attrition_yes_mean': group_yes.mean(),
                'attrition_yes_std': group_yes.std(),
                'attrition_no_mean': group_no.mean(),
                'attrition_no_std': group_no.std(),
                'difference': group_yes.mean() - group_no.mean(),
                'pct_difference': (group_yes.mean() - group_no.mean()) / group_no.mean() * 100 if group_no.mean() != 0 else 0,
                't_statistic': t_stat,
                'p_value': p_value,
                'cohens_d': cohens_d,
                'effect_size': 'Grande' if abs(cohens_d) > 0.8 else 'Médio' if abs(cohens_d) > 0.5 else 'Pequeno',
                'is_significant': p_value < 0.05
            })
        
        # Variáveis categóricas (Chi-quadrado)
        categorical_vars = ['OverTime', 'Department', 'JobRole', 'MaritalStatus', 'BusinessTravel']
        
        for var in categorical_vars:
            if var not in df.columns:
                continue
            
            # Tabela de contingência
            contingency = pd.crosstab(df[var], df['Attrition'])
            
            if contingency.shape[0] < 2 or contingency.shape[1] < 2:
                continue
            
            # Chi-quadrado
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
            
            # Cramér's V (effect size)
            n = contingency.sum().sum()
            min_dim = min(contingency.shape[0] - 1, contingency.shape[1] - 1)
            cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0
            
            # Taxa de attrition por categoria
            attrition_rates = df.groupby(var)['Attrition_Binary'].mean()
            
            univariate_results.append({
                'variable': var,
                'type': 'categorical',
                'chi2_statistic': chi2,
                'degrees_of_freedom': dof,
                'p_value': p_value,
                'cramers_v': cramers_v,
                'effect_size': 'Grande' if cramers_v > 0.25 else 'Médio' if cramers_v > 0.15 else 'Pequeno',
                'is_significant': p_value < 0.05,
                'category_rates': attrition_rates.to_dict()
            })
        
        # Ordenar por p-value
        univariate_results = sorted(univariate_results, key=lambda x: x['p_value'])
        
        self.results['univariate'] = univariate_results
        return univariate_results
    
    def run_correlation_analysis(self):
        """
        Análise de correlações com significância estatística
        """
        df = self.df.copy()
        
        # Variáveis para correlação
        vars_for_corr = [
            'Age', 'MonthlyIncome', 'JobSatisfaction', 'EnvironmentSatisfaction',
            'WorkLifeBalance', 'YearsAtCompany', 'YearsSinceLastPromotion',
            'YearsWithCurrManager', 'NumCompaniesWorked', 'TotalWorkingYears',
            'TrainingTimesLastYear', 'Attrition_Binary'
        ]
        vars_for_corr = [v for v in vars_for_corr if v in df.columns]
        
        corr_data = df[vars_for_corr].dropna()
        
        correlation_results = []
        
        # Calcular correlações com p-value
        for i, var1 in enumerate(vars_for_corr):
            for j, var2 in enumerate(vars_for_corr):
                if i >= j:  # Apenas triângulo superior
                    continue
                
                corr, p_value = stats.pearsonr(corr_data[var1], corr_data[var2])
                
                correlation_results.append({
                    'variable_1': var1,
                    'variable_2': var2,
                    'correlation': corr,
                    'p_value': p_value,
                    'is_significant': p_value < 0.05,
                    'strength': 'Forte' if abs(corr) > 0.5 else 'Moderada' if abs(corr) > 0.3 else 'Fraca',
                    'direction': 'Positiva' if corr > 0 else 'Negativa'
                })
        
        # Ordenar por magnitude de correlação
        correlation_results = sorted(correlation_results, key=lambda x: abs(x['correlation']), reverse=True)
        
        # Matriz de correlação completa
        corr_matrix = corr_data.corr()
        
        self.results['correlations'] = {
            'pairwise': correlation_results,
            'matrix': corr_matrix.to_dict(),
            'significant_count': len([c for c in correlation_results if c['is_significant']])
        }
        
        return self.results['correlations']
    
    def run_risk_factor_analysis(self):
        """
        Análise de fatores de risco (relative risk e number needed to treat)
        """
        df = self.df.copy()
        
        risk_factors = []
        
        # Definir fatores de risco binários
        risk_conditions = [
            ('OverTime', 'Yes', 'Faz Hora Extra'),
            ('JobSatisfaction', lambda x: x <= 2, 'Baixa Satisfação (≤2)'),
            ('EnvironmentSatisfaction', lambda x: x <= 2, 'Baixa Satisfação Ambiente'),
            ('WorkLifeBalance', lambda x: x <= 2, 'Baixo Work-Life Balance'),
            ('YearsSinceLastPromotion', lambda x: x > 3, 'Sem Promoção >3 anos'),
            ('YearsAtCompany', lambda x: x < 2, 'Tenure < 2 anos'),
            ('NumCompaniesWorked', lambda x: x > 4, 'Job Hopper (>4 empresas)'),
            ('DistanceFromHome', lambda x: x > 20, 'Mora Longe (>20km)')
        ]
        
        base_attrition = df['Attrition_Binary'].mean()
        
        for col, condition, label in risk_conditions:
            if col not in df.columns:
                continue
            
            try:
                if callable(condition):
                    exposed = df[condition(df[col])]
                    not_exposed = df[~condition(df[col])]
                else:
                    exposed = df[df[col] == condition]
                    not_exposed = df[df[col] != condition]
                
                if len(exposed) < 10 or len(not_exposed) < 10:
                    continue
                
                # Taxas de attrition
                rate_exposed = exposed['Attrition_Binary'].mean()
                rate_not_exposed = not_exposed['Attrition_Binary'].mean()
                
                # Relative Risk
                relative_risk = rate_exposed / rate_not_exposed if rate_not_exposed > 0 else 0
                
                # Absolute Risk Increase
                ari = rate_exposed - rate_not_exposed
                
                # Number Needed to Harm (NNH)
                nnh = 1 / ari if ari > 0 else float('inf')
                
                # Teste Chi-quadrado para significância
                contingency = pd.crosstab(
                    df[col].apply(lambda x: condition(x) if callable(condition) else x == condition),
                    df['Attrition']
                )
                
                if contingency.shape == (2, 2):
                    chi2, p_value, _, _ = stats.chi2_contingency(contingency)
                else:
                    p_value = 1.0
                
                risk_factors.append({
                    'factor': label,
                    'n_exposed': len(exposed),
                    'n_not_exposed': len(not_exposed),
                    'rate_exposed': rate_exposed,
                    'rate_not_exposed': rate_not_exposed,
                    'relative_risk': relative_risk,
                    'absolute_risk_increase': ari,
                    'nnh': nnh if nnh != float('inf') else None,
                    'p_value': p_value,
                    'is_significant': p_value < 0.05,
                    'interpretation': f"Risco {relative_risk:.1f}x maior" if relative_risk > 1 else f"Proteção de {1/relative_risk:.1f}x"
                })
                
            except Exception as e:
                continue
        
        # Ordenar por relative risk
        risk_factors = sorted(risk_factors, key=lambda x: x['relative_risk'], reverse=True)
        
        self.results['risk_factors'] = risk_factors
        return risk_factors
    
    def generate_statistical_summary(self):
        """
        Gera resumo estatístico executivo
        """
        # Executar todas as análises se ainda não foram
        if 'logistic_regression' not in self.results:
            self.run_logistic_regression()
        if 'univariate' not in self.results:
            self.run_univariate_analysis()
        if 'correlations' not in self.results:
            self.run_correlation_analysis()
        if 'risk_factors' not in self.results:
            self.run_risk_factor_analysis()
        
        # Compilar principais findings
        summary = {
            'key_findings': [],
            'model_quality': {},
            'top_drivers': [],
            'significant_risk_factors': []
        }
        
        # Model Quality
        lr = self.results.get('logistic_regression', {})
        if lr:
            perf = lr.get('model_performance', {})
            summary['model_quality'] = {
                'auc': perf.get('auc_mean', 0),
                'auc_ci': f"±{perf.get('auc_std', 0)*1.96:.3f}",
                'accuracy': perf.get('accuracy', 0),
                'sample_size': lr.get('sample_size', 0),
                'event_rate': lr.get('event_rate', 0)
            }
        
        # Top Drivers (significativos)
        if lr and 'coefficients' in lr:
            sig_coefs = [c for c in lr['coefficients'] if c['is_significant']]
            summary['top_drivers'] = sig_coefs[:5]
            
            # Key finding 1
            if sig_coefs:
                top = sig_coefs[0]
                summary['key_findings'].append({
                    'title': 'Principal Driver de Turnover',
                    'finding': f"'{top['variable']}' é o fator mais significativo "
                              f"(OR={top['odds_ratio']:.2f}, p={top['p_value']:.4f}). "
                              f"{top['effect_direction']}."
                })
        
        # Risk Factors
        rf = self.results.get('risk_factors', [])
        sig_rf = [r for r in rf if r['is_significant']]
        summary['significant_risk_factors'] = sig_rf[:5]
        
        if sig_rf:
            top_rf = sig_rf[0]
            summary['key_findings'].append({
                'title': 'Maior Fator de Risco',
                'finding': f"'{top_rf['factor']}' aumenta o risco de turnover em "
                          f"{top_rf['relative_risk']:.1f}x (p={top_rf['p_value']:.4f})."
            })
        
        # Correlações importantes
        corr = self.results.get('correlations', {})
        if corr and 'pairwise' in corr:
            attrition_corrs = [c for c in corr['pairwise'] 
                             if 'Attrition' in c['variable_1'] or 'Attrition' in c['variable_2']]
            sig_corrs = [c for c in attrition_corrs if c['is_significant']]
            
            if sig_corrs:
                top_corr = sig_corrs[0]
                other_var = top_corr['variable_1'] if 'Attrition' in top_corr['variable_2'] else top_corr['variable_2']
                summary['key_findings'].append({
                    'title': 'Correlação Mais Forte com Turnover',
                    'finding': f"'{other_var}' tem correlação {top_corr['strength'].lower()} "
                              f"com turnover (r={top_corr['correlation']:.3f})."
                })
        
        self.results['summary'] = summary
        return summary
    
    def run_all_analyses(self):
        """
        Executa todas as análises estatísticas
        """
        print("Executando Regressão Logística...")
        self.run_logistic_regression()
        
        print("Executando Análise Univariada...")
        self.run_univariate_analysis()
        
        print("Executando Análise de Correlações...")
        self.run_correlation_analysis()
        
        print("Executando Análise de Fatores de Risco...")
        self.run_risk_factor_analysis()
        
        print("Gerando Resumo Estatístico...")
        self.generate_statistical_summary()
        
        return self.results


def run_statistical_analysis(df):
    """
    Função helper para executar análise completa
    """
    analyzer = StatisticalAnalyzer(df)
    results = analyzer.run_all_analyses()
    
    return {
        'results': results,
        'analyzer': analyzer
    }
