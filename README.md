# LARK Lab website

实验室主页：**https://lark-lab-hkustgz.github.io/**。域名不变。

这是一个轻量静态站点，不再依赖 Jekyll、al-folio、Ruby、Bootstrap 或 npm。
设计参考 Mosaic 项目页的暖白背景、衬线标题、陶土色与鼠尾草绿，三个页面共用同一套视觉系统：

1. **Research** `/`：简短实验室介绍 + Mosaic、SpecAgent、QK-Restore 研究展示。
2. **Publications** `/publications/`：保留原论文数据，按年份降序排列，支持搜索、年份筛选、Abstract 和 BibTeX。
3. **Members** `/members/`：保留 Faculty / PhD / MPhil / Interns、RAs、Visitors 分组及原成员资料。

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
  publications.bib        # 论文数据（延续原有 BibTeX 维护方式）
  members.yml             # 成员分组、顺序、照片、个人主页
templates/
  base.html               # 公共 head、导航和页脚
  research.html           # Research 首页
  publications.html       # Publications 布局
  members.html            # Members 布局
  diagrams/               # 三个项目的 HTML/CSS 视觉摘要
assets/
  css/site.css            # 全站样式及响应式布局
  js/site.js              # 渐进增强：搜索、年份筛选、复制 BibTeX
  images/members/         # WebP 成员照片
  images/publications/    # WebP 论文预览图片
  images/lark.png         # 原有标识抠图后配暖白背景，导航、页脚及 favicon 共用
  images/social-preview.png
scripts/build.py          # 验证数据 + 生成静态页面
tests/test_site.py        # 内容保留、页面结构、站内链接检查
.github/workflows/deploy.yml
```

旧主题、示例页面、博客代码及不再使用的资源已从工作目录删除。
如需查阅或恢复迁移前的版本，请使用 Git 历史。本次仅发布上述三个页面。

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
  preview = {your-paper.webp},
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
  image: new-member.webp
  more_info: BS University (Fall 2026)
  link: https://example.com/
```

照片放入 `assets/images/members/`。没有照片时使用 `image: null`，显示姓名首字母。
没有个人主页时省略 `link`，不要填写 `#`。
分组与成员均按 YAML 顺序展示；现有成员资料未重新编写。

## 验证与发布

```bash
python -m unittest discover -s tests -v
```

检查三页导航、当前内容与生成数量、图片、站内链接、锚点、构建安全边界。
构建不需要访问外网，前端没有 CDN、在线字体或 JS 框架依赖。

可选浏览器回归检查（先按上文启动 8000 端口预览）：

```bash
python -m pip install playwright
python -m playwright install chromium
python tests/browser_check.py
```

覆盖 1440、1024、768、390、320px 宽度下三页布局、图片、搜索、年份筛选、
BibTeX 展开、关闭 JavaScript 和减少动态效果设置。截图输出到忽略提交的 `test-results/`。

推送到 `main` 或 `master` 后，GitHub Actions 构建、测试并发布 `_site/` 至 `gh-pages`。
PR 只构建和测试，并提供 `lab-site` artifact，不会发布。
保留原部署方式：GitHub **Settings → Pages → Deploy from a branch → `gh-pages` / `(root)`**。
不需要新增 CNAME，也不需要修改域名；如果当前 Pages 设置与此不同，请使用上述设置。
本次修改不会自动推送或改变 GitHub 仓库设置。

旧 `/profiles/` 跳到 `/members/`，旧 `/about/`、`/research/` 跳到首页。
其他已撤下页面由新的 404 页面引导返回 Research，不会继续发布旧主题示例页面。

设计来源及替换依据见 [迁移记录](docs/MIGRATION.md)。
