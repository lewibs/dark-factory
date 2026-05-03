---
name: deviation-protocol
user-invocable: false
description: Invoked by implementation-agent when a plan conflict cannot be resolved independently. Stops all code writing, asks the developer how to proceed, and returns either course-correct or hard-stop.
---

## Required

You must follow this skill exactly when invoked. Do not write any code from the moment this skill is invoked until a developer decision is received.

## Steps

1. **Stop writing code immediately.** Do not edit any files until a developer decision is received.

2. Call PushNotification with title: "Developer Decision Required" and message: "A plan conflict was encountered and requires your decision to continue."

   Present clearly (as text before the question):
   - What flow was being implemented.
   - What the conflict or ambiguity is (be specific — quote the plan section if helpful).
   - Your proposed resolution, if you have one.

   Then use AskUserQuestion with:
     header: "Plan Conflict"
     question: "Plan conflict encountered in [flow]. How would you like to proceed?"
     options:
       - label: "Course-correct", description: "Provide guidance — I will update the plan and continue (use Other to type instructions)"
       - label: "Hard-stop", description: "Pause execution and return to planning"

   If "Course-correct" or "Other": treat the developer's selection and any notes as guidance.

3. **Wait for the developer's response.**

4. **If course-correct:**
   - Apply the developer's guidance to the plan file:
     - Update the affected flow contracts, pseudocode, or file structure as needed.
     - If the architecture changed, invoke the skill at `skills/create-mermaid-diagram/SKILL.md` to update the diagram.
     - Add an entry to the `## Deviations` section at the end of the plan (create the section if it does not exist):
       ```
       - Date: <today>
       - Flow: <flowName>
       - Blocker: <blockerDescription>
       - Resolution: <resolution applied>
       - Status: course-corrected
       ```
   - Set the plan `Status` back to `approved`.
   - Return `{ decision: "course-correct" }`.

5. **If hard-stop:**
   - Add an entry to the `## Deviations` section at the end of the plan (create the section if it does not exist):
     ```
     - Date: <today>
     - Flow: <flowName>
     - Blocker: <blockerDescription>
     - Status: hard-stop — awaiting replanning
     ```
   - Set the plan `Status` to `draft`.
   - Notify the developer: *"Execution is paused. The plan has been marked draft. Tell me when it is ready to resume and I will continue from the current flow."*
   - Return `{ decision: "hard-stop" }`.

## Rules

- The plan file must be updated **before** returning to the caller — not after.
- Never resume code writing without an explicit developer decision.
- On course-correct, the diagram must be updated before returning if the architecture changed.
