# /dark-factory:install

Installs or reinstalls the dark-factory plugin — registers with the plugin marketplace, installs the plugin, syncs agents and scripts to the local cache, and reopens the terminal.

## Flow

```mermaid
flowchart TD
  User["User: /dark-factory:install<br/>from repo root"] --> GitPull["git pull"]
  GitPull --> Marketplace["claude plugin marketplace add"]
  Marketplace --> Check{"First install<br/>or update?"}
  Check -->|"first time"| Install["claude plugin install"]
  Check -->|"update"| Update["marketplace update +<br/>uninstall + reinstall"]
  Install --> Copy["Copy scripts/agents<br/>to ~/.dark-factory/"]
  Update --> Copy
  Copy --> Terminal["bash scripts/reopen-remote-control.sh"]
  Terminal --> Done["Done: plugin ready"]
```

## See also

- scripts/reopen-remote-control.sh — opens new terminal
- Plugin docs
