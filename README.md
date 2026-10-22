# LARK Lab website

实验室主页：**https://lark-lab-hkustgz.github.io/**。域名不变。

这是一个轻量静态站点，不再依赖 Jekyll、al-folio、Ruby、Bootstrap 或 npm。
设计参考 Mosaic 项目页的暖白背景、衬线标题、陶土色与鼠尾草绿，四个栏目共用同一套视觉系统：

1. **Research** `/`：简短实验室介绍 + Mosaic、SpecAgent、QK-Restore 研究展示。
2. **Blog** `/blog/`：按日期降序展示博客，每篇文章有独立页面，支持 Markdown、配图、代码和多语言版本。
3. **Publications** `/publications/`：保留原论文数据，按年份降序排列，支持搜索、年份筛选、Abstract 和 BibTeX。
4. **Members** `/members/`：保留 Faculty / PhD / MPhil / Interns、RAs、Visitors 分组及原成员资料。

## 本地预览

需要 Python 3.10 或以上：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/build.py
python -m http.server 8000 --directory _site
```

访问 `http://localhost:8000`。修改内容后重新运行 `python scripts/build.py`，然后刷新浏览器。
生成文件位于 `_site/`，请不要直接编辑它们，也不需要提交它们。

## 文件布局

```text
content/
  site.yml                # 实验室名称、域名、简介、导航、GitHub
  research.yml            # 首页研究项目、排序、文案、链接
  blog.yml                # 博客列表、日期、作者、封面及语言版本
  blog/                   # 各篇博客的 Markdown 与本地配图
  publications.bib        # 论文数据（延续原有 BibTeX 维护方式）
  members.yml             # 成员分组、顺序、照片、个人主页
templates/
  base.html               # 公共 head、导航和页脚
  research.html           # Research 首页
  blog.html               # Blog 列表
  blog_post.html          # 博客文章及语言切换
  publications.html       # Publications 布局
  members.html            # Members 布局
  diagrams/               # 三个项目的 HTML/CSS 视觉摘要
assets/
  css/site.css            # 全站样式及响应式布局
  js/site.js              # 渐进增强：搜索、年份筛选、复制 BibTeX
  images/members/         # 历史原始 JPG 成员照片，不缩放、不重新编码
  images/publications/    # 历史原始 PNG 论文预览图片，不缩放、不重新编码
  images/lark.png         # 压缩前的 1024px 标识，导航、页脚及 favicon 共用
  images/social-preview.png
scripts/build.py          # 验证数据 + 生成静态页面
tests/test_site.py        # 内容保留、页面结构、站内链接检查
.github/workflows/deploy.yml
```

旧主题、示例页面及不再使用的资源已从工作目录删除。
如需查阅或恢复迁移前的版本，请使用 Git 历史。博客使用当前轻量静态构建，不依赖旧主题。

## 更新 Research

编辑 `content/research.yml`。列表中的先后顺序就是首页展示顺序。
每个项目的 `id` 必须唯一，仅包含小写字母、数字、连字符。

已有三种色调：`terracotta`、`sage`、`slate`。
已有三种视觉摘要：`mosaic`、`specagent`、`qk`，适用于对应项目。
新增不同项目，最简单的方法是提供预览图：

```yaml
- id: new-project
  name: New Project
  category: Agent reasoning
  theme: sage
  title: A concise research headline.
  paper_title: The full paper title
  summary: A short paragraph explaining the question and the contribution.
  takeaway: One clear sentence about the core idea.
  image: /assets/images/research/new-project.png
  image_alt: Describe the research figure for screen readers.
  project_url: https://example.com/project/
  links:
    - label: Paper
      url: https://example.com/paper
    - label: Code
      url: https://github.com/example/project
```

把图片放入对应路径。也可以在 `templates/diagrams/` 新建自定义 HTML 摘要，
并在 `scripts/build.py` 的支持列表中注册。
项目的 `title` 支持 `<br>`，仅用于可信的站点维护内容。
其他文案默认自动 HTML 转义，不要添加 HTML 标签。
首页描述只概括研究机制，不新增未经核实的性能数字或会议接收信息。

## 更新 Blog

首页介绍在 `content/site.yml` 的 `description` 中维护，导航顺序为 Research / Blog / Publications / Members。

新增博客时，把 Markdown 和图片放在 `content/blog/<目录名>/`，再向 `content/blog.yml` 添加一条记录：

```yaml
- slug: new-article
  title: Your article title
  date: "2026-10-20"
  author: Author Name
  category: Agentic AI
  summary: A short summary for the blog listing.
  source: new-article
  cover: assets/overview.png
  cover_alt: Describe the cover image.
  languages:
    - code: en
      label: English
      file: blog_en.md
    - code: zh-CN
      label: 中文
      file: blog.md
```

- `slug` 必须唯一，使用小写字母、数字和连字符；文章链接为 `/blog/<slug>/`。
- 按 `date` 自动降序；不要依靠列表顺序表示发布日期。
- `source` 相对于 `content/blog/`；`file`、`cover` 和正文配图路径相对于这篇文章的目录。
- 第一种语言是默认版本，其他版本位于 `/blog/<slug>/<语言代码小写>/`。只有一种语言时不显示切换。
- `cover`、`cover_alt` 可一起省略；语言版本可只提供一个。
- 正文使用 Markdown，支持代码块、列表、表格和 `![说明](assets/figure.png)`。标题建议从 `##` 开始。
- 如示例正文已有首行 `# 标题` 和 `Date: ... | Author: ...`，构建时会移除，统一由 YAML 元数据展示。
- 兼容示例中的 HTML 图片和图注；图片自动补充实际宽高并校验文件路径，多语言页共享配图。
- Markdown 中的 HTML 仅适用于可信维护者内容，不要接入未经审核的用户输入。
- 当前 Tool Schema Bias 的中英文正文及三张配图已从 `tool_schema_blog/` 复制到 `content/blog/tool-schema-bias/`；后续请编辑后者，原示例目录不会被发布。

## 更新 Publications

编辑 `content/publications.bib`，延续原有格式：

```bibtex
@inproceedings{unique2026key,
  title = {Your Paper Title},
  author = {First Author and Second Author and Zhijiang Guo},
  booktitle = {Conference Name},
  year = {2026},
  abbr = {Conference},
  html = {https://example.com/paper},
  code = {https://github.com/example/code},
  website = {https://example.com/project},
  preview = {your-paper.png},
  abstract = {Your abstract.}
}
```

- `preview` 图片放入 `assets/images/publications/`，填写文件名即可。
- 同一年内保持 BibTeX 文件中的顺序；年份自动降序。
- `html` / `pdf` / `code` / `website` / `doi` 为可选资源链接。
- `annotation` 保留共同一作、通讯作者说明。
- 无 `preview` 时显示会议名占位卡；填写了不存在的图片则构建失败，防止发布坏图。
- 原有 `selected` 等旧主题字段可以保留，但不控制当前页面。
- 未自动将 Mosaic/SpecAgent 增加进论文列表；论文记录保持与迁移前一致，由你确认后补充。
- 按需展开 Abstract/BibTeX，不挤占默认论文列表。BibTeX 导出仅保留学术引用字段。
- 有无 JavaScript 都能阅读全部论文；搜索、筛选、复制属于可选增强。
- 原始论文数据可通过 `/publications/publications.bib` 下载。

## 更新 Members

编辑 `content/members.yml`，在对应分组的 `people` 下添加：

```yaml
- name: New Member
  image: new-member.jpg
  more_info: BS University (Fall 2026)
  link: https://example.com/
```

照片放入 `assets/images/members/`。没有照片时使用 `image: null`，显示姓名首字母。
没有个人主页时省略 `link`，不要填写 `#`。
分组与成员均按 YAML 顺序展示；现有成员资料未重新编写。

## 验证与发布

### 原图与加载优化

当前 23 张成员照片与 40 张论文配图已恢复为旧站的原始文件：
一般来自 `be4046b` 的 `assets/img/`，Shuangjie Fan 照片来自 `6b0ae50`。
Logo 恢复为 `df2836d` 中抠图后、缩小前的 1024 × 1024 PNG。
没有再次缩尺寸、转 WebP 或重新编码；构建按字节复制原图。博客配图同样保留原文件。

- 首张照片/论文图优先加载，其余原图使用浏览器原生延迟加载，不主动预下载整页图片。
- 图片使用 `decoding="async"`，并声明真实宽高；CSS 控制展示尺寸，而不是修改原文件。
- 每张原图 URL 都带内容 SHA-256 的版本参数：原图未改则地址不变，替换原图则自动更新地址。
- `/sw.js` 只缓存已请求的版本化图片，不缓存 HTML；后续请求同一原图可直接复用浏览器本地缓存。
- 不预缓存全部 21 MB 原图；缓存最多 128 个资源，替换图片时清理同路径的旧版本。
- Service Worker 需要 HTTPS 或 localhost。普通远程 HTTP 预览、不支持缓存或存储不足时回退正常图片请求，不影响展示。
- 禁用 JavaScript 时仍可以正常浏览所有原图，并保留浏览器原生延迟加载。

**边界：**原图体积不会凭空消失。首次访问慢网络仍需下载所看到的原图；
这套优化减少不必要下载和重复下载，不保证原图首次加载与压缩缩略图一样快。
没有依赖第三方图床、额外 CDN，也没有改变 GitHub Pages 域名或服务器配置。

```bash
python -m unittest discover -s tests -v
```

检查四个栏目及博客文章导航、多语言切换链接、当前内容与生成数量、图片、站内链接、锚点、构建安全边界。
构建不需要访问外网，前端没有 CDN、在线字体或 JS 框架依赖。

可选浏览器回归检查（先按上文启动 8000 端口预览）：

```bash
python -m pip install playwright
python -m playwright install chromium
python tests/browser_check.py
```

覆盖 1440、1024、768、390、320px 宽度下各栏目与博客文章布局、图片、博客跳转与语言切换、搜索、年份筛选、
BibTeX 展开、关闭 JavaScript 和减少动态效果设置。截图输出到忽略提交的 `test-results/`。

推送到 `main` 或 `master` 后，GitHub Actions 构建、测试并发布 `_site/` 至 `gh-pages`。
PR 只构建和测试，并提供 `lab-site` artifact，不会发布。
保留原部署方式：GitHub **Settings → Pages → Deploy from a branch → `gh-pages` / `(root)`**。
不需要新增 CNAME，也不需要修改域名；如果当前 Pages 设置与此不同，请使用上述设置。
本次修改不会自动推送或改变 GitHub 仓库设置。

旧 `/profiles/` 跳到 `/members/`，旧 `/about/`、`/research/` 跳到首页。
其他已撤下页面由新的 404 页面引导返回 Research，不会继续发布旧主题示例页面。

设计来源及替换依据见 [迁移记录](docs/MIGRATION.md)。
