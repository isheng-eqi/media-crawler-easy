# -*- coding: utf-8 -*-
"""
MediaCrawler 环境搭建检查器
逐项检测依赖，以进度条形式展示，自动修复已知问题
"""
import subprocess, sys, os, shutil, time, json, re

CRAWLED_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.join(CRAWLED_DIR, "MediaCrawler")

# Force UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

STATUS_OK = "[OK]"
STATUS_FAIL = "[FAIL]"
STATUS_FIX = "[FIX]"
STATUS_SKIP = "[SKIP]"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

results = {"checks": [], "fixes_applied": [], "warnings": [], "chrome_available": False, "cdp_available": False, "use_uv": False, "all_ready": False}

def cprint(color, text):
    print(f"{color}{text}{RESET}")

def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=PROJECT_DIR)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return -1, "timeout"
    except Exception as e:
        return -1, str(e)

def check_step(name):
    print(f"  {CYAN}[....]{RESET} {name}")
    results["checks"].append({"name": name, "status": "running"})

def step_ok():
    results["checks"][-1]["status"] = "ok"
    # Overwrite the [....] line
    name = results["checks"][-1]["name"]
    print(f"  {GREEN}[ OK ]{RESET} {name}")

def step_fail(reason):
    results["checks"][-1]["status"] = "fail"
    results["checks"][-1]["reason"] = reason
    name = results["checks"][-1]["name"]
    print(f"  {RED}[FAIL]{RESET} {name}  -- {reason}")

def step_fix(fix_msg):
    results["checks"][-1]["status"] = "fixed"
    results["fixes_applied"].append(fix_msg)
    name = results["checks"][-1]["name"]
    print(f"  {YELLOW}[FIX]{RESET} {name}  -- {fix_msg}")

def step_skip(msg):
    results["checks"][-1]["status"] = "skipped"
    results["warnings"].append(msg)
    name = results["checks"][-1]["name"]
    print(f"  {YELLOW}[SKIP]{RESET} {name}  -- {msg}")

# ── Main ──
print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
print(f"{BOLD}{CYAN}  MediaCrawler Environment Setup{RESET}")
print(f"{BOLD}{CYAN}{'='*60}{RESET}")
print(f"\n  Project: {PROJECT_DIR}")
print(f"  Python:  {sys.version.split()[0]}")
print()

# 1. Python 版本
check_step("检查 Python 版本")
py_ver = sys.version_info
if py_ver >= (3, 13):
    step_ok()
    results["py313"] = True
elif py_ver >= (3, 10):
    step_ok()
    results["py313"] = False
else:
    step_fail(f"Python {sys.version} 太旧，需要 >= 3.10")
    sys.exit(1)

# 2. Git
check_step("检查 Git")
code, out = run("git --version")
if code == 0:
    step_ok()
    results["git_available"] = True
else:
    step_fail("Git 未安装。请从 https://git-scm.com 下载安装")
    results["git_available"] = False

# 3. pip 版本
check_step("检查 pip 版本 (>= 23.0)")
code, out = run(f"{sys.executable} -m pip --version")
if code == 0:
    m = re.search(r'pip\s+(\d+)\.', out)
    pip_ver = int(m.group(1)) if m else 0
    if pip_ver >= 23:
        step_ok()
    else:
        step_fix(f"pip {pip_ver} 太旧，升级中...")
        code2, _ = run(f"{sys.executable} -m pip install --upgrade pip --quiet")
        if code2 == 0:
            step_ok()
        else:
            step_fail("pip 升级失败，部分依赖可能安装出错")
else:
    step_fail("pip 不可用")

# 4. 磁盘空间
check_step("检查磁盘空间 (≥ 2GB 可用)")
try:
    import shutil
    free = shutil.disk_usage(PROJECT_DIR).free / (1024**3)
    if free >= 2:
        step_ok()
        results["disk_free_gb"] = round(free, 1)
    elif free >= 0.5:
        step_skip(f"仅 {free:.1f} GB，Chrome 用户数据可能占满")
        results["disk_free_gb"] = round(free, 1)
    else:
        step_fail(f"仅 {free:.2f} GB，无法运行")
except:
    step_skip("无法检测")

# 5. 网络连通
check_step("检查 PyPI 网络连通性")
code, out = run(f"{sys.executable} -m pip install --dry-run pip --quiet 2>&1", timeout=15)
if code == 0:
    step_ok()
    results["network_ok"] = True
else:
    step_skip("PyPI 可能不通，将自动尝试国内镜像")
    results["network_ok"] = False

# 6. Node.js
check_step("检查 Node.js（报告验证需要）")
code, out = run("node --version")
if code == 0:
    step_ok()
    results["node_available"] = True
else:
    step_skip("Node.js 未安装，报告 JS 无法自动验证。推荐从 https://nodejs.org 安装")
    results["node_available"] = False

# 7. uv
check_step("检查 uv 包管理器")
code, out = run("uv --version")
if code == 0:
    step_ok()
    results["use_uv"] = True
else:
    step_skip("未安装 uv，回退 pip")
    results["use_uv"] = False

# 3. pip + requirements
check_step("检查核心依赖 (playwright/aiohttp/pandas)")
code, out = run(f"{sys.executable} -c \"import playwright; import aiohttp; import pandas; print('OK')\"")
if code == 0:
    step_ok()
else:
    step_fix("安装依赖中...")
    code, out = run(f"{sys.executable} -m pip install playwright aiohttp pandas openpyxl tenacity --quiet")
    if code == 0:
        step_ok()
    else:
        step_fail(out[-200:])

# 4. playwright 浏览器
check_step("检查 Playwright 浏览器")
code, out = run(f"{sys.executable} -m playwright install --dry-run chromium 2>&1")
if "chromium" in out.lower() or code == 0:
    code2, _ = run(f"{sys.executable} -c \"from playwright.sync_api import sync_playwright; print('OK')\"")
    if code2 == 0:
        step_ok()
    else:
        step_skip("Playwright 可用（CDP模式可跳过浏览器下载）")
else:
    step_skip("将使用 CDP 模式（连接本地Chrome，无需下载）")

# 5. SQLAlchemy
check_step("检查 SQLAlchemy >= 2.0")
code, out = run(f"{sys.executable} -c \"import sqlalchemy; v=sqlalchemy.__version__; print(v); assert int(v.split('.')[0])>=2\"")
if code == 0:
    step_ok()
else:
    step_fix("升级 SQLAlchemy 到 2.x...")
    code, _ = run(f"{sys.executable} -m pip install \"sqlalchemy>=2.0\" --quiet")
    if code == 0:
        step_ok()
    else:
        step_fail("升级失败")

# 6. redis
check_step("检查 redis 模块")
code, out = run(f"{sys.executable} -c \"import redis; print('OK')\"")
if code == 0:
    step_ok()
else:
    step_fix("安装 redis...")
    code, _ = run(f"{sys.executable} -m pip install redis --quiet")
    if code == 0:
        step_ok()
    else:
        step_fail("安装失败")

# 7. Python 3.13 pyreadline 兼容
if results.get("py313"):
    check_step("Python 3.13 兼容性（pyreadline）")
    code, out = run(f"{sys.executable} -c \"import collections; collections.Callable\"")
    if code == 0:
        step_ok()
    else:
        step_fix("卸载 pyreadline，安装 pyreadline3...")
        run(f"{sys.executable} -m pip uninstall pyreadline -y --quiet")
        code2, _ = run(f"{sys.executable} -m pip install pyreadline3 --quiet")
        if code2 == 0:
            step_ok()
        else:
            step_fail("修复失败")

# 8. 数据库异步驱动
check_step("检查异步数据库驱动")
code, out = run(f"{sys.executable} -c \"import aiomysql; import motor; import aiosqlite; import aiofiles; print('OK')\"")
if code == 0:
    step_ok()
else:
    step_fix("安装异步驱动...")
    code, _ = run(f"{sys.executable} -m pip install aiomysql motor pymongo aiosqlite aiofiles asyncmy --quiet")
    if code == 0:
        step_ok()
    else:
        step_fail("部分驱动安装失败")

# 9. 剩余轻量依赖
check_step("检查剩余依赖 (httpx/fastapi/pydantic/uvicorn)")
code, out = run(f"{sys.executable} -c \"import httpx; import fastapi; import pydantic; import uvicorn; print('OK')\"")
if code == 0:
    step_ok()
else:
    step_fix("安装中...")
    code, _ = run(f"{sys.executable} -m pip install httpx pydantic fastapi uvicorn python-dotenv parsel pyexecjs pyhumps cryptography alembic xhshow pytest pytest-asyncio --quiet")
    if code == 0:
        step_ok()
    else:
        step_fail("部分依赖未安装，可能不影响核心爬取")

# 10. matplotlib（可选）
check_step("检查 matplotlib（词云需要）")
code, out = run(f"{sys.executable} -c \"import matplotlib; print('OK')\"")
if code == 0:
    step_ok()
else:
    step_skip("matplotlib 不可用，词云功能将跳过")

# 11. Chrome
check_step("检测 Chrome 浏览器")
chrome_paths = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
]
chrome_found = None
for p in chrome_paths:
    if os.path.exists(p):
        chrome_found = p
        break
if chrome_found:
    step_ok()
    results["chrome_available"] = True
    results["chrome_path"] = chrome_found
else:
    # Edge fallback (Windows only)
    edge_found = None
    if sys.platform == 'win32':
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        ]
        for ep in edge_paths:
            if os.path.exists(ep):
                edge_found = ep
                break
    if edge_found:
        step_skip("未找到 Chrome，但检测到 Edge，将自动使用 Edge")
        results["chrome_available"] = True
        results["chrome_path"] = edge_found
        results["edge_fallback"] = True
    else:
        step_fail("未找到 Chrome 或 Edge")
        results["chrome_available"] = False
        results["warnings"].append("Chrome/Edge 均未安装。请安装任意一个，或手动指定浏览器路径到 config/base_config.py CUSTOM_BROWSER_PATH")

# 12. CDP
if chrome_found:
    check_step("检查 Chrome 远程调试 (CDP)")
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:9222/json/version")
        resp = urllib.request.urlopen(req, timeout=3)
        data = json.loads(resp.read())
        step_ok()
        results["cdp_available"] = True
    except:
        step_skip("CDP 未开启，将自动启动浏览器")
        results["cdp_available"] = False
else:
    check_step("CDP 模式")
    step_skip("需要 Chrome")

# 13. Windows 专项
if sys.platform == 'win32':
    check_step("Windows: UTF-8 编码模式 (PEP 540)")
    try:
        code, out = run(f"{sys.executable} -c \"import sys; print(sys.getdefaultencoding())\"")
        if 'utf-8' in out.lower():
            step_ok()
        else:
            step_skip(f"默认编码为 {out.strip()}，中文路径可能乱码。建议在 Windows 设置中开启 'Beta: Use Unicode UTF-8'")
    except:
        step_skip("无法检测")

    check_step("Windows: 长路径支持")
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem")
        val, _ = winreg.QueryValueEx(key, "LongPathsEnabled")
        if val == 1:
            step_ok()
        else:
            step_skip("长路径未启用。如遇到 'path too long' 错误，请运行: reg add \"HKLM\\SYSTEM\\CurrentControlSet\\Control\\FileSystem\" /v LongPathsEnabled /t REG_DWORD /d 1 /f")
        winreg.CloseKey(key)
    except:
        step_skip("无法检测（如非管理员权限可忽略）")

# 14. 最终导入验证
check_step("最终验证：导入 BilibiliCrawler")
code, out = run(f"{sys.executable} -c \"from media_platform.bilibili import BilibiliCrawler; print('Import OK')\"")
if code == 0:
    step_ok()
    results["all_ready"] = True
else:
    step_fail(f"导入失败:\n{out[-300:]}")
    results["all_ready"] = False

# ── 输出摘要 ──
print(f"\n{BOLD}{CYAN}{'─'*50}{RESET}")
ok_count = sum(1 for c in results["checks"] if c["status"] == "ok")
fail_count = sum(1 for c in results["checks"] if c["status"] == "fail")
fix_count = len(results["fixes_applied"])
warn_count = len(results["warnings"])
print(f"  {GREEN}{ok_count} passed{RESET}  {RED}{fail_count} failed{RESET}  {YELLOW}{fix_count} fixed{RESET}  {YELLOW}{warn_count} warnings{RESET}")
print(f"  Git: {'YES' if results.get('git_available') else 'MISSING'}  |  Node: {'YES' if results.get('node_available') else 'NO'}")
print(f"  Chrome: {'YES' if results['chrome_available'] else 'MISSING'}{' (Edge fallback)' if results.get('edge_fallback') else ''}  |  CDP: {'READY' if results['cdp_available'] else 'WILL LAUNCH'}  |  uv: {'YES' if results['use_uv'] else 'pip'}")
print(f"  Disk: {results.get('disk_free_gb', '?')} GB  |  Network: {'OK' if results.get('network_ok') else 'RESTRICTED'}")
print(f"  Crawler ready: {GREEN + 'YES' if results['all_ready'] else RED + 'NO'}{RESET}")
print(f"{BOLD}{CYAN}{'─'*50}{RESET}")

# 分级警告
if results["warnings"]:
    print(f"\n  {YELLOW}[!] Warnings:{RESET}")
    for w in results["warnings"]:
        print(f"    - {w}")
    print()

# 阻断性错误
if fail_count > 0:
    print(f"  {RED}[!!] 以下检查未通过，请先修复再继续：{RESET}")
    for c in results["checks"]:
        if c["status"] == "fail":
            print(f"    ✗ {c['name']}")
            if c.get("reason"):
                print(f"      → {c['reason']}")
    print()

# 保存检查结果供后续使用
check_result_path = os.path.join(PROJECT_DIR, ".env_check_result.json")
with open(check_result_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

sys.exit(0 if results["all_ready"] else 1)
