# MediaCrawler 配置文件精确映射表

## 配置文件位置

```
D:\study\MediaCrawler\config\
├── base_config.py      ← 主配置（平台、模式、评论、保存格式等）
├── bilibili_config.py  ← B站专属（BV号列表、时间范围、创作者UID）
├── xhs_config.py       ← 小红书专属（笔记URL列表）
├── dy_config.py        ← 抖音专属
├── ks_config.py        ← 快手专属
├── weibo_config.py     ← 微博专属
├── tieba_config.py     ← 贴吧专属
├── zhihu_config.py     ← 知乎专属
└── db_config.py        ← 数据库配置
```

## base_config.py 全部配置项

| 配置项 | 类型 | 默认值 | 说明 | Q&A对应 |
|--------|------|--------|------|---------|
| `PLATFORM` | str | `"xhs"` | 平台: xhs\|dy\|ks\|bili\|wb\|tieba\|zhihu | 第1轮问题2 |
| `KEYWORDS` | str | `"编程副业,编程兼职"` | 英文逗号分隔 | 第2A轮 |
| `LOGIN_TYPE` | str | `"qrcode"` | qrcode\|phone\|cookie | 固定qrcode |
| `CRAWLER_TYPE` | str | `"search"` | search\|detail\|creator | 第1轮问题1 |
| `ENABLE_IP_PROXY` | bool | `False` | 是否启用代理池 | 一般不改 |
| `HEADLESS` | bool | `False` | 是否无头模式(不显示浏览器) | 固定False |
| `SAVE_LOGIN_STATE` | bool | `True` | 保存登录状态免重复登录 | 固定True |
| `ENABLE_CDP_MODE` | bool | `True` | 使用CDP连接真实浏览器 | 固定True |
| `CDP_CONNECT_EXISTING` | bool | `True` | 连接已有浏览器 | 固定True |
| `CDP_DEBUG_PORT` | int | `9222` | CDP调试端口 | 一般不改 |
| `SAVE_DATA_OPTION` | str | `"jsonl"` | csv\|json\|jsonl\|sqlite\|excel\|postgres | 第4轮 |
| `CRAWLER_MAX_NOTES_COUNT` | int | `15` | 最多爬多少视频/帖子 | 第2A/2B轮 |
| `CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES` | int | `10` | 每个视频最多爬多少评论 | 第3轮问题1 |
| `ENABLE_GET_COMMENTS` | bool | `True` | 是否爬评论 | 固定True |
| `ENABLE_GET_SUB_COMMENTS` | bool | `False` | 是否爬二级评论(楼中楼) | 第3轮问题2 |
| `ENABLE_GET_MEIDAS` | bool | `False` | 是否下载图片/视频 | 一般不改 |
| `ENABLE_GET_WORDCLOUD` | bool | `False` | 是否生成词云 | 第3轮问题3 |
| `CRAWLER_MAX_SLEEP_SEC` | int | `2` | 请求间隔(秒) | 第4轮 |
| `MAX_CONCURRENCY_NUM` | int | `1` | 并发数 | 保持不变 |
| `START_PAGE` | int | `1` | 起始页码 | 一般不改 |
| `SAVE_DATA_PATH` | str | `""` | 保存路径(空=默认data目录) | 一般不改 |

## bilibili_config.py 全部配置项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `BILI_SPECIFIED_ID_LIST` | list | `["BV1dwu...", "BV1Sz4..."]` | detail模式的BV号列表 |
| `BILI_CREATOR_ID_LIST` | list | `["https://space.bilibili.com/434377496"]` | creator模式的UID/链接 |
| `START_DAY` | str | `"2024-01-01"` | 起始日期 |
| `END_DAY` | str | `"2024-01-01"` | 结束日期 |
| `BILI_SEARCH_MODE` | str | `"normal"` | normal\|all_in_time_range\|daily_limit_in_time_range |
| `MAX_NOTES_PER_DAY` | int | `1` | 每天最多爬视频数(时间范围模式) |
| `BILI_QN` | int | `80` | 视频清晰度(80=1080p) |
| `CREATOR_MODE` | bool | `True` | creator模式下是否爬用户信息 |
| `CRAWLER_MAX_CONTACTS_COUNT_SINGLENOTES` | int | `100` | 单视频最大爬取联系人数 |
| `CRAWLER_MAX_DYNAMICS_COUNT_SINGLENOTES` | int | `50` | 单用户最大爬取动态数 |

## xhs_config.py 全部配置项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `SORT_TYPE` | str | `"popularity_descending"` | 排序方式 |
| `XHS_SPECIFIED_NOTE_URL_LIST` | list | `[...]` | detail模式笔记URL |
| `XHS_CREATOR_ID_LIST` | list | `[...]` | creator模式用户主页 |

## 执行命令速查

```bash
cd "D:/study/MediaCrawler"

# B站 - 关键词搜索
uv run main.py --platform bili --lt qrcode --type search

# B站 - 指定视频
uv run main.py --platform bili --lt qrcode --type detail

# B站 - 创作者主页
uv run main.py --platform bili --lt qrcode --type creator

# 小红书 - 关键词搜索
uv run main.py --platform xhs --lt qrcode --type search

# 抖音 - 关键词搜索
uv run main.py --platform dy --lt qrcode --type search

# 微博 - 关键词搜索
uv run main.py --platform wb --lt qrcode --type search

# 贴吧
uv run main.py --platform tieba --lt qrcode --type search

# 知乎
uv run main.py --platform zhihu --lt qrcode --type search

# 快手
uv run main.py --platform ks --lt qrcode --type search
```

## 输出数据位置

```
D:\study\MediaCrawler\data\
├── bilibili\          ← B站数据
├── xhs\               ← 小红书数据
├── dy\                ← 抖音数据
└── ...
```
