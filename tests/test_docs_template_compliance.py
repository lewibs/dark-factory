"""
Tests that each docs/docs/ file conforms to the required documentation template.

Required sections (from agents/documentation/skills/documentation/templates/documentation-template.md):
  - Metadata
  - Mermaid Diagram
  - Flows
  - Logs
  - Deployment
"""

import os
import pytest

DOCS_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "docs")

DOC_FILES = [
    f"{DOCS_ROOT}/agents.md",
    f"{DOCS_ROOT}/commands.md",
    f"{DOCS_ROOT}/skills.md",
    f"{DOCS_ROOT}/tests.md",
]

REQUIRED_SECTIONS = [
    "## Metadata",
    "## Mermaid Diagram",
    "## Flows",
    "## Logs",
    "## Deployment",
]

REQUIRED_FLOW_SUBSECTIONS = [
    "#### Types",
    "#### Paths",
]

REQUIRED_METADATA_FIELDS = [
    "System type:",
]


@pytest.mark.parametrize("doc_path", DOC_FILES)
def test_required_sections_present(doc_path):
    with open(doc_path) as f:
        content = f.read()

    missing = [s for s in REQUIRED_SECTIONS if s not in content]
    assert not missing, (
        f"{doc_path} is missing required template sections: {missing}"
    )


@pytest.mark.parametrize("doc_path", DOC_FILES)
def test_metadata_has_system_type(doc_path):
    with open(doc_path) as f:
        content = f.read()

    assert "System type:" in content, (
        f"{doc_path} Metadata section must declare 'System type:'"
    )


@pytest.mark.parametrize("doc_path", DOC_FILES)
def test_mermaid_diagram_has_code_block(doc_path):
    with open(doc_path) as f:
        content = f.read()

    assert "```mermaid" in content, (
        f"{doc_path} must contain a ```mermaid code block in the Mermaid Diagram section"
    )


@pytest.mark.parametrize("doc_path", DOC_FILES)
def test_flows_section_has_types_and_paths(doc_path):
    with open(doc_path) as f:
        content = f.read()

    missing = [s for s in REQUIRED_FLOW_SUBSECTIONS if s not in content]
    assert not missing, (
        f"{doc_path} Flows section is missing subsections: {missing}"
    )


@pytest.mark.parametrize("doc_path", DOC_FILES)
def test_logs_section_has_table(doc_path):
    with open(doc_path) as f:
        content = f.read()

    # The Logs section must contain a markdown table (indicated by | Source |)
    assert "| Source |" in content, (
        f"{doc_path} Logs section must contain a table with a 'Source' column"
    )


@pytest.mark.parametrize("doc_path", DOC_FILES)
def test_deployment_section_has_mechanism(doc_path):
    with open(doc_path) as f:
        content = f.read()

    assert "- Mechanism:" in content, (
        f"{doc_path} Deployment section must declare '- Mechanism:'"
    )
