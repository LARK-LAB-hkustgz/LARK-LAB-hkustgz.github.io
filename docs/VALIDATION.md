# Redesign validation

Validated locally on October 19, 2026.

- Initial migration audit: all **40** original BibTeX entries retained.
- Initial migration audit: all **22** member records retained, including names,
  ordering, biographies, and available personal links; `#` links are omitted.
- Three research features: Mosaic, SpecAgent, QK-Restore.
- Seven Python tests passed: compact introductions and original logo, current content/output counts, bibliography parsing
  and ordering, metadata/navigation, images/local links/anchors, deployment
  boundaries, and rejection of unsafe URLs/output paths.
- Chromium browser checks passed on all three pages at **1440, 1024, 768, 390,
  and 320px** viewport widths.
- No horizontal overflow, failed image loads, browser JavaScript errors, or
  HTTP errors during the browser run.
- Search empty-state, title search, year filtering, and BibTeX expansion passed.
- All three pages remain readable with JavaScript disabled.
- Reduced-motion preference disables smooth scrolling.
- Desktop and mobile screenshots were visually inspected. Regression screenshots
  can be regenerated in `test-results/` with `tests/browser_check.py`.
- Active images are resized/optimized. Unused theme/example resources and legacy
  code have been deleted; the previous version remains in Git history.
- The homepage uses code-native diagrams and no
  image/CDN/font/framework dependencies.
- `git diff --check` passed.

Future maintenance tests validate current data rather than requiring the initial
40/22/3 counts, so content can be added or removed without changing test fixtures.
Migration-day preservation was separately compared against the original source
before deleting the temporary legacy archive.

## Not performed

- No commit or push.
- No modification of Git remote, GitHub Pages settings, DNS, or hostname.
- No claim that the live site has already been updated.
- No full re-certification of every external paper, code, or member URL; local
  references and the three supplied project pages were checked.
- No claim of exhaustive accessibility certification; structural labels, keyboard
  focus, skip navigation, reduced-motion, and no-JavaScript behavior are included.
