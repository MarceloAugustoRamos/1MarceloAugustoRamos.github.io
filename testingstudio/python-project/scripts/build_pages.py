"""Gera os exemplos e copia o motor Python compartilhado para o GitHub Pages."""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from project_guide import PROTOCOLS, REQUIREMENTS
from studio_engine import CORRECTED_SAMPLE, analyze, report_markdown


def build():
    docs = ROOT / "docs"
    (docs / "assets").mkdir(parents=True, exist_ok=True)
    sources = {"original": (ROOT / "cad0001_item_calculo.txt").read_text(encoding="utf-8"),
               "corrected": CORRECTED_SAMPLE}
    data = {"requirements": REQUIREMENTS, "protocols": PROTOCOLS,
            "repository_url": "", "streamlit_url": ""}
    config = ROOT / "deployment.json"
    if config.exists():
        data.update(json.loads(config.read_text(encoding="utf-8")))
    for name, source in sources.items():
        result = analyze(source)
        result["report"] = report_markdown(result)
        data[name] = {"source": source, "result": result}
    (docs / "assets" / "samples.js").write_text("window.TESTING_STUDIO = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    for name in ("studio_engine.py", "analysis.py"):
        shutil.copyfile(ROOT / name, docs / name)
    (docs / ".nojekyll").touch()
    print("GitHub Pages preparado: exemplos rastreáveis e motor Python compartilhado.")


if __name__ == "__main__":
    build()
