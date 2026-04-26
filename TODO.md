managing learning and automaking skills for the project.

DARK for top level agent repo for skills agents that the top level has access to.

pull tasks and resolve them.
debugger vs fix flow? what is the difference? lets just delete debugger. Fix flow needs to do the same thing but its more deterministic. WHich I like... perhaps it can be moved into fix flow. but also this is useful for other agents. maybe they can use them????

/clear at the end of the manufacture loop

hooks
* execution logs
* debugging logs
* project skills - manage learning
* logging AI data
* documentation

Maybe:
security


----


● Bash(cd dark_factory && git status && git log --oneline -5)          
  ⎿  Running…
                                                                                
────────────────────────────────────────────────────────────────────────────────
 Bash command                                                                   
                  
   cd dark_factory && git status && git log --oneline -5
   Check git status and recent log in dark_factory

 This command changes directory before running git, which can execute untrusted
  hooks from the target directory. Approve only if you trust it.

 Do you want to proceed?
 ❯ 1. Yes
   2. No

ng…                                                                   
                                                                                
────────────────────────────────────────────────────────────────────────────────
 Bash command                                                                   
                                                                                
   cd dark_factory && git checkout main && git pull origin main 2>&1            
   Switch to main and pull latest                                               
                                                                                
 This command changes directory before running git, which can execute untrusted 
  hooks from the target directory. Approve only if you trust it.                

 Do you want to proceed?
 ❯ 1. Yes
   2. No


 checkout main && git pull origin main 2>&1)                          
  ⎿  Switched to branch 'main'                                                  
     Your branch is behind 'origin/main' by 1 commit, and can be fast-forwa     
     rded.                                                                      
     … +11 lines (ctrl+o to expand)                                             
                                                                                
● Bash(bash dark_factory/agents/dark-factory/scripts/prep-feature-dir.sh        
      open-plan-in-vscode 2>&1)                                                 
  ⎿  Error: Exit code 127                                                       
     bash: dark_factory/agents/dark-factory/scripts/prep-feature-dir.sh: No such
      file or directory                                                         
                                                                                
  Listed 2 directories (ctrl+o to expand)                                       
                                  
                                                                          
────────────────────────────────────────────────────────────────────────────────
 Bash command                                                                   
                                                                                
   mkdir -p /home/lewibs/github/dark_factory/dark_factory-open-plan-in-vscode   
   /skills/open-in-vscode                                                       
   Run shell command                                                            

 Do you want to proceed?
 ❯ 1. Yes
   2. Yes, and always allow access to skills/ from this project
   3. No

 Esc to cancel · Tab to amend · ctrl+e to explain

+23 tool uses (ctrl+o to expand)                                         
     (ctrl+b to run in background)                                              
                                                                                
────────────────────────────────────────────────────────────────────────────────
 Bash command                                                                   
                                                                                
   diff <(ls /home/lewibs/github/dark_factory/dark_factory/skills/) <(ls
   /home/lewibs/github/dark_factory/dark_factory-open-plan-in-vscode/skills/)   
   Compare skills directories

 Contains process_substitution

 Do you want to proceed?
 ❯ 1. Yes
   2. No

 Esc to cancel · Tab to amend · ctrl+


trl+o to expand)                                         
     (ctrl+b to run in background)                                              
                                                                                
────────────────────────────────────────────────────────────────────────────────
 Bash command                                                                   
                                                                                
   cd /home/lewibs/github/dark_factory/dark_factory-skill-update-agent && git   
    status                                                                      
   Check git status of working tree                                             
                                                                                
 This command changes directory before running git, which can execute untrusted 
  hooks from the target directory. Approve only if you trust it.                

 Do you want to proceed?                                                        
 ❯ 1. Yes
   2. No

 Esc to cancel · Tab to amend · ctrl+e to explain


────────────────────────────────────────────────────────────────────────────────
 Bash command                                                                  
                                                             
   cd /home/lewibs/github/dark_factory/dark_factory-skill-update-agent && git
    log --oneline -5                                                            
   Show recent git log
                                                                                
 This command changes directory before running git, which can execute untrusted
  hooks from the target directory. Approve only if you trust it.              

 Do you want to proceed?
 ❯ 1. Yes
   2. No

 Esc to cancel · Tab to amend · ctrl+e to explain

✻ Julienn3ng… (7m 40s · ↓ 5.7k tokens)                                          
  ⎿  Tip: Create skills by adding .md files to .claude/skills/ in your project 
     or ~/.claude/skills/ for skills that work in any project
────────────────────────────────────────────────────────────────────────────────
 Bash command                                                                  ─
❯                                                            
───cd─/home/lewibs/github/dark_factory/dark_factory-skill-update-agent─&&─git───
    diff agents/dark-factory/agents/dark-factory-agent.md                       
   Show changes to dark-factory-agent.md                    ◐ medium · /effort
                                                                                
 This command changes directory before running git, which can execute untrusted 
  hooks from the target directory. Approve only if you trust it.                
                                                                                
 Do you want to proceed?                                                        
 ❯ 1. Yes                                                                       
   2. No

 Esc to cancel · Tab to amend · ctrl+e to explain


ses (ctrl+o to expand)at work in any project
 ─   (ctrl+b to run in background)                                    ─  ─   ───
                                                                               ─
────────────────────────────────────────────────────────────────────────────────
 Bash command                                                                  ─
                                                                                
   cd /home/lewibs/github/dark_factory/dark_factory-skill-update-agent &&fgitt  
    diff TODO.md                                                                
   Show TODO.md diff                                                            
                                                                                
 This command changes directory before running git, which can execute untrusted 
  hooks from the target directory. Approve only if you trust it.                
                                                                                
 Do you want to proceed?
 ❯ 1. Yes
   2. No

 Esc to cancel · Tab to amend · ctrl+e to explain

 erun in background)     iles to .claude/skills/ in your project 
────────────────────────────────────────────────────────────────────────────────
 Bash command                                                                  
  ⎿                                                          / in your project ─
   cat > /tmp/pr-body.md << 'PREOF'  that work in  ny project                   
   ## Description                                                               
  ───                                                        ───────────────────
   # skill-update-agent                                                         
                                                                                
   ## Plan Metadata                                                             
                                                                                
   - Plan type: `plan`                                                          
   - Parent plan: `docs/plans/2026-04-25-dark-factory-agent.md`
   - Depends on: N/A
   - Status: `approved`

   ## System Intent

   - What is being built: A `skill-update-agent` that runs near the end of
   the `dark-factory-agent` manufacture loop (after code review and doc
   updates, before the PR step). It reviews the work that was just completed,
    identifies any non-obvious patterns or workarounds that were encountered
   during the task, and — only when those patterns are likely to recur —
   writes or updates skill files in the target project's `skills/` directory
   so future manufacture runs benefit from that knowledge.
   - Primary consumer(s): `dark-factory-agent` (invokes it as Step 4c,
   between `detect-drift-agent` and `pr-agent`). Indirectly benefits future
   invocations of any agent that reads project skills.
   - Boundary (black-box scope only): Accepts the completed work context
   (plan file path, work dir, and a summary of what was done). Produces zero
   or more new/updated skill files in `<workDir>/skills/`. Returns a list of
   skills written (may be empty). Does not open PRs, does not modify agent
   files, does not edit plans.

   ## Flows

   ### Flow: `skillUpdateAgent`

   New agent file: `agents/skill-update/agents/skill-update-agent.md`

   Reads plan + git diff, identifies non-obvious recurring patterns, applies
   recurrence filter, writes/updates `skills/<slug>/SKILL.md` files, returns
   `skillsWritten` list.

   ### Flow: `darkFactoryAgentIntegration`

   Updated: `agents/dark-factory/agents/dark-factory-agent.md`

   Adds Step 4c (skill-update-agent invocation) between detect-drift and PR
   steps. Non-fatal: if skill-update-agent errors, dark-factory-agent logs a
   warning and continues to PR.

   ---
   🤖 Generated with [dark factory](https://github.com/lewibs/dark-factory)
   PREOF
   Write PR body to /tmp/pr-body.md

 Do you want to proceed?
   1. Yes
 ❯ 2. Yes, and always allow access to tmp/ from this project
   3. No

 Esc to cancel · ctrl+e to explain               


