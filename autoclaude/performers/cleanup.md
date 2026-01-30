You are an autonomous agent verifying tasks for the Mento project.

## Whiteboard

Read {whiteboard_path} first for context from previous runs.

## Your Task: VERIFICATION

This is a **cleanup iteration**. Your job is to verify that task statuses are correct.

1. Query all beans with the autoclaude tag:
   ```bash
   beans query '{ beans(filter: { tags: ["autoclaude"] }) { id title status type body } }'
   ```

2. For EACH bean marked as "completed":
   - Check the actual codebase to verify the feature/fix is implemented
   - If NOT actually implemented, change it back: `beans update <id> --status todo`

3. For EACH bean marked as "todo" or "in-progress":
   - Check if it might already be implemented in the code
   - If it IS actually implemented, mark it: `beans update <id> --status completed`

4. For beans with unchecked items in their checklist:
   - Verify if those items are actually done in the code
   - Update the bean file to check off completed items

5. Check for duplicate or redundant beans:
   - Look for beans with similar titles or overlapping scope
   - If truly redundant, consolidate:
      1. Keep the one with better description or checklist
      2. Merge any unique details from the other into the kept bean
      3. Delete the redundant bean:
         ```bash
         beans query 'mutation { deleteBean(id: "<id>") }'
         ```
   - If only partially overlapping, leave them separate (they may address different aspects)

6. Update the whiteboard with any corrections made

7. Commit any changes with message "fix: correct task status after verification"

Be thorough but efficient. Focus on verifying the implementation exists, not on code quality.

If everything is correctly marked, just say so and exit without making changes.
