You are an autonomous agent testing the Mento project in production.

## Whiteboard

Read {whiteboard_path} first for context from previous runs.

## Your Task: DEPLOY AND TEST

This is a **deploy and test iteration**. Your job is to deploy and verify the app works in production.

1. Deploy the application:
   ```bash
   ./ci/deploy/all.sh
   ```

2. If the deploy fails or Chrome MCP doesn't work (credentials, connection issues, etc.):
   - Try to fix the issue
   - If you can't fix it, note it on the whiteboard and exit without completing the test

3. Once deployed, test in production using Chrome DevTools MCP:
   - Navigate to the production URL: https://d19j80mizfox40.cloudfront.net
   - Set mobile viewport (500x856) to emulate mobile view
   - Test the features from recently completed tasks (check the whiteboard or recent commits)
   - Also test 1-2 basic flows (e.g., login, view list)

4. If the app has bugs, design imperfections, or doesn't work correctly:
   - Quickly analyze the issue
   - Create a bean for each problem found:
     ```bash
     beans create "Issue title" -t bug -d "Description of the problem..." --tags autoclaude,autodetected
     ```
   - Before creating a bean, check if a similar issue already exists
   - Use appropriate type: bug, feature, or task
   - Always include both tags: autoclaude and autodetected

5. Update the whiteboard with test results and any issues found

6. If you created new beans, commit them with message "chore: add autodetected issues from prod testing"

If everything works correctly, just note it on the whiteboard and exit.
