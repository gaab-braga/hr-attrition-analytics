"""
Funções executivas para o Dashboard Principal melhorado
Inclui: Sumário Executivo, Alertas Críticos, Health Scorecard e gráficos estratégicos
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from dash import html, dcc
import dash_bootstrap_components as dbc


def create_alert_card(title, message, severity="warning", action_text=None, COLORS=None):
    """Cria card de alerta com severidade"""
    if COLORS is None:
        COLORS = {
            'danger': '#EF4444',
            'warning': '#F59E0B',
            'info': '#3B82F6',
            'success': '#10B981',
            'dark': '#1E293B',
            'gray': '#64748B'
        }
    
    icons = {
        'critical': ('🚨', COLORS['danger']),
        'warning': ('⚠️', COLORS['warning']),
        'info': ('ℹ️', COLORS['info']),
        'success': ('✅', COLORS['success'])
    }
    
    icon, color = icons.get(severity, icons['info'])
    
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Span(icon, style={'fontSize': '24px', 'marginRight': '12px'}),
                html.Div([
                    html.H6(title, style={'color': COLORS['dark'], 'marginBottom': '4px'}),
                    html.P(message, style={'color': COLORS['gray'], 'fontSize': '13px', 'marginBottom': '8px' if action_text else '0'}),
                    dbc.Button(action_text, size="sm", color="link", style={'padding': '0', 'fontSize': '12px'}) if action_text else None
                ], style={'flex': '1'})
            ], style={'display': 'flex', 'alignItems': 'flex-start'})
        ], style={'padding': '12px 16px'})
    ], style={
        'borderRadius': '8px',
        'border': 'none',
        'borderLeft': f'4px solid {color}',
        'backgroundColor': f'{color}08',
        'marginBottom': '12px'
    })


def create_executive_summary_card(df, metrics, driver_analysis, COLORS):
    """Card com resumo executivo narrativo"""
    
    # Calcular métricas-chave
    turnover_target = 12.0  # Meta de turnover
    turnover_gap = metrics['attrition_rate'] - turnover_target
    high_risk_pct = (metrics['high_risk_count'] / metrics['total_employees']) * 100
    
    # Departamento com maior problema
    dept_turnover = df.groupby('Department')['Attrition_Binary'].mean() * 100
    worst_dept = dept_turnover.idxmax()
    worst_dept_rate = dept_turnover.max()
    
    # Principais drivers
    top_driver = (
        driver_analysis['impact_ranking'][0]['variable']
        if driver_analysis and 'impact_ranking' in driver_analysis and len(driver_analysis['impact_ranking']) > 0
        else "Satisfação"
    )
    
    summary_html = html.Div([
        html.H5("📊 Sumário Executivo", style={'color': COLORS['dark'], 'marginBottom': '16px'}),
        
        # Status geral
        html.Div([
            html.Div([
                html.Span("Status Geral: ", style={'fontWeight': '600', 'color': COLORS['gray']}),
                html.Span("ATENÇÃO NECESSÁRIA", style={
                    'color': COLORS['danger'] if turnover_gap > 3 else COLORS['warning'],
                    'fontWeight': '700',
                    'fontSize': '16px'
                })
            ], style={'marginBottom': '12px'}),
        ]),
        
        # Destaques críticos
        html.Div([
            html.P([
                "• ",
                html.Strong(f"Turnover {turnover_gap:.1f}% acima da meta "),
                f"({metrics['attrition_rate']:.1f}% vs {turnover_target}% alvo) - representa {metrics['total_attrition']} saídas no período"
            ], style={'marginBottom': '8px', 'fontSize': '14px'}),
            
            html.P([
                "• ",
                html.Strong(f"{metrics['high_risk_count']} colaboradores em risco crítico "),
                f"({high_risk_pct:.1f}% do total) - potencial custo de R$ {metrics['cost_at_risk']:,.0f}"
            ], style={'marginBottom': '8px', 'fontSize': '14px'}),
            
            html.P([
                "• ",
                html.Strong(f"Departamento {worst_dept} com {worst_dept_rate:.1f}% de turnover "),
                "- requer intervenção imediata"
            ], style={'marginBottom': '8px', 'fontSize': '14px'}),
            
            html.P([
                "• ",
                html.Strong(f"Principal driver identificado: {top_driver} "),
                "- foco prioritário para ações de retenção"
            ], style={'marginBottom': '0', 'fontSize': '14px'}),
        ], style={'color': COLORS['dark']}),
        
        html.Hr(style={'margin': '16px 0'}),
        
        # Recomendação executiva
        html.Div([
            html.P("💡 Recomendação Executiva:", style={
                'fontWeight': '700',
                'color': COLORS['primary'],
                'marginBottom': '8px'
            }),
            html.P(
                f"Implementar plano de retenção focado no departamento {worst_dept} "
                f"com ações específicas sobre {top_driver}. "
                f"Prioridade: acompanhamento dos {metrics['high_risk_count']} talentos críticos identificados.",
                style={'fontSize': '14px', 'color': COLORS['gray'], 'marginBottom': '0'}
            )
        ])
    ], style={'padding': '4px 0'})
    
    return summary_html


def create_critical_alerts_section(df, metrics, COLORS):
    """Seção de alertas críticos priorizados"""
    alerts = []
    
    # Alerta 1: Talentos críticos em risco
    stars_at_risk = len(df[(df['Flight_Risk_Score'] >= 70) & (df['Critical_Talent_Score'] >= 60) & (df['Attrition'] == 'No')])
    if stars_at_risk > 0:
        alerts.append(
            create_alert_card(
                "Talentos Críticos em Risco de Saída",
                f"{stars_at_risk} colaboradores de alto valor com alto risco de saída - ação imediata necessária",
                "critical",
                "Ver Watchlist →",
                COLORS
            )
        )
    
    # Alerta 2: Overtime excessivo
    overtime_pct = len(df[df['OverTime'] == 'Yes']) / len(df) * 100
    if overtime_pct > 30:
        alerts.append(
            create_alert_card(
                "Overtime Acima do Recomendado",
                f"{overtime_pct:.1f}% dos colaboradores fazem hora extra regularmente - risco de burnout",
                "warning",
                "Ver Análise →",
                COLORS
            )
        )
    
    # Alerta 3: Promoções atrasadas
    overdue_promotions = len(df[df['YearsSinceLastPromotion'] > 4])
    if overdue_promotions > 50:
        alerts.append(
            create_alert_card(
                "Ciclo de Promoções Atrasado",
                f"{overdue_promotions} colaboradores há mais de 4 anos sem promoção - risco de desmotivação",
                "warning",
                None,
                COLORS
            )
        )
    
    # Alerta 4: Satisfação baixa
    low_satisfaction = len(df[df['JobSatisfaction'] <= 2])
    if low_satisfaction > 100:
        alerts.append(
            create_alert_card(
                "Satisfação Abaixo do Esperado",
                f"{low_satisfaction} colaboradores com satisfação baixa (≤2) - investigar causas",
                "info",
                None,
                COLORS
            )
        )
    
    return html.Div(alerts[:3])  # Mostrar apenas top 3 alertas


def create_health_scorecard(df, metrics, COLORS):
    """Scorecard de saúde organizacional"""
    
    # Calcular scores
    scores = {
        'Retenção': {
            'value': 100 - metrics['attrition_rate'],
            'target': 88,  # 12% turnover = 88% retenção
            'color': COLORS['success']
        },
        'Engajamento': {
            'value': df['Engagement_Index'].mean(),
            'target': 70,
            'color': COLORS['info']
        },
        'Satisfação': {
            'value': (metrics['avg_job_satisfaction'] / 4) * 100,
            'target': 75,
            'color': COLORS['primary']
        },
        'Work-Life': {
            'value': (df['WorkLifeBalance'].mean() / 4) * 100,
            'target': 75,
            'color': COLORS['accent_dark']
        }
    }
    
    # Determinar cor baseado no target
    for key in scores:
        gap = scores[key]['value'] - scores[key]['target']
        if gap >= 5:
            scores[key]['status'] = 'success'
            scores[key]['color'] = COLORS['success']
        elif gap >= 0:
            scores[key]['status'] = 'warning'
            scores[key]['color'] = COLORS['warning']
        else:
            scores[key]['status'] = 'danger'
            scores[key]['color'] = COLORS['danger']
    
    cards = []
    for metric, data in scores.items():
        cards.append(
            dbc.Col([
                html.Div([
                    html.Div([
                        html.P(metric, style={
                            'fontSize': '11px',
                            'fontWeight': '600',
                            'textTransform': 'uppercase',
                            'color': COLORS['gray'],
                            'marginBottom': '8px',
                            'letterSpacing': '0.5px'
                        }),
                        html.Div([
                            html.H3(f"{data['value']:.0f}%", style={
                                'fontSize': '32px',
                                'fontWeight': '700',
                                'color': data['color'],
                                'marginBottom': '0',
                                'lineHeight': '1'
                            }),
                        ], style={'marginBottom': '8px'}),
                        html.Div([
                            html.Span("Meta: ", style={'fontSize': '11px', 'color': COLORS['gray']}),
                            html.Span(f"{data['target']}%", style={
                                'fontSize': '12px',
                                'fontWeight': '600',
                                'color': COLORS['gray']
                            })
                        ]),
                        # Barra de progresso
                        html.Div([
                            html.Div(style={
                                'width': f"{min(data['value'], 100)}%",
                                'height': '4px',
                                'backgroundColor': data['color'],
                                'borderRadius': '2px',
                                'transition': 'width 0.3s ease'
                            })
                        ], style={
                            'width': '100%',
                            'height': '4px',
                            'backgroundColor': COLORS['gray_light'],
                            'borderRadius': '2px',
                            'marginTop': '12px'
                        })
                    ])
                ], style={
                    'padding': '20px',
                    'backgroundColor': COLORS['white'],
                    'borderRadius': '12px',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
                    'height': '100%',
                    'borderLeft': f'4px solid {data["color"]}'
                })
            ], md=3)
        )
    
    return dbc.Row(cards)


def create_turnover_trend_chart(df, COLORS):
    """Gráfico de tendência de turnover (simulado com cohorts)"""
    df_active = df[df['Attrition'] == 'No'].copy()
    
    # Criar grupos de tenure
    df_active['tenure_group'] = pd.cut(
        df_active['YearsAtCompany'],
        bins=[0, 2, 5, 10, 20, 50],
        labels=['0-2 anos', '2-5 anos', '5-10 anos', '10-20 anos', '20+ anos']
    )
    
    # Calcular turnover por grupo
    turnover_by_tenure = df.groupby(
        pd.cut(df['YearsAtCompany'], bins=[0, 2, 5, 10, 20, 50], labels=['0-2 anos', '2-5 anos', '5-10 anos', '10-20 anos', '20+ anos'])
    )['Attrition_Binary'].mean() * 100
    
    fig = go.Figure()
    
    # Linha de turnover
    fig.add_trace(go.Scatter(
        x=turnover_by_tenure.index.astype(str),
        y=turnover_by_tenure.values,
        mode='lines+markers',
        name='Turnover',
        line=dict(color=COLORS['danger'], width=3),
        marker=dict(size=10, color=COLORS['danger']),
        fill='tozeroy',
        fillcolor=f'rgba(239, 68, 68, 0.1)'
    ))
    
    # Linha de meta
    fig.add_hline(
        y=12,
        line_dash="dash",
        line_color=COLORS['success'],
        annotation_text="Meta: 12%",
        annotation_position="right"
    )
    
    fig.update_layout(
        title="Taxa de Turnover por Tempo de Casa",
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            title='Grupo de Tenure',
            showgrid=False
        ),
        yaxis=dict(
            title='Turnover (%)',
            showgrid=True,
            gridcolor=COLORS['gray_light']
        ),
        height=300,
        showlegend=False,
        font=dict(family='Inter, sans-serif', size=12)
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def create_risk_quadrant_summary(df, COLORS):
    """Quadrantes de risco - versão compacta"""
    active_df = df[df['Attrition'] == 'No'].copy()
    
    # Definir quadrantes
    quadrants = {
        'Stars at Risk': len(active_df[(active_df['Flight_Risk_Score'] >= 50) & (active_df['Critical_Talent_Score'] >= 60)]),
        'Stars Seguros': len(active_df[(active_df['Flight_Risk_Score'] < 50) & (active_df['Critical_Talent_Score'] >= 60)]),
        'Monitorar': len(active_df[(active_df['Flight_Risk_Score'] >= 50) & (active_df['Critical_Talent_Score'] < 60)]),
        'Estáveis': len(active_df[(active_df['Flight_Risk_Score'] < 50) & (active_df['Critical_Talent_Score'] < 60)])
    }
    
    colors_map = {
        'Stars at Risk': COLORS['danger'],
        'Stars Seguros': COLORS['success'],
        'Monitorar': COLORS['warning'],
        'Estáveis': COLORS['info']
    }
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=list(quadrants.keys()),
        y=list(quadrants.values()),
        marker=dict(color=[colors_map[k] for k in quadrants.keys()]),
        text=list(quadrants.values()),
        textposition='outside',
        hovertemplate="<b>%{x}</b><br>Colaboradores: %{y}<extra></extra>"
    ))
    
    fig.update_layout(
        title="Distribuição nos Quadrantes de Risco",
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(
            title='Colaboradores',
            showgrid=True,
            gridcolor=COLORS['gray_light']
        ),
        height=300,
        showlegend=False,
        font=dict(family='Inter, sans-serif', size=12)
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def create_top_drivers_compact(driver_analysis, COLORS):
    """Top 5 drivers de turnover - versão compacta"""
    if not driver_analysis or 'impact_ranking' not in driver_analysis:
        return html.P("Análise não disponível")
    
    top_5 = driver_analysis['impact_ranking'][:5]
    
    fig = go.Figure()
    
    colors = [COLORS['danger'] if d['direction'] == 'Aumenta Risco' else COLORS['success'] for d in top_5]
    
    fig.add_trace(go.Bar(
        x=[d['impact_score'] for d in top_5],
        y=[d['variable'][:30] for d in top_5],  # Truncar nomes longos
        orientation='h',
        marker=dict(color=colors),
        text=[f"{d['impact_score']:.0f}%" for d in top_5],
        textposition='outside',
        hovertemplate="<b>%{y}</b><br>Impacto: %{x:.1f}%<extra></extra>"
    ))
    
    fig.update_layout(
        title="Top 5 Drivers de Turnover",
        margin=dict(l=0, r=40, t=40, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            title='Impacto (%)',
            showgrid=True,
            gridcolor=COLORS['gray_light']
        ),
        yaxis=dict(showgrid=False, autorange='reversed'),
        height=280,
        showlegend=False,
        font=dict(family='Inter, sans-serif', size=11)
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def create_department_comparison(df, COLORS):
    """Comparação de departamentos - KPIs múltiplos"""
    dept_metrics = df.groupby('Department').agg({
        'Attrition_Binary': 'mean',
        'Flight_Risk_Score': 'mean',
        'JobSatisfaction': 'mean',
        'EmployeeNumber': 'count'
    }).reset_index()
    
    dept_metrics.columns = ['Department', 'Turnover', 'Flight_Risk', 'Satisfaction', 'Count']
    dept_metrics['Turnover'] *= 100
    
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=('Turnover (%)', 'Flight Risk Score', 'Satisfação (1-4)'),
        horizontal_spacing=0.12
    )
    
    # Turnover
    fig.add_trace(
        go.Bar(
            x=dept_metrics['Department'],
            y=dept_metrics['Turnover'],
            marker=dict(color=COLORS['danger']),
            name='Turnover',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Flight Risk
    fig.add_trace(
        go.Bar(
            x=dept_metrics['Department'],
            y=dept_metrics['Flight_Risk'],
            marker=dict(color=COLORS['warning']),
            name='Flight Risk',
            showlegend=False
        ),
        row=1, col=2
    )
    
    # Satisfação
    fig.add_trace(
        go.Bar(
            x=dept_metrics['Department'],
            y=dept_metrics['Satisfaction'],
            marker=dict(color=COLORS['success']),
            name='Satisfação',
            showlegend=False
        ),
        row=1, col=3
    )
    
    fig.update_layout(
        title="Comparativo por Departamento",
        height=300,
        showlegend=False,
        margin=dict(l=0, r=0, t=60, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', size=11)
    )
    
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor=COLORS['gray_light'])
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})
