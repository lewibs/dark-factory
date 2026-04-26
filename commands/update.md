---
description: Update the dark-factory plugin to the latest version.
---

Run these commands from the repo root (`~/github/dark_factory/dark_factory` or wherever you cloned it):

```bash
git pull
claude plugin marketplace add "$(pwd)"
claude plugin marketplace update dark-factory
claude plugin update "dark-factory@dark-factory"
```
