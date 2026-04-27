"""
mermaid_to_image.py

Extracts a Mermaid fenced code block from a plan .md file and returns
a mermaid.ink URL for rendering.
"""

import argparse
import base64
import os
import re
import subprocess
import sys
import tempfile


def extract_mermaid_from_plan(plan_file_path: str, block_index: int = 1) -> str:
    """
    Extract the Mermaid diagram text at block_index (1-indexed) from plan_file_path.

    Flow: extractMermaidFromPlan
    """
    # flow | extract_mermaid_from_plan | reading file
    if block_index < 1:
        raise ValueError(f"block_index must be >= 1, got {block_index}")

    with open(plan_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Collect all ```mermaid...``` blocks
    pattern = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
    blocks = pattern.findall(content)

    # flow | extract_mermaid_from_plan | blocks_found={len(blocks)}
    if not blocks:
        raise ValueError(f"No mermaid block found in {plan_file_path}")

    if block_index > len(blocks):
        raise ValueError(
            f"Block index {block_index} out of range: only {len(blocks)} mermaid block(s) found in {plan_file_path}"
        )

    return blocks[block_index - 1]


def generate_mermaid_ink_url(mermaid_string: str) -> str:
    """
    Base64-encode mermaid_string and return a mermaid.ink URL.

    Flow: generateMermaidInkUrl
    """
    # flow | generate_mermaid_ink_url | validating input
    if mermaid_string.strip() == "":
        raise ValueError("empty mermaid input")

    encoded = base64.urlsafe_b64encode(mermaid_string.encode("utf-8")).decode("utf-8")
    # flow | generate_mermaid_ink_url | url_generated
    return f"https://mermaid.ink/img/{encoded}"


def validate_mermaid_syntax(mermaid_string: str) -> tuple:
    """
    Parse mermaid_string with mmdc (npx @mermaid-js/mermaid-cli).
    Returns (is_valid: bool, error: str).

    Flow: validateMermaidSyntax
    """
    import json

    tmp_in = tmp_out = tmp_cfg = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as f:
            f.write(mermaid_string)
            tmp_in = f.name
        tmp_out = tmp_in.replace(".mmd", ".svg")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"args": ["--no-sandbox", "--disable-setuid-sandbox"]}, f)
            tmp_cfg = f.name
        result = subprocess.run(
            ["npx", "--yes", "@mermaid-js/mermaid-cli", "-i", tmp_in, "-o", tmp_out, "-p", tmp_cfg, "--quiet"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return False, (result.stderr or result.stdout).strip()
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "mmdc timed out"
    except FileNotFoundError:
        return False, "npx not found — cannot validate mermaid syntax"
    finally:
        for p in (tmp_in, tmp_out, tmp_cfg):
            if p and os.path.exists(p):
                os.unlink(p)


def main() -> None:
    """
    CLI entry point.

    Flow: cliEntryPoint
    """
    # flow | cli | parsing_args
    parser = argparse.ArgumentParser(
        description="Extract a Mermaid diagram from a plan file and return a mermaid.ink URL."
    )
    parser.add_argument("plan_file_path", help="Absolute path to a docs/plans/*.md file")
    parser.add_argument(
        "block_index_pos",
        nargs="?",
        type=int,
        default=None,
        help="1-indexed position of the mermaid block to extract (optional positional; default: 1)",
    )
    parser.add_argument(
        "--block",
        dest="block_index_flag",
        type=int,
        default=None,
        help="1-indexed position of the mermaid block to extract (default: 1)",
    )
    args = parser.parse_args()

    # Resolve block_index: positional takes precedence over --block flag; default is 1
    if args.block_index_pos is not None:
        args.block_index = args.block_index_pos
    elif args.block_index_flag is not None:
        args.block_index = args.block_index_flag
    else:
        args.block_index = 1

    # flow | cli | extracting_mermaid | plan_file_path={args.plan_file_path} block_index={args.block_index}
    try:
        mermaid_string = extract_mermaid_from_plan(args.plan_file_path, args.block_index)
        if not os.environ.get("MERMAID_SKIP_VALIDATE"):
            valid, err = validate_mermaid_syntax(mermaid_string)
            if not valid:
                print(f"Error: mermaid diagram failed validation: {err}", file=sys.stderr)
                sys.exit(1)
        url = generate_mermaid_ink_url(mermaid_string)
        print(url)
        sys.exit(0)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
