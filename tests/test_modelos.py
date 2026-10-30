"""Checagens da validação dos modelos."""
import pytest

from rh_analytics.data_processor import load_and_process_data
from rh_analytics.paths import DADOS
from rh_analytics.people_science import predict_turnover, run_attrition_driver_analysis


@pytest.fixture(scope="module")
def df():
    return load_and_process_data(DADOS)


def test_auc_em_validacao_cruzada_acima_do_acaso(df):
    desempenho = run_attrition_driver_analysis(df)["model_performance"]
    for chave in ("logistic_auc", "rf_auc", "gb_auc"):
        assert 0.7 < desempenho[chave] < 0.95, chave


def test_probabilidade_dos_ativos_vem_de_fora_da_dobra(df):
    # Prevendo quem o modelo já viu no treino, todo ativo saía como risco "Baixo"
    # (probabilidade máxima de 0,29). Fora da dobra, parte deles aparece com risco maior.
    resultado = predict_turnover(df)
    nao_baixo = sum(n for faixa, n in resultado["risk_distribution"].items() if faixa != "Baixo")
    assert nao_baixo > 0
    assert 0.7 < resultado["model_auc"] < 0.95
