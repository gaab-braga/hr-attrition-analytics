"""
Módulo de People Science
Modelos estatísticos, regressão, correlação e previsões
People Analytics Dashboard - BB Previdência
"""

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
import warnings
warnings.filterwarnings('ignore')


def prepare_features(df):
    """
    Prepara features para modelagem
    """
    df_model = df.copy()
    
    # Encode categorical variables
    label_encoders = {}
    categorical_cols = ['Department', 'JobRole', 'MaritalStatus', 'OverTime', 
                        'BusinessTravel', 'Gender', 'EducationField']
    
    for col in categorical_cols:
        if col in df_model.columns:
            le = LabelEncoder()
            df_model[f'{col}_encoded'] = le.fit_transform(df_model[col].astype(str))
            label_encoders[col] = le
    
    return df_model, label_encoders


def run_attrition_driver_analysis(df):
    """
    Identifica quais variáveis têm maior impacto no Attrition
    usando múltiplos modelos
    """
    df_model, label_encoders = prepare_features(df)
    
    # Features para análise
    feature_cols = [
        'Age', 'MonthlyIncome', 'DistanceFromHome', 'JobSatisfaction',
        'EnvironmentSatisfaction', 'WorkLifeBalance', 'YearsAtCompany',
        'YearsSinceLastPromotion', 'YearsWithCurrManager', 'NumCompaniesWorked',
        'TotalWorkingYears', 'TrainingTimesLastYear', 'PercentSalaryHike',
        'StockOptionLevel', 'JobLevel', 'JobInvolvement', 'RelationshipSatisfaction'
    ]
    
    # Adicionar variáveis categóricas encodadas
    for col in ['Department', 'JobRole', 'OverTime', 'BusinessTravel', 'MaritalStatus']:
        if f'{col}_encoded' in df_model.columns:
            feature_cols.append(f'{col}_encoded')
    
    # Filtrar colunas existentes
    feature_cols = [col for col in feature_cols if col in df_model.columns]
    
    X = df_model[feature_cols].fillna(0)
    y = df_model['Attrition_Binary']
    
    # Normalizar features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    results = {}
    
    # Modelo 1: Regressão Logística (para interpretabilidade)
    log_reg = LogisticRegression(max_iter=1000, random_state=42)
    log_reg.fit(X_scaled, y)
    log_scores = cross_val_score(log_reg, X_scaled, y, cv=5, scoring='roc_auc')
    
    # Modelo 2: Random Forest (para importância de features)
    rf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
    rf.fit(X_scaled, y)
    rf_scores = cross_val_score(rf, X_scaled, y, cv=5, scoring='roc_auc')
    
    # Modelo 3: Gradient Boosting
    gb = GradientBoostingClassifier(n_estimators=100, random_state=42, max_depth=5)
    gb.fit(X_scaled, y)
    gb_scores = cross_val_score(gb, X_scaled, y, cv=5, scoring='roc_auc')
    
    # Nomes mais legíveis para features
    feature_names_readable = {
        'Age': 'Idade',
        'MonthlyIncome': 'Salário Mensal',
        'DistanceFromHome': 'Distância de Casa',
        'JobSatisfaction': 'Satisfação no Trabalho',
        'EnvironmentSatisfaction': 'Satisfação com Ambiente',
        'WorkLifeBalance': 'Work-Life Balance',
        'YearsAtCompany': 'Anos na Empresa',
        'YearsSinceLastPromotion': 'Anos sem Promoção',
        'YearsWithCurrManager': 'Anos com Gestor Atual',
        'NumCompaniesWorked': 'Empresas Anteriores',
        'TotalWorkingYears': 'Anos de Experiência Total',
        'TrainingTimesLastYear': 'Treinamentos no Ano',
        'PercentSalaryHike': '% Aumento Salarial',
        'StockOptionLevel': 'Nível Stock Options',
        'JobLevel': 'Nível do Cargo',
        'JobInvolvement': 'Envolvimento no Trabalho',
        'RelationshipSatisfaction': 'Satisfação com Relações',
        'Department_encoded': 'Departamento',
        'JobRole_encoded': 'Cargo',
        'OverTime_encoded': 'Hora Extra',
        'BusinessTravel_encoded': 'Viagens de Trabalho',
        'MaritalStatus_encoded': 'Estado Civil'
    }
    
    # Normalizar importâncias
    log_importance = np.abs(log_reg.coef_[0]) / np.sum(np.abs(log_reg.coef_[0])) * 100
    rf_importance = rf.feature_importances_ / np.sum(rf.feature_importances_) * 100
    gb_importance = gb.feature_importances_ / np.sum(gb.feature_importances_) * 100
    
    # Média ponderada das importâncias
    combined_importance = (log_importance * 0.3 + rf_importance * 0.4 + gb_importance * 0.3)
    
    # Criar ranking
    impact_ranking = []
    for i, col in enumerate(feature_cols):
        readable_name = feature_names_readable.get(col, col)
        
        # Determinar direção do impacto
        coef = log_reg.coef_[0][i]
        if coef > 0:
            direction = 'Aumenta Risco'
        else:
            direction = 'Reduz Risco'
        
        impact_ranking.append({
            'variable': readable_name,
            'original_name': col,
            'impact_score': combined_importance[i],
            'log_coef': coef,
            'rf_importance': rf_importance[i],
            'gb_importance': gb_importance[i],
            'direction': direction
        })
    
    # Ordenar por impacto
    impact_ranking = sorted(impact_ranking, key=lambda x: x['impact_score'], reverse=True)
    
    results['impact_ranking'] = impact_ranking
    results['model_performance'] = {
        'logistic_auc': np.mean(log_scores),
        'rf_auc': np.mean(rf_scores),
        'gb_auc': np.mean(gb_scores),
        'best_model': 'Gradient Boosting' if np.mean(gb_scores) >= max(np.mean(log_scores), np.mean(rf_scores)) else 
                     'Random Forest' if np.mean(rf_scores) > np.mean(log_scores) else 'Logistic Regression'
    }
    
    return results


def analyze_overtime_impact(df):
    """
    Análise Difference-in-Differences para OverTime
    Compara grupos com e sem hora extra
    """
    # Grupos
    overtime_yes = df[df['OverTime'] == 'Yes']
    overtime_no = df[df['OverTime'] == 'No']
    
    results = {}
    
    # Métricas para comparação
    metrics_config = {
        'Attrition_Binary': 'Taxa de Turnover',
        'Flight_Risk_Score': 'Flight Risk Score',
        'JobSatisfaction': 'Satisfação no Trabalho',
        'WorkLifeBalance': 'Work-Life Balance',
        'Engagement_Index': 'Índice de Engajamento'
    }
    
    for metric, label in metrics_config.items():
        if metric not in df.columns:
            continue
            
        yes_mean = overtime_yes[metric].mean()
        yes_std = overtime_yes[metric].std()
        no_mean = overtime_no[metric].mean()
        no_std = overtime_no[metric].std()
        
        # Diferença
        diff = yes_mean - no_mean
        pct_diff = (diff / no_mean * 100) if no_mean != 0 else 0
        
        # Teste t para significância
        if len(overtime_yes) > 1 and len(overtime_no) > 1:
            t_stat, p_value = stats.ttest_ind(
                overtime_yes[metric].dropna(), 
                overtime_no[metric].dropna()
            )
            # Cohen's d (effect size)
            pooled_std = np.sqrt((yes_std**2 + no_std**2) / 2)
            cohens_d = diff / pooled_std if pooled_std > 0 else 0
        else:
            t_stat, p_value, cohens_d = 0, 1, 0
        
        results[label] = {
            'overtime_yes_mean': yes_mean,
            'overtime_yes_std': yes_std,
            'overtime_yes_n': len(overtime_yes),
            'overtime_no_mean': no_mean,
            'overtime_no_std': no_std,
            'overtime_no_n': len(overtime_no),
            'difference': diff,
            'percentage_difference': pct_diff,
            't_statistic': t_stat,
            'p_value': p_value,
            'is_significant': p_value < 0.05,
            'cohens_d': cohens_d,
            'effect_size': 'Grande' if abs(cohens_d) > 0.8 else 'Médio' if abs(cohens_d) > 0.5 else 'Pequeno'
        }
    
    # Resumo
    results['summary'] = {
        'total_overtime_yes': len(overtime_yes),
        'total_overtime_no': len(overtime_no),
        'attrition_uplift': results.get('Taxa de Turnover', {}).get('percentage_difference', 0),
        'engagement_impact': results.get('Índice de Engajamento', {}).get('percentage_difference', 0)
    }
    
    return results


def analyze_correlations(df):
    """
    Analisa correlações entre métricas de RH
    """
    correlations = {}
    
    # Correlações-chave para People Analytics
    correlation_pairs = [
        ('YearsSinceLastPromotion', 'JobSatisfaction', 'Estagnação × Satisfação'),
        ('MonthlyIncome', 'Attrition_Binary', 'Salário × Turnover'),
        ('DistanceFromHome', 'Attrition_Binary', 'Distância × Turnover'),
        ('WorkLifeBalance', 'Engagement_Index', 'Work-Life Balance × Engajamento'),
        ('YearsAtCompany', 'Attrition_Binary', 'Tenure × Turnover'),
        ('TrainingTimesLastYear', 'JobSatisfaction', 'Treinamento × Satisfação'),
        ('OverTime_Binary', 'Attrition_Binary', 'Hora Extra × Turnover'),
        ('Compa_Ratio', 'Attrition_Binary', 'Competitividade Salarial × Turnover')
    ]
    
    for col1, col2, label in correlation_pairs:
        if col1 in df.columns and col2 in df.columns:
            # Remover NaN
            valid_data = df[[col1, col2]].dropna()
            if len(valid_data) > 10:
                corr, p_value = stats.pearsonr(valid_data[col1], valid_data[col2])
                
                correlations[label] = {
                    'correlation': corr,
                    'p_value': p_value,
                    'interpretation': 'Positiva' if corr > 0 else 'Negativa',
                    'strength': 'Forte' if abs(corr) > 0.5 else 'Moderada' if abs(corr) > 0.3 else 'Fraca',
                    'is_significant': p_value < 0.05
                }
    
    # Matriz de correlação para heatmap
    numeric_cols = [
        'Age', 'MonthlyIncome', 'JobSatisfaction', 'EnvironmentSatisfaction',
        'WorkLifeBalance', 'YearsAtCompany', 'YearsSinceLastPromotion',
        'Flight_Risk_Score', 'Engagement_Index', 'Attrition_Binary'
    ]
    numeric_cols = [col for col in numeric_cols if col in df.columns]
    correlations['matrix'] = df[numeric_cols].corr().to_dict()
    
    return correlations


def predict_turnover(df, months=6):
    """
    Modelo preditivo de turnover
    Identifica colaboradores com maior probabilidade de saída
    """
    df_model, _ = prepare_features(df)
    
    # Apenas colaboradores ativos
    active_df = df_model[df_model['Attrition'] == 'No'].copy()
    
    # Features para previsão
    feature_cols = [
        'Age', 'MonthlyIncome', 'DistanceFromHome', 'JobSatisfaction',
        'EnvironmentSatisfaction', 'WorkLifeBalance', 'YearsAtCompany',
        'YearsSinceLastPromotion', 'YearsWithCurrManager', 'NumCompaniesWorked',
        'JobLevel', 'JobInvolvement', 'Flight_Risk_Score', 'Engagement_Index'
    ]
    
    # Adicionar encoded se existirem
    for col in ['OverTime_encoded', 'Department_encoded']:
        if col in df_model.columns:
            feature_cols.append(col)
    
    feature_cols = [col for col in feature_cols if col in df_model.columns]
    
    # Treinar modelo no dataset completo (com labels conhecidos)
    X_train = df_model[feature_cols].fillna(0)
    y_train = df_model['Attrition_Binary']
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    # Modelo de previsão
    model = GradientBoostingClassifier(n_estimators=100, random_state=42, max_depth=5)
    model.fit(X_train_scaled, y_train)
    
    # Prever para colaboradores ativos
    X_active = active_df[feature_cols].fillna(0)
    X_active_scaled = scaler.transform(X_active)
    
    # Probabilidades de saída
    probabilities = model.predict_proba(X_active_scaled)[:, 1]
    active_df['Predicted_Turnover_Prob'] = probabilities
    active_df['Predicted_Turnover_Risk'] = pd.cut(
        probabilities, 
        bins=[0, 0.3, 0.5, 0.7, 1.0],
        labels=['Baixo', 'Médio', 'Alto', 'Crítico']
    )
    
    # Top 10 mais prováveis de sair
    top_likely_to_leave = active_df.nlargest(10, 'Predicted_Turnover_Prob')[[
        'EmployeeNumber', 'JobRole', 'Department', 'YearsAtCompany',
        'Flight_Risk_Score', 'Predicted_Turnover_Prob', 'Predicted_Turnover_Risk'
    ]]
    
    # Projeções agregadas
    high_risk_count = len(active_df[active_df['Predicted_Turnover_Prob'] > 0.5])
    expected_turnover = active_df['Predicted_Turnover_Prob'].sum()
    expected_turnover_pct = (expected_turnover / len(active_df)) * 100 if len(active_df) > 0 else 0
    expected_cost = (active_df['Predicted_Turnover_Prob'] * active_df['MonthlyIncome'] * 6).sum()
    
    results = {
        'top_likely_to_leave': top_likely_to_leave.to_dict('records'),
        'projections': {
            'period_months': months,
            'total_active': len(active_df),
            'high_risk_count': high_risk_count,
            'expected_turnover': expected_turnover,
            'expected_turnover_pct': expected_turnover_pct,
            'expected_cost': expected_cost,
            'expected_cost_monthly': expected_cost / months
        },
        'risk_distribution': active_df['Predicted_Turnover_Risk'].value_counts().to_dict(),
        'model_accuracy': cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='roc_auc').mean()
    }
    
    return results


def scenario_analysis(df, scenario_type='promotion', improvement=0.2):
    """
    Simulação What-If de cenários
    """
    results = {}
    
    if scenario_type == 'promotion':
        # Cenário: Aumentar taxa de promoção em X%
        # Identificar colaboradores elegíveis (>3 anos sem promoção, boa performance)
        eligible = df[
            (df['YearsSinceLastPromotion'] > 3) & 
            (df['PerformanceRating'] >= 3) &
            (df['Attrition'] == 'No')
        ]
        
        n_promoted = int(len(eligible) * improvement)
        
        # Estimar impacto
        # Assumindo que promoção reduz flight risk em 30%
        avg_salary = eligible['MonthlyIncome'].mean()
        promotion_cost = n_promoted * avg_salary * 0.15 * 12  # 15% aumento anual
        
        # Redução estimada de turnover
        current_turnover = df['Attrition_Binary'].mean()
        estimated_reduction = current_turnover * 0.15  # 15% de redução
        
        avoided_attrition = int(len(df[df['Attrition'] == 'No']) * estimated_reduction)
        savings = avoided_attrition * avg_salary * 6
        
        results = {
            'scenario': f'Aumentar promoções em {improvement*100:.0f}%',
            'eligible_employees': len(eligible),
            'employees_promoted': n_promoted,
            'investment': promotion_cost,
            'turnover_reduction': estimated_reduction * 100,
            'avoided_attrition': avoided_attrition,
            'savings': savings,
            'roi': savings / promotion_cost if promotion_cost > 0 else 0,
            'payback_months': (promotion_cost / (savings / 12)) if savings > 0 else 0
        }
    
    elif scenario_type == 'overtime':
        # Cenário: Reduzir overtime para X% do time
        current_overtime = df[df['OverTime'] == 'Yes']
        target_overtime = int(len(df) * (1 - improvement))  # improvement = redução
        
        employees_affected = len(current_overtime) - target_overtime
        
        # Custo de contratação adicional
        avg_salary = df['MonthlyIncome'].mean()
        hiring_cost = max(0, employees_affected * 0.3) * avg_salary * 12 * 0.5  # 50% de custo adicional
        
        # Benefício: redução de turnover
        overtime_attrition = current_overtime['Attrition_Binary'].mean()
        no_overtime_attrition = df[df['OverTime'] == 'No']['Attrition_Binary'].mean()
        attrition_reduction = overtime_attrition - no_overtime_attrition
        
        avoided = employees_affected * attrition_reduction
        savings = avoided * avg_salary * 6
        
        results = {
            'scenario': f'Reduzir overtime para {(1-improvement)*100:.0f}% do time',
            'current_overtime_count': len(current_overtime),
            'employees_affected': max(0, employees_affected),
            'investment': hiring_cost,
            'turnover_reduction_pct': attrition_reduction * 100,
            'avoided_attrition': max(0, int(avoided)),
            'savings': max(0, savings),
            'roi': savings / hiring_cost if hiring_cost > 0 else 0
        }
    
    elif scenario_type == 'salary':
        # Cenário: Ajustar salários para Compa-Ratio >= 0.95
        below_market = df[df['Compa_Ratio'] < 0.9]
        
        # Calcular custo do ajuste
        adjustment_needed = below_market.apply(
            lambda row: (0.95 - row['Compa_Ratio']) * row['MonthlyIncome'] * 12,
            axis=1
        )
        total_adjustment = adjustment_needed.sum()
        
        # Estimar impacto
        # Colaboradores com salário baixo têm 40% mais chance de sair
        expected_retention = len(below_market) * 0.3  # 30% de retenção adicional
        savings = expected_retention * below_market['MonthlyIncome'].mean() * 6
        
        results = {
            'scenario': 'Ajustar Compa-Ratio < 0.9 para 0.95',
            'employees_affected': len(below_market),
            'total_adjustment_annual': total_adjustment,
            'expected_retention': int(expected_retention),
            'savings': savings,
            'roi': savings / total_adjustment if total_adjustment > 0 else 0,
            'payback_months': (total_adjustment / (savings / 12)) if savings > 0 else 0
        }
    
    return results


def generate_science_summary(driver_analysis, overtime_impact, correlations, predictions):
    """
    Gera resumo executivo das análises de People Science
    """
    summary = {
        'key_findings': [],
        'recommendations': [],
        'metrics': {}
    }
    
    # Finding 1: Principal driver de turnover
    if driver_analysis and 'impact_ranking' in driver_analysis:
        top_driver = driver_analysis['impact_ranking'][0]
        summary['key_findings'].append({
            'title': 'Principal Driver de Turnover',
            'finding': f"A variável '{top_driver['variable']}' tem o maior impacto no turnover "
                      f"({top_driver['impact_score']:.1f}% de importância). {top_driver['direction']}.",
            'model_confidence': f"AUC = {driver_analysis['model_performance']['gb_auc']:.2%}"
        })
    
    # Finding 2: Impacto de Overtime
    if overtime_impact and 'Taxa de Turnover' in overtime_impact:
        ot_data = overtime_impact['Taxa de Turnover']
        if ot_data['is_significant']:
            summary['key_findings'].append({
                'title': 'Impacto de Hora Extra',
                'finding': f"Colaboradores com overtime têm {ot_data['percentage_difference']:.1f}% mais "
                          f"chance de sair (p-value = {ot_data['p_value']:.4f}).",
                'effect_size': ot_data['effect_size']
            })
    
    # Finding 3: Correlação chave
    if correlations:
        for label, data in correlations.items():
            if label != 'matrix' and isinstance(data, dict) and data.get('is_significant') and abs(data.get('correlation', 0)) > 0.3:
                summary['key_findings'].append({
                    'title': f'Correlação: {label}',
                    'finding': f"Correlação {data['strength'].lower()} {data['interpretation'].lower()} "
                              f"(r = {data['correlation']:.3f})",
                    'p_value': data['p_value']
                })
                break
    
    # Finding 4: Projeção de turnover
    if predictions and 'projections' in predictions:
        proj = predictions['projections']
        summary['key_findings'].append({
            'title': 'Projeção de Turnover',
            'finding': f"Previsão de {proj['expected_turnover']:.0f} saídas nos próximos {proj['period_months']} meses "
                      f"({proj['expected_turnover_pct']:.1f}% do headcount ativo).",
            'cost_impact': f"R$ {proj['expected_cost']:,.0f} em custos projetados"
        })
    
    # Métricas consolidadas
    summary['metrics'] = {
        'model_performance': driver_analysis.get('model_performance', {}) if driver_analysis else {},
        'statistical_significance': {
            'overtime_effect': overtime_impact.get('Taxa de Turnover', {}).get('p_value', None) if overtime_impact else None,
            'overtime_cohens_d': overtime_impact.get('Taxa de Turnover', {}).get('cohens_d', None) if overtime_impact else None
        },
        'predictions': predictions.get('projections', {}) if predictions else {}
    }
    
    return summary
