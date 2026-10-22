"""Optional browser smoke test. Run after serving _site on localhost:8000.

pip install playwright
python -m playwright install chromium
python tests/browser_check.py
"""
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build

BASE = "http://127.0.0.1:8000"
SCREENSHOTS = Path("test-results")


def run():
    SCREENSHOTS.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=["--no-sandbox"])
        errors = []
        publication_count = None
        pages = [("/", "research"), ("/blog/", "blog"), ("/publications/", "publications"), ("/members/", "members")]
        pages.extend((variant["path"], f"blog-{post['slug']}-{variant['code'].lower()}")
                     for post in build.load_blogs() for variant in post["languages"])
        for width in (1440, 1024, 768, 390, 320):
            context = browser.new_context(viewport={"width": width, "height": 1000}, device_scale_factor=1)
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("response", lambda response: errors.append(f"{response.status}: {response.url}") if response.status >= 400 else None)
            for path, name in pages:
                page.goto(BASE + path, wait_until="networkidle")
                assert page.locator("h1").count() == 1
                assert page.locator('[aria-current="page"]').get_attribute("href") == ("/blog/" if name.startswith("blog") else path)
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), f"Overflow: {name} at {width}"
                # Trigger lazy loading throughout the page before inspecting all images.
                page.evaluate("async () => { for(let y=0;y<document.body.scrollHeight;y+=700) { window.scrollTo(0,y); await new Promise(r=>setTimeout(r,50)); } }")
                page.locator("img").evaluate_all("async images => { for (const img of images) { img.loading = 'eager'; } await Promise.all(images.map(img => img.decode().catch(() => {}))); }")
                broken = page.locator("img").evaluate_all("(images) => images.filter(img => !img.complete || img.naturalWidth === 0).map(img => img.src)")
                assert not broken, broken
                page.evaluate("window.scrollTo(0,0)")
                if width in (1440, 390):
                    page.screenshot(path=str(SCREENSHOTS / f"{name}-{width}.png"), full_page=True)
                if name == "publications":
                    publication_count = page.locator(".publication").count()
                    page.locator("#publication-search").fill("zzzz-no-match")
                    assert page.locator(".no-results").is_visible()
                    assert page.locator(".publication:visible").count() == 0
                    first_title = page.locator(".publication h3").first.inner_text()
                    page.locator("#publication-search").fill(first_title)
                    assert page.locator(".publication:visible").count() >= 1
                    page.locator("#publication-search").fill("")
                    selected_year = page.locator("#publication-year option").last.get_attribute("value")
                    page.locator("#publication-year").select_option(selected_year)
                    assert page.locator(".publication:visible").count() > 0
                    assert page.locator(".publication:visible").evaluate_all("(papers) => papers.every(p => p.dataset.year === document.querySelector('#publication-year').value)")
                    page.locator("#publication-year").select_option("all")
                    paper = page.locator(".publication").first
                    paper.locator("summary").last.click()
                    assert paper.locator("pre").is_visible()
                    assert paper.locator("pre").inner_text().startswith("@")
                    page.locator("#publication-search").fill("")
            page.goto(BASE + "/blog/")
            page.locator(".blog-card h2 a").first.click()
            assert page.locator(".blog-body").is_visible()
            if page.locator(".blog-languages").count():
                page.locator(".blog-languages a").last.click()
                assert page.locator(".blog-body").is_visible()
            page.locator(".blog-post-footer a").click()
            assert page.url == BASE + "/blog/"
            context.close()
        context = browser.new_context(java_script_enabled=False, viewport={"width": 390, "height": 844})
        page = context.new_page()
        for path, name in pages:
            page.goto(BASE + path)
            assert page.locator("main").is_visible()
            assert page.locator("h1").count() == 1
            if path == "/publications/":
                assert page.locator(".publication").count() == publication_count
                assert page.locator("[data-search-tools]").is_hidden()
        context.close()
        # Original images are cached byte-for-byte and can be reused without network.
        context = browser.new_context()
        page = context.new_page()
        page.goto(BASE + "/members/", wait_until="networkidle")
        page.evaluate("""async () => {
          await navigator.serviceWorker.ready;
          if (!navigator.serviceWorker.controller) {
            await new Promise(resolve => navigator.serviceWorker.addEventListener('controllerchange', resolve, {once: true}));
          }
        }""")
        page.reload(wait_until="networkidle")
        source = page.locator(".member-photo img").first.get_attribute("src")
        page.wait_for_function("""async src => {
          return Boolean(await caches.match(new Request(new URL(src, location.origin)), {cacheName: 'lark-original-images-v1'}));
        }""", arg=source)
        context.set_offline(True)
        assert page.evaluate("""async src => {
          const response = await fetch(src);
          return response.ok && (await response.blob()).size > 0;
        }""", source)
        context.set_offline(False)
        context.close()
        context = browser.new_context(reduced_motion="reduce")
        page = context.new_page()
        page.goto(BASE)
        assert page.evaluate("getComputedStyle(document.documentElement).scrollBehavior") == "auto"
        context.close()
        browser.close()
        assert not errors, errors
    print(f"Browser checks passed: {len(pages)} pages × 5 viewport widths; original-image cache/offline reuse; blog navigation/languages; search/year/BibTeX; no-JS; reduced motion; no broken images or JS errors.")


if __name__ == "__main__":
    run()
