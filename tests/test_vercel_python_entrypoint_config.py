import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERCEL_CONFIG = ROOT / "vercel.json"
PYPROJECT = ROOT / "pyproject.toml"
WEB_APP = ROOT / "web_app.py"


def test_vercel_uses_fastapi_preset_and_explicit_python_entrypoint():
    config = json.loads(VERCEL_CONFIG.read_text(encoding="utf-8"))
    pyproject = PYPROJECT.read_text(encoding="utf-8")
    web_app = WEB_APP.read_text(encoding="utf-8")

    assert config["$schema"] == "https://openapi.vercel.sh/vercel.json"
    assert config["framework"] == "fastapi"
    assert "functions" not in config
    assert '[tool.vercel]' in pyproject
    assert 'entrypoint = "web_app:app"' in pyproject
    assert "app = FastAPI(" in web_app
