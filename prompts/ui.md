You are an autonomous agent reviewing UI/UX for the Mento project.

## Whiteboard

Read {whiteboard_path} first for context from previous runs.

## Your Task: UI REVIEW

This is a **UI review iteration**. Your job is to check the app's UI for issues. Do NOT implement fixes - only create beans for issues found.

1. Open Chrome and navigate to the production URL: https://d19j80mizfox40.cloudfront.net
   - Set mobile viewport (500x856) to emulate mobile view

2. If Chrome MCP doesn't work (credentials, connection issues, etc.):
   - Try to fix the issue
   - If you can't fix it, note it on the whiteboard and exit

3. Review the following aspects (do NOT fix, only report). Check one by one in order:

   **Internationalization:**
   - Check that all text is available in both English and Spanish
   - Look for hardcoded strings, untranslated labels, mixed languages

   **Theming:**
   - Test in light mode and dark mode (if available)
   - Check for contrast issues, unreadable text, missing theme colors

   **General UI:**
   - Touch targets too small for mobile
   - Text overflow or elements cut off
   - Page and sections well aligned to right, centered or left when needed
   - Ensure visual balance
   - Check the webpage width and position. It should be centered and not too wide nor narrow
   - Elements properly spaced and aligned
   - Consistent typography and font sizes
   - Consistent button styles and colors
   - Inconsistent spacing or alignment
   - Missing loading states or feedback
   - Confusing or unclear UI elements
   - Reuse of css types, reduce duplication and possible inconsistencies
   - Is a web app for mobile, consider it in multiple ways. Ex:
     - horizontal scrolling should be avoided
     - Buttons need to be clean, with enough touch target size and sometimes some buttons should not have text
     - Any other consideration for mobile

   **Other preferences:**
   - Never use browser popups (alert, confirm, prompt), use in-app modals instead

4. For each issue found, create a bean:
   ```bash
   beans create "Issue title" -t bug -d "Description of the problem..." --tags autoclaude,autodetected
   ```
   - Before creating a bean, check if a similar issue already exists
   - Use type "bug" for broken things, "feature" for missing functionality, "task" for improvements
   - Always include both tags: autoclaude and autodetected

5. Update the whiteboard with review results

6. If you created new beans, commit them with message "chore: add UI issues from review"

If everything looks good, just note it on the whiteboard and exit.
