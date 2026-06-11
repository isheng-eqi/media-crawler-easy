# 环境搭建参考资料

> 本文档是参考材料，**仅在遇到环境问题时查阅**。正常执行流程中不要向用户展示。

## 预检清单

在运行 `env_setup.py` 之前，确保以下基础条件满足：

| 分类 | 必需项 | 检查方式 | 安装方法 |
|------|--------|----------|----------|
| 🔴 必需 | Python ≥ 3.10 | `python --version` | [python.org](https://python.org)，勾选 Add to PATH |
| 🔴 必需 | Git | `git --version` | [git-scm.com](https://git-scm.com) |
| 🔴 必需 | Chrome 或 Edge | 开始菜单搜索 | Chrome: [google.com/chrome](https://google.com/chrome)；Edge: Windows 已预装 |
| 🟡 推荐 | Node.js | `node --version` | [nodejs.org](https://nodejs.org) LTS 版 |
| 🟡 推荐 | pip ≥ 23.0 | `pip --version` | env_setup 自动升级 |

**Windows 用户注意：**
- Python 安装时必须勾选 "Add python.exe to PATH"
- 如已安装但 `python` 命令无效：Windows 设置 → 应用 → 应用执行别名 → 关闭 App Installer 的 `python.exe`
- 建议开启 "Beta: Use Unicode UTF-8"（设置 → 时间和语言 → 语言和区域 → 管理语言设置 → 更改系统区域设置），否则中文文件名可能乱码

## 常见阻断场景

| 症状 | 原因 | 解决 |
|------|------|------|
| `python: command not found` | Python 未安装或不在 PATH | 重新安装，勾选 Add to PATH |
| `git: command not found` | Git 未安装 | 安装 Git，重启终端 |
| pip 安装全部超时 | 国内网络不通 PyPI | env_setup 自动切清华/阿里镜像 |
| `error: Microsoft Visual C++ 14.0 is required` | 缺少 C++ 编译工具 | 安装 [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) |
| `playwright install` 下载超时 | 国内 150MB 太慢 | env_setup 自动跳过，启用 CDP 模式用本机 Chrome |
| Chrome 未找到 | 没装 Chrome | Windows 上回退 Edge；Mac 上手动安装或设 `CUSTOM_BROWSER_PATH` |
| `ModuleNotFoundError` | 某依赖漏装 | `pip install <包名>` 或重跑 env_setup |
| macOS `SSL: CERTIFICATE_VERIFY_FAILED` | Python 证书链问题 | 运行 `/Applications/Python 3.x/Install Certificates.command` |
| Linux `libgbm.so.1` 缺失 | 缺 Playwright 系统依赖 | `npx playwright install-deps` |
