def test_api_app_imports_with_declared_dependencies():
    from redteam.api.app import app

    assert app.title == "LLM Red-Team Framework"
