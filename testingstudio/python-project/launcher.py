"""Instalação e execução no Windows, Linux ou macOS. Apenas biblioteca padrão."""

import argparse
import hashlib
import os
import platform
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent
ENV = ROOT / ".venv"
ENV_PYTHON = ENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
MARKER = ENV / ".testingstudio-installed"


def requirements_fingerprint() -> str:
    return hashlib.sha256((ROOT / "requirements.txt").read_bytes()).hexdigest()


def install(force: bool = False) -> None:
    if sys.version_info < (3, 10):
        raise RuntimeError("Instale Python 3.10 ou superior antes de continuar.")
    print(f"Python detectado: {platform.python_version()} ({platform.machine()})", flush=True)
    if not ENV_PYTHON.exists():
        print("Criando ambiente Python do projeto...", flush=True)
        venv.create(ENV, with_pip=True)
    fingerprint = requirements_fingerprint()
    installed = MARKER.read_text(encoding="utf-8").strip() if MARKER.exists() else ""
    if force or installed != fingerprint:
        print("Instalando dependencias. A primeira execucao precisa de internet...", flush=True)
        subprocess.run([str(ENV_PYTHON), "-m", "pip", "install", "--upgrade", "--only-binary=:all:", "pip"], check=True, cwd=ROOT)
        # Instala somente wheels. Evita compilar pandas/NumPy em maquinas de laboratorio.
        subprocess.run([str(ENV_PYTHON), "-m", "pip", "install", "--only-binary=:all:",
                        "-r", str(ROOT / "requirements.txt")], check=True, cwd=ROOT)
        MARKER.write_text(fingerprint + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="TestingStudio Sprint 1")
    parser.add_argument("action", choices=["install", "start"], nargs="?", default="start")
    args = parser.parse_args()
    try:
        install(force=args.action == "install")
        if args.action == "install":
            print("Instalacao concluida. Agora abra iniciar.bat.")
            return 0
        print("Abrindo http://localhost:8501. Mantenha este terminal aberto.", flush=True)
        return subprocess.call([str(ENV_PYTHON), "-m", "streamlit", "run", str(ROOT / "app.py"),
                                "--server.address=127.0.0.1", "--server.headless=false"], cwd=ROOT)
    except KeyboardInterrupt:
        return 0
    except subprocess.CalledProcessError:
        print("A instalacao de dependencias falhou. O Python foi encontrado.\n"
              "Leia a mensagem acima. O instalador aceita somente pacotes prontos, sem compilacao.\n"
              "Confira a conexao e tente instalar.bat. Se nao houver pacote compativel, use Python 3.12.")
        return 1
    except (OSError, RuntimeError) as exc:
        print(f"Nao foi possivel iniciar: {exc}\nConfira a mensagem acima e as permissoes da pasta do projeto.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
