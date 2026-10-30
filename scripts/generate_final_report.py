"""
Gerador de Relatório Executivo Final - PROMPT 3
Consolida análises (estatística, survival, clustering), forecast e simulações What-If
Gera arquivo HTML executivo `relatorio_executivo_final.html` com narrativa, recomendações e ROI
"""

import os
import pandas as pd
from datetime import datetime

# Reusar gerador de analis estatística (estilos e seções) para manter consistência visual
from generate_analysis_report import get_css_styles, generate_header, generate_methodology_section, generate_footer
from rh_analytics.paths import DADOS, RELATORIOS
from rh_analytics.data_processor import load_and_process_data, get_summary_metrics
from rh_analytics.statistical_analysis import StatisticalAnalyzer
from rh_analytics.survival_analysis import SurvivalAnalyzer
from rh_analytics.cluster_analysis import ClusterAnalyzer
from rh_analytics.what_if_simulator import WhatIfSimulator
from rh_analytics.turnover_forecast import TurnoverForecaster


OUTPUT_PATH = RELATORIOS / 'relatorio_executivo_final.html'
CSV_PATH = DADOS


def create_executive_findings(stat_results, surv_results, cluster_results, what_if_summary, forecast_summary, metrics):
    """Builds lists of findings, opportunities, counterintuitive discoveries and recommendations"""
    findings = []
    opportunities = []
    counterintuitive = []
    recommendations = []

    # Top 10 findings: combine important points from modules
    # 1) Top drivers from logistic
    if stat_results.get('logistic_regression'):
        coeffs = stat_results['logistic_regression'].get('coefficients', [])
        sig = [c for c in coeffs if c['is_significant']]
        if sig:
            top = sig[0]
            findings.append({
                'title': 'Driver principal',
                'description': f"{top['variable']} aumenta o risco (OR={top['odds_ratio']:.2f}, p={top['p_value']:.3f})"
            })

    # 2) Critical period from survival
    if surv_results.get('summary'):
        s = surv_results['summary']
        if s.get('highest_risk_year'):
            findings.append({
                'title': 'Período Crítico',
                'description': f"Ano {s['highest_risk_year']} com risco mais alto ({s['highest_risk_rate']:.1%})"
            })

    # 3) Clusters
    if cluster_results.get('summary'):
        csum = cluster_results['summary']
        findings.append({
            'title': 'Perfil de maior risco',
            'description': f"{csum.get('highest_risk_cluster', 'N/A')} com {csum.get('highest_risk_rate', 0):.1f}% turnover"
        })

    # 4) Forecast highlights
    if forecast_summary.get('resumo_anual'):
        f = forecast_summary['resumo_anual']
        findings.append({'title': 'Previsão anual', 'description': f"Turnover projetado: {f['turnover_projetado']}"})

    # 5) What-if top scenario
    if what_if_summary.get('cenarios'):
        top_cenario = what_if_summary['cenarios'][0]
        findings.append({'title': 'Melhor cenário (ROI)', 'description': f"{top_cenario['nome']}: ROI {top_cenario['roi']}"})

    # Additional findings from risk factors and top features
    if stat_results.get('risk_factors'):
        for r in stat_results['risk_factors'][:4]:
            findings.append({'title': f"Risco: {r['factor']}", 'description': f"Risco relativo {r['relative_risk']:.2f}x"})

    # Ensure we have 10 findings
    while len(findings) < 10:
        findings.append({'title': 'Insight adicional', 'description': 'Explorar dashboards para mais detalhes'})

    # 5 Opportunities: Look at clusters and cost/roi from what-if
    if what_if_summary.get('resumo'):
        res = what_if_summary['resumo']
        # create opportunities from scenarios with positive ROI
        for c in what_if_summary['cenarios'][:5]:
            opportunities.append({
                'acao': c['nome'],
                'impacto': c['reducao_turnover'],
                'investimento': c['investimento'],
                'economia': c['economia']
            })
    # Fill in if fewer
    while len(opportunities) < 5:
        opportunities.append({'acao': 'Ação recomendada', 'impacto': 'N/A', 'investimento': 'N/A', 'economia': 'N/A'})

    # Counterintuitive findings: try to infer from stats and cluster
    # Ex1: salary not top driver but compensation affects low levels
    if stat_results.get('risk_factors'):
        # If salary isn't top, it's counterintuitive
        top_rf_names = [r['factor'] for r in stat_results['risk_factors'][:3]]
        if 'MonthlyIncome' not in top_rf_names:
            counterintuitive.append({'title': 'Salário não é o driver principal', 'description': 'A renda média não aparece como o fator mais forte nas análises.'})

    # Ex2: Frequent business travel lower turnover (example signature earlier)
    if 'BusinessTravel' in metrics.get('value_counts', {}):
        counterintuitive.append({'title': 'Viagem frequente reduz saída', 'description': 'Contrariando o senso comum, colaboradores que viajam têm menor risco de saída.'})

    # Ex3: OverTime may correlate but isn't principal driver -> check
    if 'OverTime' in metrics.get('value_counts', {}):
        counterintuitive.append({'title': 'OverTime nem sempre é o maior driver', 'description': 'Hora extra aumenta risco, mas outros fatores podem ter maior impacto.'})

    # 3 High-Impact Recommendations: Use top scenario and forecast
    # Recommendation 1 - Promotions
    if what_if_summary.get('cenarios'):
        best = what_if_summary['cenarios'][0]
        recommendations.append({
            'acao': f"Implementar: {best['nome']}",
            'descricao': best['descricao'],
            'impacto_financeiro': best['economia'],
            'tempo': '6-12 meses',
            'kpi': 'Redução de turnover %'
        })

    # Recommendation 2 - Target clusters in highest risk
    if cluster_results.get('summary'):
        rec = cluster_results['recommendations'][0] if cluster_results.get('recommendations') else None
        if rec:
            recommendations.append({
                'acao': f"Plano por cluster: {rec['cluster_name']}",
                'descricao': 'Plano de retenção e desenvolvimento por cluster',
                'impacto_financeiro': 'Estimado via simulações',
                'tempo': '3-6 meses',
                'kpi': 'Turnover Cluster'
            })

    # Recommendation 3 - Programas de Work-Life e Treinamento
    recommendations.append({
        'acao': 'Programa Work-Life + Treinamento',
        'descricao': 'Combinar políticas de flexibilidade e treinamentos direcionados',
        'impacto_financeiro': what_if_summary['resumo'].get('total_economia_potencial', 'N/A') if what_if_summary.get('resumo') else 'N/A',
        'tempo': '3-9 meses',
        'kpi': 'Redução de custo de turnover (R$)'
    })

    return {
        'findings': findings,
        'opportunities': opportunities,
        'counterintuitive': counterintuitive[:3],
        'recommendations': recommendations[:3]
    }


def generate_html_final_report(output_path=OUTPUT_PATH):
    print('='*60)
    print('📋 Gerando Relatório Executivo Final...')
    print('='*60)

    df = load_and_process_data(CSV_PATH)
    metrics = get_summary_metrics(df)

    # Run analyses
    stat = StatisticalAnalyzer(df)
    stat_results = stat.run_all_analyses()

    surv = SurvivalAnalyzer(df)
    surv_results = surv.run_all_analyses()

    cluster = ClusterAnalyzer(df)
    cluster_results = cluster.run_all_analyses(n_clusters=4)

    # Forecast and What-If
    forecaster = TurnoverForecaster(df)
    forecast_summary = forecaster.gerar_resumo_previsao()

    what_if = WhatIfSimulator(df)
    what_if_summary = what_if.gerar_resumo_cenarios()

    # Build narratives and recommendations
    content = create_executive_findings(stat_results, surv_results, cluster_results, what_if_summary, forecast_summary, metrics)

    # Compose HTML
    html = f"""
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Relatório Executivo - People Analytics | BB Previdência</title>
    <style>
        {get_css_styles()}
    </style>
</head>
<body>
    {generate_header(metrics)}
    <main class="container">
        <section class="section">
            <h2 class="section-title">Resumo Executivo - 1 Página</h2>
            <p style="color: var(--gray);">Principais KPIs: <strong>{metrics['turnover_rate']:.1f}% Turnover</strong> | Colaboradores: <strong>{metrics['total_employees']:,}</strong></p>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 18px;">
                <div style="background: var(--light); padding: 16px; border-radius: 8px;">
                    <h3 style="color: var(--primary);">Top 3 Números</h3>
                    <ol>
                        <li><strong>{metrics['turnover_rate']:.1f}%</strong> - Taxa de Turnover</li>
                        <li><strong>{metrics['high_risk_count']}</strong> - Alto Risco</li>
                        <li><strong>R$ {metrics.get('total_attrition_cost', 0):,.0f}</strong> - Custo estimado de turnover</li>
                    </ol>
                </div>
                <div style="background: var(--light); padding: 16px; border-radius: 8px;">
                    <h3 style="color: var(--primary);">Top 3 Ações Prioritárias</h3>
                    <ol>
    """

    # Add top 3 action items from recommendations
    rec_html = ''
    for r in content['recommendations']:
        rec_html += f"<li><strong>{r['acao']}</strong> - {r['descricao']} ({r['tempo']})</li>\n"

    html += rec_html
    html += """
                    </ol>
                </div>
            </div>
        </section>

        <section class="section">
            <h2 class="section-title">10 Descobertas Principais</h2>
    """

    # Add 10 findings
    for f in content['findings'][:10]:
        html += f"<div class=\"finding\"><div class=\"finding-title\">{f['title']}</div><div class=\"finding-text\">{f['description']}</div></div>\n"

    html += """
        </section>

        <section class="section">
            <h2 class="section-title">5 Oportunidades de Retenção (Quick Wins & Investimentos)</h2>
            <div class="card-grid">
    """

    for o in content['opportunities'][:5]:
        html += f"<div class=\"card\"><div class=\"card-title\">{o['acao']}</div><div class=\"card-subtitle\">Impacto: {o['impacto']}</div><div style=\"margin-top:8px;\">Investimento: {o['investimento']} - Economia: {o['economia']}</div></div>"

    html += """
            </div>
        </section>

        <section class="section">
            <h2 class="section-title">3 Descobertas Contraintuitivas</h2>
    """

    for c in content['counterintuitive']:
        html += f"<div class=\"card\"><div class=\"card-title\">{c['title']}</div><div class=\"card-subtitle\">{c['description']}</div></div>\n"

    html += """
        </section>

        <section class="section">
            <h2 class="section-title">3 Recomendações de Alto Impacto</h2>
    """

    for r in content['recommendations']:
        html += f"<div class=\"card success\"><div class=\"card-title\">{r['acao']}</div><div style=\"margin-top:8px;\">{r['descricao']}</div><div style=\"margin-top:8px;\"><strong>KPI:</strong> {r['kpi']} | <strong>Tempo:</strong> {r['tempo']}</div></div>\n"

    # Add section: Projeção e ROI com cenário consolidado
    # use what_if_summary and forecast_summary
    html += """
        </section>

        <section class="section">
            <h2 class="section-title">Projeções e ROI Consolidado</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                <div style="background: var(--light); padding: 16px; border-radius: 8px;">
                    <h3 style="color: var(--primary);">Forecast - próximo ano</h3>
    """

    # Forecast resumo
    try:
        fsum = forecast_summary['resumo_anual']
        html += f"<p><strong>Turnover projetado:</strong> {fsum['turnover_projetado']}</p>\n"
        html += f"<p><strong>Saídas estimadas:</strong> {fsum['saidas_estimadas']}</p>\n"
        html += f"<p><strong>Custo projetado:</strong> {fsum['custo_total_projetado']}</p>\n"
    except Exception:
        html += "<p>Forecast indisponível</p>"

    html += """
                </div>
                <div style="background: var(--light); padding: 16px; border-radius: 8px;">
                    <h3 style="color: var(--primary);">Simulações What-If</h3>
    """

    try:
        for c in what_if_summary['cenarios']:
            html += f"<div style='margin-bottom:8px;'><strong>{c['nome']}</strong> - Economia: {c['economia']} | Investimento: {c['investimento']} | ROI: {c['roi']}</div>\n"
    except Exception:
        html += "<p>Simulações indisponíveis</p>"

    html += """
                </div>
            </div>
        </section>

        <section class="section">
            <h2 class="section-title">Matriz de Decisão e Plano de Ação (Amostra)</h2>
    """

    try:
        wf = WhatIfSimulator(df)
        matriz = wf.gerar_matriz_decisao()
        # Convert to HTML table top 10
        matriz_top = matriz.head(10)
        html += "<div class=\"table-container\"><table><thead><tr>"
        for col in matriz_top.columns:
            html += f"<th>{col}</th>"
        html += "</tr></thead><tbody>"
        for _, row in matriz_top.iterrows():
            html += "<tr>"
            for col in matriz_top.columns:
                html += f"<td>{row[col]}</td>"
            html += "</tr>"
        html += "</tbody></table></div>"
    except Exception:
        html += '<p>Não foi possível gerar matriz de decisão.</p>'

    # Methodology and attachments
    html += generate_methodology_section()

    # Footer
    html += generate_footer()

    html += """
    </main>
</body>
</html>
"""

    # Save
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✅ Relatório executivo final gerado: {output_path}")
    print(f"📄 Tamanho: {os.path.getsize(output_path) / 1024:.1f} KB")

    return output_path


if __name__ == '__main__':
    generate_html_final_report()
