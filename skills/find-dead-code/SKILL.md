---
name: find-dead-code
description: Audit the repo for dead code — unused exports, unreachable functions, orphaned files, and unused dependencies. Use when removing dead code, cleaning up the codebase, or enforcing zero dead code policy. Triggers on phrases like "find dead code", "remove unused code", "clean up dead code", "audit for dead code".
disable-model-invocation: true
user-invocable: true
---

# Find Dead Code

Deep audit of the repo for dead code — including hard-to-find chunks that static tools miss. Covers TypeScript/JS, Python, unused dependencies, and structural patterns that indicate dead code even when tools report nothing.

## Tools

| Language / Target | Tool | Purpose |
|---|---|---|
| TypeScript / JavaScript | `knip` | Unused exports, files, and dependencies across the project |
| TypeScript / JavaScript | `depcheck` | Unused `package.json` dependencies |
| Python | `vulture` | Unused functions, classes, variables, and imports |
| Any | `grep` | Feature flags, unreachable branches, dynamic dispatch patterns |
| Any | `git log` | Recently deleted features that left orphaned references |

## Steps

### 1. Discover source roots

Before running any tool, identify the project's source directories:

```bash
# Find top-level Python source dirs
find . -maxdepth 3 -name "*.py" -not -path "*/node_modules/*" -not -path "*/.git/*" \
  | sed 's|/[^/]*$||' | sort -u | head -20

# Find top-level JS/TS source dirs
find . -maxdepth 3 \( -name "*.ts" -o -name "*.tsx" \) -not -path "*/node_modules/*" \
  | sed 's|/[^/]*$||' | sort -u | head -20
```

Use the results to scope every tool invocation below.

### 2. TypeScript / JavaScript (knip)

Run knip from the repo root:

```bash
npx knip --reporter compact 2>&1 | head -200
```

If `knip` is not installed:
```bash
npm install --save-dev knip
```

Review findings grouped by:
- **Unused files** — highest priority, safe to delete if not dynamic imports
- **Unused exports** — remove the `export` keyword or delete if truly internal
- **Unused dependencies** — remove from `package.json` after confirming no runtime/dynamic usage

### 3. Python (vulture)

Run vulture against the discovered Python source roots at 80% confidence:

```bash
pip install vulture --quiet
python3 -m vulture <src-root-1> <src-root-2> --min-confidence 80
```

Then a second pass at 60% to catch lower-confidence dead code:

```bash
python3 -m vulture <src-root-1> <src-root-2> --min-confidence 60
```

If the project has a `vulture_whitelist.py`, include it:
```bash
python3 -m vulture <src-root> vulture_whitelist.py --min-confidence 80
```

Review findings:
- **Unused functions/classes** — verify no dynamic dispatch (`getattr`, decorators, string-based calls) before deleting
- **Unused variables** — prefix with `_` if intentionally unused, otherwise remove
- **Unused imports** — remove directly

### 4. Unused JS/TS Dependencies (depcheck)

```bash
npx depcheck --ignore-dirs=node_modules,dist,build 2>&1 | head -100
```

Cross-reference with knip's dependency findings before removing.

### 5. Deep Manual Analysis — Hard-to-Find Dead Code

Static tools miss entire categories of dead code. Run each targeted search below against the source roots identified in step 1.

#### 5a. Feature Flags / Disabled Branches

```bash
grep -rn "if (false\|if False\|enabled = False\|enabled = false\|ENABLE.*= false\|FEATURE.*= false" \
  <src-roots> --include="*.py" --include="*.ts" --include="*.tsx" -l
```

Read each file and confirm whether the disabled branch is ever reachable.

#### 5b. Unreachable Code After Early Returns

```bash
grep -rn "^\s*return\b\|^\s*raise\b\|^\s*sys\.exit" <python-src> --include="*.py" -n | head -100
```

For each hit, read the surrounding function to check if anything after the return is unreachable.

#### 5c. Event Handlers / Callbacks Never Registered

```bash
grep -rn "def on_\|def handle_\|_handler\b\|_callback\b" <python-src> --include="*.py" | \
  awk -F: '{print $3}' | sed 's/def //' | sed 's/(.*//' | sort -u
```

For each symbol, grep the codebase to verify it is referenced outside its own definition.

#### 5d. Overridden but Never-Called Methods

```bash
grep -rn "def [a-z_]*(" <python-src> --include="*.py" -h | \
  sed 's/.*def \([a-z_]*\)(.*/\1/' | sort | uniq -c | sort -rn | head -40
```

Cross-reference high-count names against actual call sites.

#### 5e. Stale Route / Endpoint Definitions

```bash
# Python (FastAPI / Flask / Django)
grep -rn "@router\.\|@app\.\|@blueprint\." <python-src> --include="*.py" | grep -v "^.*#" | head -80

# JS/TS (Express / Next.js / React Router)
grep -rn "router\.\(get\|post\|put\|delete\|patch\)\|<Route\b\|createBrowserRouter\|path:" <js-src> \
  --include="*.ts" --include="*.tsx" --include="*.js" | head -80
```

For each route, search for any caller or link that references it.

#### 5f. Orphaned Test Helpers / Fixtures

```bash
# Python
grep -rn "^def \|^class " <test-src> --include="*.py" | grep -v "test_" | head -60

# TypeScript
grep -rn "export function\|export const\|export class" <test-src> \
  --include="*.test.*" --include="*.spec.*" | head -60
```

For each exported test symbol, check whether any other test file imports it.

#### 5g. Dead Configuration / Environment Variables

```bash
# Python
grep -rn "os\.environ\.get\|os\.getenv" <python-src> --include="*.py" | \
  sed "s/.*os\.environ\.get(\(['\"][^'\"]*['\"]\).*/\1/" | sort -u

# JS/TS
grep -rn "process\.env\." <js-src> --include="*.ts" --include="*.tsx" --include="*.js" | \
  sed "s/.*process\.env\.\([A-Z_a-z_]*\).*/\1/" | sort -u
```

Cross-check against actual env var definitions (`.env`, CI config, infra templates).

#### 5h. Shadowed / Overwritten Assignments

```bash
grep -rn "^\s*[a-z_]* = " <python-src> --include="*.py" | \
  awk -F: '{print $1 ":" $2 " " $3}' | head -100
```

Manually review dense assignment blocks for values written but immediately clobbered.

#### 5i. JS/TS: Dead `useEffect` / Abandoned State

```bash
grep -rn "const \[.*\] = useState" <js-src> --include="*.tsx" --include="*.ts" | head -60
```

For each state variable, verify it appears in JSX or is passed as a prop.

#### 5j. Git Log — Recently Deleted Features Leaving Orphans

```bash
git log --oneline --diff-filter=D --name-only --since="6 months ago" | head -80
```

For each deleted file, search for any remaining import or reference to it.

### 6. Triage & Remove

For each finding from any step above:
1. **Confirm** — grep for all usages; check for dynamic imports, reflection, or test-only references
2. **Remove** — delete dead code or unexport symbols
3. **Verify** — run the test suite and type-check after each batch of removals

```bash
# Type check TS (if applicable)
npx tsc --noEmit

# Run tests
npm test          # JS/TS
pytest            # Python
```

### 7. Update CI Gates (if not already present)

After cleanup, add the tools to CI so dead code cannot re-accumulate:
- Add `npx knip` to the lint step
- Add `python -m vulture <src-root> --min-confidence 80` to the Python lint step

## Notes

- **Dynamic dispatch caution**: Python code using `getattr`, decorators, or ORM models may appear unused to vulture — verify before deleting.
- **Barrel files**: knip may flag re-export barrel files (`index.ts`) as unused — check if they serve as public API boundaries.
- **Test files**: knip excludes test files by default; configure `knip.config.ts` to include them if needed.
- **Confidence**: Start vulture at `--min-confidence 80`; lower to 60 for a second pass.
- **Hard-to-find patterns**: Steps 5a–5j catch what automated tools miss — run them even when tools report nothing.
