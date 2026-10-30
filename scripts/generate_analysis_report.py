"""Gera o relatório HTML da análise estatística em reports/."""

import pandas as pd
import numpy as np
from datetime import datetime
import os

# Módulos internos
from rh_analytics.paths import DADOS, RELATORIOS
from rh_analytics.data_processor import load_and_process_data, get_summary_metrics
from rh_analytics.statistical_analysis import StatisticalAnalyzer
from rh_analytics.survival_analysis import SurvivalAnalyzer
from rh_analytics.cluster_analysis import ClusterAnalyzer


# ============================================================
# Paleta de cores
# ============================================================
COLORS = {
    'primary': '#005CA9',
    'primary_dark': '#003366',
    'accent': '#FEDF00',
    'success': '#10B981',
    'warning': '#F59E0B',
    'danger': '#EF4444',
    'info': '#3B82F6',
    'light': '#F8FAFC',
    'dark': '#1E293B',
    'gray': '#64748B',
    'white': '#FFFFFF'
}


def generate_html_report(output_path=RELATORIOS / 'relatorio_analise_estatistica.html'):
    """
    Gera relatório HTML completo com todas as análises estatísticas
    """
    print("=" * 60)
    print("GERANDO RELATÓRIO DE ANÁLISE ESTATÍSTICA")
    print("=" * 60)
    
    # Carregar dados
    print("\nCarregando dados...")
    csv_path = DADOS
    df = load_and_process_data(csv_path)
    metrics = get_summary_metrics(df)
    
    # Adicionar aliases para compatibilidade
    metrics['attrition_rate'] = metrics['turnover_rate']
    metrics['total_attrition'] = metrics['attrition_employees']
    metrics['avg_tenure'] = metrics['avg_years_at_company']
    metrics['cost_at_risk'] = metrics['total_attrition_cost']
    
    # Executar análises
    print("\nExecutando Análise Estatística...")
    stat_analyzer = StatisticalAnalyzer(df)
    stat_results = stat_analyzer.run_all_analyses()
    
    print("\nExecutando Análise de Sobrevivência...")
    surv_analyzer = SurvivalAnalyzer(df)
    surv_results = surv_analyzer.run_all_analyses()
    
    print("\nExecutando Análise de Clusters...")
    cluster_analyzer = ClusterAnalyzer(df)
    cluster_results = cluster_analyzer.run_all_analyses(n_clusters=4)
    
    # Gerar HTML
    print("\nGerando relatório HTML...")
    
    html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análise Estatística Profunda | People Analytics</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        {get_css_styles()}
    </style>
</head>
<body>
    {generate_header(metrics)}
    
    <main class="container">
        {generate_executive_summary(stat_results, surv_results, cluster_results, metrics)}
        
        {generate_statistical_section(stat_results)}
        
        {generate_survival_section(surv_results)}
        
        {generate_cluster_section(cluster_results)}
        
        {generate_methodology_section()}
    </main>
    
    {generate_footer()}
</body>
</html>
"""
    
    # Salvar arquivo
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\nRelatório gerado com sucesso: {output_path}")
    print(f"Tamanho: {os.path.getsize(output_path) / 1024:.1f} KB")
    
    return output_path


def get_css_styles():
    """Retorna CSS do relatório"""
    return f"""
        :root {{
            --primary: {COLORS['primary']};
            --primary-dark: {COLORS['primary_dark']};
            --accent: {COLORS['accent']};
            --success: {COLORS['success']};
            --warning: {COLORS['warning']};
            --danger: {COLORS['danger']};
            --info: {COLORS['info']};
            --light: {COLORS['light']};
            --dark: {COLORS['dark']};
            --gray: {COLORS['gray']};
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--light);
            color: var(--dark);
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
        }}
        
        /* Header */
        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            padding: 40px 0;
            color: white;
        }}
        
        .header h1 {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        
        .header .subtitle {{
            opacity: 0.8;
            font-size: 16px;
        }}
        
        .header-meta {{
            display: flex;
            gap: 24px;
            margin-top: 20px;
        }}
        
        .header-meta-item {{
            background: rgba(255,255,255,0.1);
            padding: 12px 20px;
            border-radius: 8px;
        }}
        
        .header-meta-item .value {{
            font-size: 24px;
            font-weight: 700;
            color: var(--accent);
        }}
        
        .header-meta-item .label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            opacity: 0.8;
        }}
        
        /* Sections */
        .section {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 32px;
            margin: 24px 0;
        }}
        
        .section-title {{
            font-size: 20px;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 24px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--light);
        }}
        
        .section-title .emoji {{
            margin-right: 8px;
        }}
        
        /* Cards */
        .card-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .card {{
            background: var(--light);
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid var(--primary);
        }}
        
        .card.success {{ border-left-color: var(--success); }}
        .card.warning {{ border-left-color: var(--warning); }}
        .card.danger {{ border-left-color: var(--danger); }}
        
        .card-title {{
            font-size: 14px;
            font-weight: 600;
            color: var(--gray);
            margin-bottom: 8px;
        }}
        
        .card-value {{
            font-size: 28px;
            font-weight: 700;
            color: var(--dark);
        }}
        
        .card-subtitle {{
            font-size: 13px;
            color: var(--gray);
            margin-top: 4px;
        }}
        
        /* Tables */
        .table-container {{
            overflow-x: auto;
            margin: 20px 0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        
        th {{
            background: var(--light);
            color: var(--gray);
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 12px 16px;
            text-align: left;
            border-bottom: 2px solid #e2e8f0;
        }}
        
        td {{
            padding: 12px 16px;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        tr:hover {{
            background: rgba(0,92,169,0.03);
        }}
        
        /* Badges */
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .badge-success {{ background: var(--success); color: white; }}
        .badge-warning {{ background: var(--warning); color: white; }}
        .badge-danger {{ background: var(--danger); color: white; }}
        .badge-info {{ background: var(--info); color: white; }}
        .badge-gray {{ background: #e2e8f0; color: var(--gray); }}
        
        /* Finding Cards */
        .finding {{
            background: linear-gradient(135deg, rgba(0,92,169,0.05) 0%, rgba(0,51,102,0.05) 100%);
            border-radius: 10px;
            padding: 20px;
            margin: 16px 0;
            border-left: 4px solid var(--primary);
        }}
        
        .finding-title {{
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 8px;
        }}
        
        .finding-text {{
            color: var(--dark);
            font-size: 15px;
        }}
        
        /* Progress Bars */
        .progress-container {{
            margin: 8px 0;
        }}
        
        .progress-bar {{
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }}
        
        .progress-fill.success {{ background: var(--success); }}
        .progress-fill.warning {{ background: var(--warning); }}
        .progress-fill.danger {{ background: var(--danger); }}
        .progress-fill.primary {{ background: var(--primary); }}
        
        /* Cluster Profile Cards */
        .cluster-card {{
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 24px;
            margin: 16px 0;
        }}
        
        .cluster-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }}
        
        .cluster-name {{
            font-size: 18px;
            font-weight: 700;
            color: var(--dark);
        }}
        
        .cluster-metrics {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        }}
        
        .cluster-metric {{
            text-align: center;
        }}
        
        .cluster-metric .value {{
            font-size: 24px;
            font-weight: 700;
            color: var(--primary);
        }}
        
        .cluster-metric .label {{
            font-size: 12px;
            color: var(--gray);
        }}
        
        /* Footer */
        .footer {{
            background: var(--primary-dark);
            color: white;
            padding: 24px 0;
            margin-top: 40px;
            text-align: center;
        }}
        
        .footer p {{
            opacity: 0.7;
            font-size: 13px;
        }}
        
        /* Utility */
        .text-success {{ color: var(--success); }}
        .text-warning {{ color: var(--warning); }}
        .text-danger {{ color: var(--danger); }}
        .text-primary {{ color: var(--primary); }}
        .text-gray {{ color: var(--gray); }}
        
        .mt-4 {{ margin-top: 24px; }}
        .mb-4 {{ margin-bottom: 24px; }}
        
        @media print {{
            .section {{ page-break-inside: avoid; }}
            .header {{ padding: 20px 0; }}
        }}
    """


def generate_header(metrics):
    """Gera header do relatório"""
    return f"""
    <header class="header">
        <div class="container">
            <h1>Análise Estatística Profunda</h1>
            <p class="subtitle">People Analytics</p>
            
            <div class="header-meta">
                <div class="header-meta-item">
                    <div class="value">{metrics['total_employees']:,}</div>
                    <div class="label">Colaboradores</div>
                </div>
                <div class="header-meta-item">
                    <div class="value">{metrics['turnover_rate']:.1f}%</div>
                    <div class="label">Taxa de Turnover</div>
                </div>
                <div class="header-meta-item">
                    <div class="value">{metrics['high_risk_count']}</div>
                    <div class="label">Alto Risco</div>
                </div>
                <div class="header-meta-item">
                    <div class="value">{datetime.now().strftime('%d/%m/%Y')}</div>
                    <div class="label">Data do Relatório</div>
                </div>
            </div>
        </div>
    </header>
    """


def generate_executive_summary(stat_results, surv_results, cluster_results, metrics):
    """Gera resumo executivo"""
    
    # Key findings
    findings_html = ""
    
    # Finding 1: Top driver
    if stat_results.get('logistic_regression'):
        sig_coefs = [c for c in stat_results['logistic_regression']['coefficients'] if c['is_significant']]
        if sig_coefs:
            top = sig_coefs[0]
            findings_html += f"""
            <div class="finding">
                <div class="finding-title">Principal Driver de Turnover</div>
                <div class="finding-text">
                    <strong>{top['variable']}</strong> é o fator mais significativo 
                    (Odds Ratio = {top['odds_ratio']:.2f}, p-value = {top['p_value']:.4f}).
                    {top['effect_direction']} {top['significance_stars']}
                </div>
            </div>
            """
    
    # Finding 2: Survival
    if surv_results.get('summary'):
        summary = surv_results['summary']
        if summary.get('highest_risk_year'):
            findings_html += f"""
            <div class="finding">
                <div class="finding-title">Período Crítico de Retenção</div>
                <div class="finding-text">
                    O <strong>ano {summary['highest_risk_year']}</strong> apresenta a maior taxa de risco 
                    ({summary['highest_risk_rate']:.1%}). 
                    Taxa de retenção final: {summary['final_retention']:.1f}%
                </div>
            </div>
            """
    
    # Finding 3: Clusters
    if cluster_results.get('summary'):
        summary = cluster_results['summary']
        findings_html += f"""
        <div class="finding">
            <div class="finding-title">Segmentação de Colaboradores</div>
            <div class="finding-text">
                Identificados <strong>{summary['n_clusters']} clusters</strong> distintos.
                Cluster de maior risco: <strong>{summary.get('highest_risk_cluster', 'N/A')}</strong> 
                ({summary.get('highest_risk_rate', 0):.1f}% turnover).
                Qualidade do clustering: {summary.get('cluster_quality', 'N/A')} (Silhouette: {summary.get('overall_silhouette', 0):.3f})
            </div>
        </div>
        """
    
    # Risk factors
    risk_html = ""
    if stat_results.get('risk_factors'):
        sig_rf = [r for r in stat_results['risk_factors'] if r['is_significant']][:5]
        for rf in sig_rf:
            risk_html += f"""
            <tr>
                <td><strong>{rf['factor']}</strong></td>
                <td class="text-center">{rf['relative_risk']:.2f}x</td>
                <td class="text-center">{rf['rate_exposed']*100:.1f}%</td>
                <td class="text-center">{rf['rate_not_exposed']*100:.1f}%</td>
                <td class="text-center">{rf['p_value']:.4f}</td>
            </tr>
            """
    
    return f"""
    <section class="section">
        <h2 class="section-title"><span class="emoji"></span> Resumo Executivo</h2>
        
        <p style="color: var(--gray); margin-bottom: 24px;">
            Este relatório apresenta uma análise estatística profunda dos dados de People Analytics,
            utilizando técnicas avançadas como Regressão Logística, Análise de Sobrevivência (Kaplan-Meier)
            e Segmentação por Clusters (K-Means).
        </p>
        
        <h3 style="font-size: 16px; color: var(--dark); margin: 24px 0 16px 0;">Principais Descobertas</h3>
        {findings_html}
        
        <h3 style="font-size: 16px; color: var(--dark); margin: 24px 0 16px 0;">Fatores de Risco Significativos</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Fator de Risco</th>
                        <th class="text-center">Risco Relativo</th>
                        <th class="text-center">Taxa Exposto</th>
                        <th class="text-center">Taxa Não Exposto</th>
                        <th class="text-center">p-value</th>
                    </tr>
                </thead>
                <tbody>
                    {risk_html}
                </tbody>
            </table>
        </div>
    </section>
    """


def generate_statistical_section(stat_results):
    """Gera seção de análise estatística"""
    
    # Model Performance
    perf = stat_results.get('logistic_regression', {}).get('model_performance', {})
    
    # Coefficients table
    coef_html = ""
    coefficients = stat_results.get('logistic_regression', {}).get('coefficients', [])[:15]
    
    for coef in coefficients:
        sig_class = 'text-success' if coef['is_significant'] else 'text-gray'
        direction_class = 'text-danger' if coef['effect_direction'] == 'Aumenta Risco' else 'text-success'
        
        coef_html += f"""
        <tr>
            <td><strong>{coef['variable']}</strong></td>
            <td class="text-center">{coef['coefficient']:.4f}</td>
            <td class="text-center">{coef['odds_ratio']:.3f}</td>
            <td class="text-center">[{coef['or_ci_lower']:.3f}, {coef['or_ci_upper']:.3f}]</td>
            <td class="text-center {sig_class}">{coef['p_value']:.4f} {coef['significance_stars']}</td>
            <td class="text-center {direction_class}">{coef['effect_direction']}</td>
        </tr>
        """
    
    # Univariate analysis
    univariate_html = ""
    univariate = stat_results.get('univariate', [])[:10]
    
    for u in univariate:
        if u['type'] == 'numeric':
            effect = f"Cohen's d = {u.get('cohens_d', 0):.3f}"
        else:
            effect = f"Cramér's V = {u.get('cramers_v', 0):.3f}"
        
        sig_badge = '<span class="badge badge-success">Significativo</span>' if u['is_significant'] else '<span class="badge badge-gray">NS</span>'
        
        univariate_html += f"""
        <tr>
            <td><strong>{u['variable']}</strong></td>
            <td class="text-center">{u['type'].capitalize()}</td>
            <td class="text-center">{effect}</td>
            <td class="text-center">{u.get('effect_size', 'N/A')}</td>
            <td class="text-center">{u['p_value']:.4f}</td>
            <td class="text-center">{sig_badge}</td>
        </tr>
        """
    
    return f"""
    <section class="section">
        <h2 class="section-title"><span class="emoji"></span> Análise Estatística - Regressão Logística</h2>
        
        <div class="card-grid">
            <div class="card success">
                <div class="card-title">AUC-ROC</div>
                <div class="card-value">{perf.get('auc_mean', 0):.1%}</div>
                <div class="card-subtitle">± {perf.get('auc_std', 0)*1.96:.3f} (IC 95%)</div>
            </div>
            <div class="card">
                <div class="card-title">Acurácia</div>
                <div class="card-value">{perf.get('accuracy', 0):.1%}</div>
                <div class="card-subtitle">Validação cruzada; quem chuta "ninguém sai" acerta {perf.get('baseline_accuracy', 0):.1%}</div>
            </div>
            <div class="card">
                <div class="card-title">Tamanho da Amostra</div>
                <div class="card-value">{stat_results.get('logistic_regression', {}).get('sample_size', 0):,}</div>
                <div class="card-subtitle">Observações</div>
            </div>
            <div class="card warning">
                <div class="card-title">Taxa de Evento</div>
                <div class="card-value">{stat_results.get('logistic_regression', {}).get('event_rate', 0):.1%}</div>
                <div class="card-subtitle">Attrition = Yes</div>
            </div>
        </div>
        
        <h3 style="font-size: 16px; color: var(--dark); margin: 24px 0 16px 0;">Coeficientes e Odds Ratios</h3>
        <p style="color: var(--gray); font-size: 14px; margin-bottom: 16px;">
            Odds Ratio > 1 indica aumento no risco de turnover. * p < 0.05, ** p < 0.01, *** p < 0.001
        </p>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Variável</th>
                        <th class="text-center">Coeficiente (β)</th>
                        <th class="text-center">Odds Ratio</th>
                        <th class="text-center">IC 95%</th>
                        <th class="text-center">p-value</th>
                        <th class="text-center">Efeito</th>
                    </tr>
                </thead>
                <tbody>
                    {coef_html}
                </tbody>
            </table>
        </div>
        
        <h3 style="font-size: 16px; color: var(--dark); margin: 24px 0 16px 0;">Análise Univariada</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Variável</th>
                        <th class="text-center">Tipo</th>
                        <th class="text-center">Tamanho do Efeito</th>
                        <th class="text-center">Magnitude</th>
                        <th class="text-center">p-value</th>
                        <th class="text-center">Significância</th>
                    </tr>
                </thead>
                <tbody>
                    {univariate_html}
                </tbody>
            </table>
        </div>
    </section>
    """


def generate_survival_section(surv_results):
    """Gera seção de análise de sobrevivência"""
    
    summary = surv_results.get('summary', {})
    milestones = surv_results.get('milestones', [])
    critical = surv_results.get('critical_periods', [])
    
    # Milestones
    milestone_html = ""
    for m in milestones:
        retention_class = 'success' if m['retention_rate'] > 80 else 'warning' if m['retention_rate'] > 60 else 'danger'
        milestone_html += f"""
        <tr>
            <td><strong>{m['label']}</strong></td>
            <td class="text-center">{m['retention_rate']:.1f}%</td>
            <td class="text-center">{m['attrition_rate']:.1f}%</td>
            <td class="text-center">[{m['ci_lower']:.1f}%, {m['ci_upper']:.1f}%]</td>
            <td class="text-center">{m['at_risk']:,}</td>
            <td class="text-center">
                <div class="progress-container" style="width: 100px;">
                    <div class="progress-bar">
                        <div class="progress-fill {retention_class}" style="width: {m['retention_rate']}%;"></div>
                    </div>
                </div>
            </td>
        </tr>
        """
    
    # Critical periods
    critical_html = ""
    for c in critical[:5]:
        critical_html += f"""
        <div class="card danger" style="margin: 8px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>Ano {c['year']}</strong>
                    <div style="font-size: 13px; color: var(--gray);">{c['recommendation']}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 24px; font-weight: 700; color: var(--danger);">{c['hazard_rate']:.1%}</div>
                    <div style="font-size: 12px; color: var(--gray);">Hazard Rate</div>
                </div>
            </div>
        </div>
        """
    
    # Segment analysis
    segment_html = ""
    segments = surv_results.get('segments', {})
    
    if 'OverTime' in segments:
        ot_data = segments['OverTime']
        log_rank = ot_data.get('log_rank_test', {})
        
        segment_html += f"""
        <div class="card" style="margin: 16px 0; border-left-color: var(--info);">
            <h4 style="margin-bottom: 12px;">Comparação: Hora Extra</h4>
            <p style="font-size: 14px; color: var(--gray);">
                Teste Log-Rank: χ² = {log_rank.get('chi2_statistic', 0):.2f}, 
                p-value = {log_rank.get('p_value', 1):.4f}
            </p>
            <p style="font-size: 14px; margin-top: 8px;">
                <strong>{log_rank.get('interpretation', 'N/A')}</strong>
            </p>
        </div>
        """
    
    return f"""
    <section class="section">
        <h2 class="section-title"><span class="emoji"></span> Análise de Sobrevivência (Kaplan-Meier)</h2>
        
        <div class="card-grid">
            <div class="card">
                <div class="card-title">Mediana de Sobrevivência</div>
                <div class="card-value">{summary.get('median_tenure', 'N/A') or '>Max'}</div>
                <div class="card-subtitle">Anos até 50% de attrition</div>
            </div>
            <div class="card success">
                <div class="card-title">RMST</div>
                <div class="card-value">{summary.get('rmst', 0):.1f}</div>
                <div class="card-subtitle">Restricted Mean Survival Time</div>
            </div>
            <div class="card">
                <div class="card-title">Retenção Final</div>
                <div class="card-value">{summary.get('final_retention', 0):.1f}%</div>
                <div class="card-subtitle">Ao final do período</div>
            </div>
            <div class="card danger">
                <div class="card-title">Períodos Críticos</div>
                <div class="card-value">{summary.get('critical_periods_count', 0)}</div>
                <div class="card-subtitle">Com hazard > 10%</div>
            </div>
        </div>
        
        <h3 style="font-size: 16px; color: var(--dark); margin: 24px 0 16px 0;">Taxa de Retenção por Marco</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Marco</th>
                        <th class="text-center">Retenção</th>
                        <th class="text-center">Turnover Acumulado</th>
                        <th class="text-center">IC 95%</th>
                        <th class="text-center">Em Risco</th>
                        <th class="text-center">Visualização</th>
                    </tr>
                </thead>
                <tbody>
                    {milestone_html}
                </tbody>
            </table>
        </div>
        
        <h3 style="font-size: 16px; color: var(--dark); margin: 24px 0 16px 0;">Períodos Críticos Identificados</h3>
        {critical_html if critical_html else '<p style="color: var(--gray);">Nenhum período com hazard rate > 10% identificado.</p>'}
        
        <h3 style="font-size: 16px; color: var(--dark); margin: 24px 0 16px 0;">Análise Comparativa por Segmento</h3>
        {segment_html}
    </section>
    """


def generate_cluster_section(cluster_results):
    """Gera seção de análise de clusters"""
    
    summary = cluster_results.get('summary', {})
    profiles = cluster_results.get('profiles', [])
    recommendations = cluster_results.get('recommendations', [])
    feature_imp = cluster_results.get('feature_importance', [])
    
    # Cluster profiles
    profile_html = ""
    for p in profiles:
        attrition_class = 'danger' if p['attrition_rate'] > 20 else 'warning' if p['attrition_rate'] > 10 else 'success'
        
        profile_html += f"""
        <div class="cluster-card">
            <div class="cluster-header">
                <div class="cluster-name">{p['cluster_name']}</div>
                <span class="badge badge-{attrition_class}">{p['attrition_rate']:.1f}% Turnover</span>
            </div>
            <p style="color: var(--gray); font-size: 14px; margin-bottom: 16px;">{p['description']}</p>
            
            <div class="cluster-metrics">
                <div class="cluster-metric">
                    <div class="value">{p['size']}</div>
                    <div class="label">Colaboradores ({p['pct_total']:.1f}%)</div>
                </div>
                <div class="cluster-metric">
                    <div class="value">{p['avg_age']:.0f}</div>
                    <div class="label">Idade Média</div>
                </div>
                <div class="cluster-metric">
                    <div class="value">{p['avg_tenure']:.1f}</div>
                    <div class="label">Tenure (anos)</div>
                </div>
                <div class="cluster-metric">
                    <div class="value">R$ {p['avg_income']:,.0f}</div>
                    <div class="label">Salário Médio</div>
                </div>
            </div>
            
            <div style="margin-top: 16px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
                <div style="text-align: center; padding: 12px; background: var(--light); border-radius: 8px;">
                    <div style="font-size: 20px; font-weight: 600;">{p['avg_job_satisfaction']:.1f}/4</div>
                    <div style="font-size: 11px; color: var(--gray);">Satisfação</div>
                </div>
                <div style="text-align: center; padding: 12px; background: var(--light); border-radius: 8px;">
                    <div style="font-size: 20px; font-weight: 600;">{p.get('avg_flight_risk', 0):.0f}</div>
                    <div style="font-size: 11px; color: var(--gray);">Flight Risk</div>
                </div>
                <div style="text-align: center; padding: 12px; background: var(--light); border-radius: 8px;">
                    <div style="font-size: 20px; font-weight: 600;">{p['overtime_pct']:.0f}%</div>
                    <div style="font-size: 11px; color: var(--gray);">Overtime</div>
                </div>
            </div>
        </div>
        """
    
    # Feature importance
    feature_html = ""
    for f in feature_imp[:8]:
        feature_html += f"""
        <tr>
            <td><strong>{f['feature']}</strong></td>
            <td class="text-center">{f['max_deviation']:.2f}</td>
            <td>
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill primary" style="width: {min(f['max_deviation']*30, 100)}%;"></div>
                    </div>
                </div>
            </td>
        </tr>
        """
    
    # Recommendations
    rec_html = ""
    for r in recommendations[:4]:
        priority_class = 'danger' if r['priority'] == 'Alta' else 'warning' if r['priority'] == 'Média' else 'success'
        
        actions_list = "".join([f"<li>{a['action']}: <span style='color: var(--gray);'>{a['rationale']}</span></li>" for a in r['actions'][:3]])
        
        rec_html += f"""
        <div class="card {priority_class}" style="margin: 12px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <strong>{r['cluster_name']}</strong>
                <span class="badge badge-{priority_class}">{r['priority']}</span>
            </div>
            <ul style="margin: 0; padding-left: 20px; font-size: 14px;">
                {actions_list}
            </ul>
        </div>
        """
    
    return f"""
    <section class="section">
        <h2 class="section-title"><span class="emoji"></span> Análise de Clusters (K-Means)</h2>
        
        <div class="card-grid">
            <div class="card">
                <div class="card-title">Número de Clusters</div>
                <div class="card-value">{summary.get('n_clusters', 0)}</div>
                <div class="card-subtitle">Segmentos identificados</div>
            </div>
            <div class="card success">
                <div class="card-title">Silhouette Score</div>
                <div class="card-value">{summary.get('overall_silhouette', 0):.3f}</div>
                <div class="card-subtitle">Qualidade: {summary.get('cluster_quality', 'N/A')}</div>
            </div>
            <div class="card danger">
                <div class="card-title">Cluster Maior Risco</div>
                <div class="card-value">{summary.get('highest_risk_rate', 0):.1f}%</div>
                <div class="card-subtitle">{summary.get('highest_risk_cluster', 'N/A')}</div>
            </div>
            <div class="card success">
                <div class="card-title">Cluster Mais Estável</div>
                <div class="card-value">{summary.get('most_stable_rate', 0):.1f}%</div>
                <div class="card-subtitle">{summary.get('most_stable_cluster', 'N/A')}</div>
            </div>
        </div>
        
        <h3 style="font-size: 16px; color: var(--dark); margin: 24px 0 16px 0;">Perfis dos Clusters</h3>
        {profile_html}
        
        <h3 style="font-size: 16px; color: var(--dark); margin: 24px 0 16px 0;">Variáveis Mais Discriminantes</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Variável</th>
                        <th class="text-center">Desvio Máximo (Z)</th>
                        <th>Importância</th>
                    </tr>
                </thead>
                <tbody>
                    {feature_html}
                </tbody>
            </table>
        </div>
        
        <h3 style="font-size: 16px; color: var(--dark); margin: 24px 0 16px 0;">Recomendações por Cluster</h3>
        {rec_html}
    </section>
    """


def generate_methodology_section():
    """Gera seção de metodologia"""
    return """
    <section class="section">
        <h2 class="section-title"><span class="emoji"></span> Metodologia</h2>
        
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px;">
            <div>
                <h4 style="color: var(--primary); margin-bottom: 12px;">Regressão Logística</h4>
                <p style="font-size: 14px; color: var(--gray);">
                    Modelo interpretável para identificar drivers de turnover.
                    Odds Ratios indicam o aumento proporcional no risco.
                    Validação cruzada (5-fold) para robustez.
                    Intervalos de confiança via matriz de Fisher.
                </p>
            </div>
            <div>
                <h4 style="color: var(--primary); margin-bottom: 12px;">Análise de Sobrevivência</h4>
                <p style="font-size: 14px; color: var(--gray);">
                    Kaplan-Meier para estimar curvas de retenção.
                    Hazard rates identificam períodos críticos.
                    Teste Log-Rank compara grupos.
                    Greenwood para intervalos de confiança.
                </p>
            </div>
            <div>
                <h4 style="color: var(--primary); margin-bottom: 12px;">Clustering K-Means</h4>
                <p style="font-size: 14px; color: var(--gray);">
                    Segmentação não-supervisionada de colaboradores.
                    Silhouette Score para validação.
                    Features normalizadas (Z-score).
                    Perfis gerados automaticamente.
                </p>
            </div>
        </div>
        
        <div style="margin-top: 24px; padding: 16px; background: var(--light); border-radius: 8px;">
            <h4 style="margin-bottom: 8px;">Interpretação dos Níveis de Significância</h4>
            <p style="font-size: 14px; color: var(--gray);">
                <strong>* p < 0.05:</strong> Significativo | 
                <strong>** p < 0.01:</strong> Muito Significativo | 
                <strong>*** p < 0.001:</strong> Altamente Significativo | 
                <strong>NS:</strong> Não Significativo
            </p>
        </div>
    </section>
    """


def generate_footer():
    """Gera footer do relatório"""
    return f"""
    <footer class="footer">
        <div class="container">
            <p>People Analytics · base IBM HR Analytics</p>
            <p>Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
        </div>
    </footer>
    """


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    generate_html_report()
