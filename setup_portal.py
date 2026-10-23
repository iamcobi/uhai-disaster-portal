"""One-time local setup using Python's private virtual environment."""
from pathlib import Path
import subprocess,sys,venv
root=Path(__file__).resolve().parent
if sys.version_info<(3,11):raise SystemExit('Install Python 3.11 or newer from python.org, then run this setup again.')
environment=root/'.venv'
if not (environment/'Scripts/python.exe').exists():venv.EnvBuilder(with_pip=True).create(environment)
python=environment/'Scripts/python.exe'
subprocess.run([str(python),'-m','pip','install','--disable-pip-version-check','-r',str(root/'requirements.txt')],check=True)
print('\nSetup complete. Double-click START_PORTAL.cmd.')
