#!/usr/bin/env python3
"""Generate drift checklist artifacts from plans/docs and code references."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


CANONICAL_CATALOG_PATH = Path("docs/index.md")
LEGACY_CATALOG_PATH = Path("docs/plans/index.md")

FLOW_HEADING_RE = re.compile(r"^### Flow:\s*(.+)$")
BACKTICK_RE = re.compile(r"`([^`]+)`")
PATH_RE = re.compile(
    r"((?:main|docs|apps|scripts|schemas)/[A-Za-z0-9_./-]+\.(?:tsx|ts|jsx|js|py|kt|swift|md|sh|yaml|yml|json))"
)


@dataclass
class FlowRef:
    plan_file: str
    line_no: int
    raw_heading: str
    target_raw: str | None
    target_file: str | None
    target_symbol: str | None
    test_raw: list[str]
    test_files: list[str]


@dataclass
class PlanParse:
    plan_file: str
    in_catalog: bool
    flow_refs: list[FlowRef]
    core_files: list[str]
    mermaid_files: list[str]
    missing_doc_refs: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root path (default: current directory).",
    )
    parser.add_argument(
        "--plans-dir",
        default="docs/docs",
        help="Relative path to docs directory (default: docs/docs).",
    )
    parser.add_argument(
        "--output-dir",
        default="tmp/drift-checklists",
        help="Relative path where checklist artifacts are written (default: tmp/drift-checklists).",
    )
    parser.add_argument(
        "--ui-surfaces-dir",
        default=None,
        help="Relative path to UI entry surfaces directory to audit (optional).",
    )
    parser.add_argument(
        "--api-surfaces-dir",
        default=None,
        help="Relative path to server API directory to audit (optional).",
    )
    return parser.parse_args()


def find_repo_root_from(start: Path) -> Path | None:
    for candidate in [start.resolve(), *start.resolve().parents]:
        if (candidate / CANONICAL_CATALOG_PATH).is_file():
            return candidate
        if (candidate / LEGACY_CATALOG_PATH).is_file():
            return candidate
        if (candidate / "docs" / "docs").is_dir():
            return candidate
    return None


def resolve_repo_root(repo_root_arg: str, script_path: Path) -> Path:
    candidates = [Path(repo_root_arg), Path.cwd(), script_path]
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        found = find_repo_root_from(resolved)
        if found:
            return found
    raise FileNotFoundError(
        "Could not locate repo root containing docs/index.md or docs/plans/index.md. "
        "Pass --repo-root explicitly."
    )


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def slugify(path: str) -> str:
    return path.replace("/", "__").replace(".", "_")


def read_template(skill_root: Path, template_name: str) -> str:
    template_path = skill_root / "templates" / template_name
    return load_text(template_path)


def render_template(template: str, replacements: dict[str, str]) -> str:
    output = template
    for key, value in replacements.items():
        output = output.replace(f"{{{{{key}}}}}", value)
    return output


def is_within_path(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def parse_catalog(catalog_path: Path, plans_dir: Path) -> set[str]:
    text = load_text(catalog_path)
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    catalog_entries = set()
    plans_dir_resolved = plans_dir.resolve()
    for link in links:
        if link.startswith("http"):
            continue
        resolved = (catalog_path.parent / link).resolve()
        if resolved.suffix == ".md" and is_within_path(resolved, plans_dir_resolved):
            catalog_entries.add(str(resolved))
    return catalog_entries


def resolve_catalog_path(repo_root: Path) -> Path | None:
    canonical = (repo_root / CANONICAL_CATALOG_PATH).resolve()
    if canonical.is_file():
        return canonical
    legacy = (repo_root / LEGACY_CATALOG_PATH).resolve()
    if legacy.is_file():
        return legacy
    return None


def infer_file_from_target(repo_root: Path, target: str) -> tuple[str | None, str | None]:
    target = target.strip()
    if target.upper() == "N/A":
        return None, None
    direct = (repo_root / target).resolve()
    if direct.is_file():
        return target, None
    if "/" not in target:
        return None, None

    parts = target.split(".")
    for idx in range(len(parts), 0, -1):
        candidate = ".".join(parts[:idx])
        candidate_path = (repo_root / candidate).resolve()
        if candidate_path.is_file():
            symbol = ".".join(parts[idx:]) if idx < len(parts) else None
            return candidate, symbol

    ext_match = re.search(
        r"(.+?\.(?:tsx|ts|jsx|js|py|kt|swift|md|sh|yaml|yml|json))", target
    )
    if ext_match:
        return ext_match.group(1), None
    return None, None


def gather_flow_tokens(raw_heading: str) -> list[str]:
    tokens = BACKTICK_RE.findall(raw_heading)
    if tokens:
        return [token.strip() for token in tokens if token.strip()]
    parts = [part.strip() for part in raw_heading.split(",")]
    return [part for part in parts if part]


def parse_plan_file(  # skipcq: PY-R1000
    repo_root: Path,
    plan_path: Path,
    catalog_entries: set[str],
) -> PlanParse:
    lines = load_text(plan_path).splitlines()
    flow_refs: list[FlowRef] = []
    core_files: set[str] = set()
    mermaid_files: set[str] = set()
    in_mermaid_block = False

    for line_no, line in enumerate(lines, start=1):
        if line.strip().startswith("```mermaid"):
            in_mermaid_block = True
            continue
        if in_mermaid_block and line.strip().startswith("```"):
            in_mermaid_block = False
            continue

        flow_match = FLOW_HEADING_RE.match(line)
        if flow_match:
            raw_heading = flow_match.group(1).strip()
            tokens = gather_flow_tokens(raw_heading)
            target_raw = tokens[0] if tokens else None
            target_file = None
            target_symbol = None
            if target_raw:
                target_file, target_symbol = infer_file_from_target(repo_root, target_raw)

            test_raw = tokens[1:] if len(tokens) > 1 else []
            test_files: list[str] = []
            for test_token in test_raw:
                test_file, _ = infer_file_from_target(repo_root, test_token)
                if test_file:
                    test_files.append(test_file)

            flow_refs.append(
                FlowRef(
                    plan_file=str(plan_path.relative_to(repo_root)),
                    line_no=line_no,
                    raw_heading=raw_heading,
                    target_raw=target_raw,
                    target_file=target_file,
                    target_symbol=target_symbol,
                    test_raw=test_raw,
                    test_files=test_files,
                )
            )

        if "Core files" in line:
            for token in BACKTICK_RE.findall(line):
                if (
                    "<" in token
                    or ">" in token
                    or "..." in token
                    or token.startswith("path/to/")
                ):
                    continue
                core_file, _ = infer_file_from_target(repo_root, token)
                if core_file:
                    core_files.add(core_file)
                elif "/" in token:
                    core_files.add(token)

        if in_mermaid_block:
            for match in PATH_RE.findall(line):
                mermaid_files.add(match)

    referenced_files: set[str] = set(core_files) | set(mermaid_files)
    for flow_ref in flow_refs:
        if flow_ref.target_file:
            referenced_files.add(flow_ref.target_file)
        for test_file in flow_ref.test_files:
            referenced_files.add(test_file)

    missing_doc_refs = sorted(
        ref for ref in referenced_files if not (repo_root / ref).resolve().is_file()
    )

    return PlanParse(
        plan_file=str(plan_path.relative_to(repo_root)),
        in_catalog=str(plan_path.resolve()) in catalog_entries,
        flow_refs=flow_refs,
        core_files=sorted(core_files),
        mermaid_files=sorted(mermaid_files),
        missing_doc_refs=missing_doc_refs,
    )


def collect_ui_surfaces(repo_root: Path, ui_surfaces_dir: str | None) -> list[str]:
    if not ui_surfaces_dir:
        return []
    surfaces_root = repo_root / ui_surfaces_dir
    if not surfaces_root.exists():
        return []
    ui_surfaces: set[str] = set()
    for file_path in surfaces_root.rglob("*"):
        if not file_path.is_file():
            continue
        if "__tests__" in file_path.parts:
            continue
        ui_surfaces.add(str(file_path.relative_to(repo_root)))
    return sorted(ui_surfaces)


def collect_server_api_surfaces(repo_root: Path, api_surfaces_dir: str | None) -> list[str]:
    if not api_surfaces_dir:
        return []
    api_root = repo_root / api_surfaces_dir
    if not api_root.exists():
        return []
    return sorted(str(path.relative_to(repo_root)) for path in api_root.rglob("*") if path.is_file())


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def clear_markdown_files(path: Path) -> None:
    if not path.exists():
        return
    for markdown_file in path.glob("*.md"):
        markdown_file.unlink()


def collect_plan_refs(plans: Iterable[PlanParse]) -> dict[str, set[str]]:
    refs: dict[str, set[str]] = {}
    for plan in plans:
        plan_name = plan.plan_file
        for flow_ref in plan.flow_refs:
            if flow_ref.target_file:
                refs.setdefault(flow_ref.target_file, set()).add(plan_name)
            for test_file in flow_ref.test_files:
                refs.setdefault(test_file, set()).add(plan_name)
        for core_file in plan.core_files:
            refs.setdefault(core_file, set()).add(plan_name)
        for mermaid_file in plan.mermaid_files:
            refs.setdefault(mermaid_file, set()).add(plan_name)
    return refs


def extract_flow_rows(flow_refs: list[FlowRef], repo_root: Path) -> str:
    if not flow_refs:
        return "- No flow headings found."
    rows: list[str] = []
    for flow in flow_refs:
        target_state = "missing"
        if flow.target_file and (repo_root / flow.target_file).resolve().is_file():
            target_state = "ok"
        elif flow.target_raw and "/" not in flow.target_raw:
            target_state = "symbolic"
        test_state = "N/A"
        concrete_tests = [raw for raw in flow.test_raw if raw.upper() != "N/A"]
        if concrete_tests:
            test_state = "ok"
            for raw in concrete_tests:
                test_file, _ = infer_file_from_target(repo_root, raw)
                if not test_file or not (repo_root / test_file).resolve().is_file():
                    test_state = "missing"
                    break
        rows.append(
            f"- `{flow.target_raw or flow.raw_heading}` (line {flow.line_no}): "
            f"target={target_state}, tests={test_state}"
        )
    return "\n".join(rows)


def extract_missing_doc_refs_rows(missing_refs: list[str]) -> str:
    if not missing_refs:
        return "- None."
    return "\n".join(f"- `{ref}`" for ref in missing_refs)


def summarize_findings(  # skipcq: PY-R1000
    repo_root: Path,
    plans: list[PlanParse],
    catalog_entries: set[str],
    ui_surfaces_dir: str | None = None,
    api_surfaces_dir: str | None = None,
) -> dict[str, list[str]]:
    findings = {
        "extra": [],
        "missing": [],
        "different": [],
        "wrong": [],
    }

    # extra: catalog entries missing plan files + docs references to missing files.
    for entry in sorted(catalog_entries):
        if not Path(entry).is_file():
            rel = str(Path(entry).relative_to(repo_root))
            findings["extra"].append(f"Catalog lists missing plan file `{rel}`.")
    for plan in plans:
        for missing_ref in plan.missing_doc_refs:
            findings["extra"].append(
                f"`{plan.plan_file}` references missing path `{missing_ref}`."
            )

    # missing: UI/API entry surfaces not covered by docs.
    plan_refs = collect_plan_refs(plans)
    for ui_surface in collect_ui_surfaces(repo_root, ui_surfaces_dir):
        if ui_surface not in plan_refs:
            findings["missing"].append(
                f"UI surface `{ui_surface}` is not referenced by any doc flow."
            )
    for api_surface in collect_server_api_surfaces(repo_root, api_surfaces_dir):
        if api_surface not in plan_refs:
            findings["missing"].append(
                f"API surface `{api_surface}` is not referenced by any doc."
            )

    # different: flow tests declared but missing.
    for plan in plans:
        for flow in plan.flow_refs:
            for test_raw in flow.test_raw:
                if test_raw.upper() == "N/A":
                    continue
                test_file, _ = infer_file_from_target(repo_root, test_raw)
                if not test_file or not (repo_root / test_file).resolve().is_file():
                    findings["different"].append(
                        f"`{plan.plan_file}` flow line {flow.line_no} test target `{test_raw}` does not exist."
                    )

    # wrong: ownership overlap for server api handlers in multiple plans.
    server_owner_map: dict[str, set[str]] = {}
    for plan in plans:
        for flow in plan.flow_refs:
            if flow.target_file and flow.target_file.startswith("main/server/api/"):
                server_owner_map.setdefault(flow.target_file, set()).add(plan.plan_file)
        for core_file in plan.core_files:
            if core_file.startswith("main/server/api/"):
                server_owner_map.setdefault(core_file, set()).add(plan.plan_file)
    for api_file, owners in sorted(server_owner_map.items()):
        if len(owners) > 1:
            owner_list = ", ".join(sorted(owners))
            findings["wrong"].append(
                f"Server API file `{api_file}` appears to have multiple owners: {owner_list}."
            )

    return findings


def write_plan_checklists(
    repo_root: Path,
    plans: list[PlanParse],
    output_plans_dir: Path,
    skill_root: Path,
    catalog_display_path: str,
) -> None:
    ensure_dir(output_plans_dir)
    clear_markdown_files(output_plans_dir)
    template = read_template(skill_root, "plan-checklist-template.md")

    for plan in plans:
        content = render_template(
            template,
            {
                "PLAN_FILE": plan.plan_file,
                "IN_CATALOG": "yes" if plan.in_catalog else "no",
                "CATALOG_PATH": catalog_display_path,
                "FLOW_COUNT": str(len(plan.flow_refs)),
                "CATALOG_CHECK": "x" if plan.in_catalog else " ",
                "FLOW_EXISTS_CHECK": "x" if plan.flow_refs else " ",
                "MISSING_DOC_REFS_CHECK": "x" if not plan.missing_doc_refs else " ",
                "FLOW_ROWS": extract_flow_rows(plan.flow_refs, repo_root),
                "MISSING_DOC_REFERENCES": extract_missing_doc_refs_rows(plan.missing_doc_refs),
            },
        )
        file_name = f"{Path(plan.plan_file).stem}.md"
        (output_plans_dir / file_name).write_text(content + "\n", encoding="utf-8")


def write_ui_checklists(
    repo_root: Path,
    plans: list[PlanParse],
    output_ui_dir: Path,
    skill_root: Path,
    ui_surfaces_dir: str | None = None,
) -> None:
    ensure_dir(output_ui_dir)
    clear_markdown_files(output_ui_dir)
    template = read_template(skill_root, "ui-surface-checklist-template.md")
    plan_refs = collect_plan_refs(plans)

    # Build flow-level test map by code target.
    flow_test_map: dict[str, set[str]] = {}
    for plan in plans:
        for flow in plan.flow_refs:
            if not flow.target_file:
                continue
            for test_file in flow.test_files:
                flow_test_map.setdefault(flow.target_file, set()).add(test_file)

    for ui_surface in collect_ui_surfaces(repo_root, ui_surfaces_dir):
        owners = sorted(plan_refs.get(ui_surface, set()))
        test_refs = sorted(flow_test_map.get(ui_surface, set()))
        content = render_template(
            template,
            {
                "UI_SURFACE": ui_surface,
                "REFERENCE_COUNT": str(len(owners)),
                "HAS_PLAN_REF_CHECK": "x" if owners else " ",
                "HAS_TEST_MAP_CHECK": "x" if test_refs else " ",
                "OWNERSHIP_CLEAR_CHECK": "x" if len(owners) <= 1 else " ",
                "PLAN_REFERENCES": (
                    "\n".join(f"- `{owner}`" for owner in owners) if owners else "- None."
                ),
                "TEST_REFERENCES": (
                    "\n".join(f"- `{test_ref}`" for test_ref in test_refs)
                    if test_refs
                    else "- None."
                ),
            },
        )
        output_name = f"{slugify(ui_surface)}.md"
        (output_ui_dir / output_name).write_text(content + "\n", encoding="utf-8")


def write_summary(
    findings: dict[str, list[str]],
    output_summary_path: Path,
) -> None:
    sections = []
    for key in ("extra", "missing", "different", "wrong"):
        items = findings[key]
        header = key.capitalize()
        if not items:
            body = "- None."
        else:
            body = "\n".join(f"- {item}" for item in items)
        sections.append(f"## {header}\n\n{body}")

    summary = (
        "# Drift Summary\n\n"
        "Generated by `agents/documentation/skills/detect-drift/scripts/generate_checklists.py`.\n\n"
        "Buckets:\n"
        "- `extra`: docs/catalog references with no valid implementation target\n"
        "- `missing`: implemented entry surfaces not covered by plans\n"
        "- `different`: docs and implementation both exist but mapping differs\n"
        "- `wrong`: ownership mapped to the wrong plan or multiple conflicting owners\n\n"
        + "\n\n".join(sections)
        + "\n"
    )
    output_summary_path.write_text(summary, encoding="utf-8")


def main() -> int:
    args = parse_args()
    script_path = Path(__file__).resolve()
    repo_root = resolve_repo_root(args.repo_root, script_path)
    plans_dir = (repo_root / args.plans_dir).resolve()
    output_dir = (repo_root / args.output_dir).resolve()

    skill_root = script_path.parent.parent
    catalog_path = resolve_catalog_path(repo_root)
    if catalog_path is not None:
        catalog_entries = parse_catalog(catalog_path, plans_dir)
        catalog_display_path = str(catalog_path.relative_to(repo_root))
    else:
        catalog_entries = set()
        catalog_display_path = "N/A"

    plan_files = sorted(path for path in plans_dir.glob("*.md") if path.name != "index.md")
    parsed_plans = [parse_plan_file(repo_root, plan_path, catalog_entries) for plan_path in plan_files]

    ensure_dir(output_dir)
    output_plans_dir = output_dir / "docs"
    output_ui_dir = output_dir / "ui-surfaces"
    summary_path = output_dir / "DRIFT-SUMMARY.md"

    write_plan_checklists(
        repo_root,
        parsed_plans,
        output_plans_dir,
        skill_root,
        catalog_display_path,
    )
    write_ui_checklists(repo_root, parsed_plans, output_ui_dir, skill_root, args.ui_surfaces_dir)
    findings = summarize_findings(
        repo_root,
        parsed_plans,
        catalog_entries,
        args.ui_surfaces_dir,
        args.api_surfaces_dir,
    )
    write_summary(findings, summary_path)

    print(f"Wrote summary: {summary_path.relative_to(repo_root)}")
    print(f"Wrote doc checklists: {output_plans_dir.relative_to(repo_root)}")
    if args.ui_surfaces_dir:
        print(f"Wrote UI checklists: {output_ui_dir.relative_to(repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
