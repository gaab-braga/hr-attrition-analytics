"""O app sobe e as abas montam sem erro."""
from rh_analytics.dashboard.app import app, create_action_tab, create_insights_tab, create_profile_tab


def test_layout_monta():
    assert app.layout is not None


def test_abas_montam():
    for criar_aba in (create_insights_tab, create_action_tab, create_profile_tab):
        assert criar_aba() is not None
