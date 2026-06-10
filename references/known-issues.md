# 已知问题速查

> 本文档是参考材料，**仅在排查具体问题时查阅**。正常执行流程中不要向用户展示。

| 问题 | 症状 | 自动修复 |
|------|------|----------|
| uv 未安装 | `command not found` | 回退 pip |
| Python 3.13 `collections.Callable` | 导入报错 | 卸载 pyreadline → 安装 pyreadline3 |
| SQLAlchemy < 2.0 | asyncio 模块缺失 | 自动升级 |
| redis/motor/aiomysql 缺失 | import 报错 | 自动安装 |
| matplotlib 编译失败 | 无 C 编译器 | 跳过，词云降级 |
| Playwright Chromium 下载慢 | 150MB 超时 | 切 CDP 模式 |
| 时间范围模式只爬 1 个 | `MAX_NOTES_PER_DAY=1` | env_setup 检查并提示 |
| 设时间范围后不生效 | `BILI_SEARCH_MODE` 还是 normal | env_setup 检查一致性 |
| 扫码超时 | 20 秒倒计时 | 进度轮询提醒用户操作 |
| HTML 全部评论空白 | JS 函数定义顺序错误 | 已修复（公共 JS 放 `<head>`） |
| 中文评论乱码 | atob 解码问题 | 已修复（TextDecoder） |
| 打开文件夹无反应 | fetch localhost | 已改为 `file:///` |
| 抖音目录名 `douyin` | 报告只识别 `dy` | 已内置别名映射 |
| 没有 Chrome | CDP 无法启动 | 检测 Edge 回退或提示安装 |
| 全部评论翻页无效 | 点击按钮无反应 | `PAGE` 变量已挂 `window` |
| 抖音短链→图文笔记解析失败 | `/share/note/` 报错 | 已增加 note URL 正则 |
| 全部评论表格 JS 语法错误 | Node `--check` 报错 | 用 `window.PAGE_xx` 点号，禁止方括号 |
