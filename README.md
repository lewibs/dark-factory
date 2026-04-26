```
██████╗  █████╗ ██████╗ ██╗  ██╗    ███████╗ █████╗  ██████╗████████╗ ██████╗ ██████╗ ██╗   ██╗
██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝    ██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗╚██╗ ██╔╝
██║  ██║███████║██████╔╝█████╔╝     █████╗  ███████║██║        ██║   ██║   ██║██████╔╝ ╚████╔╝ 
██║  ██║██╔══██║██╔══██╗██╔═██╗     ██╔══╝  ██╔══██║██║        ██║   ██║   ██║██╔══██╗  ╚██╔╝  
██████╔╝██║  ██║██║  ██║██║  ██╗    ██║     ██║  ██║╚██████╗   ██║   ╚██████╔╝██║  ██║   ██║   
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝  
```

Dark Factory is a fully autonomous coding plugin for [Claude Code](https://claude.ai/code). Give it a plan file and it outputs working features — end-to-end. No hand-holding, no back-and-forth. Dark Factory handles the implementation, debugging, code review, and PR from start to finish.

---

## Install

```bash
git clone https://github.com/lewibs/dark-factory
cd dark-factory
claude plugin marketplace add "$(pwd)"
claude plugin install dark-factory
```

### Verify

```bash
claude plugin list
```

---

## Commands

| Command | Input | Description |
|---|---|---|
| `/dark-factory:manufacture` | Task description (e.g. "add OAuth login") | Full orchestration — routes to the right agent (feature, debug, or fix-flow) end-to-end, runs code review, opens a PR, and cleans up |
| `/dark-factory:init` | Optional GitHub URL | Onboard a project onto dark factory — sets up the structure for infinite autonomous changes and generates a `CLAUDE.md` |
| `/dark-factory:update` | None | Update the plugin to the latest version |
