---
name: accessibility-audit
description: >-
  Audit a web page for accessibility, layout, and mobile-friendliness issues and
  report them by severity. Use when the user asks to check accessibility, a11y, WCAG
  compliance, contrast, keyboard/screen-reader support, responsive/mobile layout, or
  whether a page's UI looks broken.
---

# Accessibility & UX Audit

Inspect a page with the browser tools and deliver a saved markdown report.

## Steps

1. Open the page; take an accessibility snapshot and a desktop screenshot
   (`<output_dir>/desktop.png`). Look at the screenshot for problems a DOM check misses:
   overlap, misalignment, low contrast, off-screen or overflowing content.
2. Run the a11y (axe-core) audit for WCAG violations (impact, rule, nodes).
3. Confirm suspected issues by measuring bounding boxes and computed styles instead of
   guessing (overflow, overlap, tap targets < 44×44px).
4. Emulate a phone (e.g. "iPhone 15"), re-screenshot (`<output_dir>/mobile.png`), recheck.

Prefer viewport screenshots (scroll to see below the fold). Note: under viewport/device
emulation, full-page screenshots come out zoomed out with blank white space to the right
and bottom — that's a capture artifact, not a page layout bug; never report it as one.

Report only issues backed by evidence: a selector, a measured box, an axe rule, or a
failed request.

## Report

Save it with `save_report` (writes `report.md` beside the screenshots; reference them by
filename, e.g. `![desktop](desktop.png)`). Group findings by severity
(Critical / Serious / Moderate / Minor); for each give **what**, **where** (selector),
**evidence**, and a **fix**. End with a one-line summary; if the page is healthy, say so.
Then tell the user where the report was saved.
