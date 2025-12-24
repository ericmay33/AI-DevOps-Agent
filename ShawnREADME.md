# Shawn – Responsibilities & Development Plan

## Role Summary
Shawn leads:

- System architecture
- Prompt and reasoning design
- Failure classification logic
- Patch-generation strategy
- Ensuring future infrastructure audit features can slot in without system redesign

Eric implements, Shawn defines how the machine “thinks.”

---

# Sprint Plan

## Sprint 1 – Repository Intelligence Design
### User Story
As the agent, I need to understand the structure and components of the repository so I can analyze and modify it effectively.

### Shawn Responsibilities
- Define:
  - How repos are scanned
  - What files are recognized
  - Data structure of the “repo knowledge model”
- Define how AI will summarize and tag artifacts
- Ensure design supports future infra policy scans without rework

### Definition of Done
- A specification describing:
  - How scanned files are represented
  - What metadata is stored
  - How the LLM queries repo knowledge

---

## Sprint 2 – Failure Analysis Reasoning
### User Story
As the agent, I want to read CI logs and determine the failure source so I can fix it logically.

### Shawn Responsibilities
- Create the reasoning workflow, including:
  - Classification categories (e.g. dependency failure, version mismatch, missing command, etc.)
  - Multi-step prompt logic
  - Structured output format

### Definition of Done
- Documented prompt templates
- Output schema such as:

{
"root_cause": "...",
"fix_summary": "...",
"severity": "Medium"
}

yaml
Copy code

---

## Sprint 3 – Patch Strategy Design
### User Story
As the system, I need to generate deterministic file modifications safely.

### Shawn Responsibilities
- Define how changes are calculated
- Define file mutation rules
- Establish standards for:
  - Patch output
  - PR narratives
  - Confidence scoring

### Definition of Done
- Clear specification of patch-generation workflow

---

## Sprint 4 – Integration & Future-Proofing
### Role
- Verify that the entire pipeline is modular
- Ensure that “infra drift scanning” can be added later with minimal new code

---

## Deliverable Philosophy
Shawn’s output enables Eric to build a robust system where:

- All decision-making is predictable
- AI outputs are structured and actionable
- Future expansion does not break system architecture