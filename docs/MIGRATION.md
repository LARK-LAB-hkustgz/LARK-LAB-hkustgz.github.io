# Redesign notes

## Inspected sources

- Current repository: `_config.yml`, `Gemfile`, `.github/workflows/deploy.yml`,
  `_pages/profiles.md`, `_layouts/profiles.liquid`, `_pages/publications.md`,
  `_bibliography/papers.bib`, and relevant static assets.
- Mosaic repository: `https://github.com/LARK-AI-Lab/Mosaic`, branch `master`,
  inspected commit `7cf7fbd184b84215a6e937b6a3e712428f2a0ccb`.
  Its project website lives in `docs/`, not in the model-training code at the root.
  Read `docs/index.html`, `docs/static/css/style.css`, `docs/static/js/main.js`,
  `docs/static/data/paper.json`, and `docs/README.md`.
- Rendered HTML of `https://lark-ai-lab.github.io/specagent.github.io/` and
  `https://lark-ai-lab.github.io/QK-Restore/`, including project descriptions
  and resource links.

These project pages use warm paper, system sans-serif body copy, editorial serif
headings, fine borders, and earth-tone diagrams. Their article-style storytelling
is appropriate for the lab's research landing page, but the full article lengths
are not. The new homepage therefore presents compact, original visual summaries
and sends readers to each complete project page.

## Architecture decision

Replace the active al-folio stack with Python/Jinja static generation:

- No Ruby gem chain, Bootstrap, theme-specific plugins, or runtime content fetches.
- Research and member content are maintained independently in YAML.
- Publication content stays in BibTeX to avoid losing the existing editing workflow.
- Shared templates keep all three pages visually consistent.
- Existing branch-based `gh-pages` deployment is retained.
- Only explicitly generated pages and `assets/` are published.

The former site has many template examples, blog infrastructure, third-party
libraries, and workflows tied to Jekyll. These files were inspected during
migration and then removed from the working tree at the owner's request.
The pre-migration version remains recoverable from Git history.
Only the new deployment workflow remains in `.github/workflows/`.

## Content policy

- All existing publication entries and member records are retained.
- Existing venue/year claims are preserved as supplied, not independently re-certified.
- The three featured projects use concise mechanism-level descriptions, not
  newly invented quantitative results.
- Mosaic and SpecAgent are featured on Research but are not silently added as new
  bibliography records. Add their confirmed paper metadata to
  `content/publications.bib` when appropriate.
- Publication preview images and member photos used by the new site are retained
  in the new asset directories. Unused example images are removed.
- Homepage diagrams are code-native original illustrations, not screenshots of
  the source pages.
- The navigation, footer, and favicon use the original bird/network LARK logo
  originally stored in `assets/img/lark.jpg`, now in `assets/images/lark.png`.
  The neutral textured background is locally removed and composited onto the
  site's warm-white `#faf9f5`; the blue/cyan mark and geometry are preserved.
- Page introductions are compact: Research shows only the lab name and affiliation,
  followed directly by the projects; Publications and Members start directly with their content.
  The latter two retain screen-reader-only page headings.

## Deployment boundaries

The public hostname remains `https://lark-lab-hkustgz.github.io/`.
The Git remote is not changed. Publishing still requires pushing the changes to
the repository that serves this hostname. A local checkout alone does not update
the deployed website, and this migration does not change GitHub settings remotely.
