"""
Módulo de carregamento e processamento de dados
People Analytics & Talent Intelligence Dashboard
Inspirado no projeto de Marketing Science para BB Previdência
"""

import pandas as pd
import numpy as np


def load_and_process_data(filepath):
    """
    Carrega o CSV e calcula todas as métricas derivadas (Feature Engineering)
    """
    # Carregar dados
    df = pd.read_csv(filepath)
    
    # Garantir tipos numéricos
    numeric_cols = [
        'Age', 'DailyRate', 'DistanceFromHome', 'Education', 'EmployeeCount',
        'EmployeeNumber', 'EnvironmentSatisfaction', 'HourlyRate', 'JobInvolvement',
        'JobLevel', 'JobSatisfaction', 'MonthlyIncome', 'MonthlyRate', 
        'NumCompaniesWorked', 'PercentSalaryHike', 'PerformanceRating',
        'RelationshipSatisfaction', 'StandardHours', 'StockOptionLevel',
        'TotalWorkingYears', 'TrainingTimesLastYear', 'WorkLifeBalance',
        'YearsAtCompany', 'YearsInCurrentRole', 'YearsSinceLastPromotion',
        'YearsWithCurrManager'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # ============================================
    # FEATURE ENGINEERING - Métricas Avançadas
    # ============================================
    
    # 1. Attrition Binary (para modelos)
    df['Attrition_Binary'] = (df['Attrition'] == 'Yes').astype(int)
    
    # 2. Overtime Binary
    df['OverTime_Binary'] = (df['OverTime'] == 'Yes').astype(int)
    
    # 3. Tenure Band - Ciclo de vida do colaborador
    def categorize_tenure(years):
        if years < 1:
            return 'Onboarding (<1 ano)'
        elif years < 2:
            return 'Ramping (1-2 anos)'
        elif years <= 5:
            return 'Core (2-5 anos)'
        else:
            return 'Veterano (>5 anos)'
    
    df['Tenure_Band'] = df['YearsAtCompany'].apply(categorize_tenure)
    # Ensure Tenure_Band is a pandas Categorical type with a fixed order
    tenure_categories = ['Onboarding (<1 ano)', 'Ramping (1-2 anos)', 'Core (2-5 anos)', 'Veterano (>5 anos)']
    df['Tenure_Band'] = pd.Categorical(df['Tenure_Band'], categories=tenure_categories, ordered=True)
    
    # 4. Compa-Ratio - Posicionamento salarial vs. média do cargo
    job_salary_avg = df.groupby('JobRole')['MonthlyIncome'].transform('mean')
    df['Compa_Ratio'] = df['MonthlyIncome'] / job_salary_avg
    df['Compa_Ratio'] = df['Compa_Ratio'].replace([np.inf, -np.inf], 1).fillna(1)
    
    # 5. Salary Competitiveness
    def salary_competitiveness(ratio):
        if ratio < 0.9:
            return 'Abaixo do Mercado'
        elif ratio <= 1.1:
            return 'Adequado'
        else:
            return 'Acima do Mercado'
    
    df['Salary_Competitiveness'] = df['Compa_Ratio'].apply(salary_competitiveness)
    
    # 6. Promotion Velocity - Velocidade de progressão
    df['Promotion_Velocity'] = df['YearsAtCompany'] / (df['YearsSinceLastPromotion'] + 1)
    df['Promotion_Velocity'] = df['Promotion_Velocity'].replace([np.inf, -np.inf], 0).fillna(0)
    
    # 7. Engagement Index (0-100)
    df['Engagement_Index'] = (
        (df['JobSatisfaction'] + df['EnvironmentSatisfaction'] + 
         df['RelationshipSatisfaction'] + df['WorkLifeBalance']) / 16
    ) * 100
    
    # 8. Flight Risk Score (0-100)
    def calculate_flight_risk(row):
        score = 0
        # Insatisfação (0-60 pontos)
        score += (5 - row['JobSatisfaction']) * 15
        # Sobrecarga - OverTime (0-15 pontos)
        if row['OverTime'] == 'Yes':
            score += 15
        # Estagnação - Anos sem promoção (0-15 pontos)
        score += min(row['YearsSinceLastPromotion'] * 3, 15)
        # Salário baixo (0-10 pontos)
        if row['Compa_Ratio'] < 0.9:
            score += 10
        # Normalizar para 0-100
        return min(score, 100)
    
    df['Flight_Risk_Score'] = df.apply(calculate_flight_risk, axis=1)
    
    # 9. Flight Risk Category
    def flight_risk_category(score):
        if score <= 25:
            return 'Baixo'
        elif score <= 50:
            return 'Médio'
        elif score <= 70:
            return 'Alto'
        else:
            return 'Crítico'
    
    df['Flight_Risk_Category'] = df['Flight_Risk_Score'].apply(flight_risk_category)
    
    # 10. High Potential Flag
    df['High_Potential'] = (
        (df['PerformanceRating'] >= 3) & (df['JobInvolvement'] >= 3)
    ).astype(int)
    df['High_Potential_Label'] = df['High_Potential'].map({1: 'Sim', 0: 'Não'})
    
    # 11. Burnout Risk
    df['Burnout_Risk'] = (
        (df['OverTime'] == 'Yes') & (df['WorkLifeBalance'] <= 2)
    ).astype(int)
    df['Burnout_Risk_Label'] = df['Burnout_Risk'].map({1: 'Alto Risco', 0: 'Normal'})
    
    # 12. Cost of Attrition (6x salário mensal)
    df['Cost_of_Attrition'] = df.apply(
        lambda row: row['MonthlyIncome'] * 6 if row['Attrition'] == 'Yes' else 0, 
        axis=1
    )
    
    # 13. Potential Cost of Attrition (para ativos)
    df['Potential_Attrition_Cost'] = df['MonthlyIncome'] * 6
    
    # 14. Critical Talent Score (para Watchlist)
    def calculate_critical_score(row):
        score = 0
        # Performance alta (0-30 pontos)
        if row['PerformanceRating'] == 4:
            score += 30
        elif row['PerformanceRating'] == 3:
            score += 20
        # Flight Risk alto (0-30 pontos)
        if row['Flight_Risk_Score'] > 70:
            score += 30
        elif row['Flight_Risk_Score'] > 50:
            score += 15
        # Compa-Ratio baixo (0-20 pontos)
        if row['Compa_Ratio'] < 0.9:
            score += 20
        # OverTime (0-10 pontos)
        if row['OverTime'] == 'Yes':
            score += 10
        # Anos sem promoção (0-10 pontos)
        if row['YearsSinceLastPromotion'] > 3:
            score += 10
        return score
    
    df['Critical_Talent_Score'] = df.apply(calculate_critical_score, axis=1)
    
    # 15. Age Band
    def age_band(age):
        if age < 25:
            return '18-24'
        elif age < 35:
            return '25-34'
        elif age < 45:
            return '35-44'
        elif age < 55:
            return '45-54'
        else:
            return '55+'
    
    df['Age_Band'] = df['Age'].apply(age_band)
    
    # 16. Education Level Label
    education_map = {
        1: 'Below College',
        2: 'College',
        3: 'Bachelor',
        4: 'Master',
        5: 'Doctor'
    }
    df['Education_Level'] = df['Education'].map(education_map)
    
    # 17. eNPS Category (baseado em JobSatisfaction)
    # 1-2 = Detratores, 3 = Neutros, 4 = Promotores
    def enps_category(satisfaction):
        if satisfaction <= 2:
            return 'Detrator'
        elif satisfaction == 3:
            return 'Neutro'
        else:
            return 'Promotor'
    
    df['eNPS_Category'] = df['JobSatisfaction'].apply(enps_category)
    
    return df


def get_summary_metrics(df):
    """
    Retorna métricas agregadas para o dashboard
    """
    total_employees = len(df)
    active_employees = len(df[df['Attrition'] == 'No'])
    attrition_employees = len(df[df['Attrition'] == 'Yes'])
    
    # Turnover Rate
    turnover_rate = (attrition_employees / total_employees) * 100 if total_employees > 0 else 0
    
    # Custo Total de Attrition
    total_attrition_cost = df['Cost_of_Attrition'].sum()
    
    # eNPS Calculation
    promoters = len(df[df['eNPS_Category'] == 'Promotor'])
    detractors = len(df[df['eNPS_Category'] == 'Detrator'])
    enps = ((promoters - detractors) / total_employees) * 100 if total_employees > 0 else 0
    
    # Métricas de Satisfação
    avg_job_satisfaction = df['JobSatisfaction'].mean()
    avg_env_satisfaction = df['EnvironmentSatisfaction'].mean()
    avg_engagement = df['Engagement_Index'].mean()
    
    # Tempo médio para promoção
    avg_years_since_promotion = df['YearsSinceLastPromotion'].mean()
    
    # Flight Risk
    avg_flight_risk = df['Flight_Risk_Score'].mean()
    high_risk_count = len(df[df['Flight_Risk_Score'] > 70])
    critical_risk_count = len(df[df['Flight_Risk_Category'] == 'Crítico'])
    
    # High Potentials
    high_potential_count = df['High_Potential'].sum()
    high_potential_at_risk = len(df[(df['High_Potential'] == 1) & (df['Flight_Risk_Score'] > 50)])
    
    # Métricas salariais
    avg_monthly_income = df['MonthlyIncome'].mean()
    avg_compa_ratio = df['Compa_Ratio'].mean()
    below_market_count = len(df[df['Salary_Competitiveness'] == 'Abaixo do Mercado'])
    
    # Overtime
    overtime_pct = (df['OverTime_Binary'].sum() / total_employees) * 100 if total_employees > 0 else 0
    burnout_risk_count = df['Burnout_Risk'].sum()
    
    # Tenure
    avg_years_at_company = df['YearsAtCompany'].mean()
    
    return {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'attrition_employees': attrition_employees,
        'turnover_rate': turnover_rate,
        'total_attrition_cost': total_attrition_cost,
        'enps': enps,
        'promoters': promoters,
        'detractors': detractors,
        'avg_job_satisfaction': avg_job_satisfaction,
        'avg_env_satisfaction': avg_env_satisfaction,
        'avg_engagement': avg_engagement,
        'avg_years_since_promotion': avg_years_since_promotion,
        'avg_flight_risk': avg_flight_risk,
        'high_risk_count': high_risk_count,
        'critical_risk_count': critical_risk_count,
        'high_potential_count': high_potential_count,
        'high_potential_at_risk': high_potential_at_risk,
        'avg_monthly_income': avg_monthly_income,
        'avg_compa_ratio': avg_compa_ratio,
        'below_market_count': below_market_count,
        'overtime_pct': overtime_pct,
        'burnout_risk_count': burnout_risk_count,
        'avg_years_at_company': avg_years_at_company
    }


def identify_critical_talents(df, n=10):
    """
    Identifica os talentos críticos que requerem atenção imediata
    Critérios: Alta Performance + Alto Risco + Compa-Ratio baixo
    """
    # Filtrar apenas funcionários ativos com alta performance e risco elevado
    critical_df = df[
        (df['Attrition'] == 'No') &  # Apenas ativos
        (df['PerformanceRating'] >= 3) &  # Alta performance
        (df['Flight_Risk_Score'] > 50)  # Risco elevado
    ].copy()
    
    # Ordenar por Critical Talent Score
    critical_df = critical_df.nlargest(n, 'Critical_Talent_Score')
    
    # Gerar recomendações para cada talento crítico
    def generate_recommendation(row):
        recommendations = []
        if row['Compa_Ratio'] < 0.9:
            recommendations.append('Revisão Salarial Urgente')
        if row['YearsSinceLastPromotion'] > 3:
            recommendations.append('Plano de Carreira / Promoção')
        if row['OverTime'] == 'Yes' and row['WorkLifeBalance'] <= 2:
            recommendations.append('Rebalanceamento de Carga')
        if row['EnvironmentSatisfaction'] <= 2:
            recommendations.append('Check-in com Gestor / Cultura')
        if row['JobSatisfaction'] <= 2:
            recommendations.append('Entrevista de Engajamento')
        return '; '.join(recommendations) if recommendations else 'Monitoramento Contínuo'
    
    critical_df['Recommendation'] = critical_df.apply(generate_recommendation, axis=1)
    
    # Gerar motivos do risco
    def generate_risk_reasons(row):
        reasons = []
        if row['JobSatisfaction'] <= 2:
            reasons.append(f'Baixa satisfação no trabalho ({row["JobSatisfaction"]}/4)')
        if row['OverTime'] == 'Yes':
            reasons.append('Faz hora extra regularmente')
        if row['YearsSinceLastPromotion'] > 3:
            reasons.append(f'{row["YearsSinceLastPromotion"]} anos sem promoção')
        if row['Compa_Ratio'] < 0.9:
            reasons.append(f'Salário {(1-row["Compa_Ratio"])*100:.1f}% abaixo da média do cargo')
        if row['WorkLifeBalance'] <= 2:
            reasons.append('Work-Life Balance comprometido')
        return reasons
    
    critical_df['Risk_Reasons'] = critical_df.apply(generate_risk_reasons, axis=1)
    
    return critical_df


def analyze_attrition_patterns(df):
    """
    Analisa padrões de attrition por diferentes dimensões
    """
    patterns = {}
    
    # Por Departamento
    dept_attrition = df.groupby('Department').agg({
        'Attrition_Binary': ['sum', 'count', 'mean'],
        'Cost_of_Attrition': 'sum',
        'MonthlyIncome': 'mean',
        'Flight_Risk_Score': 'mean'
    }).round(2)
    dept_attrition.columns = ['Saídas', 'Total', 'Taxa_Turnover', 'Custo_Attrition', 'Salário_Médio', 'Flight_Risk_Médio']
    dept_attrition['Taxa_Turnover'] = (dept_attrition['Taxa_Turnover'] * 100).round(2)
    patterns['by_department'] = dept_attrition.to_dict('index')
    
    # Por JobRole
    role_attrition = df.groupby('JobRole').agg({
        'Attrition_Binary': ['sum', 'count', 'mean'],
        'Cost_of_Attrition': 'sum',
        'Flight_Risk_Score': 'mean'
    }).round(2)
    role_attrition.columns = ['Saídas', 'Total', 'Taxa_Turnover', 'Custo_Attrition', 'Flight_Risk_Médio']
    role_attrition['Taxa_Turnover'] = (role_attrition['Taxa_Turnover'] * 100).round(2)
    patterns['by_job_role'] = role_attrition.to_dict('index')
    
    # Por Tenure Band
    tenure_attrition = df.groupby('Tenure_Band').agg({
        'Attrition_Binary': ['sum', 'count', 'mean'],
        'Cost_of_Attrition': 'sum'
    }).round(2)
    tenure_attrition.columns = ['Saídas', 'Total', 'Taxa_Turnover', 'Custo_Attrition']
    tenure_attrition['Taxa_Turnover'] = (tenure_attrition['Taxa_Turnover'] * 100).round(2)
    patterns['by_tenure'] = tenure_attrition.to_dict('index')
    
    # Por Faixa de OverTime
    overtime_attrition = df.groupby('OverTime').agg({
        'Attrition_Binary': ['sum', 'count', 'mean']
    }).round(2)
    overtime_attrition.columns = ['Saídas', 'Total', 'Taxa_Turnover']
    overtime_attrition['Taxa_Turnover'] = (overtime_attrition['Taxa_Turnover'] * 100).round(2)
    patterns['by_overtime'] = overtime_attrition.to_dict('index')
    
    # Por Salary Competitiveness
    salary_attrition = df.groupby('Salary_Competitiveness').agg({
        'Attrition_Binary': ['sum', 'count', 'mean']
    }).round(2)
    salary_attrition.columns = ['Saídas', 'Total', 'Taxa_Turnover']
    salary_attrition['Taxa_Turnover'] = (salary_attrition['Taxa_Turnover'] * 100).round(2)
    patterns['by_salary'] = salary_attrition.to_dict('index')
    
    return patterns


def generate_insights(df, metrics):
    """
    Gera insights automáticos em linguagem natural
    """
    insights = []
    
    # Insight 1: Visão Geral
    insights.append({
        'type': 'Visão Geral',
        'title': 'Visão Geral da Organização',
        'description': f"A organização possui {metrics['total_employees']} colaboradores, com uma taxa de turnover de {metrics['turnover_rate']:.1f}%. "
                       f"O custo total de attrition foi de R$ {metrics['total_attrition_cost']:,.0f}.",
        'icon': '📊',
        'priority': 'info',
        'recommendation': 'Monitorar as métricas e priorizar quick wins para redução de turnover.'
    })
    
    # Insight 2: eNPS
    enps_status = "positivo" if metrics['enps'] > 0 else "negativo"
    insights.append({
        'type': 'Engajamento',
        'title': 'eNPS e Engajamento',
        'description': f"O eNPS estimado é de {metrics['enps']:.0f} ({enps_status}). "
                       f"Existem {metrics['promoters']} promotores e {metrics['detractors']} detratores.",
        'icon': '💚' if metrics['enps'] > 0 else '🔴',
        'priority': 'high' if metrics['enps'] < 0 else 'medium',
        'recommendation': 'Melhorar iniciativas de engajamento e medir impacto em ciclos trimestrais.'
    })
    
    # Insight 3: Talentos em Risco
    if metrics['high_potential_at_risk'] > 0:
        insights.append({
            'type': 'Talentos Críticos',
            'title': 'Talentos Críticos em Risco',
            'description': f"⚠️ ALERTA: {metrics['high_potential_at_risk']} colaboradores de alta performance estão em risco de saída. "
                           f"Isso representa uma potencial perda de capital intelectual crítico.",
            'icon': '🚨',
            'priority': 'critical',
            'recommendation': 'Configurar medidas imediatas de retenção para talentos críticos (one-on-one, retenção salarial, plano de carreira).'
        })
    
    # Insight 4: Overtime e Burnout
    if metrics['burnout_risk_count'] > 0:
        insights.append({
            'type': 'Bem-estar',
            'title': 'Risco de Burnout e Overtime',
            'description': f"{metrics['burnout_risk_count']} colaboradores apresentam alto risco de burnout "
                           f"(overtime + baixo work-life balance). {metrics['overtime_pct']:.1f}% do time faz hora extra regularmente.",
            'icon': '🔥',
            'priority': 'high',
            'recommendation': 'Reduzir horas extras e revisar políticas de carga de trabalho.'
        })
    
    # Insight 5: Salários
    if metrics['below_market_count'] > 0:
        pct_below = (metrics['below_market_count'] / metrics['total_employees']) * 100
        insights.append({
            'type': 'Compensação',
            'title': 'Salários abaixo do mercado',
            'description': f"{metrics['below_market_count']} colaboradores ({pct_below:.1f}%) estão com salário abaixo da média do cargo. "
                           f"Isso pode estar contribuindo para o flight risk.",
            'icon': '💰',
            'priority': 'medium',
            'recommendation': 'Considerar revisão salarial para cargos sensíveis; priorizar posições críticas.'
        })
    
    # Insight 6: Promoções
    if metrics['avg_years_since_promotion'] > 2:
        insights.append({
            'type': 'Carreira',
            'title': 'Tempo sem promoção',
            'description': f"O tempo médio sem promoção é de {metrics['avg_years_since_promotion']:.1f} anos. "
                           f"Estagnação de carreira é um dos principais drivers de turnover.",
            'icon': '📈',
            'priority': 'medium',
            'recommendation': 'Criar planos de carreira e metas de promoção anuais.'
        })
    
    return insights


def generate_action_plan(df, metrics, patterns):
    """
    Gera plano de ação priorizado por impacto financeiro
    """
    actions = []
    
    # Ação 1: Revisão salarial para Compa-Ratio baixo
    below_market = df[df['Salary_Competitiveness'] == 'Abaixo do Mercado']
    if len(below_market) > 0:
        estimated_cost = below_market['MonthlyIncome'].sum() * 0.1 * 12  # 10% de aumento anual
        potential_savings = len(below_market) * below_market['MonthlyIncome'].mean() * 6 * 0.3  # 30% de redução turnover
        actions.append({
            'priority': 'Crítica',
            'title': f'Revisão salarial para {len(below_market)} colaboradores com Compa-Ratio < 0.9',
            'description': 'Ajuste de salários para melhorar a competitividade do cargo e reduzir riscos.',
            'target': f'{len(below_market)} pessoas',
            'investment': f'R$ {estimated_cost:,.0f}/ano',
            'expected_impact': f'{(potential_savings/estimated_cost):.1f}x',
            'timeline': '6-12 meses',
            'owner': 'People Team',
            'icon': '🔴'
        })
    
    # Ação 2: Programa anti-overtime
    overtime_employees = df[df['OverTime'] == 'Yes']
    if len(overtime_employees) > 0:
        actions.append({
            'priority': 'Alta',
            'title': 'Política de redução de horas extras e rebalanceamento de carga',
            'description': 'Implementar políticas, redistribuição de tarefas e monitoramento de overtime.',
            'target': f'{len(overtime_employees)} pessoas',
            'investment': 'R$ 50.000 (consultoria + ferramentas)',
            'expected_impact': '2.5x',
            'timeline': '3-6 meses',
            'owner': 'People Team & Managers',
            'icon': '🟠'
        })
    
    # Ação 3: Programa de carreira para estagnados
    stagnated = df[df['YearsSinceLastPromotion'] > 3]
    if len(stagnated) > 0:
        actions.append({
            'priority': 'Alta',
            'title': f'Programa de Career Path para colaboradores sem promoção há mais de 3 anos',
            'description': 'Programa de desenvolvimento e trajetórias de carreira para reduzir a estagnação.',
            'target': f'{len(stagnated)} pessoas',
            'investment': 'R$ 80.000 (PDI + mentoria)',
            'expected_impact': '2.8x',
            'timeline': '6-12 meses',
            'owner': 'People Team',
            'icon': '🟠'
        })
    
    # Ação 4: Onboarding para novos
    onboarding = df[df['Tenure_Band'] == 'Onboarding (<1 ano)']
    if len(onboarding) > 0:
        actions.append({
            'priority': 'Média',
            'title': 'Programa de mentoria e acompanhamento no primeiro ano',
            'description': 'Mentoria estruturada durante o onboarding para melhorar retenção.',
            'target': f'{len(onboarding)} pessoas',
            'investment': 'R$ 30.000',
            'expected_impact': '1.8x',
            'timeline': '3-6 meses',
            'owner': 'People Team',
            'icon': '🟡'
        })
    
    return actions


def get_ideal_employee_profile(df):
    """
    Analisa características dos colaboradores ideais
    (>5 anos de empresa, alta performance, sem turnover)
    """
    ideal_employees = df[
        (df['YearsAtCompany'] > 5) &
        (df['PerformanceRating'] >= 3) &
        (df['Attrition'] == 'No')
    ]
    
    if len(ideal_employees) == 0:
        return None
    
    # Build profile with keys used by the dashboard UI
    avg_age = ideal_employees['Age'].mean()
    if avg_age < 25:
        age_range = '18-24'
    elif avg_age < 35:
        age_range = '25-34'
    elif avg_age < 45:
        age_range = '35-44'
    elif avg_age < 55:
        age_range = '45-54'
    else:
        age_range = '55+'

    avg_income = ideal_employees['MonthlyIncome'].mean()
    avg_tenure = ideal_employees['YearsAtCompany'].mean()
    avg_satisfaction = ideal_employees['JobSatisfaction'].mean()
    avg_work_life_balance = ideal_employees['WorkLifeBalance'].mean()
    avg_engagement = ideal_employees['Engagement_Index'].mean()
    avg_training = ideal_employees['TrainingTimesLastYear'].mean()
    top_department = ideal_employees['Department'].mode().iloc[0] if len(ideal_employees) > 0 else 'N/A'
    overtime_pct = (ideal_employees['OverTime'] == 'Yes').mean() * 100

    profile = {
        'count': len(ideal_employees),
        'age_range': age_range,
        'avg_age': avg_age,
        'avg_income': avg_income,
        'avg_tenure': avg_tenure,
        'avg_satisfaction': avg_satisfaction,
        'avg_work_life_balance': avg_work_life_balance,
        'avg_engagement': avg_engagement,
        'avg_training': avg_training,
        'overtime_profile': f"{overtime_pct:.0f}%",
        'top_department': top_department,
        'marital_status': ideal_employees['MaritalStatus'].mode().iloc[0] if len(ideal_employees) > 0 else 'N/A'
    }
    
    return profile
