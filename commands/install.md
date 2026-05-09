---
description: "Install or reinstall the dark-factory plugin. Run from the repo root."
---

Run these commands from the repo root (`~/github/dark_factory/dark_factory` or wherever you cloned it):

```bash
git pull
claude plugin marketplace add "$(pwd)"
claude plugin marketplace update dark-factory
claude plugin uninstall "dark-factory@dark-factory"
claude plugin install "dark-factory@dark-factory"
bash "$(python3 -c "import json,os; d=json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json'))); p=d['plugins'].get('dark-factory@dark-factory',[{}]); print(p[0].get('installPath','') if p else '')")/scripts/reopen-remote-control.sh" "dark factory"
```
