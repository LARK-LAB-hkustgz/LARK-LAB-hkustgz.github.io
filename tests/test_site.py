"""Fast build/content checks; no browser or network required."""
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import sys
import unittest
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.images = []
        self.current = []
        self.headings = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "h1":
            self.headings += 1
        if tag == "a" and "aria-current" in attrs:
            self.current.append(attrs["href"])
        if tag == "img":
            self.images.append(attrs)
        for attr in ("href", "src"):
            if attr in attrs:
                self.links.append(attrs[attr])


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build.build()

    def test_content_data_and_generated_counts(self):
        # Validate current content rather than freezing migration-day counts:
        # adding/removing projects or members must not require editing tests.
        groups = build.load_members()
        self.assertTrue(groups)
        members_html = (ROOT / "_site/members/index.html").read_text()
        self.assertEqual(sum(len(g["people"]) for g in groups), members_html.count('class="member-card"'))
        for group in groups:
            self.assertTrue(group["title"])
            for person in group["people"]:
                self.assertTrue(person["name"])
        research = build.load_research()
        self.assertTrue(research)
        research_html = (ROOT / "_site/index.html").read_text()
        self.assertEqual(len(research), research_html.count('class="research-feature '))

    def test_publications_preserved_and_sorted(self):
        groups = build.load_publications()
        years = [g["year"] for g in groups]
        self.assertEqual(years, sorted(years, reverse=True))
        current = (ROOT / "content/publications.bib").read_text()
        expected = build.re.findall(r"(?mi)^\s*@(?!comment\b|string\b|preamble\b)[a-z]+\s*\{", current)
        self.assertEqual(len(expected), sum(len(g["papers"]) for g in groups))

    def test_primary_pages_metadata_and_navigation(self):
        for filename, current in (("index.html", "/"), ("publications/index.html", "/publications/"), ("members/index.html", "/members/")):
            html = (ROOT / "_site" / filename).read_text()
            parser = PageParser()
            parser.feed(html)
            self.assertEqual(1, parser.headings, filename)
            self.assertEqual([current], parser.current, filename)
            self.assertEqual(len(parser.ids), len(set(parser.ids)), filename)
            self.assertIn('https://lark-lab-hkustgz.github.io' + current, html)
            self.assertNotIn("Powered by", html)
            self.assertNotIn("al-folio", html)
            for image in parser.images:
                self.assertTrue(image.get("alt"), filename)
                self.assertTrue(image.get("width"), filename)
                self.assertTrue(image.get("height"), filename)

    def test_local_links_and_fragments(self):
        output = ROOT / "_site"
        for file in output.rglob("*.html"):
            parser = PageParser()
            parser.feed(file.read_text())
            for link in parser.links:
                parsed = urlparse(link)
                if parsed.scheme or parsed.netloc:
                    continue
                target = output / unquote(parsed.path).lstrip("/") if parsed.path.startswith("/") else file.parent / unquote(parsed.path)
                if not parsed.path:
                    target = file
                elif target.is_dir():
                    target = target / "index.html"
                self.assertTrue(target.is_file(), f"{file.relative_to(output)} → {link}")
                if parsed.fragment and target.suffix == ".html":
                    linked = PageParser()
                    linked.feed(target.read_text())
                    self.assertIn(parsed.fragment, linked.ids, f"{file} → {link}")

    def test_compact_page_introductions_and_original_logo(self):
        research = (ROOT / "_site/index.html").read_text()
        self.assertNotIn("Learning to act.", research)
        self.assertNotIn("Explore our research", research)
        self.assertNotIn("From learning to reliable action.", research)
        self.assertNotIn("Three perspectives", research)
        self.assertNotIn("The wider picture", research)
        self.assertNotIn("More ideas. The same curiosity.", research)
        self.assertNotIn('class="research-closing', research)
        self.assertNotIn('class="hero-description"', research)
        self.assertIn('class="lab-name"', research)
        for filename in ("publications/index.html", "members/index.html"):
            html = (ROOT / "_site" / filename).read_text()
            self.assertNotIn('class="page-hero', html)
            self.assertIn('<h1 class="visually-hidden">', html)
            self.assertIn('src="/assets/images/lark.png"', html)
        self.assertEqual(
            hashlib.sha256((ROOT / "assets/images/lark.png").read_bytes()).hexdigest(),
            "834b3e9bae92fd0a89e5a872aedca7818815e3d401eae04546b44e3ffea888dc",
        )

    def test_output_is_minimal(self):
        output = ROOT / "_site"
        self.assertTrue((output / ".nojekyll").is_file())
        self.assertTrue((output / "404.html").is_file())
        self.assertTrue((output / "sitemap.xml").is_file())
        self.assertTrue((output / "publications/publications.bib").is_file())
        for folder in ("legacy", "_posts", "_pages", "node_modules", "templates", "content"):
            self.assertFalse((output / folder).exists())

    def test_unsafe_output_and_urls_rejected(self):
        with self.assertRaises(ValueError):
            build.build(ROOT)
        with self.assertRaises(ValueError):
            build.safe_url("javascript:alert(1)")
        with self.assertRaises(ValueError):
            build.asset_path("members", "../favicon.svg")


if __name__ == "__main__":
    unittest.main()
