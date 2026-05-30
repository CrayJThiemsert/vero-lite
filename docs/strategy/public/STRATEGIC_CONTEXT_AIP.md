# VERO-LITE Strategic Context

## Agentic Operational Platform Principles

Version: Draft v1
Purpose: Long-term architectural context for future LLM sessions, planning, ADR reviews, and system evolution.

---

# Executive Summary

VERO-LITE should not be treated as a chatbot project.

The long-term direction is closer to a lightweight operational intelligence platform inspired by concepts found in Palantir AIP, modern agent systems, workflow orchestration platforms, and ontology-driven software architecture.

The goal is NOT to replicate Palantir.

The goal is to extract the architectural patterns that make such systems effective and adapt them into a smaller, developer-centric, practical system.

---

# Core Principle

Most AI projects are designed like this:

```text
User
 ↓
LLM
 ↓
Answer
```

VERO-LITE should gradually evolve toward:

```text
User
 ↓
Planner
 ↓
Workflow System
 ↓
Skills / Tools / Agents
 ↓
Execution
 ↓
Review
 ↓
Trace
```

The system should think in terms of operations rather than conversations.

---

# Strategic Observation

Palantir's advantage is not primarily the LLM.

The durable advantage comes from combining:

```text
Ontology
+
Workflow
+
Governance
+
Observability
+
Agents
```

into a single operational system.

VERO-LITE should use this as a conceptual reference model.

---

# Pillar 1: Ontology-Driven Design

## Principle

The system should understand relationships between entities rather than treating everything as isolated files or prompts.

Avoid:

```json
{
  "customer_id": 123
}
```

Prefer conceptual models:

```yaml
Customer:
  owns:
    - Order

Order:
  created_by:
    - Customer
```

---

## Long-Term Goal

Represent important system concepts as explicit entities.

Examples:

```text
Project
Task
Dispatch
ADR
Lesson
Skill
Workflow
Agent
Session
Evaluation
```

Relationships should be first-class concepts.

Example:

```text
Dispatch
  implements
      ↓
ADR

Lesson
  originated_from
      ↓
Incident

Workflow
  uses
      ↓
Skill
```

---

# Pillar 2: Workflow-First Architecture

## Principle

AI should execute within workflows.

Do not treat AI as the workflow.

Wrong model:

```text
AI
+
Workflow
```

Preferred model:

```text
Workflow System
+
AI Capabilities
```

---

## Desired Pattern

```text
Event
 ↓
Planner
 ↓
Execution Graph
 ↓
Skill Calls
 ↓
Validation
 ↓
Review
 ↓
Completion
```

Every major action should be representable as a workflow.

---

# Pillar 3: Skills as Operational Capabilities

Skills are not prompts.

Skills are reusable operational units.

Each skill should have:

```text
Purpose
Inputs
Outputs
Constraints
Failure Modes
References
```

Possible future categories:

```text
Planning Skills
Review Skills
Documentation Skills
Architecture Skills
Research Skills
Governance Skills
Evaluation Skills
```

---

# Pillar 4: Agent Layer

## Principle

Agents should have narrow responsibilities.

Avoid:

```text
One Giant Agent
```

Prefer:

```text
Planner Agent
 ↓
Executor Agent
 ↓
Reviewer Agent
 ↓
Auditor Agent
```

Each agent should have a clear scope.

---

# Pillar 5: Governance

## Principle

Every important action should be explainable.

The system should eventually support:

```text
Who initiated action
Why action occurred
What changed
What evidence was used
```

---

## Desired Future State

Every execution should produce traceable records.

Example:

```yaml
execution:
  actor: planner-agent
  workflow: adr-review
  reason: architecture conflict
  evidence:
    - ADR-006
    - LESSON-014
```

---

# Pillar 6: Observability

## Principle

Invisible systems become unmaintainable.

The platform should make reasoning paths observable.

Track:

```text
Agent decisions
Workflow transitions
Tool calls
Skill usage
Validation outcomes
Failures
```

---

# Pillar 7: Evaluation Infrastructure

## Principle

Reliability matters more than clever prompts.

Future architecture should support:

```text
Golden datasets
Regression testing
Agent evaluation
Workflow evaluation
Prompt evaluation
```

The objective is repeatability.

Not merely impressive demos.

---

# Pillar 8: Memory Architecture

## Principle

Memory should become structured.

Avoid:

```text
Conversation history only
```

Prefer:

```text
Lessons
Knowledge
Relationships
Operational Records
```

Potential future directions:

```text
Knowledge Graph
Graph Memory
Semantic Memory
Hybrid RAG
```

---

# Pillar 9: Human-in-the-Loop

## Principle

High-impact actions should require review.

Preferred pattern:

```text
Agent
 ↓
Recommendation
 ↓
Human Approval
 ↓
Execution
```

The system should optimize for decision support rather than blind autonomy.

---

# Architectural North Star

If future design decisions become ambiguous, prefer the option that moves the system toward:

```text
Ontology
→ Workflow
→ Governance
→ Observability
→ Evaluation
→ Agents
```

rather than:

```text
Bigger Prompt
→ Bigger Context Window
→ More Tool Calls
```

---

# Anti-Patterns

Avoid evolving into:

```text
Prompt Collection Repository
```

Avoid:

```text
Single Massive Agent
```

Avoid:

```text
Workflow Hidden Inside Prompt Logic
```

Avoid:

```text
Business Logic Embedded Entirely In LLM Reasoning
```

Avoid:

```text
Untraceable Autonomous Actions
```

---

# Long-Term Vision

VERO-LITE should gradually evolve toward:

```text
Agentic Operational System
```

rather than:

```text
AI Chat Application
```

The objective is not maximum autonomy.

The objective is reliable operational intelligence with traceable execution, structured workflows, reusable skills, and governed decision-making.
