# 已知问题速查

> 本文档是参考材料，**仅在排查具体问题时查阅**。正常执行流程中不要向用户展示。

## 环境类

| 问题 | 症状 | 自动修复 |
|------|------|----------|
| uv 未安装 | `command not found` | 回退 pip |
| Python 3.13 `collections.Callable` | 导入报错 | 卸载 pyreadline → 安装 pyreadline3 |
| SQLAlchemy < 2.0 | asyncio 模块缺失 | 自动升级 |
| redis/motor/aiomysql 缺失 | import 报错 | 自动安装 |
| matplotlib 编译失败 | 无 C 编译器 | 跳过，词云降级 |
| Playwright Chromium 下载慢 | 150MB 超时 | 切 CDP 模式 |
| 没有 Chrome | CDP 无法启动 | 检测 Edge 回退或提示安装 |

## 登录类（新环境最常见）

| 症状 | 可能原因 | 处理 |
|------|---------|------|
| Chrome 打开 bilibili.com 但 60s+ 无反应 | XPath 选择器失效（B站改版） | 让用户**手动点击 Chrome 里的"登录"按钮**，脚本会自动接管 |
| Chrome 弹出但没有二维码 | B站反爬弹出滑块/CAPTCHA | 让用户在 Chrome 里**手动完成验证**，完成后脚本继续 |
| Chrome 弹出 Windows 防火墙对话框 | `--remote-debugging-address=0.0.0.0` 触发 | 已修复为 `127.0.0.1`。旧版需点击"允许" |
| 二维码出现但扫了没反应 | 二维码过期 / Cookie 域不匹配 | 刷新页面重试。确保手机和电脑在同一网络 |
| `login failed, have not found qrcode` | 页面加载异常或选择器不匹配 | 检查 Chrome 窗口是否正常显示了 B站首页 |
| 脚本在 `Waiting for scan code login` 卡 10 分钟 | 用户没扫码或没注意到二维码 | 提醒用户扫码，二维码有效期约 2 分钟 |
| 首次使用无论如何都登不上 | CDP 新 profile 被 B站 标记为可疑 | 手动在 Chrome 里先登录一次 B站，让 profile 积累 cookies 后再爬 |
| Chrome 打开 → 关闭 → 重新打开 | Chrome 版本太旧，CDP 连接失败后 fallback 到 Playwright 托管 Chromium | **已修复**：启动前检查版本，<115 直接跳过 CDP 避免双次打开。长期解决：更新 Chrome |
| Chrome 一闪就关 | `AUTO_CLOSE_BROWSER=True` 或 `atexit` 无条件杀进程 | 已将默认值改为 `False`。旧配置需手动改 `base_config.py:87` 为 `False` |

## 配置类

| 问题 | 症状 | 自动修复 |
|------|------|----------|
| 时间范围模式只爬 1 个 | `MAX_NOTES_PER_DAY=1` | env_setup 检查并提示 |
| 设时间范围后不生效 | `BILI_SEARCH_MODE` 还是 normal | env_setup 检查一致性 |

## 报告类

| 问题 | 症状 | 自动修复 |
|------|------|----------|
| HTML 全部评论空白 | JS 函数定义顺序错误 | 已修复（公共 JS 放 `<head>`） |
| 中文评论乱码 | atob 解码问题 | 已修复（TextDecoder） |
| 打开文件夹无反应 | fetch localhost | 已改为 `file:///` |
| 抖音目录名 `douyin` | 报告只识别 `dy` | 已内置别名映射 |
| 全部评论翻页无效 | 点击按钮无反应 | `PAGE` 变量已挂 `window` |
| 新爬的数据没进报告 | JSONL 未转 CSV 或同日覆盖 | 已修复（逐文件转换 + 类型分离） |
