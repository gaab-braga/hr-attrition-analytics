"""Segmentação dos colaboradores com K-Means, escolha de k pelo silhouette e perfil de cada grupo."""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, silhouette_samples
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


class ClusterAnalyzer:
    """
    Análise de Segmentação de Colaboradores
    K-Means com interpretação detalhada
    """
    
    def __init__(self, df):
        self.df = df.copy()
        self.scaler = None
        self.model = None
        self.feature_names = None
        self.results = {}
        
    def prepare_features(self):
        """
        Prepara features para clustering
        """
        df = self.df.copy()
        
        # Features para clustering
        cluster_features = [
            'Age', 'MonthlyIncome', 'YearsAtCompany', 'JobSatisfaction',
            'EnvironmentSatisfaction', 'WorkLifeBalance', 'YearsWithCurrManager',
            'YearsSinceLastPromotion', 'NumCompaniesWorked', 'TotalWorkingYears',
            'TrainingTimesLastYear', 'JobLevel', 'JobInvolvement',
            'DistanceFromHome', 'PercentSalaryHike'
        ]
        
        # Adicionar features calculadas se existirem
        optional_features = ['Flight_Risk_Score', 'Engagement_Index', 'Critical_Talent_Score']
        for feat in optional_features:
            if feat in df.columns:
                cluster_features.append(feat)
        
        # Filtrar existentes
        self.feature_names = [f for f in cluster_features if f in df.columns]
        
        X = df[self.feature_names].fillna(df[self.feature_names].median())
        
        # Normalizar
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled, X
    
    def find_optimal_k(self, max_k=8):
        """
        Encontra número ótimo de clusters usando Elbow e Silhouette
        """
        X_scaled, _ = self.prepare_features()
        
        results = {
            'k_values': [],
            'inertias': [],
            'silhouette_scores': [],
            'optimal_k_elbow': None,
            'optimal_k_silhouette': None
        }
        
        for k in range(2, max_k + 1):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X_scaled)
            
            inertia = kmeans.inertia_
            silhouette = silhouette_score(X_scaled, kmeans.labels_)
            
            results['k_values'].append(k)
            results['inertias'].append(inertia)
            results['silhouette_scores'].append(silhouette)
        
        # Optimal K por Silhouette (máximo)
        best_silhouette_idx = np.argmax(results['silhouette_scores'])
        results['optimal_k_silhouette'] = results['k_values'][best_silhouette_idx]
        
        # Optimal K por Elbow (maior queda relativa)
        inertias = np.array(results['inertias'])
        diffs = np.diff(inertias)
        diffs2 = np.diff(diffs)
        if len(diffs2) > 0:
            elbow_idx = np.argmax(np.abs(diffs2)) + 2
            results['optimal_k_elbow'] = results['k_values'][elbow_idx] if elbow_idx < len(results['k_values']) else 4
        else:
            results['optimal_k_elbow'] = 4
        
        self.results['optimal_k'] = results
        return results
    
    def run_clustering(self, n_clusters=4):
        """
        Executa K-Means com n_clusters
        """
        X_scaled, X_original = self.prepare_features()
        
        # Fit K-Means
        self.model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = self.model.fit_predict(X_scaled)
        
        # Adicionar labels ao dataframe
        self.df['Cluster'] = cluster_labels
        
        # Silhouette scores
        overall_silhouette = silhouette_score(X_scaled, cluster_labels)
        sample_silhouettes = silhouette_samples(X_scaled, cluster_labels)
        
        # Distância ao centróide
        distances = self.model.transform(X_scaled)
        min_distances = distances.min(axis=1)
        
        self.df['Silhouette_Score'] = sample_silhouettes
        self.df['Distance_to_Centroid'] = min_distances
        
        self.results['clustering'] = {
            'n_clusters': n_clusters,
            'inertia': self.model.inertia_,
            'overall_silhouette': overall_silhouette,
            'cluster_labels': cluster_labels.tolist(),
            'centroids': self.model.cluster_centers_.tolist()
        }
        
        return cluster_labels
    
    def create_cluster_profiles(self):
        """
        Cria perfis detalhados de cada cluster
        """
        df = self.df.copy()
        
        if 'Cluster' not in df.columns:
            self.run_clustering()
            df = self.df.copy()
        
        profiles = []
        
        for cluster_id in sorted(df['Cluster'].unique()):
            cluster_df = df[df['Cluster'] == cluster_id]
            
            # Métricas básicas
            profile = {
                'cluster_id': int(cluster_id),
                'size': len(cluster_df),
                'pct_total': len(cluster_df) / len(df) * 100,
                
                # Demográficos
                'avg_age': cluster_df['Age'].mean(),
                'age_std': cluster_df['Age'].std(),
                'age_range': f"{cluster_df['Age'].min():.0f}-{cluster_df['Age'].max():.0f}",
                
                # Tenure
                'avg_tenure': cluster_df['YearsAtCompany'].mean(),
                'tenure_std': cluster_df['YearsAtCompany'].std(),
                
                # Compensação
                'avg_income': cluster_df['MonthlyIncome'].mean(),
                'income_std': cluster_df['MonthlyIncome'].std(),
                'avg_job_level': cluster_df['JobLevel'].mean(),
                
                # Satisfação
                'avg_job_satisfaction': cluster_df['JobSatisfaction'].mean(),
                'avg_environment_satisfaction': cluster_df['EnvironmentSatisfaction'].mean(),
                'avg_work_life_balance': cluster_df['WorkLifeBalance'].mean(),
                
                # Attrition
                'attrition_rate': cluster_df['Attrition_Binary'].mean() * 100,
                'attrition_count': int(cluster_df['Attrition_Binary'].sum()),
                
                # Performance/Engajamento
                'avg_training': cluster_df['TrainingTimesLastYear'].mean(),
                'avg_years_since_promotion': cluster_df['YearsSinceLastPromotion'].mean(),
                
                # Silhouette (qualidade do cluster)
                'avg_silhouette': cluster_df['Silhouette_Score'].mean(),
                'silhouette_std': cluster_df['Silhouette_Score'].std(),
                
                # Distribuições categóricas
                'overtime_pct': len(cluster_df[cluster_df['OverTime'] == 'Yes']) / len(cluster_df) * 100 if 'OverTime' in cluster_df.columns else 0,
                'department_distribution': cluster_df['Department'].value_counts(normalize=True).head(3).to_dict() if 'Department' in cluster_df.columns else {},
                'job_role_top': cluster_df['JobRole'].mode().iloc[0] if 'JobRole' in cluster_df.columns and len(cluster_df['JobRole'].mode()) > 0 else 'N/A',
                'gender_distribution': cluster_df['Gender'].value_counts(normalize=True).to_dict() if 'Gender' in cluster_df.columns else {}
            }
            
            # Adicionar métricas calculadas se existirem
            if 'Flight_Risk_Score' in cluster_df.columns:
                profile['avg_flight_risk'] = cluster_df['Flight_Risk_Score'].mean()
            if 'Engagement_Index' in cluster_df.columns:
                profile['avg_engagement'] = cluster_df['Engagement_Index'].mean()
            if 'Critical_Talent_Score' in cluster_df.columns:
                profile['avg_critical_score'] = cluster_df['Critical_Talent_Score'].mean()
            
            # Gerar nome e descrição do cluster
            profile['cluster_name'], profile['description'] = self._generate_cluster_name(profile)
            
            profiles.append(profile)
        
        # Ordenar por tamanho
        profiles = sorted(profiles, key=lambda x: x['size'], reverse=True)
        
        self.results['profiles'] = profiles
        return profiles
    
    def _generate_cluster_name(self, profile):
        """
        Gera nome e descrição automática do cluster baseado nas características
        """
        name = "Indefinido"
        description = ""
        
        # Regras para naming
        high_risk = profile.get('avg_flight_risk', 50) > 60 or profile.get('attrition_rate', 0) > 20
        high_engagement = profile.get('avg_engagement', 50) > 70
        senior = profile.get('avg_tenure', 0) > 8
        junior = profile.get('avg_tenure', 0) < 2
        high_income = profile.get('avg_income', 0) > 8000
        low_satisfaction = profile.get('avg_job_satisfaction', 3) < 2.5
        high_overtime = profile.get('overtime_pct', 0) > 40
        
        if high_risk and low_satisfaction:
            name = "Em Risco"
            description = "Colaboradores insatisfeitos com alto risco de saída. Atenção imediata necessária."
        elif senior and high_engagement and not high_risk:
            name = "Veteranos Engajados"
            description = "Colaboradores experientes e comprometidos. Potenciais mentores e líderes."
        elif junior and high_risk:
            name = "Novatos Instáveis"
            description = "Colaboradores recentes com sinais de desengajamento. Fortalecer onboarding."
        elif high_income and not high_risk:
            name = "Talentos Premium"
            description = "Colaboradores bem remunerados e estáveis. Proteger investimento."
        elif high_engagement and not high_risk:
            name = "Alta Performance"
            description = "Colaboradores engajados e produtivos. Desenvolver para liderança."
        elif high_overtime:
            name = "Sobrecarregados"
            description = "Alta carga de trabalho. Monitorar burnout e redistribuir demandas."
        elif low_satisfaction and not high_risk:
            name = "Silenciosos"
            description = "Baixa satisfação mas não saíram ainda. Investigar causas."
        else:
            name = "Base Sólida"
            description = "Colaboradores estáveis com métricas moderadas. Manter engajamento."
        
        return name, description
    
    def compare_clusters_statistically(self):
        """
        Compara clusters estatisticamente
        """
        df = self.df.copy()
        
        if 'Cluster' not in df.columns:
            return {}
        
        comparisons = []
        
        # Variáveis para comparação
        compare_vars = [
            'MonthlyIncome', 'YearsAtCompany', 'JobSatisfaction',
            'Attrition_Binary', 'Age', 'WorkLifeBalance'
        ]
        compare_vars = [v for v in compare_vars if v in df.columns]
        
        for var in compare_vars:
            groups = [df[df['Cluster'] == c][var].dropna().values for c in df['Cluster'].unique()]
            
            # ANOVA
            f_stat, p_value = stats.f_oneway(*groups) if len(groups) > 2 else stats.ttest_ind(*groups)
            
            # Effect size (eta-squared)
            if len(groups) > 2:
                ss_between = sum(len(g) * (g.mean() - df[var].mean())**2 for g in groups)
                ss_total = sum((df[var] - df[var].mean())**2)
                eta_squared = ss_between / ss_total if ss_total > 0 else 0
            else:
                # Cohen's d para 2 grupos
                pooled_std = np.sqrt((groups[0].std()**2 + groups[1].std()**2) / 2)
                eta_squared = abs(groups[0].mean() - groups[1].mean()) / pooled_std if pooled_std > 0 else 0
            
            comparisons.append({
                'variable': var,
                'f_statistic': f_stat,
                'p_value': p_value,
                'is_significant': p_value < 0.05,
                'effect_size': eta_squared,
                'effect_interpretation': 'Grande' if eta_squared > 0.14 else 'Médio' if eta_squared > 0.06 else 'Pequeno'
            })
        
        self.results['statistical_comparison'] = comparisons
        return comparisons
    
    def identify_cluster_drivers(self):
        """
        Identifica quais features mais diferenciam os clusters
        """
        df = self.df.copy()
        
        if 'Cluster' not in df.columns:
            return {}
        
        # Calcular médias por cluster e geral
        feature_importance = []
        
        for feature in self.feature_names:
            overall_mean = df[feature].mean()
            overall_std = df[feature].std()
            
            if overall_std == 0:
                continue
            
            # Calcular quanto cada cluster desvia da média
            max_deviation = 0
            deviations = []
            
            for cluster_id in df['Cluster'].unique():
                cluster_mean = df[df['Cluster'] == cluster_id][feature].mean()
                z_deviation = (cluster_mean - overall_mean) / overall_std
                deviations.append({
                    'cluster': int(cluster_id),
                    'z_deviation': z_deviation,
                    'direction': 'Acima' if z_deviation > 0 else 'Abaixo'
                })
                max_deviation = max(max_deviation, abs(z_deviation))
            
            feature_importance.append({
                'feature': feature,
                'max_deviation': max_deviation,
                'cluster_deviations': deviations
            })
        
        # Ordenar por importância
        feature_importance = sorted(feature_importance, key=lambda x: x['max_deviation'], reverse=True)
        
        self.results['feature_importance'] = feature_importance[:10]
        return feature_importance[:10]
    
    def get_cluster_recommendations(self):
        """
        Gera recomendações específicas para cada cluster
        """
        profiles = self.results.get('profiles', [])
        
        if not profiles:
            profiles = self.create_cluster_profiles()
        
        recommendations = []
        
        for profile in profiles:
            cluster_recs = {
                'cluster_id': profile['cluster_id'],
                'cluster_name': profile['cluster_name'],
                'size': profile['size'],
                'attrition_rate': profile['attrition_rate'],
                'priority': 'Alta' if profile['attrition_rate'] > 20 else 'Média' if profile['attrition_rate'] > 10 else 'Baixa',
                'actions': []
            }
            
            # Recomendações baseadas em métricas
            if profile['attrition_rate'] > 20:
                cluster_recs['actions'].append({
                    'action': 'Programa de retenção urgente',
                    'rationale': f"Taxa de turnover de {profile['attrition_rate']:.1f}% é crítica"
                })
            
            if profile['avg_job_satisfaction'] < 2.5:
                cluster_recs['actions'].append({
                    'action': 'Pesquisa de clima focada',
                    'rationale': f"Satisfação média de {profile['avg_job_satisfaction']:.1f}/4 está baixa"
                })
            
            if profile.get('overtime_pct', 0) > 40:
                cluster_recs['actions'].append({
                    'action': 'Revisão de carga de trabalho',
                    'rationale': f"{profile.get('overtime_pct', 0):.0f}% fazem hora extra"
                })
            
            if profile['avg_years_since_promotion'] > 4:
                cluster_recs['actions'].append({
                    'action': 'Programa de carreira',
                    'rationale': f"Média de {profile['avg_years_since_promotion']:.1f} anos sem promoção"
                })
            
            if profile['avg_training'] < 2:
                cluster_recs['actions'].append({
                    'action': 'Aumentar investimento em T&D',
                    'rationale': f"Média de apenas {profile['avg_training']:.1f} treinamentos/ano"
                })
            
            if not cluster_recs['actions']:
                cluster_recs['actions'].append({
                    'action': 'Manter monitoramento regular',
                    'rationale': 'Métricas dentro dos parâmetros aceitáveis'
                })
            
            recommendations.append(cluster_recs)
        
        # Ordenar por prioridade
        priority_order = {'Alta': 0, 'Média': 1, 'Baixa': 2}
        recommendations = sorted(recommendations, key=lambda x: priority_order.get(x['priority'], 2))
        
        self.results['recommendations'] = recommendations
        return recommendations
    
    def run_all_analyses(self, n_clusters=4):
        """
        Executa todas as análises de clustering
        """
        print("Encontrando número ótimo de clusters...")
        optimal_k = self.find_optimal_k()
        
        # Usar K ótimo ou o especificado
        k = n_clusters or optimal_k['optimal_k_silhouette']
        
        print(f"Executando clustering com K={k}...")
        self.run_clustering(n_clusters=k)
        
        print("Criando perfis de clusters...")
        self.create_cluster_profiles()
        
        print("Comparação estatística...")
        self.compare_clusters_statistically()
        
        print("Identificando drivers...")
        self.identify_cluster_drivers()
        
        print("Gerando recomendações...")
        self.get_cluster_recommendations()
        
        # Resumo
        self.results['summary'] = self._generate_summary()
        
        return self.results
    
    def _generate_summary(self):
        """
        Gera resumo executivo do clustering
        """
        profiles = self.results.get('profiles', [])
        clustering = self.results.get('clustering', {})
        
        # Cluster mais problemático
        highest_risk = max(profiles, key=lambda x: x['attrition_rate']) if profiles else None
        
        # Cluster mais engajado
        lowest_risk = min(profiles, key=lambda x: x['attrition_rate']) if profiles else None
        
        summary = {
            'n_clusters': clustering.get('n_clusters', 0),
            'overall_silhouette': clustering.get('overall_silhouette', 0),
            'cluster_quality': 'Boa' if clustering.get('overall_silhouette', 0) > 0.25 else 'Moderada' if clustering.get('overall_silhouette', 0) > 0.15 else 'Fraca',
            'highest_risk_cluster': highest_risk['cluster_name'] if highest_risk else None,
            'highest_risk_rate': highest_risk['attrition_rate'] if highest_risk else 0,
            'most_stable_cluster': lowest_risk['cluster_name'] if lowest_risk else None,
            'most_stable_rate': lowest_risk['attrition_rate'] if lowest_risk else 0,
            'key_findings': []
        }
        
        # Findings
        if highest_risk:
            summary['key_findings'].append({
                'title': 'Cluster de Maior Risco',
                'finding': f"'{highest_risk['cluster_name']}' tem {highest_risk['attrition_rate']:.1f}% de turnover ({highest_risk['size']} colaboradores)"
            })
        
        if lowest_risk and lowest_risk != highest_risk:
            summary['key_findings'].append({
                'title': 'Cluster Mais Estável',
                'finding': f"'{lowest_risk['cluster_name']}' tem apenas {lowest_risk['attrition_rate']:.1f}% de turnover"
            })
        
        # Feature mais discriminante
        feat_imp = self.results.get('feature_importance', [])
        if feat_imp:
            summary['key_findings'].append({
                'title': 'Variável Mais Discriminante',
                'finding': f"'{feat_imp[0]['feature']}' é a variável que mais diferencia os clusters"
            })
        
        return summary


def run_cluster_analysis(df, n_clusters=4):
    """
    Função helper para executar análise completa
    """
    analyzer = ClusterAnalyzer(df)
    results = analyzer.run_all_analyses(n_clusters=n_clusters)
    
    return {
        'results': results,
        'analyzer': analyzer
    }
