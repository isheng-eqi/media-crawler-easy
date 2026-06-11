# 代码生成守则（修改 generate_report.py 必读）

`generate_report.py` 用 Python f-string 生成 JavaScript 代码，涉及三层嵌套：`Python → JavaScript → HTML 属性`。

## 规则 1：window 属性用点号，禁止方括号

```python
# ❌ 错误：window['PAGE_{p["key"]}'] → window['PAGE_douyin']
#   单引号在 JS 字符串 '...' 内部截断，导致 SyntaxError
onclick="window['PAGE_{p["key"]}']=..."

# ✅ 正确：window.PAGE_{p["key"]} → window.PAGE_douyin
#   不含引号，任何 JS 字符串内都安全
onclick="window.PAGE_{p["key"]}=..."
```

## 规则 2：改模板必须跑 Node 语法检查

```bash
python -c "
import re, tempfile, subprocess, os, glob

reports = sorted(glob.glob('MediaCrawler/data/reports/report*.html'))
if not reports: raise SystemExit('找不到报告文件')
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
    raise SystemExit(1)
"
```

通过后才算报告生成成功。**必须先跑 `--no-open` 生成再验证，通过后才打开报告。**

## 规则 3：f-string 花括号排查

生成的 HTML 中出现裸露的 `{` 或 `}`，说明 f-string 的 `{{`/`}}` 转义有遗漏。搜索 `function(` 手动检查花括号配对。
