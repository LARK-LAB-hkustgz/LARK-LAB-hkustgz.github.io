"""Fast build/content checks; no browser or network required."""
from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
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
        if tag == "a" and attrs.get("aria-current") == "page":
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
        pages = [("index.html", "/"), ("blog/index.html", "/blog/"), ("publications/index.html", "/publications/"), ("members/index.html", "/members/")]
        pages.extend((variant["path"].lstrip("/") + "index.html", "/blog/")
                     for post in build.load_blogs() for variant in post["languages"])
        for filename, current in pages:
            html = (ROOT / "_site" / filename).read_text()
            parser = PageParser()
            parser.feed(html)
            self.assertEqual(1, parser.headings, filename)
            self.assertEqual([current], parser.current, filename)
            self.assertEqual(len(parser.ids), len(set(parser.ids)), filename)
            canonical_path = "/" if filename == "index.html" else "/" + filename.removesuffix("index.html")
            self.assertIn('href="https://lark-lab-hkustgz.github.io' + canonical_path + '"', html)
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
        self.assertIn(build.read_yaml("site.yml")["description"], research)
        self.assertNotIn('<p class="affiliation">', research)
        for filename in ("publications/index.html", "members/index.html"):
            html = (ROOT / "_site" / filename).read_text()
            self.assertNotIn('class="page-hero', html)
            self.assertIn('<h1 class="visually-hidden">', html)
            self.assertIn('src="/assets/images/lark.png?v=', html)
        self.assertEqual({"width": 1024, "height": 1024}, build.image_dimensions("/assets/images/lark.png"))

    def test_original_images_and_loading_policy(self):
        for folder, suffix in (("members", ".jpg"), ("publications", ".png")):
            self.assertFalse(list((ROOT / "assets/images" / folder).glob("*.webp")))
            for image in (ROOT / "assets/images" / folder).glob("*" + suffix):
                generated = ROOT / "_site" / image.relative_to(ROOT)
                self.assertEqual(image.read_bytes(), generated.read_bytes(), image.name)
        for filename in ("members/index.html", "publications/index.html"):
            parser = PageParser()
            parser.feed((ROOT / "_site" / filename).read_text())
            content_images = [img for img in parser.images if img.get("class") != "lab-mark"]
            self.assertEqual(1, sum(img.get("fetchpriority") == "high" for img in content_images))
            for image in content_images:
                url = urlparse(image["src"])
                self.assertIn("v=", url.query)
                self.assertEqual("async", image["decoding"])
                dimensions = build.image_dimensions(url.path)
                self.assertEqual(dimensions["width"], int(image["width"]))
                self.assertEqual(dimensions["height"], int(image["height"]))
                if image.get("fetchpriority") != "high":
                    self.assertEqual("lazy", image["loading"])
        self.assertTrue((ROOT / "_site/sw.js").is_file())
        self.assertEqual((ROOT / "templates/image-worker.js").read_bytes(), (ROOT / "_site/sw.js").read_bytes())

    def test_blog_posts_languages_and_assets(self):
        posts = build.load_blogs()
        listing = (ROOT / "_site/blog/index.html").read_text()
        self.assertEqual(len(posts), listing.count('class="blog-card"'))
        self.assertEqual(sorted((p["date"] for p in posts), reverse=True), [p["date"] for p in posts])
        sitemap = (ROOT / "_site/sitemap.xml").read_text()
        for post in posts:
            self.assertIn(post["title"], listing)
            for variant in post["languages"]:
                html = (ROOT / "_site" / variant["path"].lstrip("/") / "index.html").read_text()
                self.assertIn(f'<html lang="{variant["code"]}">', html)
                self.assertIn('property="og:type" content="article"', html)
                self.assertIn(post["author"], html)
                self.assertNotIn("Date: Oct", html)
                self.assertIn(post["path"], listing)
                self.assertIn(variant["path"], sitemap)
                self.assertIn('class="blog-body"', html)
                for other in post["languages"]:
                    self.assertIn(f'href="{other["path"]}"', html)
        english = (ROOT / "_site/blog/tool-schema-bias/index.html").read_text()
        self.assertEqual(3, english.count("<figure>"))
        self.assertEqual(3, english.count("<figcaption>"))
        self.assertIn("language-python", english)
        self.assertIn("language-bibtex", english)
        self.assertIn("https://github.com/williamLyh/ToolSchemaSpace", english)
        chinese = (ROOT / "_site/blog/tool-schema-bias/zh-cn/index.html").read_text()
        self.assertIn("同一个动作，不同的说法", chinese)

    def test_multiple_blog_posts_and_validation(self):
        data = build.read_yaml("blog.yml")
        second = dict(data[0], slug="another-post", title="Another post", date="2026-10-17")
        with patch.object(build, "read_yaml", return_value=[data[0], second]):
            posts = build.load_blogs()
            self.assertEqual(["another-post", data[0]["slug"]], [p["slug"] for p in posts])
            self.assertEqual("/blog/another-post/", posts[0]["path"])
            self.assertIn("/blog/another-post/assets/blog_action_space.png", build.render_blog(posts[0], posts[0]["languages"][0]))
        for changes in ({"slug": "../escape"}, {"source": "../../"}, {"cover": "../site.yml"},
                        {"date": "invalid"}, {"languages": []}):
            with self.subTest(changes=changes), patch.object(build, "read_yaml", return_value=[dict(data[0], **changes)]):
                with self.assertRaises(ValueError):
                    build.load_blogs()
        with patch.object(build, "read_yaml", return_value=[data[0], dict(data[0])]):
            with self.assertRaises(ValueError):
                build.load_blogs()

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
