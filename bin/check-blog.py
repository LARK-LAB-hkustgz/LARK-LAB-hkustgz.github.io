#!/usr/bin/env python3
"""Validate blog metadata and optionally the Jekyll build. Requires PyYAML."""

import argparse
import datetime as dt
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
ERRORS = []


def check(condition, message):
    if not condition:
        ERRORS.append(message)


def front_matter(path):
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise ValueError(f"{path}: missing YAML front matter")
    return yaml.safe_load(parts[1]), parts[2]


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.links = []
        self.images = []
        self.lang = None
        self.headings = 0
        self.cards = 0
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.lang = attrs.get("lang")
        if tag == "h1":
            self.headings += 1
        if tag == "article" and "blog-card" in attrs.get("class", "").split():
            self.cards += 1
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
        if tag == "img":
            self.images.append(attrs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, help="Also check a built _site directory")
    args = parser.parse_args()
    config = yaml.safe_load((ROOT / "_config.yml").read_text())
    sources = sorted((ROOT / "_posts").glob("*.md"))
    sources += sorted((ROOT / "_pages/blog").glob("*.md"))
    documents = {}
    posts = []
    now = dt.datetime.now(dt.timezone.utc)

    for source in sources:
        data, body = front_matter(source)
        label = str(source.relative_to(ROOT))
        for field in ("title", "date", "author", "description", "permalink", "lang"):
            check(bool(data.get(field)), f"{label}: missing {field}")
        url = data.get("permalink", "")
        check(url.startswith("/blog/") and url.endswith("/"), f"{label}: invalid permalink")
        check(url not in documents, f"{label}: duplicate permalink {url}")
        is_post = source.parent.name == "_posts"
        date = data.get("date")
        if isinstance(date, str):
            try:
                date = dt.datetime.fromisoformat(date)
            except ValueError:
                pass
        if isinstance(date, dt.datetime):
            date = date if date.tzinfo else date.replace(tzinfo=dt.timezone.utc)
        elif isinstance(date, dt.date):
            date = dt.datetime.combine(date, dt.time(), dt.timezone.utc)
        else:
            check(False, f"{label}: date must be a YAML date or timestamp")
            date = now
        published = data.get("published", True) and (not is_post or date <= now)
        documents[url] = (data, published)
        if is_post:
            check(source.name.startswith(date.strftime("%Y-%m-%d")), f"{label}: filename/date mismatch")
            if published:
                posts.append(url)
        else:
            check(data.get("blog_post") is True, f"{label}: translation needs blog_post: true")
            check(data.get("nav") is False, f"{label}: translation needs nav: false")

        assets = re.findall(r"""['"](/assets/blog/[^'"]+)['"]\s*\|\s*relative_url""", body)
        if data.get("cover"):
            assets.append(data["cover"])
            check(bool(data.get("cover_alt")), f"{label}: cover needs cover_alt")
        for asset in assets:
            check((ROOT / asset.lstrip("/")).is_file(), f"{label}: missing asset {asset}")
        check(not re.search(r'src=["\'](?:assets|results)/', body), f"{label}: ZIP-relative image path")
        check(not re.search(r"^# ", body, re.MULTILINE), f"{label}: duplicate H1 in body")

    for url, (data, published) in documents.items():
        translations = data.get("translations", [])
        languages = [item.get("lang") for item in translations]
        check(len(languages) == len(set(languages)), f"{url}: duplicate translation language")
        if translations:
            check(any(t.get("url") == url and t.get("lang") == data["lang"] for t in translations),
                  f"{url}: translation list must include this page")
        for item in translations:
            target = item.get("url")
            check(bool(item.get("label")), f"{url}: missing translation label")
            check(target in documents, f"{url}: missing translation {target}")
            if target in documents:
                other, other_published = documents[target]
                check(other.get("lang") == item.get("lang"), f"{url}: translation language mismatch")
                check(other.get("translations") == translations, f"{url}: translations must be reciprocal")
                check(not published or other_published, f"{url}: links to an unpublished translation")

    for excluded in ("_blog_examples/", "_templates/", "*.zip", "BLOGGING.md"):
        check(excluded in config.get("exclude", []), f"_config.yml: must exclude {excluded}")

    if args.site:
        site = args.site.resolve()
        baseurl = (config.get("baseurl") or "").rstrip("/")
        # --site checks normal production builds, not --future / --unpublished previews.
        for url in ["/blog/"] + [url for url, (_, public) in documents.items() if public]:
            output = site / url.lstrip("/") / "index.html"
            check(output.is_file(), f"Missing built page: {url}")
            if not output.is_file():
                continue
            page = Page(output)
            check(page.headings == 1, f"{url}: expected exactly one H1")
            if url == "/blog/":
                check(page.cards == len(posts), f"{url}: expected {len(posts)} article cards, got {page.cards}")
                for post in posts:
                    check(baseurl + post in page.links, f"Blog index missing {post}")
            else:
                check(page.lang == documents[url][0]["lang"], f"{url}: wrong HTML language")
            for image in page.images:
                check(bool(image.get("alt")), f"{url}: image missing alt text")
            for link in page.links + [image.get("src", "") for image in page.images]:
                parsed = urlsplit(link)
                if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
                    continue
                path = unquote(parsed.path)
                if baseurl and path.startswith(baseurl + "/"):
                    path = path[len(baseurl):]
                target = site / path.lstrip("/")
                check(target.is_file() or (target / "index.html").is_file(), f"{url}: broken internal URL {link}")
        check(not list(site.glob("*.zip")), "ZIP archives leaked into the build")
        check(not (site / "_blog_examples").exists(), "Theme examples leaked into the build")

    if ERRORS:
        print("\n".join(f"ERROR: {message}" for message in ERRORS), file=sys.stderr)
        return 1
    print(f"Blog checks passed: {len(posts)} published primary post(s), {len(documents)} source document(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
