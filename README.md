# collector_analyzer 🚀

Welcome to the **collector_analyzer Suite**—a multi-tier infrastructure assessment application engineered to parse complex RVTools workbooks and deliver high-precision vCPU, storage footprint, and allocation profile analytics natively on your machine via a clean web interface.

---

## 🎨 Application Architecture Overview

This application separates data computing from visual rendering to guarantee scale and speed:
*   **Backend Engine (Python / Pandas):** Bypasses fragile browser memory limits to map messy Excel worksheets directly by absolute structural indexes.
*   **Frontend Dashboard (Tailwind CSS):** A responsive, dark-mode workspace displaying global fleet KPIs, high-contention compute targets, and a dual-context workload ledger.

---

## ⚡ First-Time One-Minute Setup (Do this once)

Because this application runs securely on your local machine, your Mac needs authorized execution permission to run the automated startup scripts:

1. Open your Mac **Terminal** application (Press `Cmd + Space`, type *Terminal*, and hit Enter).
2. Copy and paste the following line to clone the repository and grant it execution permissions:
   ```bash
   git clone [https://github.com/YOUR_GITHUB_USERNAME/Collector-Analyzer-App.git](https://github.com/YOUR_GITHUB_USERNAME/Collector-Analyzer-App.git) && cd Collector-Analyzer-App && chmod +x run_app.command && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org