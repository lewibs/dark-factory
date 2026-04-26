---
name: deviation-protocol
user-invocable: false
description: Invoked by implementation-agent when a plan conflict cannot be resolved independently. Stops all code writing, asks the developer how to proceed, and returns either course-correct or hard-stop.
---

## Required

You must follow this skill exactly when invoked. Do not write any code from the moment this skill is invoked until a developer decision is received.

## Steps

1. **Stop writing code immediately.** Do not edit any files until a developer decision is received.

2. Before asking the developer how to proceed on a plan conflict, call PushNotification with title: "Developer Decision Required" and message: "A plan conflict was encountered and requires your decision to continue."

   **Ask the developer how to proceed.** Present clearly:
   - What flow was being implemented.
   - What the conflict or ambiguity is (be specific — quote the plan section if helpful).
   - Your proposed resolution, if you have one.
   - Then ask: *"How would you like to proceed? Options: (1) course-correct — give me guidance and I will update the plan and continue, or (2) hard-stop — pause execution and return to planning."*

3. **Wait for the developer's response.**

4. **If course-correct:**
   - Apply the developer's guidance to the plan file:
     - Update the affected flow contracts, pseudocode, or file structure as needed.
     - If the architecture changed, invoke the `create-mermaid-diagram` skill to update the diagram.
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
