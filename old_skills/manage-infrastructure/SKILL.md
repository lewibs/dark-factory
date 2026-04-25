---
name: manage-infrastructure
description: Use this skill when modifying, validating, or deploying AWS infrastructure using Terraform.
---

## Required

You must add the following steps to your current task checklist or implementation plan:

1. Navigate to `main/devops`.
2. Run `terraform init` if modules/providers changed.
3. Run `jj fix` to handle HCL formatting.
4. Run `terraform validate` to check syntax.
5. Run `terraform plan` and REVIEW the output carefully.
6. Verify security group rules allow the intended access (do not rely on "publicly accessible" flags).
7. Only run `terraform apply` after confirming the plan is safe.

## Context

I manage infrastructure using Terraform in `main/devops`.

- **Workflow**: `init` -> `fmt` -> `validate` -> `plan` -> `apply`.
- **Critical Rule**: I NEVER modify infrastructure without running a plan first.
- **Formatting**: I always use `jj fix` (which runs `terraform fmt`).
- **Safety**: I review cost impacts for major changes (e.g., instance types, IOPS).
- **Terraform Scope**: Terraform only exposes outputs/state for resources it manages. Import external resources if needed.

## Examples

## Good Example

# Running a plan before applying

```bash
terraform plan -out=tfplan
terraform apply tfplan
```

## Bad Example

# Blindly applying changes

```bash
terraform apply -auto-approve
```
