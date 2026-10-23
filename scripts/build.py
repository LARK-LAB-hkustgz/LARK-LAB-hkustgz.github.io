#!/usr/bin/env python3
"""Build the lab site from YAML/BibTeX and autoescaped Jinja templates."""
from __future__ import annotations

import argparse
import hashlib
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from html import escape as html_escape
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
from urllib.parse import unquote, urlparse
from xml.sax.saxutils import escape

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
import yaml
from markdown_it import MarkdownIt
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"


def read_yaml(name):
    return yaml.safe_load((CONTENT / name).read_text(encoding="utf-8"))


def plain_tex(text):
    """Readable plain text for common formatting in our existing bibliography."""
    text = re.sub(r"\\(?:textbf|textit|textsc|emph|mathrm|textrm)\s*\{([^{}]*)\}", r"\1", text)
    text = text.replace(r"\%", "%").replace(r"\&", "&").replace(r"\_", "_")
    text = text.replace(r"\LaTeX", "LaTeX").replace(r"\text", "")
    text = re.sub(r"\\[a-zA-Z]+\s*", "", text)
    return re.sub(r"\s+", " ", text.replace("{", "").replace("}", "")).strip()


def safe_url(value):
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme not in ("https", "http") or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError(f"Invalid external URL: {value}")
    return value


def asset_path(folder, filename):
    if not filename:
        return None
    base = (ROOT / "assets" / "images" / folder).resolve()
    target = (base / filename).resolve()
    if not target.is_relative_to(base) or not target.is_file():
        raise ValueError(f"Missing or invalid image: {folder}/{filename}")
    return "/" + target.relative_to(ROOT).as_posix()


def image_url(value):
    """Content-versioned URL; original image bytes are never transformed."""
    target = ROOT / value.lstrip("/")
    if not target.is_file():
        raise ValueError(f"Missing image: {value}")
    digest = hashlib.sha256(target.read_bytes()).hexdigest()[:16]
    return value + "?v=" + digest


def image_dimensions(value):
    with Image.open(ROOT / value.lstrip("/")) as image:
        return dict(width=image.width, height=image.height)


def load_members():
    groups = read_yaml("members.yml")
    ids = set()
    for group in groups:
        if group["id"] in ids:
            raise ValueError(f"Duplicate member group: {group['id']}")
        ids.add(group["id"])
        for person in group["people"]:
            person["image"] = asset_path("members", person.get("image"))
            person["dimensions"] = image_dimensions(person["image"]) if person["image"] else None
            person["link"] = safe_url(person.get("link"))
            person["initials"] = "".join(part[0] for part in person["name"].split()[:2])
            person.setdefault("more_info", "")
    return groups


def load_research():
    projects = read_yaml("research.yml")
    ids = set()
    for project in projects:
        if not re.fullmatch(r"[a-z0-9-]+", project["id"]) or project["id"] in ids:
            raise ValueError(f"Invalid or duplicate project id: {project['id']}")
        ids.add(project["id"])
        if project["theme"] not in ("terracotta", "sage", "slate"):
            raise ValueError(f"Unknown theme: {project['theme']}")
        project["project_url"] = safe_url(project["project_url"])
        project.setdefault("links", [])
        for link in project["links"]:
            link["url"] = safe_url(link["url"])
        project.setdefault("image", None)
        if project["image"]:
            image = project["image"]
            target = (ROOT / image.lstrip("/")).resolve()
            if not image.startswith("/assets/") or not target.is_relative_to(ROOT / "assets") or not target.is_file():
                raise ValueError(f"Missing or invalid research image: {image}")
            if not project.get("image_alt"):
                raise ValueError("Research images require image_alt")
        elif project.get("diagram") not in ("mosaic", "specagent", "qk"):
            raise ValueError("Use a supported diagram, or supply image and image_alt")
    return projects


def load_publications():
    raw = (CONTENT / "publications.bib").read_text(encoding="utf-8")
    raw = re.sub(r"\A\s*---\s*\n---\s*\n", "", raw)
    parser = BibTexParser(common_strings=True)
    parser.ignore_nonstandard_types = False
    entries = bibtexparser.loads(raw, parser=parser).entries
    if not entries:
        raise ValueError("The bibliography contains no publications")
    expected = re.findall(r"(?mi)^\s*@(?!comment\b|string\b|preamble\b)[a-z]+\s*\{", raw)
    if len(entries) != len(expected):
        raise ValueError("Not all BibTeX entries could be parsed")
    groups = defaultdict(list)
    ids = set()
    for entry in entries:
        if entry["ID"] in ids:
            raise ValueError(f"Duplicate publication ID: {entry['ID']}")
        ids.add(entry["ID"])
        year = int(entry["year"])
        title = plain_tex(entry["title"])
        authors = [plain_tex(a) for a in re.split(r"\s+and\s+", entry["author"])]
        links = []
        for field, label in (("html", "Paper"), ("pdf", "PDF"), ("code", "Code"), ("website", "Project"), ("doi", "DOI")):
            value = entry.get(field)
            if value:
                url = ("https://doi.org/" + value) if field == "doi" and not value.startswith("http") else value
                links.append({"label": label, "url": safe_url(url)})
        venue = plain_tex(entry.get("booktitle") or entry.get("journal") or entry.get("abbr", "Preprint"))
        # Export scholarly fields only, not display-only al-folio metadata.
        fields = {"ID", "ENTRYTYPE", "title", "author", "year", "booktitle", "journal", "volume", "number", "pages", "publisher", "doi", "url", "eprint", "archiveprefix", "primaryclass"}
        db = BibDatabase()
        db.entries = [{k: v for k, v in entry.items() if k in fields}]
        writer = BibTexWriter()
        writer.indent = "  "
        preview = asset_path("publications", entry.get("preview"))
        groups[year].append({
            "id": entry["ID"], "year": year, "title": title, "authors": authors,
            "abbr": entry.get("abbr", "Paper"), "venue": venue, "links": links,
            "primary_url": links[0]["url"] if links else "",
            "preview": preview,
            "dimensions": image_dimensions(preview) if preview else None,
            "abstract": plain_tex(entry.get("abstract", "")),
            "annotation": plain_tex(entry.get("annotation", "")),
            "search": f"{title} {' '.join(authors)} {venue} {year}".lower(),
            "bibtex": bibtexparser.dumps(db, writer).strip(),
        })
    return [{"year": y, "papers": groups[y]} for y in sorted(groups, reverse=True)]


def blog_resource(post, value):
    """Resolve local article resources without allowing paths outside its folder."""
    parsed = urlparse(value)
    target = (post["source_dir"] / unquote(parsed.path)).resolve()
    if parsed.scheme or parsed.netloc or not target.is_relative_to(post["source_dir"]) or not target.is_file():
        raise ValueError(f"Missing or invalid blog resource: {value}")
    url = post["path"] + target.relative_to(post["source_dir"]).as_posix()
    if parsed.query:
        url += "?" + parsed.query
    if parsed.fragment:
        url += "#" + parsed.fragment
    return target, url


def blog_image(post, value):
    target, url = blog_resource(post, value)
    with Image.open(target) as image:
        width, height = image.size
    digest = hashlib.sha256(target.read_bytes()).hexdigest()[:16]
    url += ("&" if "?" in url else "?") + "v=" + digest
    return dict(url=url, width=width, height=height)


def load_blogs():
    posts = deepcopy(read_yaml("blog.yml") or [])
    slugs = set()
    base = (CONTENT / "blog").resolve()
    for post in posts:
        slug = post["slug"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or slug in slugs:
            raise ValueError(f"Invalid or duplicate blog slug: {slug}")
        slugs.add(slug)
        source = (base / post["source"]).resolve()
        if not source.is_relative_to(base) or not source.is_dir():
            raise ValueError(f"Missing or invalid blog source: {post['source']}")
        post["source_dir"] = source
        post["path"] = f"/blog/{slug}/"
        date = datetime.strptime(str(post["date"]), "%Y-%m-%d").date()
        post["date"] = date.isoformat()
        post["date_label"] = date.strftime("%b %d, %Y")
        for field in ("title", "author", "summary"):
            if not post.get(field):
                raise ValueError(f"Blog requires {field}: {slug}")
        post.setdefault("category", "From the lab")
        post["cover"] = blog_image(post, post["cover"]) if post.get("cover") else None
        if post["cover"] and not post.get("cover_alt"):
            raise ValueError(f"Blog cover requires cover_alt: {slug}")
        codes = set()
        if not post.get("languages"):
            raise ValueError(f"Blog requires at least one language: {slug}")
        for index, variant in enumerate(post["languages"]):
            code = variant["code"]
            if not re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z]{2,4})?", code) or code in codes:
                raise ValueError(f"Invalid or duplicate blog language: {code}")
            codes.add(code)
            target, _ = blog_resource(post, variant["file"])
            if target.suffix != ".md":
                raise ValueError("Blog source must be Markdown")
            variant["source_file"] = target
            variant["path"] = post["path"] if index == 0 else post["path"] + code.lower() + "/"
    return sorted(posts, key=lambda post: post["date"], reverse=True)


class BlogHTML(HTMLParser):
    """Keep trusted author HTML, but validate/rebase images and resource links."""
    def __init__(self, post):
        super().__init__(convert_charrefs=False)
        self.post = post
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "img":
            image = blog_image(self.post, attrs.get("src", ""))
            display_width = attrs.get("width", "")
            attrs.update(src=image["url"], width=str(image["width"]), height=str(image["height"]))
            attrs.setdefault("alt", self.post["title"] + " — research figure")
            attrs["loading"] = "lazy"
            attrs["decoding"] = "async"
            attrs["fetchpriority"] = "low"
            if re.fullmatch(r"\d+%", display_width):
                attrs["style"] = f"width: {display_width};"
        elif tag == "a" and attrs.get("href"):
            parsed = urlparse(attrs["href"])
            if parsed.scheme or parsed.netloc:
                safe_url(attrs["href"])
                attrs["rel"] = "noopener noreferrer"
            elif parsed.path and not parsed.path.startswith("/"):
                _, attrs["href"] = blog_resource(self.post, attrs["href"])
        text = "".join(f' {key}="{html_escape(value, quote=True)}"' if value is not None else f" {key}" for key, value in attrs.items())
        self.parts.append(f"<{tag}{text}>")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        self.parts.append(data)

    def handle_entityref(self, name):
        self.parts.append(f"&{name};")

    def handle_charref(self, name):
        self.parts.append(f"&#{name};")


def render_blog(post, variant):
    text = variant["source_file"].read_text(encoding="utf-8")
    # Title, date and author are supplied by the article template.
    text = re.sub(r"\A\s*# [^\n]+\n", "", text, count=1)
    text = re.sub(r"\A\s*Date:[^\n]+\n", "", text, count=1)
    # Turn the supplied centered figure/caption pairs into semantic figures.
    text = re.sub(
        r'<p align="center">(<img [^>]+>)</p>\s*<p align="center"><sub>(.*?)</sub></p>',
        r"<figure>\1<figcaption>\2</figcaption></figure>", text, flags=re.S)
    markdown = MarkdownIt("commonmark", {"html": True}).enable("table")
    tokens = markdown.parse(text)
    ids = set()
    for index, token in enumerate(tokens):
        if token.type == "heading_open":
            if token.tag == "h1":
                raise ValueError(f"Blog body must use headings at level 2 or below: {post['slug']}")
            heading = tokens[index + 1].content
            anchor = re.sub(r"[^\w-]+", "-", heading.lower()).strip("-") or "section"
            anchor = "section-" + anchor
            unique = anchor
            number = 2
            while unique in ids:
                unique = f"{anchor}-{number}"
                number += 1
            ids.add(unique)
            token.attrSet("id", unique)
    parser = BlogHTML(post)
    parser.feed(markdown.renderer.render(tokens, markdown.options, {}))
    parser.close()
    return "".join(parser.parts)


def build(destination=None):
    output = Path(destination).resolve() if destination else ROOT / "_site"
    # Never let a mistyped --output delete source or unrelated directories.
    if output != ROOT / "_site":
        raise ValueError("Build output must be this repository's _site/ directory")
    site = read_yaml("site.yml")
    site["url"] = safe_url(site["url"]).rstrip("/")
    site["github"] = safe_url(site["github"])
    research, members, publications = load_research(), load_members(), load_publications()
    blogs = load_blogs()
    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(["html", "xml"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["image_url"] = image_url
    context = dict(site=site, research=research, members=members, publications=publications, blogs=blogs,
                   publication_count=sum(len(g["papers"]) for g in publications), year=datetime.now().year)
    pages = [
        ("research", "/", "Research", site["description"], "index.html"),
        ("blog", "/blog/", "Blog", "Ideas and experiments from " + site["full_name"], "blog/index.html"),
        ("publications", "/publications/", "Publications", "Publications from " + site["full_name"], "publications/index.html"),
        ("members", "/members/", "Members", "Meet the people at " + site["full_name"], "members/index.html"),
        ("404", "/404.html", "Page not found", site["description"], "404.html"),
    ]
    # Render/validate everything before replacing an existing successful build.
    rendered = {}
    for key, path, title, description, filename in pages:
        rendered[filename] = env.get_template(key + ".html").render(
            **context, key=key, path=path, title=title, description=description)
    blog_paths = []
    for post in blogs:
        for variant in post["languages"]:
            path = variant["path"]
            blog_paths.append(path)
            rendered[path.lstrip("/") + "index.html"] = env.get_template("blog_post.html").render(
                **context, key="blog", path=path, title=post["title"], description=post["summary"],
                post=post, language=variant["code"], og_type="article", body=render_blog(post, variant))
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(ROOT / "assets", output / "assets")
    (output / "sw.js").write_text((ROOT / "templates/image-worker.js").read_text(encoding="utf-8"),
                                  encoding="utf-8")
    for post in blogs:
        shutil.copytree(post["source_dir"], output / post["path"].lstrip("/"),
                        ignore=shutil.ignore_patterns("*.md"))
    for filename, html in rendered.items():
        target = output / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
    (output / ".nojekyll").touch()
    # Keep useful old URLs without deploying legacy theme/demo pages.
    for old, new in (("profiles", "/members/"), ("about", "/"), ("research", "/")):
        folder = output / old
        folder.mkdir()
        (folder / "index.html").write_text(
            f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<meta http-equiv="refresh" content="0;url={new}"><link rel="canonical" href="{site["url"]}{new}">'
            f'<title>Redirect · LARK Lab</title></head><body><a href="{new}">Continue to LARK Lab</a></body></html>',
            encoding="utf-8")
    (output / "robots.txt").write_text(f'User-agent: *\nAllow: /\nSitemap: {site["url"]}/sitemap.xml\n', encoding="utf-8")
    urls = [site["url"] + p[1] for p in pages if p[0] != "404"]
    urls.extend(site["url"] + path for path in blog_paths)
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    sitemap += "".join(f"<url><loc>{escape(url)}</loc></url>" for url in urls) + "</urlset>\n"
    (output / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    shutil.copy2(CONTENT / "publications.bib", output / "publications" / "publications.bib")
    print(f"Built {len(research)} projects, {len(blogs)} blog posts, {context['publication_count']} publications, "
          f"{sum(len(g['people']) for g in members)} members → {output}")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output", type=Path, help="Output directory (only _site is allowed)")
    build(cli.parse_args().output)
