# UI/UX Review - Nielsen Heuristics

Evaluate this mobile web app against Nielsen's 10 usability heuristics.

## Setup

1. Navigate to: https://d19j80mizfox40.cloudfront.net/
2. Set mobile viewport: `mcp__chrome-devtools__resize_page` with width=500, height=856
3. Take a snapshot

## Heuristics Evaluation

For each heuristic, explore the app looking for violations:

### 1. Visibility of System Status
- Does the app show what's happening? Loading states, progress, confirmations?
- Are there delays without feedback?

### 2. Match Between System and Real World
- Does language make sense to users? No jargon?
- Do icons and metaphors match expectations?

### 3. User Control and Freedom
- Can users undo actions? Cancel operations?
- Is there a clear way to go back?

### 4. Consistency and Standards
- Do similar things look and work the same way?
- Does it follow platform conventions?

### 5. Error Prevention
- Are dangerous actions protected? (delete, irreversible changes)
- Are inputs validated before submission?

### 6. Recognition Rather Than Recall
- Is everything visible or easily retrievable?
- Do users have to remember info from one screen to another?

### 7. Flexibility and Efficiency of Use
- Are there shortcuts for frequent actions?
- Can experienced users speed up interactions?

### 8. Aesthetic and Minimalist Design
- Is there visual clutter?
- Is irrelevant information shown?

### 9. Help Users Recognize, Diagnose, and Recover from Errors
- Are error messages clear and helpful?
- Do they suggest solutions?

### 10. Help and Documentation
- Is help available when needed?
- Is it easy to find?

## For each violation:

```bash
beans create "[Heuristic #] - Issue title" -t bug -p normal -d "Heuristic: [name]
Violation: [what's wrong]
Impact: [how it affects users]
Recommendation: [how to fix]" --tag {tag}
```

Example: "H4 - Inconsistent button styles across screens"
