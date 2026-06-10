# -*- coding: utf-8 -*-
"""
MediaCrawler 爬取后清理器
清理过程中产生的浏览器缓存、临时文件，保留数据输出
"""
import os, sys, shutil

# Force UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CRAWLED_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.join(CRAWLED_DIR, "MediaCrawler")

GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
print(f"{BOLD}{CYAN}  MediaCrawler Cleanup{RESET}")
print(f"{BOLD}{CYAN}{'='*60}{RESET}")

cleaned_items = []
total_size = 0
errors = []

def get_size(path):
    """递归计算目录大小"""
    total = 0
    try:
        if os.path.isfile(path):
            return os.path.getsize(path)
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except:
                    pass
    except:
        pass
    return total

def fmt_size(n):
    for unit in ['B','KB','MB','GB']:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"

def safe_rm(path, label):
    global total_size
    if not os.path.exists(path):
        return
    sz = get_size(path)
    try:
        if os.path.isfile(path):
            os.remove(path)
        else:
            shutil.rmtree(path, ignore_errors=True)
    except Exception as e:
        errors.append(f"{label}: {e}")
        return
    total_size += sz
    cleaned_items.append((label, path, sz))

# ── 清理目标 ──
# 1. 浏览器临时数据（CDP session 缓存）
browser_data = os.path.join(PROJECT_DIR, "browser_data")
safe_rm(browser_data, "浏览器CDP缓存")

# 2. Python 缓存 (.pyc / __pycache__)
pycache_dirs = []
for root, dirs, files in os.walk(PROJECT_DIR):
    for d in dirs:
        if d == "__pycache__":
            pycache_dirs.append(os.path.join(root, d))
for d in pycache_dirs:
    safe_rm(d, f"Python缓存 {os.path.basename(os.path.dirname(d))}")

# 3. 环境检查结果文件
env_check = os.path.join(PROJECT_DIR, ".env_check_result.json")
safe_rm(env_check, "环境检查缓存")

# 4. 空的 data 中间文件（保留 CSV/JSON 输出）
data_dir = os.path.join(PROJECT_DIR, "data")
if os.path.isdir(data_dir):
    for root, dirs, files in os.walk(data_dir):
        for f in files:
            if f.endswith(('.tmp', '.temp', '.lock')):
                fp = os.path.join(root, f)
                safe_rm(fp, f"临时文件 {f}")

# 5. 词云生成留下的字体文件（如果已生成则保留最终图片）
wordcloud_cache = os.path.join(PROJECT_DIR, "data", "bili", "wordcloud")
if os.path.isdir(wordcloud_cache):
    for f in os.listdir(wordcloud_cache):
        fp = os.path.join(wordcloud_cache, f)
        if f.endswith(('.png', '.jpg')):
            continue  # 保留词云图片
        safe_rm(fp, f"词云临时文件 {f}")

# ── 报告 ──
print(f"\n  {GREEN}已清理 {len(cleaned_items)} 项，释放 {fmt_size(total_size)}{RESET}")
for label, path, sz in cleaned_items:
    print(f"    {label}")
    print(f"      {path} ({fmt_size(sz)})")

if errors:
    print(f"\n  {YELLOW}未能清理 {len(errors)} 项:{RESET}")
    for e in errors:
        print(f"    {e}")

# 保留的数据文件
data_csv = os.path.join(PROJECT_DIR, "data", "bili", "csv")
data_json = os.path.join(PROJECT_DIR, "data", "bili", "json")
data_reports = os.path.join(PROJECT_DIR, "data", "bili", "reports")
preserved = []
for d in [data_csv, data_json, data_reports]:
    if os.path.isdir(d):
        sz = get_size(d)
        preserved.append((os.path.basename(d), sz))
    elif os.path.isfile(d):
        preserved.append((os.path.basename(d), get_size(d)))

print(f"\n  {CYAN}保留数据文件:{RESET}")
for name, sz in preserved:
    if sz > 0:
        print(f"    {name}: {fmt_size(sz)}")
    else:
        print(f"    {name}: (空)")

print(f"\n  {GREEN}清理完成{RESET}\n")
