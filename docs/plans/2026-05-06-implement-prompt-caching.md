# Implementation Plan: Prompt Caching on High-Frequency Agents

## System Intent

Add `cache-control: ephemeral` to the YAML frontmatter of the 5 highest-cost dark-factory agents. Claude Code reads this field and applies prompt caching when spawning sub-agents, reducing system prompt token costs by ~90% for repeated invocations.

## Mermaid Diagram

```mermaid
graph LR
    A[metrics.csv analysis] --> B[5 target agents]
    B --> C[add cache-control field to YAML frontmatter]
    C --> D[~90% token savings on system prompts]
```

## Flow: Add cache-control frontmatter

**Agents modified:**
1. agents/featurework/agents/feature-agent.md
2. agents/code-review/agents/code-review-orchestrator-agent.md
3. agents/documentation/agents/update-documentation-agent.md
4. agents/skill-update/agents/skill-update-agent.md
5. agents/featurework/execution/agents/execution-agent.md

**Change:** one new YAML field per file — `cache-control: ephemeral` — inserted after the `model:` line.
