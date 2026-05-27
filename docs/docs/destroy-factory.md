# /dark-factory:destroy-factory

Terminates all other running Claude/dark-factory terminal sessions and spawns one fresh factory terminal.

## Flow

```mermaid
flowchart TD
  User["User: /dark-factory:destroy-factory<br/>name (optional)"] --> Cmd["commands/destroy-factory.md"]
  Cmd -->|"bash scripts/destroy-factory.sh"| Script["scripts/destroy-factory.sh"]
  Script --> Scan["Scan running terminals<br/>for claude descendants"]
  Scan --> Kill["Kill all found<br/>(except caller)"]
  Kill --> Open["gnome-terminal / xterm / konsole<br/>running claude /remote-control"]
  Open --> Done["Done: fresh terminal"]
```

## See also

- scripts/destroy-factory.sh — terminal detection and cleanup
- [/dark-factory:build-factory](build-factory.md) — opens one additional terminal without cleanup
