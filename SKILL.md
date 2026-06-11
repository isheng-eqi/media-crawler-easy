---
name: media-crawler-easy
description: >-
  多平台社媒评论数据采集爬虫工具。覆盖 B站(bilibili)/小红书/抖音(douyin)/快手/微博/贴吧/知乎 7大平台。
  当用户提到"爬评论""采集评论""下载评论""爬数据""批量采集""舆情分析""评论分析""社媒数据"
  "抓取评论""导出评论""获取评论""视频评论""帖子评论""笔记评论""UP主评论""博主评论"
  "关键词搜索爬取""社交媒体数据采集""爬虫""数据爬取""评论数据""用户评论"时自动触发。
  支持按关键词搜索、指定链接采集、创作者主页三种模式。生成交互式 HTML 报告 + 数据文件。
when_to_use: >-
  用户想从社交媒体平台获取评论数据、做舆情分析、竞品调研、内容分析、或批量导出评论时。
  典型触发："帮我爬XX的评论""把这个视频的评论爬下来""搜索XX关键词的讨论"
  "这个UP主最近视频的评论都爬了""采集一下小红书关于XX的笔记评论"
version: "2.2"
dependencies: "python>=3.10, git, chrome-or-edge, node>=16"
---

# MediaCrawler 多平台采集助手

基于 [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) (⭐30K+)，7 大平台社媒数据采集。

## ⚠️ 关键约束

1. **严格 3 轮问答**，每轮只问一个问题，不提前列出所有选项。
2. **参考材料仅排查时查阅**，不主动展示给用户。
3. **每次不超过 4 个选项**。
4. **环境检测只报结论**："X 项通过，Y 项修复，可以继续"。

## 执行流程

```
① 配置问答（3轮）→ ② 环境搭建 → ③ 写入配置 →
④ 执行爬取 → ⑤ 生成报告+验证 → ⑥ 汇报+清理
```

---

## ① 配置问答（严格 3 轮，不可合并）

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

## ② 环境搭建

```bash
cd ~/.claude/skills/media-crawler-easy && python scripts/env_setup.py
```

报结论即可。有 FAIL 先修再继续；不确定错误查 `references/env-troubleshooting.md`。

---

## ③ 写入配置

Edit 修改 `config/base_config.py`：`PLATFORM`, `KEYWORDS`, `CRAWLER_TYPE`, `CRAWLER_MAX_NOTES_COUNT`, `CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES`, `ENABLE_GET_SUB_COMMENTS`, `ENABLE_GET_WORDCLOUD`, `CRAWLER_MAX_SLEEP_SEC`。

平台专属 config 只改当前平台对应的文件（如抖音改 `dy_config.py`）。

**重要**：`AUTO_CLOSE_BROWSER` 默认为 `False`（保持浏览器打开）。**永远不要把它改成 True**——否则爬虫结束/出错时 Chrome 会立刻关闭，用户看不到状态。

---

## ④ 执行爬取

用 `run_in_background: true` 启动，每 20-30 秒检查日志。

```bash
cd ~/.claude/skills/media-crawler-easy/MediaCrawler
python main.py --platform <代码> --lt qrcode --type <模式>
```

### 登录阶段监控（关键！容易卡住）

每轮检查日志时按以下信号判断状态：

| 日志关键词 | 状态 | Agent 动作 |
|-----------|------|-----------|
| `Waiting for scan code login` | ✅ 二维码已弹出，等待扫码 | 提醒用户扫码 |
| `Login successful` | ✅ 登录成功 | 继续监控采集进度 |
| `Begin login Bilibili` | ⚠️ 进入登录流程 | 再等 20-30s 看是否有后续信号 |
| 启动后 60s 无任何新日志 | 🔴 可能卡在 XPath/反爬 | 提醒用户看 Chrome 窗口：是否显示验证码/滑块？ |
| `login failed` / `have not found qrcode` | 🔴 登录失败 | 查 `references/known-issues.md` 登录章节 |

**如果 60 秒内 Chrome 打开了 bilibili.com 但没有弹出二维码**，大概率是：
- Bilibili 弹了滑块验证（需要用户手动滑一下）
- 页面结构变了，XPath 选择器失效

让用户在 Chrome 里**手动点击右上角"登录"按钮**，脚本会自动检测到二维码并继续。

---

## ⑤ 生成报告 + 验证

**必须严格有序：生成（不打开）→ JS 语法验证 → 通过后自动打开。**

### 步骤 1：生成（不自动打开）

```bash
cd ~/.claude/skills/media-crawler-easy
python scripts/generate_report.py --no-open
```

报告生成器扫描 `data/` 下**所有平台、所有爬取类型、所有日期**的 CSV（CSV 为空自动从 JSONL 转），按"平台 + 爬取类型 + 日期"分 tab。同一份报告持续累积，每次覆盖 Desktop 同名文件。

### 步骤 2：JS 语法验证

```bash
python -c "
import re, tempfile, subprocess, os, glob
reports = sorted(glob.glob('MediaCrawler/data/reports/report*.html'))
report = reports[-1]
with open(report, 'r', encoding='utf-8') as f:
    scripts = re.findall(r'<script>(.*?)</script>', f.read(), re.DOTALL)
path = os.path.join(tempfile.gettempdir(), 'report_check.js')
with open(path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(scripts))
r = subprocess.run(['node', '--check', path], capture_output=True, text=True)
if r.returncode == 0:
    print('[PASS] JS syntax verification passed')
else:
    print('[FAIL] JS syntax error:')
    print(r.stderr.strip())
    exit(1)
"
```

不通过则修复 `generate_report.py` 模板，回到步骤 1。

### 步骤 3：验证通过，重新生成并自动打开

```bash
cd ~/.claude/skills/media-crawler-easy
python scripts/generate_report.py
```

不带 `--no-open`，生成后**自动在浏览器打开报告**。合并步骤 2 和 3：两个命令依次执行，中间由验证阻断。

---

## ⑥ 汇报 + 清理

汇报采集量、数据路径、报告路径。AskUserQuestion 询问：清理临时文件？选项：「清理（推荐）」/「暂不清理」。选清理执行：

```bash
python ~/.claude/skills/media-crawler-easy/scripts/cleanup.py
```

---

## 参考文件

| 文件 | 何时查阅 |
|------|---------|
| `references/env-troubleshooting.md` | 环境检测 FAIL 或安装问题 |
| `references/known-issues.md` | 爬取报错或报告异常 |
| `references/code-rules.md` | 修改 generate_report.py 模板时（必读） |
| `README.md` | 用户问"能干嘛""需要什么条件" |
