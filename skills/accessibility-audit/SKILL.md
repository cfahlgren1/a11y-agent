---
name: accessibility-audit
description: >-
  Audit a web page for accessibility, layout, and mobile-friendliness issues and
  report them by severity. Use when the user asks to check accessibility, a11y, WCAG
  compliance, contrast, keyboard/screen-reader support, responsive/mobile layout, or
  whether a page's UI looks broken.
---

# Accessibility & UX Audit

Drive the browser to inspect a page and report concrete, actionable issues.

## Steps

1. Open the page, then take an accessibility-tree snapshot to understand its structure.
2. Take a screenshot and LOOK at it. Use your vision to spot problems a DOM check would
   miss: text overlapping images, misaligned or cramped elements, low-contrast text,
   content running off-screen, broken layout.
3. Run the a11y (axe-core) audit for objective WCAG violations — note the impact level,
   rule, and failing nodes.
4. When something looks wrong, CONFIRM it with measurements instead of guessing — read
   bounding boxes and computed styles and check geometry (overflow, overlap, off-screen,
   tap targets smaller than 44x44px).
5. For mobile checks, emulate a phone (e.g. "iPhone 15") or set a narrow viewport, then
   re-screenshot and re-measure.
6. Prefer evidence over speculation. Every issue you report should cite what you saw or
   measured (a selector, a box, an axe rule, a failed request).

## Report format

Group findings by severity: **Critical / Serious / Moderate / Minor**. For each issue
give:

- **What** the issue is
- **Where** it is (a selector or region)
- **Evidence** — what you saw or measured (axe rule, bounding box, contrast, failed request)
- **Fix** — a concrete suggested change

Be concise. End with a one-line summary. If the page looks healthy, say so plainly.
