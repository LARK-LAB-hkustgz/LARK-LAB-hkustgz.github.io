# 博客维护指南

## 当前结构

网站沿用 Jekyll / al-folio 的原生 `posts`，不需要另建前端项目、手工维护文章列表或增加博客插件。

```text
_pages/blog.md                          # 导航入口 /blog/
_layouts/blog.liquid                    # 按日期倒序自动生成文章列表
_layouts/post.liquid                    # 正文、日期、作者、语言切换
_includes/blog_languages.liquid         # 可复用的语言切换
_posts/YYYY-MM-DD-slug.md               # 每篇博客的主语言版本
_pages/blog/slug-zh.md                  # 可选的中文译文，不重复进入 posts
assets/blog/slug/                       # 每篇文章独立的图片/附件目录
_templates/blog-post.md                 # 新文章模板（不发布）
_blog_examples/                         # 原主题示例（保留参考，不发布）
```

首篇文章来自 `tool_schema_blog.zip`，保留原文、作者 Yinhong Liu、日期 2026-10-16、代码、引用及三张原图：

- 英文：`/blog/2026/tool-schema-bias/`
- 中文：`/blog/2026/tool-schema-bias/zh/`

网站默认语言为英文，因此英文为主文章，中文可由文章列表或正文切换访问。中文使用普通页面，不会导致博客列表、RSS、年份/标签/分类归档中同一文章出现两次。归档指向主文章，译文共用它的标签。

## 新增一篇博客

1. 复制模板：

   ```bash
   cp _templates/blog-post.md _posts/2026-10-20-your-slug.md
   mkdir -p assets/blog/your-slug
   ```

2. 修改文件顶部的 YAML：
   - `title`、`date`、`author`、`description`：标题、实际发布日期（含时区）、作者、列表摘要。
   - 文件名使用 `YYYY-MM-DD-slug.md`，日期与 `date` 保持一致。
   - `permalink`：使用 `/blog/YYYY/slug/`，发布后尽量不要修改，避免旧链接失效。
   - `lang`：英文 `en`，中文 `zh-CN`；单独发布中文文章也可直接放在 `_posts/`。
   - `tags`、`categories`：使用数组。标签建议沿用小写英文和短横线，避免同义标签碎片化。
   - `cover`、`cover_alt`：可选；没有封面就删掉这两项，列表会显示纯文字卡片。
   - `related_posts`：首篇设为 `false`；积累文章后可删除此项以使用主题的相关文章功能。
   - **模板默认 `published: false`，正式发布时删除此项或改为 `true`。**
3. 将 Markdown 正文放在 YAML 后面。不要重复写一级标题或作者日期行，布局会统一显示。
4. 图片和附件放入 `assets/blog/your-slug/`，使用站点路径和 `relative_url`：

   ```liquid
   ![有意义的图片说明]({{ '/assets/blog/your-slug/figure.png' | relative_url }})
   ```

   原稿中的 `assets/foo.png`、`results/foo.png` 等相对地址必须改写，否则浏览器会从正文 URL 下寻找图片而产生 404。路径区分大小写，建议避免空格。不要引用本机绝对路径。

5. 单语言文章删除整个 `translations` 块即可。无需修改 `_pages/blog.md`，列表、原生 RSS 和归档会随构建更新。

## 添加中文或其他语言版本

1. 将译文放入 `_pages/blog/your-slug-zh.md`，不要再向 `_posts/` 添加一个译文副本。
2. 复制主文章 YAML，保留日期、作者、标签、分类，修改：

   ```yaml
   layout: post
   permalink: /blog/2026/your-slug/zh/
   lang: zh-CN
   blog_post: true
   nav: false
   ```

   `title`、`description` 可以翻译；`blog_post: true` 启用博客专用样式和返回链接，`nav: false` 避免译文出现在主导航。

3. **两个文件都**填写相同的 `translations` 数组，包含各语言的 `lang`、`label`、`url`。只有译文已准备发布时才添加入口，避免悬空链接。
4. 多语言版本共用图片目录；布局自动设置页面语言、语言切换和 `hreflang`。
5. 草稿期两份文件都设 `published: false`，发布时同时移除。译文是普通页面，不受 Jekyll 的未来 post 日期过滤影响，不要依靠 `date` 隐藏译文。

## 接收下一份 ZIP

1. 先检查压缩包，确定主文、译文、作者、日期和配图；不要把整个压缩包直接放进站点发布目录。
2. 选择唯一的 `slug`，按上述目录结构放置 Markdown 和资源。
3. 将原稿标题和作者日期迁移到 YAML，将所有本地图片/附件引用改为 `relative_url`；保留正文内容和引用。
4. 如有 HTML 图片，添加 `alt` 和 `loading="lazy"`。博客样式会限制图片宽度，代码块支持横向滚动。
5. 运行下面的检查，通过后提交源文件与资源即可。

根目录的 `*.zip` 已从 Jekyll 输出排除；原始压缩包可自行归档，不是部署依赖。当前没有加入自动解包工具，因为未来压缩包未必采用相同格式，自动推断作者、日期或语言可能导致误发布。

## 本地预览与发布检查

按仓库 `INSTALL.md` 安装 Ruby / Bundler 和依赖后：

```bash
bundle install
bundle exec jekyll serve
```

打开本地 `/blog/` 并检查：

- 新文章只显示一张卡片，标题、作者、日期、摘要和封面正确。
- 正文没有重复标题，所有图片、代码块、引用正常。
- 每个语言切换、返回博客、年份、标签、分类链接能访问。
- 手机宽度下图片不溢出，宽代码块可以横向滚动；检查明暗两种主题。

构建与自动检查：

```bash
bundle exec jekyll build
pip3 install -r requirements.txt
python3 bin/check-blog.py
python3 bin/check-blog.py --site _site
```

第一条 Python 命令检查源文件元数据、译文互链、资源是否存在与模板示例隔离；第二条额外检查生成页面、文章列表、图片和内部链接。部署工作流会在 Jekyll 构建后运行同一检查。

注意：

- 未来日期的主文章默认不会发布；预览未来文章可用 `bundle exec jekyll serve --future`，仅预览草稿可加 `--unpublished`。
- 默认部署流程是 `.github/workflows/deploy.yml`；新增 Markdown、图片、布局会触发现有构建。
- 原主题示例已迁移到 `_blog_examples/`，默认外部演示文章源已关闭，避免混入实验室博客和 RSS。
- 当前列表一次展示所有主文章。文章积累较多后可在 `_layouts/blog.liquid` 中接入仓库已安装的分页插件；不要只开启配置而不修改列表循环。
