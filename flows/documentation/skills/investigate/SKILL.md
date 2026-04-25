---
name: investigate
user-invocable: false
description: Techniques for gathering everything needed to fill out the documentation template for a system. Use before writing any docs.
---

# investigate

Each section maps to a section in the documentation template. Work through them in order.

## System Intent — what is this and what does it do?

- Search for the system name: `grep -r "<system-name>" --include="*.py" -l`
- Look for a README, docstring, or comment near the entry point that describes purpose
- Identify the primary caller or consumer (who invokes this?)

## Flows — what are the inputs and outputs of each flow?

For each flow in the system:

**Find the inputs:**
- Read the entry point signature (handler args, route body, CLI params)
- Look for schema/validation classes near the entry: Pydantic models, marshmallow schemas, dataclasses
- Check tests for example input payloads: `grep -r "def test_" --include="*.py" -l`

**Find the outputs:**
- Read return statements and response construction near the end of each flow
- Look for success and error response shapes — note HTTP status codes, error codes, and output fields
- Check tests for expected output assertions

**Find all parts that participate in the flow:**
- Trace imports forward from the entry point through every function call
- Note each file and its role as the data passes through it
- Find all reads/writes: `grep -r "boto3\|sqlalchemy\|psycopg\|redis\|sqs\|dynamodb\|open(" -l`
- Look for downstream calls: HTTP clients, queue publishes, SNS, other service invocations
- Check for non-obvious paths: feature flags, env var branches, retry logic, fallback handlers

**Find error paths:**
- Search for `raise`, `except`, `return.*error`, explicit status codes near the flow
- Check tests for known failure cases: `grep -r "raises\|assert.*error\|assert.*status.*4\|assert.*status.*5" -l`
- Cross-reference `docs/bugs/` for previously encountered failures

## Logs — where does this system write logs?

- Find log calls: `grep -r "logger\.\|logging\.\|print(" --include="*.py" -l`
- For AWS: find CloudWatch log group names in `template.yaml`, `serverless.yml`, or CDK config
- For local: find log file paths in config, startup scripts, or env vars

## Deployment — how does code get deployed?

- Check `Makefile`, `deploy.sh`, `scripts/` at the project root
- Look for SAM (`sam build`/`sam deploy`), CDK (`cdk deploy`), docker-compose, or direct Lambda update targets
- Check CI config (`.github/workflows/`, `buildspec.yml`) for deploy steps
