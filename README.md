# DevOps AutoPilot — An AI Agent That Self-Heals Your CI/CD 🚀🛠️

DevOps AutoPilot is an AI-powered DevOps companion that **analyzes**, **diagnoses**, and **self-heals** your repository's infrastructure.  
It scans your repo, identifies missing or broken DevOps components, proposes fixes, and—when approved—**automatically generates pull requests** to repair or upgrade your CI/CD pipeline.

Think of it as your tired, overworked senior DevOps engineer…  
But powered by LLMs, less grumpy, and actually excited to fix YAML files at 3AM.

---

## ⭐ What It Does

### 🧠 1. Repository Understanding  
The agent deeply inspects your project:
- CI/CD configs (GitHub Actions, Docker, Terraform, etc.)
- Pipeline health & patterns
- Missing or outdated workflows
- Security risks / misconfigurations
- DevOps “maturity score” (because judgement builds character)

### 🔧 2. Self-Healing Pipeline Engine  
When issues are found, the agent can:
- Auto-generate new GitHub Actions workflows
- Patch Dockerfiles and build configs
- Repair broken pipelines
- Propose infra upgrades or sanity checks

### ⚡ 3. Automated Fix Orchestration  
The system can:
- Open PRs for fixes  
- Run sandbox simulations  
- Trigger CI workflows  
- Validate repairs and roll back if needed (we are responsible adults)

### 🔍 4. Interactive DevOps Command Center UI  
A beautiful(ish) frontend where you can:
- Browse your repo like a mini VSCode  
- Watch the agent think live  
- Approve/deny automated fixes  
- See pipeline changes side-by-side  
- Feel like Iron Man, but with YAML

---

## 🏗️ Architecture Overview

**Shawn — The Brain 🧠**  
Analysis Engine → Missing Pipeline Detector → Risk Assessment → Recommendations

**Eric — The Hands 🛠️**  
Self-Healing Engine → Fix Generator → PR Automation → Pipeline Re-Runner

**Shared Work 🤝**  
UI + API Backend + Deployment

---

## ⚙️ Tech Stack

- **Backend:** FastAPI, Python, Pydantic, GitHub API, OpenAI API  
- **Frontend:** React + Tailwind (lightweight, simple, effective)  
- **Infra:** Docker, GitHub Actions, Railway/Render  
- **AI:** GPT-4o / GPT-5-series models with function-calling  
- **Storage:** SQLite or Postgres (depending on time and tears shed)  

---

## 🧪 Running Locally

```bash
git clone <repo-url>
cd devops-autopilot

# Backend
cd backend
pip install -r requirements.txt
uvicorn app:app --reload

# Frontend
cd ../frontend
npm install
npm run dev