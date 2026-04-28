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
rm -rf ~/.dark-factory && mkdir -p ~/.dark-factory && cp -r "$(pwd)/scripts" ~/.dark-factory/ && cp -r "$(pwd)/agents" ~/.dark-factory/
bash scripts/reopen-remote-control.sh "dark factory"
```
