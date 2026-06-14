# Healthcare Credentialing Automation – Claude Agent Workflow

This repository provides a starter workflow for automating the **healthcare provider credentialing process** using Claude and the `agency-agents` framework.

The goal is to orchestrate a team of specialized AI agents to execute the full credentialing lifecycle:

1. Provider Applies  
2. CAQH Profile Retrieval  
3. License Verification (State Board)  
4. Sanctions & Exclusions Check (OIG, SAM, State)  
5. NPI Verification & Contracting  
6. Committee Review & Approval  
7. Provider Added to Network / Onboarding

---

## 📦 1. Clone the Agency Agents Framework

This project depends on the open‑source `agency-agents` framework.

Clone it locally:

```bash
git clone https://github.com/msitarzewski/agency-agents.git

Navigate into the directory:

bash
cd agency-agents

📁 2. # Copy neccessary agents to your Claude Code agents directory 
mkdir -p ~/.claude/agents

# 👔 Senior Project Manager
cp management/senior-project-manager.md ~/.claude/agents/

# 💎 Senior Developer
cp engineering/senior-developer.md ~/.claude/agents/

# 🎨 UI Designer
cp design/ui-designer.md ~/.claude/agents/

# 🧪 Experiment Tracker
cp quality/experiment-tracker.md ~/.claude/agents/

# 📸 Evidence Collector
cp quality/evidence-collector.md ~/.claude/agents/

# 🔍 Reality Checker
cp quality/reality-checker.md ~/.claude/agents/

🤖 3. Open Claude and enter prompts from prompt.md

🤖 4. it will e=generate md files for you 

Claude will automatically:

Assign tasks to the Senior PM, Senior Developer, UI Designer, Experiment Tracker, Evidence Collector, and Reality Checker

Generate system architecture

Produce UI mockups

Create workflow automation logic

Validate compliance and readiness

Output documentation and artifacts

Wait for Claude to complete the full workflow.

🧩 4. Agents Included
This project uses the following enterprise‑grade agents:

👔 Senior Project Manager – Scope, milestones, dependencies

💎 Senior Developer – Backend workflow automation, API integration

🎨 UI Designer – Credentialing dashboard & provider portal

🧪 Experiment Tracker – A/B testing and optimization

📸 Evidence Collector – Verification, compliance checks

🔍 Reality Checker – Production readiness, HIPAA alignment

These agents collaborate to produce a complete, audit‑ready credentialing system.

🚀 5. Running the System
Once your .md file is in the agents/ folder:

Open Claude

Load your agent file

Run the workflow prompt

Review generated artifacts

Export code, diagrams, and documentation as needed

📚 6. Credentialing Workflow Overview
The automated system will support:

CAQH API retrieval

State license board verification

OIG/SAM/state sanctions checks

NPI registry validation

Contracting eligibility

Committee review workflow

Provider onboarding handoff

Audit logs and compliance documentation

📝 7. Contributing
Pull requests are welcome.
For major changes, open an issue to discuss your proposal.