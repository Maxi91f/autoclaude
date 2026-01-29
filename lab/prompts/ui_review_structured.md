# UI/UX Review - Structured

Review this mobile web app systematically. Create a bean for every issue found.

## Setup

1. Navigate to: https://d19j80mizfox40.cloudfront.net/
2. Set mobile viewport: `mcp__chrome-devtools__resize_page` with width=500, height=856
3. Take a snapshot to see the page structure

## Review Process

### 1. First Impressions
Take a snapshot. What's confusing at first glance?

### 2. Explore Each Screen
Navigate through the app. For each screen, check:

**Visual Hierarchy**
- Clear heading structure
- Important actions are prominent
- Secondary actions are subdued

**Spacing & Alignment**
- Consistent margins and padding
- Elements properly aligned
- No awkward gaps or crowding

**Touch Targets**
- Buttons at least 44x44px
- Adequate spacing between tappable elements

**Color & Contrast**
- Text readable against background
- Consistent color usage

**Feedback & States**
- Loading indicators present
- Error states are clear
- Success feedback visible

### 3. Test Flows
Try the main user actions. What's frustrating?

### 4. Test Dark/Light Mode
Check both themes for issues.

## For each issue:

Think like a user: "Where do I tap?", "Why isn't this working?", "I can't read this"

```bash
beans create "Descriptive title" -t bug -p normal -d "As a user, I expected [X] but got [Y].
Where: [location]
Why it matters: [impact]" --tag {tag}
```

Be specific. "Button too small" is weak. "Login button requires precision tapping" is actionable.

Don't hold back - real users would complain about these things.
