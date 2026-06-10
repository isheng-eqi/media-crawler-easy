---
name: media-crawler-easy
description: >
  MediaCrawler 多平台社媒数据采集助手。支持 B站/小红书/抖音/快手/微博/贴吧/知乎。
  触发词："爬取XX评论""采集XX帖子""下载XX数据""社媒数据采集"。
  逐轮交互（每轮只问当前问题，不提前展示后续选项）→ 环境检测 → 爬取 → 报告。
---

# MediaCrawler 多平台采集助手

基于 [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) (⭐30K+)，支持 7 大平台社媒数据采集。

## ⚠️ 关键约束（违反将导致执行失败）

1. **每轮只问一个问题**。不要在第一轮列出所有平台、所有模式、所有参数。严格按 3 轮走。
2. **不要给用户看参考材料**。环境检测表、已知问题表、代码守则都在 `references/` 目录下，只在排查问题时查阅，平时不展示。
3. **不要一次给 4 个以上选项**。用简短的提问而非铺陈菜单。
4. **环境检测跑完只报结论**。"X 项通过，Y 项修复，可以继续"——不要逐项复述。

## 执行流程（6 阶段）

```
① 配置问答（3 轮）→ ② 环境搭建 → ③ 写入配置 → ④ 执行爬取 → ⑤ 生成报告+验证 → ⑥ 汇报+清理
```

---

## 阶段 ① — 配置问答（严格 3 轮，不可合并）

### 第 1 轮：只问平台

```
要爬哪个平台？
B站(bili) / 小红书(xhs) / 抖音(dy) / 快手(ks) / 微博(wb) / 贴吧(tieba) / 知乎(zhihu)
```

用户回答后再问模式：

```
用什么方式爬？
A. 关键词搜索  B. 指定链接  C. 创作者主页
```

### 第 2 轮：只问具体参数

根据第 1 轮回答：
- **选 A**：问「关键词是什么？每个关键词爬多少条？（默认20）」
- **选 B**：问「把链接发给我」
- **选 C**：问「把创作者主页链接或 UID 发给我」

### 第 3 轮：只问评论设置

```
每条内容爬多少评论？（默认30）
要楼中楼吗？（默认不要）
要词云图吗？（默认不要）
爬取间隔设几秒？（默认2秒）
```

用户回复"默认"即全部用默认值。

---

## 阶段 ② — 环境搭建

```bash
cd ~/.claude/skills/media-crawler-easy && python scripts/env_setup.py
```

输出只报告结论（X 项通过 / Y 项修复 / 有无 FAIL）。如有 FAIL 先修再继续。遇到未知错误查 `references/env-troubleshooting.md`。

---

## 阶段 ③ — 写入配置

根据阶段①回答，Edit 修改：

**`config/base_config.py`**：`PLATFORM`, `KEYWORDS`, `CRAWLER_TYPE`, `CRAWLER_MAX_NOTES_COUNT`, `CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES`, `ENABLE_GET_SUB_COMMENTS`, `ENABLE_GET_WORDCLOUD`, `CRAWLER_MAX_SLEEP_SEC`

**平台专属 config**（只改当前平台对应的文件）：
- B站 `bilibili_config.py`：`BILI_SEARCH_MODE`, `START_DAY`/`END_DAY`, `MAX_NOTES_PER_DAY`
- 抖音 `dy_config.py`：`DY_SPECIFIED_ID_LIST`
- 小红书 `xhs_config.py`：`XHS_SPECIFIED_NOTE_URL_LIST`
- 其他平台类推

---

## 阶段 ④ — 执行爬取

用 `run_in_background: true` 启动，每 20-30 秒检查日志，实时告知进度关键词（"启动浏览器""扫码登录""搜索中""采集评论""完成"）。扫码阶段超过 60 秒无变化则提醒用户去扫码。

```bash
cd ~/.claude/skills/media-crawler-easy/MediaCrawler
python main.py --platform <平台代码> --lt qrcode --type <模式>
```

---

## 阶段 ⑤ — 生成报告 + 验证

**步骤必须严格有序：先生成（不打开）→ 验证 → 通过后才打开。**

### 步骤 1：生成报告（禁止自动打开）

```bash
cd ~/.claude/skills/media-crawler-easy
python scripts/generate_report.py --focus=<平台代码> --no-open
```

`--no-open` 防止在验证前就把错误报告推给用户。

### 步骤 2：JS 语法验证

```bash
python -c "
import re, tempfile, subprocess, os, glob

# 找到最新的报告文件
reports = sorted(glob.glob('MediaCrawler/data/reports/report_*.html'))
if not reports: raise SystemExit('找不到报告文件')
report = reports[-1]

# 提取所有 <script> 内容
with open(report, 'r', encoding='utf-8') as f:
    scripts = re.findall(r'<script>(.*?)</script>', f.read(), re.DOTALL)

# 写入临时文件（Python tempfile 跨平台安全）
path = os.path.join(tempfile.gettempdir(), 'report_check.js')
with open(path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(scripts))

# 调用 node --check
r = subprocess.run(['node', '--check', path], capture_output=True, text=True)
if r.returncode == 0:
    print('✅ JS 语法验证通过')
else:
    print('❌ JS 语法错误，请检查 generate_report.py 模板：')
    print(r.stderr.strip())
    raise SystemExit(1)
"
```

用一个自包含 Python 脚本完成提取→验证，不依赖 `/tmp/` 路径，Windows/macOS/Linux 都能跑。

### 步骤 3：验证通过后再打开

```bash
# Windows
start ~/Desktop/MediaCrawler_Report_$(date +%Y-%m-%d).html
# macOS
open ~/Desktop/MediaCrawler_Report_$(date +%Y-%m-%d).html
```

如果步骤 2 不通过，修复 `generate_report.py` 后回到步骤 1 重新生成。**不要跳过验证直接打开报告。**

---

## 阶段 ⑥ — 汇报 + 清理询问

汇报：爬了多少内容、多少评论、CSV 在哪、报告在哪。

用 AskUserQuestion 问：**"数据已保存。是否清理临时文件（浏览器缓存、Python 字节码等）？数据和报告不受影响。"** 选项：「清理（推荐）」/「暂不清理」。

选清理则执行 `python ~/.claude/skills/media-crawler-easy/scripts/cleanup.py`。

---

## 参考文件

遇到问题时按需查阅（不要主动展示给用户）：

| 文件 | 何时查阅 |
|------|---------|
| `references/env-troubleshooting.md` | 环境检测报 FAIL 或用户说环境装不上 |
| `references/known-issues.md` | 爬取报错或报告异常 |
| `references/code-rules.md` | 修改 generate_report.py 模板时 |
| `README.md` | 用户问"这是什么""能干嘛""需要什么条件" |
