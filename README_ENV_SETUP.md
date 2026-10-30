# rh_dashboard - Environment Setup (Conda & Pip)

Use the steps below to create an isolated conda environment, install project dependencies via pip, then run the Dash dashboard in a way that allows network access.

## 1. Create Conda Environment
Open PowerShell and run:

```powershell
conda create -n rh_dashboard_env python=3.10 -y
conda activate rh_dashboard_env
```

Alternatively, use the provided `environment.yml`:

```powershell
conda env create -f environment.yml
conda activate rh_dashboard_env
```

## 2. Install dependencies via pip
From the root of the project (`c:\Users\gafeb\OneDrive\Desktop\projetos\rh_dashboard`):

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
# Optional extras (statsmodels, lifelines) if you need survival analysis, etc.
pip install lifelines statsmodels shap
```

## 3. Run the Dashboard locally and make it network-accessible
Run `run_dashboard.py` to launch the app on host 0.0.0.0 (making it visible from other devices on the same network):

```powershell
python run_dashboard.py
```

You can then open a browser on this PC with:

```
http://127.0.0.1:8050
```

If you're on another machine in the same network, use the IP address of this host (e.g., 192.168.1.45:8050).

> ⚠️ Windows Firewall: if you can't access the dashboard from other devices, ensure Windows Firewall allows inbound connections on port 8050.

## 4. Expose the app to the internet (Optional)
If you want to make the dashboard available over the internet for testing without changing network config, use a tunnel (e.g., ngrok).

Install and run ngrok (see https://ngrok.com/):

```powershell
ngrok http 8050
```

This outputs a public URL (https://xxxx.ngrok.io) you can share.

---

If anything fails (package installation errors, or `run_dashboard.py` doesn't start), send me the error logs and I’ll debug further.