---
name: find-dead-code
description: Audit the repo for dead code — unused exports, unreachable functions, orphaned files, and unused dependencies. Use when removing dead code, cleaning up the codebase, or enforcing zero dead code policy. Triggers on phrases like "find dead code", "remove unused code", "clean up dead code", "audit for dead code".
disable-model-invocation: true
user-invocable: true
---

# Find Dead Code

Deep audit of the entire repo for dead code — including hard-to-find chunks that static tools miss. Covers TypeScript/JS (knip), Python (vulture + manual analysis), unused dependencies (depcheck, pip), and structural patterns that indicate dead code even when tools report nothing.

## Steps

### 1. TypeScript / JavaScript (knip)

Run knip from the repo root. It detects unused exports, files, and dependencies across the monorepo.

```bash
npx knip --reporter compact 2>&1 | head -200
```

If `knip` is not installed, install it first:
```bash
npm install --save-dev knip
```

Review findings grouped by:
- **Unused files** — highest priority, safe to delete if not dynamic imports
- **Unused exports** — remove the `export` keyword or delete if the symbol is truly internal
- **Unused dependencies** — remove from `package.json` after confirming no runtime/dynamic usage

### 2. Python (vulture)

Run vulture against the server source with 80% confidence threshold:

```bash
cd "$(git rev-parse --show-toplevel)"
pip install vulture --quiet
python3 -m vulture main/server/api main/server/auth main/server/encache_types main/server/interfaces main/server/layers main/server/memories main/server/memory_pipeline main/server/memory_runtime main/server/migrate main/server/providers main/server/tests main/server/workers main/server/worldmm main/server/vulture_whitelist.py --min-confidence 80 --ignore-names "type_,ExpiresIn"
```

Then run a second pass at 60% confidence to catch lower-confidence dead code:

```bash
cd "$(git rev-parse --show-toplevel)"
python3 -m vulture main/server/api main/server/auth main/server/encache_types main/server/interfaces main/server/layers main/server/memories main/server/memory_pipeline main/server/memory_runtime main/server/migrate main/server/providers main/server/tests main/server/workers main/server/worldmm main/server/vulture_whitelist.py --min-confidence 60 --ignore-names "type_,ExpiresIn"
```

Review findings:
- **Unused functions/classes** — verify no dynamic dispatch (`getattr`, decorators, string-based calls) before deleting
- **Unused variables** — safe to remove; prefix with `_` if intentionally unused
- **Unused imports** — remove directly

### 3. Unused JS/TS Dependencies (depcheck)

```bash
npx depcheck --ignore-dirs=node_modules,dist,build 2>&1 | head -100
```

Cross-reference with knip's dependency findings before removing.

### 4. Deep Manual Analysis — Hard-to-Find Dead Code

Static tools miss entire categories of dead code. After running the automated tools, perform each of these targeted searches:

#### 4a. Feature Flags / Disabled Branches

Search for hardcoded `false` conditions, commented-out feature flags, or constants that permanently disable code paths:

```bash
grep -rn "if (false\|if False\|enabled = False\|enabled = false\|ENABLE.*= false\|FEATURE.*= false" \
  main/server main/app --include="*.py" --include="*.ts" --include="*.tsx" -l
```

Read each file and confirm whether the disabled branch is ever reachable.

#### 4b. Unreachable Code After Early Returns

Search for code after `return`, `raise`, or `sys.exit` that is not inside a conditional:

```bash
grep -rn "^\s*return\b\|^\s*raise\b\|^\s*sys\.exit" main/server --include="*.py" -n | \
  head -100
```

For each hit, read the surrounding function to see if anything after the return is unreachable.

#### 4c. Event Handlers / Callbacks Never Registered

Search for functions named `on_*`, `handle_*`, `_handler`, `_callback` and confirm each one is actually passed to an event emitter or registered somewhere:

```bash
grep -rn "def on_\|def handle_\|_handler\b\|_callback\b" main/server --include="*.py" | \
  awk -F: '{print $3}' | sed 's/def //' | sed 's/(.*//' | sort -u
```

For each symbol found, grep the codebase to verify it is referenced outside its own definition.

#### 4d. Overridden but Never-Called Methods

Look for methods that override a base class method but are never called by callers (only by the base class dispatch). These are legitimate polymorphism — skip them. But look for overrides in non-polymorphic classes:

```bash
grep -rn "def [a-z_]*(" main/server --include="*.py" -h | \
  sed 's/.*def \([a-z_]*\)(.*/\1/' | sort | uniq -c | sort -rn | head -40
```

Cross-reference high-count names against actual call sites to find methods defined many times but never called externally.

#### 4e. Stale Route / Endpoint Definitions

Find all registered API routes, then verify each has actual integration test coverage or frontend usage:

```bash
# FastAPI routes
grep -rn "@router\.\|@app\." main/server --include="*.py" | grep -v "^.*#" | head -80

# React Native / Expo navigation screens
grep -rn "component:\|screen:\|Stack.Screen\|Tab.Screen" main/app --include="*.tsx" --include="*.ts" | head -80
```

For each route/screen, search for any caller, navigator, or link that references it.

#### 4f. Orphaned Test Helpers / Fixtures

Find test utilities, fixtures, and factories that no test file imports:

```bash
# Python fixtures
grep -rn "^def \|^class " main/server/tests --include="*.py" | grep -v "test_" | head -60

# TS test utilities
grep -rn "export function\|export const\|export class" main/app/src --include="*.test.*" --include="*.spec.*" | head -60
```

For each exported test symbol, check whether any other test file imports it.

#### 4g. Dead Configuration / Environment Variables

Find all `os.environ.get`, `process.env.`, and config reads, then verify each variable is actually set in deployment config (`.env`, Terraform, SAM templates):

```bash
grep -rn "os\.environ\.get\|os\.getenv" main/server --include="*.py" | \
  sed "s/.*os\.environ\.get(\(['\"][^'\"]*['\"]\).*/\1/" | sort -u

grep -rn "process\.env\." main/app --include="*.ts" --include="*.tsx" | \
  sed "s/.*process\.env\.\([A-Z_]*\).*/\1/" | sort -u
```

Cross-check against actual env var definitions. Variables read but never set are dead config reads.

#### 4h. Shadowed / Overwritten Assignments

Find variables assigned a value that is immediately overwritten before any use:

```bash
# Python: look for sequential assignment to same variable name within short blocks
grep -rn "^\s*[a-z_]* = " main/server --include="*.py" | \
  awk -F: '{print $1 ":" $2 " " $3}' | head -100
```

Manually review dense assignment blocks for values that are written but immediately clobbered.

#### 4i. JS/TS: Dead `useEffect` / Abandoned State

In React components, look for `useEffect` calls with no dependencies that set state that is never read, or `useState` variables that are set but never rendered or passed down:

```bash
grep -rn "const \[.*\] = useState" main/app --include="*.tsx" --include="*.ts" | head -60
```

For each state variable, verify it appears in JSX or is passed as a prop.

#### 4j. Git Log — Recently Deleted Features Leaving Orphans

Check recent large deletions for files or symbols that were part of the deleted feature but were missed:

```bash
git log --oneline --diff-filter=D --name-only --since="6 months ago" | head -80
```

For each deleted file, search for any remaining import or reference to it.

### 5. Triage & Remove

For each finding from any step above:
1. **Confirm** — grep for all usages; check for dynamic imports, reflection, or test-only references
2. **Remove** — delete dead code or unexport symbols
3. **Verify** — run the test suite and type-check after each batch of removals

```bash
# Type check TS
npx tsc --noEmit

# Run tests
npm test
```

### 6. Update CI Gates (if not already present)

After cleanup, add knip and vulture to CI so dead code cannot re-accumulate:
- Add `npx knip` to the lint step in `.github/workflows/`
- Add `python -m vulture main/server/ main/server/vulture_whitelist.py --min-confidence 80 --ignore-names "type_,ExpiresIn"` to the Python lint step

## Notes

- **Dynamic dispatch caution**: Python code using `getattr`, FastAPI route decorators, or SQLAlchemy models may appear unused to vulture — verify before deleting.
- **Barrel files**: knip may flag re-export barrel files (`index.ts`) as unused — check if they serve as public API boundaries.
- **Test files**: knip excludes test files by default; configure `knip.config.ts` if you want to include them.
- **Confidence**: Start with `--min-confidence 80` for vulture; lower to 60 for a second pass if needed.
- **Hard-to-find patterns**: The deep manual steps (4a–4j) are the most valuable — run them even when automated tools report nothing. Tools only see what they're designed to see.
