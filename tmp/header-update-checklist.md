# Header Update Checklist

Rules applied to every file:
- `user-invocable: false` on all agents (only `dark-factory-agent` stays `true`)
- `skills:` lists every skill the agent invokes
- `scripts:` lists every script the agent runs
- `allowed-tools:` covers every Bash command so no permission prompts
- `model: sonnet` for purely mechanical/deterministic steps; `sonnet` for everything else
- SKILL.md files: add `user-invocable: false` if missing; no tools/model fields

## code-review

- [ ] `agents/code-review/agents/code-review-orchestrator-agent.md` — set user-invocable:false, add allowed-tools for Bash(cat >/tmp/issues.md), model:sonnet
- [ ] `agents/code-review/agents/high-level-review-agent.md` — set user-invocable:false, add allowed-tools for git diff/grep, model:sonnet
- [ ] `agents/code-review/agents/low-level-review-agent.md` — set user-invocable:false, add allowed-tools for grep, model:sonnet
- [ ] `agents/code-review/agents/resolver-agent.md` — set user-invocable:false, add allowed-tools for bash/grep, model:sonnet

## dark-factory

- [ ] `agents/dark-factory/agents/dark-factory-agent.md` — keep user-invocable:true (entry point), add scripts:prep-feature-dir.sh, allowed-tools for bash script + rm -rf, model:sonnet

## debugger

- [ ] `agents/debugger/agents/debugger-agent.md` — set user-invocable:false, add tools/model:sonnet, skills:systematic-debugging, allowed-tools for bash/pytest/npm
- [ ] `agents/debugger/skills/debug/SKILL.md` — set user-invocable:false

## documentation

- [ ] `agents/documentation/agents/detect-drift-agent.md` — set user-invocable:false, skills:detect-drift, allowed-tools for python script, model:sonnet
- [ ] `agents/documentation/agents/investigation-agent.md` — set user-invocable:false, skills:investigate,documentation, model:sonnet
- [ ] `agents/documentation/agents/update-documentation-agent.md` — set user-invocable:false, skills:documentation, model:sonnet
- [ ] `agents/documentation/skills/detect-drift/SKILL.md` — set user-invocable:false
- [ ] `agents/documentation/skills/documentation/SKILL.md` — set user-invocable:false (already)
- [ ] `agents/documentation/skills/investigate/SKILL.md` — set user-invocable:false (already)

## featurework

- [ ] `agents/featurework/agents/feature-agent.md` — set user-invocable:false, model:sonnet
- [ ] `agents/featurework/execution/agents/execution-agent.md` — set user-invocable:false, model:sonnet
- [ ] `agents/featurework/execution/agents/implementation-agent.md` — set user-invocable:false, skills:deviation-protocol, allowed-tools for test runners, model:sonnet
- [ ] `agents/featurework/execution/agents/skeleton-agent.md` — set user-invocable:false, allowed-tools for mkdir/touch, model:sonnet
- [ ] `agents/featurework/execution/agents/testing-agent.md` — set user-invocable:false, allowed-tools for test runners, model:sonnet
- [ ] `agents/featurework/execution/skills/deviation-protocol/SKILL.md` — set user-invocable:false (already)
- [ ] `agents/featurework/planning/agents/planning-agent.md` — set user-invocable:false, skills:create-mermaid-diagram (already), model:sonnet

## fix-flow

- [ ] `agents/fix-flow/agents/debug-flow-agent.md` — set user-invocable:false, tools:+Agent, scripts:trigger.sh/wait-for-completion.sh/fetch-logs.sh, allowed-tools for bash scripts, model:sonnet
- [ ] `agents/fix-flow/agents/fix-flow-orchestrator.md` — set user-invocable:false, model:sonnet
- [ ] `agents/fix-flow/agents/ralph-fix-and-push.md` — user-invocable:false (already), model:sonnet
- [ ] `agents/fix-flow/agents/setup-wizard.md` — user-invocable:false (already), skills:generate-trigger,generate-wait-for-completion,generate-fetch-logs,generate-deploy, allowed-tools for chmod +x, model:sonnet
- [ ] `agents/fix-flow/skills/generate-deploy/SKILL.md` — user-invocable:false (already)
- [ ] `agents/fix-flow/skills/generate-fetch-logs/SKILL.md` — user-invocable:false (already)
- [ ] `agents/fix-flow/skills/generate-trigger/SKILL.md` — user-invocable:false (already)
- [ ] `agents/fix-flow/skills/generate-wait-for-completion/SKILL.md` — user-invocable:false (already)

## initialization

- [ ] `agents/initialization/agents/init-docs-agent.md` — set user-invocable:false (already), add allowed-tools for ls/find, model:sonnet
- [ ] `agents/initialization/agents/init-orchestrator-agent.md` — set user-invocable:false, scripts:init.sh, allowed-tools for bash init.sh, model:sonnet

## pr

- [ ] `agents/pr/agents/pr-agent.md` — user-invocable:false (already), skills:create-pr, add gh pr create to allowed-tools, model:sonnet
- [ ] `agents/pr/agents/resolve-pr-issue.md` — user-invocable:false (already), model:sonnet
- [ ] `agents/pr/skills/create-pr/SKILL.md` — user-invocable:false (already)
