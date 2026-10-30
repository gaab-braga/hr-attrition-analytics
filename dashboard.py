"""
People Analytics Dashboard - BB Previdência
Interface principal Dash com visualizações interativas
"""

import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import pandas as pd
import numpy as np

# Importações do dashboard_executive_functions (novo dashboard)
try:
    from dashboard_executive_functions import (
        create_executive_summary_card,
        create_critical_alerts_section,
        create_health_scorecard,
        create_turnover_trend_chart,
        create_risk_quadrant_summary,
        create_top_drivers_compact,
        create_department_comparison
    )
except ModuleNotFoundError:
    from .dashboard_executive_functions import (
        create_executive_summary_card,
        create_critical_alerts_section,
        create_health_scorecard,
        create_turnover_trend_chart,
        create_risk_quadrant_summary,
        create_top_drivers_compact,
        create_department_comparison
    )

# Módulos internos
from data_processor import (
    load_and_process_data, get_summary_metrics, identify_critical_talents,
    analyze_attrition_patterns, generate_insights, generate_action_plan,
    get_ideal_employee_profile
)
from people_science import (
    run_attrition_driver_analysis, analyze_overtime_impact,
    analyze_correlations, predict_turnover, scenario_analysis,
    generate_science_summary
)
from advanced_analysis import PeopleScienceAnalyzer, run_complete_analysis

# ============================================================
# PALETA DE CORES BB PREVIDÊNCIA
# ============================================================
COLORS = {
    'primary': '#005CA9',       # Azul BB
    'primary_dark': '#003366',  # Azul escuro
    'accent': '#FEDF00',        # Amarelo BB
    'accent_dark': '#D4B800',   # Amarelo escuro
    'success': '#10B981',       # Verde
    'warning': '#F59E0B',       # Laranja
    'danger': '#EF4444',        # Vermelho
    'info': '#3B82F6',          # Azul info
    'light': '#F8FAFC',         # Fundo claro
    'dark': '#1E293B',          # Texto escuro
    'gray': '#64748B',          # Cinza médio
    'gray_light': '#E2E8F0',    # Cinza claro
    'white': '#FFFFFF',
    'card_bg': '#FFFFFF',
    'gradient_start': '#005CA9',
    'gradient_end': '#003366'
}

# Cores para gráficos
CHART_COLORS = [
    '#005CA9', '#FEDF00', '#10B981', '#F59E0B', '#EF4444',
    '#3B82F6', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'
]

# ============================================================
# CARREGAR E PROCESSAR DADOS
# ============================================================
CSV_PATH = 'WA_Fn-UseC_-HR-Employee-Attrition.csv'
print("Carregando dados...")
df = load_and_process_data(CSV_PATH)
metrics = get_summary_metrics(df)

# Adicionar aliases para compatibilidade
metrics['attrition_rate'] = metrics['turnover_rate']
metrics['total_attrition'] = metrics['attrition_employees']
metrics['avg_tenure'] = metrics['avg_years_at_company']
metrics['cost_at_risk'] = metrics['total_attrition_cost']

critical_talents = identify_critical_talents(df)
attrition_patterns = analyze_attrition_patterns(df)
insights = generate_insights(df, metrics)
action_plan = generate_action_plan(df, metrics, insights)
ideal_profile = get_ideal_employee_profile(df)

# People Science
print("Executando análises de People Science...")
# Allow skipping heavy analyses during quick visual checks
SKIP_HEAVY = os.environ.get('SKIP_HEAVY', '0') == '1'
if not SKIP_HEAVY:
    driver_analysis = run_attrition_driver_analysis(df)
    overtime_impact = analyze_overtime_impact(df)
    correlations = analyze_correlations(df)
    predictions = predict_turnover(df)
    science_summary = generate_science_summary(driver_analysis, overtime_impact, correlations, predictions)
else:
    driver_analysis = {'impact_ranking': []}
    overtime_impact = {}
    correlations = {}
    predictions = {}
    science_summary = {}

# Advanced Analysis
print("Executando análises avançadas...")
if not SKIP_HEAVY:
    analyzer = PeopleScienceAnalyzer(df)
    advanced_results = analyzer.run_all_analyses()
    executive_summary = analyzer.generate_executive_summary()
else:
    analyzer = None
    advanced_results = {}
    executive_summary = {}

print("Dashboard pronto!")

# ============================================================
# INICIALIZAR DASH APP
# ============================================================
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],
    suppress_callback_exceptions=True
)

app.title = "People Analytics | BB Previdência"

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def create_kpi_card(title, value, subtitle=None, icon=None, color=COLORS['primary'], trend=None):
    """Cria um card de KPI estilizado"""
    trend_element = None
    if trend is not None:
        trend_color = COLORS['success'] if trend >= 0 else COLORS['danger']
        trend_icon = "↑" if trend >= 0 else "↓"
        trend_element = html.Span(
            f"{trend_icon} {abs(trend):.1f}%",
            style={'color': trend_color, 'fontSize': '14px', 'marginLeft': '8px'}
        )
    
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.P(title, style={
                        'color': COLORS['gray'],
                        'fontSize': '12px',
                        'fontWeight': '600',
                        'textTransform': 'uppercase',
                        'letterSpacing': '0.5px',
                        'marginBottom': '4px'
                    }),
                    html.Div([
                        html.H3(value, style={
                            'color': COLORS['dark'],
                            'fontSize': '28px',
                            'fontWeight': '700',
                            'marginBottom': '0'
                        }),
                        trend_element
                    ], style={'display': 'flex', 'alignItems': 'baseline'}),
                    html.P(subtitle, style={
                        'color': COLORS['gray'],
                        'fontSize': '13px',
                        'marginTop': '4px',
                        'marginBottom': '0'
                    }) if subtitle else None
                ], style={'flex': '1'}),
                html.Div([
                    html.I(className=f"fas fa-{icon}", style={
                        'fontSize': '32px',
                        'color': color,
                        'opacity': '0.8'
                    })
                ]) if icon else None
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'flex-start'})
        ])
    ], style={
        'borderRadius': '12px',
        'border': 'none',
        'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
        'height': '100%',
        'borderLeft': f'4px solid {color}'
    })


def create_chart_card(title, chart, height="400px"):
    """Cria um card com gráfico"""
    return dbc.Card([
        dbc.CardHeader([
            html.H6(title, style={
                'color': COLORS['dark'],
                'fontWeight': '600',
                'marginBottom': '0'
            })
        ], style={
            'backgroundColor': COLORS['white'],
            'border': 'none',
            'padding': '16px 20px'
        }),
        dbc.CardBody([
            chart
        ], style={'padding': '0 20px 20px 20px'})
    ], style={
        'borderRadius': '12px',
        'border': 'none',
        'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
        'height': height
    })


def create_risk_badge(risk_score):
    """Cria badge de risco colorido"""
    if risk_score >= 70:
        color = COLORS['danger']
        text = 'Crítico'
    elif risk_score >= 50:
        color = COLORS['warning']
        text = 'Alto'
    elif risk_score >= 30:
        color = '#3B82F6'
        text = 'Médio'
    else:
        color = COLORS['success']
        text = 'Baixo'
    
    return html.Span(text, style={
        'backgroundColor': color,
        'color': COLORS['white'],
        'padding': '4px 12px',
        'borderRadius': '12px',
        'fontSize': '12px',
        'fontWeight': '600'
    })


# ============================================================
# GRÁFICOS
# ============================================================

def create_attrition_by_department():
    """Gráfico de turnover por departamento"""
    dept_data = df.groupby('Department').agg({
        'Attrition_Binary': 'mean',
        'EmployeeNumber': 'count'
    }).reset_index()
    dept_data['Attrition_Pct'] = dept_data['Attrition_Binary'] * 100
    dept_data = dept_data.sort_values('Attrition_Pct', ascending=True)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dept_data['Attrition_Pct'],
        y=dept_data['Department'],
        orientation='h',
        marker=dict(
            color=dept_data['Attrition_Pct'],
            colorscale=[[0, COLORS['success']], [0.5, COLORS['warning']], [1, COLORS['danger']]],
            showscale=False
        ),
        text=[f"{v:.1f}%" for v in dept_data['Attrition_Pct']],
        textposition='outside',
        hovertemplate="<b>%{y}</b><br>Turnover: %{x:.1f}%<extra></extra>"
    ))
    
    fig.update_layout(
        margin=dict(l=0, r=40, t=20, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            title='Taxa de Turnover (%)',
            showgrid=True,
            gridcolor=COLORS['gray_light']
        ),
        yaxis=dict(showgrid=False),
        height=300,
        font=dict(family='Inter, sans-serif', size=12)
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def create_flight_risk_distribution():
    """Distribuição de Flight Risk Score"""
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=df['Flight_Risk_Score'],
        nbinsx=20,
        marker=dict(
            color=COLORS['primary'],
            line=dict(color=COLORS['primary_dark'], width=1)
        ),
        hovertemplate="Score: %{x}<br>Colaboradores: %{y}<extra></extra>"
    ))
    
    # Linha de corte de risco
    fig.add_vline(x=70, line_dash="dash", line_color=COLORS['danger'],
                  annotation_text="Alto Risco", annotation_position="top right")
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            title='Flight Risk Score',
            showgrid=True,
            gridcolor=COLORS['gray_light']
        ),
        yaxis=dict(
            title='Colaboradores',
            showgrid=True,
            gridcolor=COLORS['gray_light']
        ),
        height=300,
        font=dict(family='Inter, sans-serif', size=12)
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def create_satisfaction_vs_tenure():
    """Scatter plot: Satisfação vs Tenure"""
    fig = px.scatter(
        df[df['Attrition'] == 'No'],
        x='YearsAtCompany',
        y='JobSatisfaction',
        color='Flight_Risk_Score',
        size='MonthlyIncome',
        color_continuous_scale=['#10B981', '#F59E0B', '#EF4444'],
        hover_data=['JobRole', 'Department']
    )
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            title='Anos na Empresa',
            showgrid=True,
            gridcolor=COLORS['gray_light']
        ),
        yaxis=dict(
            title='Satisfação no Trabalho',
            showgrid=True,
            gridcolor=COLORS['gray_light']
        ),
        coloraxis_colorbar=dict(title='Flight Risk'),
        height=350,
        font=dict(family='Inter, sans-serif', size=12)
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def create_overtime_impact_chart():
    """Impacto de Overtime no Turnover"""
    overtime_data = df.groupby('OverTime')['Attrition_Binary'].mean().reset_index()
    overtime_data['Attrition_Pct'] = overtime_data['Attrition_Binary'] * 100
    
    fig = go.Figure()
    
    colors = [COLORS['success'] if ot == 'No' else COLORS['danger'] for ot in overtime_data['OverTime']]
    
    fig.add_trace(go.Bar(
        x=['Sem Hora Extra', 'Com Hora Extra'],
        y=overtime_data['Attrition_Pct'],
        marker=dict(color=colors),
        text=[f"{v:.1f}%" for v in overtime_data['Attrition_Pct']],
        textposition='outside',
        hovertemplate="<b>%{x}</b><br>Turnover: %{y:.1f}%<extra></extra>"
    ))
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(
            title='Taxa de Turnover (%)',
            showgrid=True,
            gridcolor=COLORS['gray_light']
        ),
        height=300,
        font=dict(family='Inter, sans-serif', size=12)
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def create_driver_importance_chart():
    """Gráfico de importância dos drivers de turnover"""
    if not driver_analysis or 'impact_ranking' not in driver_analysis:
        return html.P("Análise não disponível")
    
    top_10 = driver_analysis['impact_ranking'][:10]
    
    fig = go.Figure()
    
    colors = [COLORS['danger'] if d['direction'] == 'Aumenta Risco' else COLORS['success'] for d in top_10]
    
    fig.add_trace(go.Bar(
        x=[d['impact_score'] for d in top_10],
        y=[d['variable'] for d in top_10],
        orientation='h',
        marker=dict(color=colors),
        text=[f"{d['impact_score']:.1f}%" for d in top_10],
        textposition='outside',
        hovertemplate="<b>%{y}</b><br>Importância: %{x:.1f}%<extra></extra>"
    ))
    
    fig.update_layout(
        margin=dict(l=0, r=60, t=20, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            title='Importância (%)',
            showgrid=True,
            gridcolor=COLORS['gray_light']
        ),
        yaxis=dict(showgrid=False, autorange='reversed'),
        height=400,
        font=dict(family='Inter, sans-serif', size=11)
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def create_survival_curve():
    """Curva de sobrevivência"""
    if 'survival_analysis' not in advanced_results:
        return html.P("Análise não disponível")
    
    surv_data = advanced_results['survival_analysis']['survival_curve']
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=[d['year'] for d in surv_data],
        y=[d['cumulative_survival'] * 100 for d in surv_data],
        mode='lines+markers',
        fill='tozeroy',
        fillcolor='rgba(0,92,169,0.1)',
        line=dict(color=COLORS['primary'], width=3),
        marker=dict(size=8, color=COLORS['primary']),
        hovertemplate="Ano %{x}<br>Retenção: %{y:.1f}%<extra></extra>"
    ))
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            title='Anos na Empresa',
            showgrid=True,
            gridcolor=COLORS['gray_light']
        ),
        yaxis=dict(
            title='Taxa de Retenção (%)',
            showgrid=True,
            gridcolor=COLORS['gray_light'],
            range=[0, 100]
        ),
        height=350,
        font=dict(family='Inter, sans-serif', size=12)
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def create_risk_matrix_chart():
    """Matriz de Risco: Flight Risk vs Critical Talent"""
    if 'risk_matrix' not in advanced_results:
        return html.P("Análise não disponível")
    
    matrix = advanced_results['risk_matrix']
    quadrants = matrix.get('quadrants', {})
    
    fig = go.Figure()
    
    # Scatter plot dos funcionários
    active_df = df[df['Attrition'] == 'No'].copy()
    
    fig.add_trace(go.Scatter(
        x=active_df['Flight_Risk_Score'],
        y=active_df['Critical_Talent_Score'],
        mode='markers',
        marker=dict(
            size=8,
            color=active_df['MonthlyIncome'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='Salário')
        ),
        text=active_df['JobRole'],
        hovertemplate="<b>%{text}</b><br>Flight Risk: %{x:.0f}<br>Critical Talent: %{y:.0f}<extra></extra>"
    ))
    
    # Linhas de divisão dos quadrantes
    fig.add_hline(y=60, line_dash="dash", line_color=COLORS['gray'])
    fig.add_vline(x=50, line_dash="dash", line_color=COLORS['gray'])
    
    # Anotações dos quadrantes
    fig.add_annotation(x=75, y=80, text="⚠️ Stars at Risk", showarrow=False,
                       font=dict(size=12, color=COLORS['danger']))
    fig.add_annotation(x=25, y=80, text="⭐ Stars", showarrow=False,
                       font=dict(size=12, color=COLORS['success']))
    fig.add_annotation(x=75, y=30, text="📉 Monitor", showarrow=False,
                       font=dict(size=12, color=COLORS['warning']))
    fig.add_annotation(x=25, y=30, text="✅ Sólidos", showarrow=False,
                       font=dict(size=12, color=COLORS['primary']))
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            title='Flight Risk Score',
            showgrid=True,
            gridcolor=COLORS['gray_light'],
            range=[0, 100]
        ),
        yaxis=dict(
            title='Critical Talent Score',
            showgrid=True,
            gridcolor=COLORS['gray_light'],
            range=[0, 100]
        ),
        height=400,
        font=dict(family='Inter, sans-serif', size=12)
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def create_correlation_heatmap():
    """Heatmap de correlações"""
    if not correlations or 'matrix' not in correlations:
        return html.P("Análise não disponível")
    
    corr_matrix = pd.DataFrame(correlations['matrix'])
    
    # Traduzir nomes
    name_mapping = {
        'Age': 'Idade',
        'MonthlyIncome': 'Salário',
        'JobSatisfaction': 'Satisfação',
        'EnvironmentSatisfaction': 'Ambiente',
        'WorkLifeBalance': 'Work-Life',
        'YearsAtCompany': 'Tenure',
        'YearsSinceLastPromotion': 'S/ Promoção',
        'Flight_Risk_Score': 'Flight Risk',
        'Engagement_Index': 'Engajamento',
        'Attrition_Binary': 'Turnover'
    }
    
    corr_matrix = corr_matrix.rename(columns=name_mapping, index=name_mapping)
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.index,
        colorscale='RdBu_r',
        zmid=0,
        text=np.round(corr_matrix.values, 2),
        texttemplate='%{text}',
        textfont={"size": 10},
        hovertemplate="%{x} vs %{y}<br>Correlação: %{z:.3f}<extra></extra>"
    ))
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400,
        font=dict(family='Inter, sans-serif', size=11)
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


# ============================================================
# LAYOUT - HEADER
# ============================================================

header = html.Div([
    html.Div([
        html.Div([
            html.H1([
                html.Span("People Analytics", style={'fontWeight': '700'}),
                html.Span(" | BB Previdência", style={'fontWeight': '400', 'color': COLORS['accent']})
            ], style={
                'color': COLORS['white'],
                'fontSize': '24px',
                'marginBottom': '0'
            }),
            html.P("Dashboard Executivo de Gestão de Pessoas", style={
                'color': 'rgba(255,255,255,0.7)',
                'fontSize': '14px',
                'marginBottom': '0'
            })
        ]),
        html.Div([
            html.Span("🏆", style={'fontSize': '20px', 'marginRight': '8px'}),
            html.Span(f"{metrics['total_employees']} colaboradores", style={
                'color': COLORS['white'],
                'marginRight': '20px',
                'fontSize': '14px'
            }),
            html.Span("📊", style={'fontSize': '20px', 'marginRight': '8px'}),
            html.Span(f"Turnover: {metrics['attrition_rate']:.1f}%", style={
                'color': COLORS['accent'],
                'fontWeight': '600',
                'fontSize': '14px'
            })
        ], style={'display': 'flex', 'alignItems': 'center'})
    ], style={
        'display': 'flex',
        'justifyContent': 'space-between',
        'alignItems': 'center',
        'maxWidth': '1400px',
        'margin': '0 auto',
        'padding': '0 24px'
    })
], style={
    'background': f'linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["primary_dark"]} 100%)',
    'padding': '20px 0',
    'marginBottom': '24px'
})


# ============================================================
# LAYOUT - TABS
# ============================================================

tabs = dcc.Tabs(
    [
        dcc.Tab(label='📊 Dashboard Principal', value='dashboard', className='custom-tab', selected_className='custom-tab--selected'),
        dcc.Tab(label='⚠️ Watchlist', value='watchlist', className='custom-tab', selected_className='custom-tab--selected'),
        dcc.Tab(label='🔬 People Science', value='science', className='custom-tab', selected_className='custom-tab--selected'),
        dcc.Tab(label='💡 Insights', value='insights', className='custom-tab', selected_className='custom-tab--selected'),
        dcc.Tab(label='📋 Plano de Ação', value='action', className='custom-tab', selected_className='custom-tab--selected'),
        dcc.Tab(label='👤 Perfil Ideal', value='profile', className='custom-tab', selected_className='custom-tab--selected'),
    ],
    id='tabs',
    value='dashboard',
    style={
        'maxWidth': '1400px',
        'margin': '0 auto',
        'padding': '0 24px'
    },
    parent_className='custom-tabs',
)


# ============================================================
# LAYOUT - TAB CONTENTS
# ============================================================

def create_dashboard_tab():
    """Tab principal - Executive Overview"""
    return html.Div([
        html.Div(id='executive-version', children='EXECUTIVE_DASH_v2', style={'display':'none'}),
            # Sumário Executivo
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            create_executive_summary_card(df, metrics, driver_analysis, COLORS)
                        ])
                    ], style={
                        'borderRadius': '12px',
                        'border': 'none',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                        'borderLeft': f'4px solid {COLORS["primary"]}'
                    })
                ], md=8),
                dbc.Col([
                    html.H6("🚨 Alertas Prioritários", style={
                        'color': COLORS['dark'],
                        'marginBottom': '16px',
                        'fontWeight': '600'
                    }),
                    create_critical_alerts_section(df, metrics, COLORS)
                ], md=4)
            ], className='mb-4'),
        
            # Health Scorecard
            dbc.Row([
                dbc.Col([
                    html.H6("📊 Health Scorecard - Indicadores de Saúde Organizacional", style={
                        'color': COLORS['dark'],
                        'marginBottom': '16px',
                        'fontWeight': '600'
                    })
                ])
            ]),
            create_health_scorecard(df, metrics, COLORS),
        
            html.Div(style={'height': '24px'}),  # Spacer
        
            # KPIs Financeiros e Operacionais
            dbc.Row([
                dbc.Col([
                    create_kpi_card(
                        "Custo em Risco",
                        f"R$ {metrics['cost_at_risk']:,.0f}",
                        "6 meses de salário dos high-risk",
                        "chart-line",
                        COLORS['danger']
                    )
                ], md=3),
                dbc.Col([
                    create_kpi_card(
                        "Salário Médio",
                        f"R$ {metrics['avg_monthly_income']:,.0f}",
                        "Mensal",
                        "dollar-sign",
                        COLORS['primary']
                    )
                ], md=3),
                dbc.Col([
                    create_kpi_card(
                        "Tenure Médio",
                        f"{metrics['avg_tenure']:.1f} anos",
                        f"{metrics['total_employees']} colaboradores",
                        "clock",
                        COLORS['info']
                    )
                ], md=3),
                dbc.Col([
                    create_kpi_card(
                        "Flight Risk Alto",
                        f"{metrics['high_risk_count']}",
                        f"{metrics['high_risk_count']/metrics['total_employees']*100:.1f}% do total",
                        "exclamation-triangle",
                        COLORS['warning']
                    )
                ], md=3),
            ], className='mb-4'),
        
            # Gráficos Estratégicos
            dbc.Row([
                dbc.Col([
                    create_chart_card(
                        "📈 Tendência de Turnover",
                        create_turnover_trend_chart(df, COLORS),
                        "360px"
                    )
                ], md=6),
                dbc.Col([
                    create_chart_card(
                        "🎯 Quadrantes de Risco",
                        create_risk_quadrant_summary(df, COLORS),
                        "360px"
                    )
                ], md=6),
            ], className='mb-4'),
        
            dbc.Row([
                dbc.Col([
                    create_chart_card(
                        "🔥 Top Drivers de Turnover",
                        create_top_drivers_compact(driver_analysis, COLORS),
                        "340px"
                    )
                ], md=5),
                dbc.Col([
                    create_chart_card(
                        "🏢 Comparativo por Departamento",
                        create_department_comparison(df, COLORS),
                        "340px"
                    )
                ], md=7),
            ])
        ])

def create_watchlist_tab():
    """Tab de Watchlist com colaboradores críticos"""
    watchlist_df = critical_talents.head(15)
    
    # Criar tabela estilizada
    table_rows = []
    for _, row in watchlist_df.iterrows():
        table_rows.append(html.Tr([
            html.Td(f"#{int(row['EmployeeNumber'])}"),
            html.Td(row['JobRole']),
            html.Td(row['Department']),
            html.Td(f"{row['YearsAtCompany']:.0f} anos"),
            html.Td(f"R$ {row['MonthlyIncome']:,.0f}"),
            html.Td(create_risk_badge(row['Flight_Risk_Score'])),
            html.Td(f"{row['Critical_Talent_Score']:.0f}"),
            html.Td(f"{row['Engagement_Index']:.0f}"),
            html.Td(
                dbc.Button(
                    "Detalhes",
                    id={"type": "open-details-modal", "index": int(row['EmployeeNumber'])},
                    color="info",
                    size="sm"
                )
            )
        ]))
    
    return html.Div([
        # Header da Watchlist
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.H4("⚠️ Watchlist de Talentos Críticos", style={
                        'color': COLORS['dark'],
                        'marginBottom': '8px'
                    }),
                    html.P(
                        f"Colaboradores de alto valor com risco elevado de saída ({len(critical_talents)} identificados)",
                        style={'color': COLORS['gray'], 'marginBottom': '0'}
                    )
                ]),
                html.Div([
                    dbc.Badge(f"Custo em risco: R$ {metrics['cost_at_risk']:,.0f}", color="danger", className="me-2"),
                    dbc.Badge(f"{metrics['high_risk_count']} em alto risco", color="warning")
                ])
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'})
        ], className='mb-4', style={
            'borderRadius': '12px',
            'border': 'none',
            'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
        }),
        # Tabela
        dbc.Card([
            html.Table([
                html.Thead([
                    html.Tr([
                        html.Th("ID"),
                        html.Th("Cargo"),
                        html.Th("Departamento"),
                        html.Th("Tenure"),
                        html.Th("Salário"),
                        html.Th("Flight Risk"),
                        html.Th("Critical Score"),
                        html.Th("Engajamento"),
                        html.Th("Detalhes"),
                    ], style={'backgroundColor': COLORS['light']})
                ]),
                html.Tbody(table_rows)
            ], style={
                'width': '100%',
                'borderCollapse': 'collapse',
                'fontSize': '14px'
            }, className='watchlist-table')
        ], style={
            'borderRadius': '12px',
            'border': 'none',
            'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
            'overflow': 'hidden'
        }),
        # Modal de detalhes
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Detalhes do Colaborador")),
            dbc.ModalBody(id="details-modal-body"),
            dbc.ModalFooter(
                dbc.Button("Fechar", id="close-details-modal", className="ms-auto", n_clicks=0)
            ),
        ], id="details-modal", is_open=False)
    ])
# Callback para abrir/fechar modal e mostrar detalhes
@callback(
    Output("details-modal", "is_open"),
    Output("details-modal-body", "children"),
    Input({"type": "open-details-modal", "index": dash.ALL}, "n_clicks"),
    State("details-modal", "is_open"),
    State({"type": "open-details-modal", "index": dash.ALL}, "id"),
    Input("close-details-modal", "n_clicks"),
    prevent_initial_call=True
)
def toggle_details_modal(open_clicks, is_open, btn_ids, close_click):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, dash.no_update
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    # Se for botão de fechar
    if "close-details-modal" in trigger:
        return False, dash.no_update
    # Se for botão de abrir
    if open_clicks and any(open_clicks):
        idx = [i for i, n in enumerate(open_clicks) if n]
        if idx:
            emp_id = btn_ids[idx[0]]["index"]
            # Buscar dados do colaborador diretamente do dataframe original
            user_row = df[df["EmployeeNumber"] == emp_id]
            if user_row.empty:
                return is_open, html.Div("Colaborador não encontrado.")
            row = user_row.iloc[0]
            # Recalcular motivos de risco para o colaborador
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
            # ...existing code for details...
            details = [
                html.Div([
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-user-circle", style={"fontSize": "54px", "color": COLORS['primary']}),
                        ], style={"marginBottom": "8px"}),
                        html.H4(row.get('EmployeeName', f"Colaborador #{int(row['EmployeeNumber'])}"), style={"color": COLORS['primary'], "marginBottom": "2px", "fontWeight": "700"}) if 'EmployeeName' in row else html.H4(f"Colaborador #{int(row['EmployeeNumber'])}", style={"color": COLORS['primary'], "marginBottom": "2px", "fontWeight": "700"}),
                        html.Div(f"ID: #{int(row['EmployeeNumber'])}", style={"color": COLORS['gray'], "fontSize": "13px", "marginBottom": "8px"}),
                    ], style={"textAlign": "center", "marginBottom": "12px"}),
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-briefcase", style={"marginRight": "6px", "color": COLORS['primary']}),
                            html.Span(f"Cargo: {row['JobRole']}")
                        ], style={"marginBottom": "4px"}),
                        html.Div([
                            html.I(className="fas fa-building", style={"marginRight": "6px", "color": COLORS['primary']}),
                            html.Span(f"Departamento: {row['Department']}")
                        ], style={"marginBottom": "4px"}),
                        html.Div([
                            html.I(className="fas fa-calendar-alt", style={"marginRight": "6px", "color": COLORS['primary']}),
                            html.Span(f"Tempo de casa: {row['YearsAtCompany']:.0f} anos")
                        ], style={"marginBottom": "4px"}),
                        html.Div([
                            html.I(className="fas fa-money-bill-wave", style={"marginRight": "6px", "color": COLORS['primary']}),
                            html.Span(f"Salário: R$ {row['MonthlyIncome']:,.0f}")
                        ], style={"marginBottom": "4px"}),
                    ], style={"marginBottom": "16px", "background": COLORS['light'], "padding": "12px 16px", "borderRadius": "8px", "boxShadow": "0 1px 3px rgba(0,0,0,0.04)"}),
                ]),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-exclamation-triangle", style={"marginRight": "6px", "color": COLORS['danger']}),
                        html.Span(f"Flight Risk: {row['Flight_Risk_Score']:.2f}")
                    ], style={"marginBottom": "4px"}),
                    html.Div([
                        html.I(className="fas fa-star", style={"marginRight": "6px", "color": COLORS['warning']}),
                        html.Span(f"Critical Score: {row['Critical_Talent_Score']:.0f}")
                    ], style={"marginBottom": "4px"}),
                    html.Div([
                        html.I(className="fas fa-heart", style={"marginRight": "6px", "color": COLORS['success']}),
                        html.Span(f"Engajamento: {row['Engagement_Index']:.0f}")
                    ], style={"marginBottom": "4px"}),
                ], style={"marginBottom": "16px", "background": "#F8FAFC", "padding": "10px 16px", "borderRadius": "8px"}),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-birthday-cake", style={"marginRight": "6px", "color": COLORS['primary']}),
                        html.Span(f"Idade: {row['Age']}")
                    ], style={"marginBottom": "4px"}),
                    html.Div([
                        html.I(className="fas fa-venus-mars", style={"marginRight": "6px", "color": COLORS['primary']}),
                        html.Span(f"Gênero: {row['Gender']}")
                    ], style={"marginBottom": "4px"}),
                    html.Div([
                        html.I(className="fas fa-ring", style={"marginRight": "6px", "color": COLORS['primary']}),
                        html.Span(f"Estado Civil: {row['MaritalStatus']}")
                    ], style={"marginBottom": "4px"}),
                    html.Div([
                        html.I(className="fas fa-graduation-cap", style={"marginRight": "6px", "color": COLORS['primary']}),
                        html.Span(f"Educação: {row['Education']}")
                    ], style={"marginBottom": "4px"}),
                ], style={"marginBottom": "16px"}),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-home", style={"marginRight": "6px", "color": COLORS['primary']}),
                        html.Span(f"Distância de Casa: {row['DistanceFromHome']} km")
                    ], style={"marginBottom": "4px"}),
                    html.Div([
                        html.I(className="fas fa-clock", style={"marginRight": "6px", "color": COLORS['primary']}),
                        html.Span(f"Total de Anos Trabalhados: {row['TotalWorkingYears']}")
                    ], style={"marginBottom": "4px"}),
                    html.Div([
                        html.I(className="fas fa-smile", style={"marginRight": "6px", "color": COLORS['primary']}),
                        html.Span(f"Satisfação no Trabalho: {row['JobSatisfaction']}")
                    ], style={"marginBottom": "4px"}),
                    html.Div([
                        html.I(className="fas fa-leaf", style={"marginRight": "6px", "color": COLORS['primary']}),
                        html.Span(f"Ambiente: {row['EnvironmentSatisfaction']}")
                    ], style={"marginBottom": "4px"}),
                    html.Div([
                        html.I(className="fas fa-chalkboard-teacher", style={"marginRight": "6px", "color": COLORS['primary']}),
                        html.Span(f"Treinamentos no Ano: {row['TrainingTimesLastYear']}")
                    ], style={"marginBottom": "4px"}),
                    html.Div([
                        html.I(className="fas fa-trophy", style={"marginRight": "6px", "color": COLORS['primary']}),
                        html.Span(f"Última Promoção: {row['YearsSinceLastPromotion']} anos atrás")
                    ], style={"marginBottom": "4px"}),
                ], style={"marginBottom": "16px"}),
                html.Hr(),
                html.Div([
                    html.H5([
                        html.I(className="fas fa-exclamation-circle", style={"marginRight": "8px", "color": COLORS['danger']}),
                        "Motivo de Risco"
                    ], style={"marginTop": "12px", "color": COLORS['danger']}),
                    (html.Ul([html.Li(m) for m in reasons]) if reasons else html.P("Não identificado como alto risco ou sem motivo específico."))
                ], style={"background": "#FFF5F5", "padding": "12px 16px", "borderRadius": "8px", "marginTop": "8px", "marginBottom": "0"})
            ]
            return True, html.Div(details, style={"fontSize": "15px"})
    return is_open, dash.no_update


def create_science_tab():
    """Tab de People Science com análises estatísticas"""
    return html.Div([
        # Performance dos modelos
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("📈 Performance dos Modelos", style={'color': COLORS['dark']}),
                        html.Div([
                            html.Div([
                                html.P("Logistic Regression", style={'marginBottom': '4px', 'color': COLORS['gray']}),
                                html.H4(f"{driver_analysis['model_performance']['logistic_auc']:.1%}", 
                                       style={'color': COLORS['primary']})
                            ], className='me-4'),
                            html.Div([
                                html.P("Random Forest", style={'marginBottom': '4px', 'color': COLORS['gray']}),
                                html.H4(f"{driver_analysis['model_performance']['rf_auc']:.1%}",
                                       style={'color': COLORS['success']})
                            ], className='me-4'),
                            html.Div([
                                html.P("Gradient Boosting", style={'marginBottom': '4px', 'color': COLORS['gray']}),
                                html.H4(f"{driver_analysis['model_performance']['gb_auc']:.1%}",
                                       style={'color': COLORS['accent_dark']})
                            ])
                        ], style={'display': 'flex'})
                    ])
                ], style={'borderRadius': '12px', 'border': 'none', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'})
            ], md=12)
        ], className='mb-4'),
        
        # Gráficos de ciência
        dbc.Row([
            dbc.Col([
                create_chart_card("🎯 Drivers de Turnover (Importância)", create_driver_importance_chart(), "450px")
            ], md=6),
            dbc.Col([
                create_chart_card("📊 Matriz de Correlações", create_correlation_heatmap(), "450px")
            ], md=6)
        ], className='mb-4'),
        
        dbc.Row([
            dbc.Col([
                create_chart_card("📈 Curva de Sobrevivência (Retenção)", create_survival_curve(), "400px")
            ], md=6),
            dbc.Col([
                create_chart_card("🎯 Matriz de Risco (Flight Risk × Valor)", create_risk_matrix_chart(), "450px")
            ], md=6)
        ]),
        
        # Overtime Impact
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H6("🔬 Análise Difference-in-Differences: Impacto de Overtime", 
                               style={'marginBottom': '0', 'color': COLORS['dark']})
                    ], style={'backgroundColor': COLORS['white'], 'border': 'none'}),
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.H5("Sem Hora Extra", style={'color': COLORS['success']}),
                                html.P(f"Turnover: {overtime_impact['Taxa de Turnover']['overtime_no_mean']*100:.1f}%"),
                                html.P(f"N = {overtime_impact['Taxa de Turnover']['overtime_no_n']}")
                            ], className='me-5'),
                            html.Div([
                                html.H5("Com Hora Extra", style={'color': COLORS['danger']}),
                                html.P(f"Turnover: {overtime_impact['Taxa de Turnover']['overtime_yes_mean']*100:.1f}%"),
                                html.P(f"N = {overtime_impact['Taxa de Turnover']['overtime_yes_n']}")
                            ], className='me-5'),
                            html.Div([
                                html.H5("Diferença", style={'color': COLORS['primary']}),
                                html.P(f"+{overtime_impact['Taxa de Turnover']['percentage_difference']:.1f}%"),
                                html.P(f"p-value: {overtime_impact['Taxa de Turnover']['p_value']:.4f}"),
                                dbc.Badge(
                                    "Significativo" if overtime_impact['Taxa de Turnover']['is_significant'] else "Não Significativo",
                                    color="success" if overtime_impact['Taxa de Turnover']['is_significant'] else "secondary"
                                )
                            ])
                        ], style={'display': 'flex'})
                    ])
                ], style={'borderRadius': '12px', 'border': 'none', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'})
            ], md=12)
        ], className='mt-4')
    ])


def create_insights_tab():
    """Tab de Insights automáticos"""
    insight_cards = []
    
    for i, insight in enumerate(insights[:8]):
        icon = "💡" if insight['type'] == 'observation' else "⚠️" if insight['type'] == 'alert' else "✅"
        color = COLORS['primary'] if insight['type'] == 'observation' else COLORS['warning'] if insight['type'] == 'alert' else COLORS['success']
        
        insight_cards.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Span(icon, style={'fontSize': '24px', 'marginRight': '12px'}),
                            html.H6(insight['title'], style={
                                'color': COLORS['dark'],
                                'marginBottom': '0',
                                'flex': '1'
                            })
                        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
                        html.P(insight['description'], style={
                            'color': COLORS['gray'],
                            'fontSize': '14px',
                            'marginBottom': '12px'
                        }),
                        html.P(insight['recommendation'], style={
                            'color': color,
                            'fontSize': '13px',
                            'fontWeight': '600',
                            'marginBottom': '0',
                            'padding': '8px 12px',
                            'backgroundColor': f'{color}10',
                            'borderRadius': '8px'
                        })
                    ])
                ], style={
                    'borderRadius': '12px',
                    'border': 'none',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
                    'height': '100%'
                })
            ], md=6, className='mb-4')
        )
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("💡 Insights Gerados Automaticamente", style={
                    'color': COLORS['dark'],
                    'marginBottom': '8px'
                }),
                html.P(
                    f"Análise identificou {len(insights)} insights acionáveis baseados nos dados",
                    style={'color': COLORS['gray'], 'marginBottom': '24px'}
                )
            ])
        ]),
        dbc.Row(insight_cards)
    ])


def create_action_tab():
    """Tab de Plano de Ação"""
    action_cards = []
    
    priority_colors = {
        'alta': COLORS['danger'],
        'média': COLORS['warning'],
        'baixa': COLORS['success']
    }
    
    for action in action_plan[:6]:
        priority_color = priority_colors.get(action['priority'].lower(), COLORS['primary'])
        
        action_cards.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            dbc.Badge(action['priority'].upper(), style={
                                'backgroundColor': priority_color,
                                'marginBottom': '12px'
                            }),
                            html.Span(f"Prazo: {action['timeline']}", style={
                                'color': COLORS['gray'],
                                'fontSize': '12px',
                                'marginLeft': '8px'
                            })
                        ]),
                        html.H6(action['title'], style={
                            'color': COLORS['dark'],
                            'marginBottom': '12px'
                        }),
                        html.P(action['description'], style={
                            'color': COLORS['gray'],
                            'fontSize': '14px',
                            'marginBottom': '16px'
                        }),
                        html.Div([
                            html.Div([
                                html.P("Responsável", style={'fontSize': '11px', 'color': COLORS['gray'], 'marginBottom': '2px'}),
                                html.P(action['owner'], style={'fontSize': '13px', 'fontWeight': '600', 'marginBottom': '0'})
                            ], className='me-4'),
                            html.Div([
                                html.P("Impacto Esperado", style={'fontSize': '11px', 'color': COLORS['gray'], 'marginBottom': '2px'}),
                                html.P(action['expected_impact'], style={'fontSize': '13px', 'fontWeight': '600', 'marginBottom': '0', 'color': COLORS['success']})
                            ])
                        ], style={'display': 'flex'})
                    ])
                ], style={
                    'borderRadius': '12px',
                    'border': 'none',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
                    'borderLeft': f'4px solid {priority_color}',
                    'height': '100%'
                })
            ], md=6, className='mb-4')
        )
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("📋 Plano de Ação Recomendado", style={
                    'color': COLORS['dark'],
                    'marginBottom': '8px'
                }),
                html.P(
                    "Ações priorizadas por impacto e urgência para redução de turnover",
                    style={'color': COLORS['gray'], 'marginBottom': '24px'}
                )
            ])
        ]),
        dbc.Row(action_cards)
    ])


def create_profile_tab():
    """Tab de Perfil Ideal do Colaborador"""
    profile = ideal_profile
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("👤 Perfil Ideal do Colaborador Engajado", style={
                    'color': COLORS['dark'],
                    'marginBottom': '8px'
                }),
                html.P(
                    "Características dos colaboradores com maior retenção e engajamento",
                    style={'color': COLORS['gray'], 'marginBottom': '24px'}
                )
            ])
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H6("📊 Métricas do Perfil Ideal", style={'marginBottom': '0'})
                    ], style={'backgroundColor': COLORS['white'], 'border': 'none'}),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.P("Idade Média", style={'color': COLORS['gray'], 'fontSize': '12px', 'marginBottom': '4px'}),
                                    html.H4(f"{profile['age_range']}", style={'color': COLORS['primary']})
                                ], className='mb-3'),
                                html.Div([
                                    html.P("Salário Médio", style={'color': COLORS['gray'], 'fontSize': '12px', 'marginBottom': '4px'}),
                                    html.H4(f"R$ {profile['avg_income']:,.0f}", style={'color': COLORS['primary']})
                                ])
                            ], md=4),
                            dbc.Col([
                                html.Div([
                                    html.P("Tenure Médio", style={'color': COLORS['gray'], 'fontSize': '12px', 'marginBottom': '4px'}),
                                    html.H4(f"{profile['avg_tenure']:.1f} anos", style={'color': COLORS['primary']})
                                ], className='mb-3'),
                                html.Div([
                                    html.P("Satisfação", style={'color': COLORS['gray'], 'fontSize': '12px', 'marginBottom': '4px'}),
                                    html.H4(f"{profile['avg_satisfaction']:.1f}/4", style={'color': COLORS['success']})
                                ])
                            ], md=4),
                            dbc.Col([
                                html.Div([
                                    html.P("Work-Life Balance", style={'color': COLORS['gray'], 'fontSize': '12px', 'marginBottom': '4px'}),
                                    html.H4(f"{profile['avg_work_life_balance']:.1f}/4", style={'color': COLORS['primary']})
                                ], className='mb-3'),
                                html.Div([
                                    html.P("Engajamento", style={'color': COLORS['gray'], 'fontSize': '12px', 'marginBottom': '4px'}),
                                    html.H4(f"{profile['avg_engagement']:.0f}/100", style={'color': COLORS['success']})
                                ])
                            ], md=4)
                        ])
                    ])
                ], style={'borderRadius': '12px', 'border': 'none', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'})
            ], md=8),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H6("🎯 Características-Chave", style={'marginBottom': '0'})
                    ], style={'backgroundColor': COLORS['white'], 'border': 'none'}),
                    dbc.CardBody([
                        html.Ul([
                            html.Li([
                                html.Strong("Overtime: "),
                                profile['overtime_profile']
                            ], style={'marginBottom': '8px'}),
                            html.Li([
                                html.Strong("Departamento mais comum: "),
                                profile['top_department']
                            ], style={'marginBottom': '8px'}),
                            html.Li([
                                html.Strong("Estado Civil frequente: "),
                                profile['marital_status']
                            ], style={'marginBottom': '8px'}),
                            html.Li([
                                html.Strong("Treinamentos/ano: "),
                                f"{profile['avg_training']:.1f}"
                            ])
                        ], style={'listStyle': 'none', 'padding': '0', 'margin': '0'})
                    ])
                ], style={
                    'borderRadius': '12px',
                    'border': 'none',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
                    'height': '100%'
                })
            ], md=4)
        ], className='mb-4'),
        
        # Recomendações baseadas no perfil
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H6("💡 Recomendações de Contratação e Retenção", style={'marginBottom': '0'})
                    ], style={'backgroundColor': COLORS['white'], 'border': 'none'}),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H6("🎯 Contratação", style={'color': COLORS['primary'], 'marginBottom': '12px'}),
                                html.Ul([
                                    html.Li("Priorizar candidatos com perfil de work-life balance"),
                                    html.Li("Avaliar fit cultural durante entrevistas"),
                                    html.Li("Buscar candidatos com expectativas salariais alinhadas"),
                                    html.Li("Valorizar experiência moderada no mercado")
                                ], style={'fontSize': '14px', 'color': COLORS['gray']})
                            ], md=4),
                            dbc.Col([
                                html.H6("🔄 Onboarding", style={'color': COLORS['success'], 'marginBottom': '12px'}),
                                html.Ul([
                                    html.Li("Programa de mentoria nos primeiros 6 meses"),
                                    html.Li("Definir expectativas claras de carreira"),
                                    html.Li("Integração cultural intensiva"),
                                    html.Li("Check-ins frequentes no primeiro ano")
                                ], style={'fontSize': '14px', 'color': COLORS['gray']})
                            ], md=4),
                            dbc.Col([
                                html.H6("⭐ Retenção", style={'color': COLORS['warning'], 'marginBottom': '12px'}),
                                html.Ul([
                                    html.Li("Política clara de promoções (máx 3 anos)"),
                                    html.Li("Limitar overtime a casos excepcionais"),
                                    html.Li("Investir em treinamento contínuo"),
                                    html.Li("Monitorar satisfação trimestralmente")
                                ], style={'fontSize': '14px', 'color': COLORS['gray']})
                            ], md=4)
                        ])
                    ])
                ], style={'borderRadius': '12px', 'border': 'none', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'})
            ])
        ])
    ])


# ============================================================
# LAYOUT PRINCIPAL
# ============================================================

app.layout = html.Div([
    header,
    html.Div([
        tabs,
        html.Div(id='tab-content', className='tab-fadein', style={'padding': '24px', 'maxWidth': '1400px', 'margin': '0 auto'})
    ]),
    
    # Footer
    html.Footer([
        html.Div([
            html.P([
                "People Analytics Dashboard | BB Previdência © 2024 | ",
                html.Span("Desenvolvido com Dash & Plotly", style={'color': COLORS['accent']})
            ], style={
                'color': 'rgba(255,255,255,0.7)',
                'fontSize': '13px',
                'marginBottom': '0'
            })
        ], style={'textAlign': 'center', 'padding': '20px'})
    ], style={
        'backgroundColor': COLORS['primary_dark'],
        'marginTop': '40px'
    })
], style={
    'backgroundColor': COLORS['light'],
    'minHeight': '100vh',
    'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif'
})


# ============================================================
# CALLBACKS
# ============================================================

@callback(
    Output('tab-content', 'children'),
    Input('tabs', 'value')
)
def render_tab_content(tab):
    print(f"[render_tab_content] requested tab: {tab}")
    if tab == 'dashboard':
        return create_dashboard_tab()
    elif tab == 'watchlist':
        return create_watchlist_tab()
    elif tab == 'science':
        return create_science_tab()
    elif tab == 'insights':
        return create_insights_tab()
    elif tab == 'action':
        return create_action_tab()
    elif tab == 'profile':
        return create_profile_tab()
    return create_dashboard_tab()


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 People Analytics Dashboard - BB Previdência")
    print("="*60)
    print(f"📊 Total de colaboradores: {metrics['total_employees']}")
    print(f"📈 Taxa de Turnover: {metrics['attrition_rate']:.1f}%")
    print(f"⚠️  Colaboradores em Alto Risco: {metrics['high_risk_count']}")
    print(f"💰 Custo em Risco: R$ {metrics['cost_at_risk']:,.0f}")
    print("="*60)
    print("\n🌐 Acesse: http://127.0.0.1:8050")
    print("\n")
    
    app.run(debug=True, port=8050)
