# /dark-factory:build-factory

Opens a new terminal window running `claude /remote-control` for parallel factory sessions.

## Flow

```mermaid
flowchart TD
  User["User: /dark-factory:build-factory<br/>name (optional)"] --> Cmd["commands/build-factory.md"]
  Cmd -->|"bash scripts/build-factory.sh"| Script["scripts/build-factory.sh"]
  Script --> Detect{"Terminal emulator?"}
  Detect -->|"gnome-terminal"| Terminal["gnome-terminal"]
  Detect -->|"xterm / konsole"| Terminal
  Terminal -->|"claude /remote-control NAME"| Done["Done: new terminal running"]
```

## See also

- scripts/build-factory.sh — terminal spawn implementation
- [/dark-factory:destroy-factory](destroy-factory.md) — clean up all other terminals
