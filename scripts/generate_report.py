# -*- coding: utf-8 -*-
"""
MediaCrawler 统一报告生成器 v5 (全平台通用)
- 自动检测 data/ 下所有平台的 CSV 数据
- 统一 UI 风格，无论哪个平台产出都一样
- 字段自动识别：title/url/content/nickname/avatar/likes 等
- 每条评论关联其所属内容条目（视频/笔记/帖子）
- Base64 + TextDecoder 避免中文乱码
"""
import csv, os, sys, glob, datetime, shutil, json, html as html_mod, base64, re

CRAWLED_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.join(CRAWLED_DIR, "MediaCrawler")
DATA_ROOT = os.path.join(PROJECT_DIR, "data")

# ── 平台显示名 ──
PLATFORM_NAMES = {
    "bili": "B站 (bilibili)", "xhs": "小红书", "dy": "抖音", "douyin": "抖音",
    "ks": "快手", "wb": "微博", "tieba": "贴吧", "zhihu": "知乎",
}
PLATFORM_LABELS = {
    "bili": ["视频", "评论"], "xhs": ["笔记", "评论"], "dy": ["视频", "评论"], "douyin": ["视频", "评论"],
    "ks": ["视频", "评论"], "wb": ["帖子", "评论"], "tieba": ["帖子", "评论"],
    "zhihu": ["问答", "评论"],
}
PLATFORM_ICONS = {
    "bili": "📹", "xhs": "📝", "dy": "🎵", "douyin": "🎵", "ks": "📱", "wb": "📢", "tieba": "💬", "zhihu": "❓",
}

def read_csv(path):
    if not path or not os.path.isfile(path): return []
    try:
        with open(path, 'r', encoding='utf-8-sig') as f: return list(csv.DictReader(f))
    except:
        try:
            with open(path, 'r', encoding='gbk') as f: return list(csv.DictReader(f))
        except:
            return []

def find_latest_csv(data_dir, prefix):
    pattern = os.path.join(data_dir, "csv", f"{prefix}_*.csv")
    files = sorted(glob.glob(pattern), reverse=True)
    return files[0] if files else None

# ── 字段自动检测 ──
def detect_field(rows, candidates):
    """从候选名列表中检测第一个存在的字段名"""
    if not rows: return None
    keys = set(rows[0].keys())
    for c in candidates:
        if c in keys: return c
    return None

def detect_content_fields(contents):
    """检测内容条目（视频/笔记/帖子）的关键字段"""
    if not contents: return {}
    return {
        "title": detect_field(contents, ["title","note_title","desc","description","question_title","thread_title"]),
        "url": detect_field(contents, ["video_url","note_url","share_url","url","aweme_url","thread_url"]),
        "author": detect_field(contents, ["nickname","author_name","owner_name","uname","user_name","name","poster_name"]),
        "stats": [f for f in ["video_play_count","liked_count","comment_count","share_count","favorite_count","view_count","read_count"]
                  if f in contents[0]],
        "id": detect_field(contents, ["video_id","note_id","aweme_id","content_id","thread_id","id","aid","question_id"]),
        "cover": detect_field(contents, ["video_cover_url","cover_url","cover","image_url","thumbnail"]),
        "time": detect_field(contents, ["create_time","pubdate","publish_time","created_at"]),
        "source_kw": detect_field(contents, ["source_keyword","keyword","search_keyword"]),
    }

def detect_comment_fields(comments):
    """检测评论条目的关键字段"""
    if not comments: return {}
    return {
        "content": detect_field(comments, ["content","comment_text","text","description","body"]),
        "nickname": detect_field(comments, ["nickname","user_name","uname","name","author_name","username","poster_name"]),
        "avatar": detect_field(comments, ["avatar","avatar_url","profile_url","user_avatar","face"]),
        "likes": detect_field(comments, ["like_count","liked_count","like_num","likes","agree_count"]),
        "time": detect_field(comments, ["create_time","ctime","pubdate","created_at","timestamp"]),
        "sex": detect_field(comments, ["sex","gender"]),
        "parent_id": detect_field(comments, ["video_id","note_id","aweme_id","content_id","thread_id","post_id","parent_id"]),
        "id": detect_field(comments, ["comment_id","id","cid","rpid"]),
        "replies": detect_field(comments, ["sub_comment_count","reply_count","rcount"]),
    }

# 检查命令行参数
import sys as _sys
_focus_platform = None
_no_open = False
for _a in _sys.argv[1:]:
    if _a.startswith('--focus='):
        _focus_platform = _a.split('=', 1)[1]
    elif _a in PLATFORM_NAMES:
        _focus_platform = _a
    elif _a == '--no-open':
        _no_open = True

# 扫描...（继续原有逻辑）
platforms = []
for pdir in sorted(os.listdir(DATA_ROOT)):
    pdir_path = os.path.join(DATA_ROOT, pdir)
    if not os.path.isdir(pdir_path) or not os.path.isdir(os.path.join(pdir_path, "csv")):
        continue
    if pdir not in PLATFORM_NAMES:
        continue

    # 找文件
    csv_dir = os.path.join(pdir_path, "csv")
    all_files = sorted(glob.glob(os.path.join(csv_dir, "*.csv")), reverse=True)

    content_files = [f for f in all_files if any(t in os.path.basename(f) for t in ["_videos_","_contents_","_notes_","_threads_","_questions_"])]
    comment_files = [f for f in all_files if "_comments_" in os.path.basename(f)]
    creator_files = [f for f in all_files if "_creators_" in os.path.basename(f)]

    content_file = content_files[0] if content_files else None
    comment_file = comment_files[0] if comment_files else None

    contents = read_csv(content_file) if content_file else []
    comments = read_csv(comment_file) if comment_file else []

    if not contents and not comments:
        continue

    cf = detect_content_fields(contents)
    cmf = detect_comment_fields(comments)

    # 构建内容ID→索引映射
    content_map = {}
    if cf["id"] and cf["title"]:
        for c in contents:
            cid = c.get(cf["id"], '')
            if cid:
                content_map[cid] = {
                    "title": c.get(cf["title"], '?'),
                    "url": c.get(cf["url"], '') if cf["url"] else '',
                    "author": c.get(cf["author"], '?') if cf["author"] else '',
                }

    # 补评论的视频信息
    if cmf["parent_id"] and content_map:
        for c in comments:
            pid = c.get(cmf["parent_id"], '')
            info = content_map.get(pid, {})
            c['_content_title'] = info.get('title', '?')
            c['_content_url'] = info.get('url', '')
            c['_content_author'] = info.get('author', '')

    keywords = set()
    if cf["source_kw"]:
        for c in contents:
            kw = c.get(cf["source_kw"], '') or c.get("source_keyword", '')
            if kw: keywords.add(kw)

    platforms.append({
        "key": pdir,
        "name": PLATFORM_NAMES[pdir],
        "emoji": PLATFORM_ICONS[pdir],
        "label1": PLATFORM_LABELS[pdir][0],
        "label2": PLATFORM_LABELS[pdir][1],
        "contents": contents, "comments": comments,
        "cf": cf, "cmf": cmf,
        "content_map": content_map,
        "keywords": ', '.join(sorted(keywords)) if keywords else 'N/A',
        "content_file": content_file, "comment_file": comment_file,
    })

if not platforms:
    print("No data found.")
    sys.exit(0)

date_str = datetime.date.today().isoformat()

# ════════════════ CSS (统一) ════════════════
CSS = '''
:root{--bg:#f8f9fb;--card:#fff;--border:#e5e7eb;--text:#1f2937;--text2:#6b7280;--accent:#6366f1;--green:#10b981;--red:#ef4444;--tag-bg:#eef2ff;--tag-text:#4338ca;--shadow:0 1px 3px rgba(0,0,0,.06),0 1px 2px rgba(0,0,0,.04);--radius:12px}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text);line-height:1.6;min-height:100vh}
.container{max-width:1200px;margin:0 auto;padding:24px 20px}
.header{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;padding:36px 40px;border-radius:var(--radius);margin-bottom:24px;box-shadow:0 4px 12px rgba(99,102,241,.25)}
.header h1{font-size:28px;font-weight:700;margin-bottom:8px}
.header .meta{opacity:.85;font-size:14px;display:flex;gap:24px;flex-wrap:wrap}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-bottom:24px}
.stat-card{background:var(--card);border-radius:var(--radius);padding:20px 24px;box-shadow:var(--shadow);border:1px solid var(--border);transition:transform .15s}
.stat-card:hover{transform:translateY(-2px)}
.stat-card .num{font-size:32px;font-weight:800;color:var(--accent);line-height:1.2}
.stat-card .label{font-size:13px;color:var(--text2);margin-top:4px}
.tabs{display:flex;gap:4px;margin-bottom:24px;flex-wrap:wrap;background:var(--card);border-radius:var(--radius);padding:6px;box-shadow:var(--shadow)}
.tab-btn{padding:10px 20px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;border:none;background:transparent;color:var(--text2);transition:all .15s;white-space:nowrap}
.tab-btn:hover{background:#f3f4f6;color:var(--text)}
.tab-btn.active{background:var(--accent);color:#fff}
.tab-panel{display:none}
.tab-panel.active{display:block}
.section{background:var(--card);border-radius:var(--radius);padding:24px 28px;margin-bottom:20px;box-shadow:var(--shadow);border:1px solid var(--border)}
.section h2{font-size:18px;font-weight:700;margin-bottom:16px;padding-bottom:10px;border-bottom:2px solid var(--accent);display:flex;align-items:center;gap:8px}
.row{display:flex;align-items:center;gap:16px;padding:12px 0;border-bottom:1px solid var(--border)}
.row:last-child{border-bottom:none}
.rank{font-size:18px;font-weight:800;color:var(--accent);min-width:28px;text-align:center}
.row-info{flex:1;min-width:0}
.row-title{font-size:15px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.row-title a{color:var(--text);text-decoration:none}
.row-title a:hover{color:var(--accent)}
.row-meta{font-size:12px;color:var(--text2);margin-top:2px}
.row-stats{display:flex;gap:16px;font-size:13px;color:var(--text2);white-space:nowrap}
.row-stats b{font-weight:600;color:var(--text)}
.bar-wrap{display:flex;align-items:center;gap:10px;margin:6px 0}
.bar-label{font-size:13px;min-width:70px;text-align:right;color:var(--text2)}
.bar-track{flex:1;height:22px;background:#f3f4f6;border-radius:11px;overflow:hidden}
.bar-fill{height:100%;border-radius:11px;background:linear-gradient(90deg,#6366f1,#8b5cf6);display:flex;align-items:center;justify-content:flex-end;padding-right:8px;font-size:11px;color:#fff;font-weight:600;min-width:30px}
.comment-item{display:flex;gap:12px;padding:12px 14px;margin:6px 0;background:#f9fafb;border-radius:8px;font-size:14px;border-left:3px solid var(--accent);align-items:flex-start}
.comment-avatar{width:36px;height:36px;border-radius:50%;flex-shrink:0;object-fit:cover;background:#e5e7eb}
.comment-body{flex:1;min-width:0}
.comment-text{line-height:1.5;word-break:break-word}
.comment-meta{display:flex;align-items:center;gap:10px;font-size:12px;color:var(--text2);margin-top:6px;flex-wrap:wrap}
.comment-meta .like{color:var(--red);font-weight:600}
.comment-source{font-size:11px;color:var(--text2);margin-top:4px}
.comment-source a{color:var(--accent);text-decoration:none}
.comment-source a:hover{text-decoration:underline}
.footer{text-align:center;padding:20px;color:var(--text2);font-size:12px}
.btn{display:inline-flex;align-items:center;gap:6px;padding:10px 20px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;text-decoration:none;border:none;transition:all .2s}
.btn-primary{background:var(--accent);color:#fff;box-shadow:0 2px 6px rgba(99,102,241,.3)}
.btn-primary:hover{background:#4f46e5;transform:translateY(-1px)}
.btn-outline{background:#fff;color:var(--accent);border:1.5px solid var(--accent)}
.btn-outline:hover{background:var(--tag-bg)}
.btn-row{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}
.toolbar{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:16px}
.toolbar input{flex:1;min-width:200px;padding:10px 14px;border:1.5px solid var(--border);border-radius:8px;font-size:14px;outline:none;transition:border .2s}
.toolbar input:focus{border-color:var(--accent)}
.toolbar select{padding:10px 14px;border:1.5px solid var(--border);border-radius:8px;font-size:14px;background:#fff;outline:none;cursor:pointer}
.data-table{width:100%;border-collapse:collapse;font-size:13px}
.data-table th{background:#f3f4f6;padding:10px 12px;text-align:left;font-weight:600;color:var(--text2);border-bottom:2px solid var(--border);white-space:nowrap;cursor:pointer;user-select:none}
.data-table th:hover{color:var(--accent)}
.data-table td{padding:10px 12px;border-bottom:1px solid var(--border);vertical-align:top}
.data-table tr:hover td{background:#f9fafb}
.data-table .avatar-cell{width:44px}
.data-table .avatar-cell img{width:32px;height:32px;border-radius:50%;object-fit:cover;background:#e5e7eb}
.data-table .avatar-fb{width:32px;height:32px;border-radius:50%;background:#eef2ff;color:#6366f1;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:bold}
.data-table .text-cell{max-width:380px;word-break:break-word;line-height:1.5}
.data-table .src-cell{max-width:160px;font-size:12px;line-height:1.4}
.data-table .src-cell a{color:var(--accent);text-decoration:none;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.data-table .src-cell a:hover{text-decoration:underline}
.pagination{display:flex;justify-content:center;align-items:center;gap:6px;margin-top:16px;flex-wrap:wrap}
.pagination button{padding:8px 14px;border:1px solid var(--border);border-radius:6px;background:#fff;font-size:13px;cursor:pointer;transition:all .15s}
.pagination button:hover:not(:disabled){background:var(--accent);color:#fff;border-color:var(--accent)}
.pagination button:disabled{opacity:.4;cursor:default}
.pagination .pg-active{background:var(--accent);color:#fff;border-color:var(--accent)}
.pagination .pg-info{font-size:13px;color:var(--text2);margin:0 8px}
.toast{position:fixed;bottom:30px;left:50%;transform:translateX(-50%);background:#1f2937;color:#fff;padding:12px 24px;border-radius:8px;font-size:14px;z-index:9999;opacity:0;transition:opacity .3s;pointer-events:none}
.toast.show{opacity:1}
'''

JS_COMMON = '''
function showToast(m) {
    var t = document.getElementById('toast');
    t.textContent = m; t.classList.add('show');
    setTimeout(function(){ t.classList.remove('show'); }, 2800);
}

function escHtml(s) {
    if (!s) return '';
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function avatarCell(avatarUrl, initial) {
    if (avatarUrl) {
        var img = document.createElement('img');
        img.src = avatarUrl;
        img.style.cssText = 'width:32px;height:32px;border-radius:50%;object-fit:cover;background:#e5e7eb';
        img.onerror = function() {
            var d = document.createElement('div');
            d.className = 'avatar-fb';
            d.textContent = initial || '?';
            img.parentNode.replaceChild(d, img);
        };
        return img.outerHTML;
    }
    return '<div class="avatar-fb">' + escHtml(initial || '?') + '</div>';
}

function srcLinkCell(title, url) {
    if (!title || !url) return '<td class="src-cell">-</td>';
    var t = escHtml(title);
    var disp = t.length > 24 ? t.substring(0,24)+'...' : t;
    return '<td class="src-cell"><a href="' + escHtml(url) + '" target="_blank" title="' + t + '">' + disp + '</a></td>';
}

function b64ToJson(b64) {
    var binary = atob(b64);
    var bytes = new Uint8Array(binary.length);
    for (var i = 0; i < binary.length; i++) { bytes[i] = binary.charCodeAt(i); }
    return JSON.parse(new TextDecoder('utf-8').decode(bytes));
}
'''

def build_platform_tab(plat):
    """为一个平台生成完整的 HTML tab 内容"""
    p = plat
    cf = p["cf"]; cmf = p["cmf"]
    contents = p["contents"]; comments = p["comments"]

    # 关键词统计
    kw_counter = {}
    if cf.get("source_kw"):
        for c in contents:
            kw = c.get(cf["source_kw"], '') or c.get("source_keyword", '')
            if kw: kw_counter[kw] = kw_counter.get(kw, 0) + 1

    # 按播放量/阅读量等排序
    stats_key = None
    for sk in cf.get("stats", []):
        if sk in (contents[0] if contents else {}):
            stats_key = sk; break
    if stats_key:
        sorted_contents = sorted(contents, key=lambda x: int(x.get(stats_key,'0') or '0'), reverse=True)
    else:
        sorted_contents = contents

    # 评论排序
    if cmf.get("likes"):
        sorted_comments = sorted(comments, key=lambda x: int(x.get(cmf["likes"],'0') or '0'), reverse=True)
    else:
        sorted_comments = comments

    # 性别
    sex_counter = {}
    if cmf.get("sex"):
        for c in comments:
            s = c.get(cmf["sex"], '保密') or '保密'
            sex_counter[s] = sex_counter.get(s, 0) + 1

    # 热门关键词（评论中高频词）
    keyword_hits = {}
    hot_words = ['DeepSeek','V4','Codex','Claude','GPT','AI','API','token','价格','便宜','额度','bug','识图','MCP','skill','华为','昇腾','中文','英文','灰度','游戏','引擎','画图','赚钱','副业','流量','涨粉','电商','直播','带货','教程','评测','推荐','分享','好物','穿搭','美食','旅游','考研','考公','职场','租房','买房','装修','育儿','宠物']
    for c in comments:
        text = c.get(cmf["content"], '') if cmf.get("content") else ''
        if not isinstance(text, str): continue
        for w in hot_words:
            if w.lower() in text.lower():
                keyword_hits[w] = keyword_hits.get(w, 0) + 1
    sorted_kws = sorted(keyword_hits.items(), key=lambda x: x[1], reverse=True)

    # Base64 编码
    comm_b64 = base64.b64encode(json.dumps(comments, ensure_ascii=False).encode('utf-8')).decode('ascii')

    parts = []

    # 统计卡
    parts.append(f'''
<div class="stats">
  <div class="stat-card"><div class="num">{len(contents)}</div><div class="label">{p['emoji']} 采集{p["label1"]}</div></div>
  <div class="stat-card"><div class="num">{len(comments)}</div><div class="label">💬 采集评论</div></div>
</div>

<div class="btn-row">
  <button class="btn btn-primary" onclick="openFolder_{p['key']}()">📂 打开数据文件夹</button>
  <button class="btn btn-outline" onclick="copyPath_{p['key']}()">📋 复制文件夹路径</button>
  <a class="btn btn-outline" href="#all-data-{p['key']}">📋 查看全部评论 ({len(comments)}条)</a>
</div>
''')

    # 关键词热度
    if sorted_kws:
        parts.append('<div class="section"><h2>🔑 评论关键词热度</h2><div>')
        for kw, cnt in sorted_kws[:18]:
            pct = min(100, cnt / max(1, len(comments)) * 100)
            parts.append(f'<div class="bar-wrap"><span class="bar-label">{kw}</span><div class="bar-track"><div class="bar-fill" style="width:{max(5,pct):.0f}%">{cnt}</div></div></div>')
        parts.append('</div></div>')

    # 热门内容 Top 10
    if sorted_contents:
        label1 = p["label1"]
        label1_icon = {"视频":"▶","笔记":"📖","帖子":"📄","问答":"❓"}.get(label1, "▶")
        parts.append(f'<div class="section"><h2>{p["emoji"]} 热门{label1} Top 10</h2>')
        for i, c in enumerate(sorted_contents[:10]):
            title = html_mod.escape((c.get(cf["title"],'?') or '?')[:60]) if cf.get("title") else '?'
            url = c.get(cf["url"],'') if cf.get("url") else ''
            author = html_mod.escape(c.get(cf["author"],'?') or '?') if cf.get("author") else ''
            kw = (c.get(cf["source_kw"],'') or c.get("source_keyword",'') or '') if cf.get("source_kw") else ''
            metric_val = int(c.get(stats_key,'0') or '0') if stats_key else 0
            parts.append(f'''<div class="row">
      <div class="rank">#{i+1}</div>
      <div class="row-info">
        <div class="row-title">{'<a href="'+html_mod.escape(url)+'" target="_blank">' if url else ''}{title}{'</a>' if url else ''}</div>
        <div class="row-meta">{author}{(' · '+html_mod.escape(kw)) if kw else ''}</div>
      </div>
      <div class="row-stats">{label1_icon} <b>{metric_val:,}</b></div>
    </div>''')
        parts.append('</div>')

    # 热门评论精选
    if sorted_comments:
        parts.append('<div class="section"><h2>💬 热门评论精选</h2>')
        for c in sorted_comments[:15]:
            content = html_mod.escape((c.get(cmf["content"],'') or '')[:300]) if cmf.get("content") else ''
            nickname = html_mod.escape(c.get(cmf["nickname"],'?') or '?') if cmf.get("nickname") else '?'
            avatar = c.get(cmf["avatar"],'') if cmf.get("avatar") else ''
            likes_c = int(c.get(cmf["likes"],'0') or '0') if cmf.get("likes") else 0
            sex = c.get(cmf["sex"],'') if cmf.get("sex") else ''
            v_title = html_mod.escape((c.get('_content_title','?') or '?')[:50])
            v_url = c.get('_content_url','')
            v_author = html_mod.escape(c.get('_content_author','?') or '?')

            if avatar:
                avatar_html = f'<img class="comment-avatar" src="{avatar}" alt="" loading="lazy" onerror="this.style.display=\'none\'">'
            else:
                initial = html_mod.escape(nickname[0]) if nickname else '?'
                avatar_html = f'<div class="comment-avatar" style="background:#6366f1;color:#fff;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:bold">{initial}</div>'

            source_html = ''
            if v_url and v_title:
                source_html = f'<div class="comment-source">{p["emoji"]} <a href="{v_url}" target="_blank" title="{v_title}">{v_title}</a> · {v_author}</div>'

            parts.append(f'''<div class="comment-item">
      {avatar_html}
      <div class="comment-body">
        <div class="comment-text">{content}</div>
        {source_html}
        <div class="comment-meta"><span>{nickname}</span>{'<span>'+sex+'</span>' if sex else ''}<span class="like">❤ {likes_c}</span></div>
      </div>
    </div>''')
        parts.append('</div>')

    # 数据分布
    if kw_counter or sex_counter:
        parts.append('<div class="section"><h2>📈 数据分布</h2><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px">')
        if kw_counter:
            parts.append('<div><h3 style="font-size:14px;color:var(--text2);margin-bottom:8px">搜索关键词命中</h3>')
            for kw, cnt in sorted(kw_counter.items(), key=lambda x: x[1], reverse=True):
                parts.append(f'<div class="bar-wrap"><span class="bar-label">{html_mod.escape(kw)}</span><div class="bar-track"><div class="bar-fill" style="width:{max(10,cnt/max(1,len(contents))*100):.0f}%">{cnt}</div></div></div>')
            parts.append('</div>')
        if sex_counter:
            parts.append('<div><h3 style="font-size:14px;color:var(--text2);margin-bottom:8px">评论用户性别</h3>')
            for s, cnt in sex_counter.items():
                parts.append(f'<div class="bar-wrap"><span class="bar-label">{s}</span><div class="bar-track"><div class="bar-fill" style="width:{max(10,cnt/max(1,len(comments))*100):.0f}%">{cnt}</div></div></div>')
            parts.append('</div>')
        parts.append('</div></div>')

    # ★ 全部评论数据表
    data_dir = os.path.join(DATA_ROOT, p["key"], "csv").replace("\\", "\\\\")
    parts.append(f'''
<div class="section" id="all-data-{p['key']}">
  <h2>📋 全部评论数据 <span style="font-size:14px;color:var(--text2);font-weight:400">({len(comments)} 条，已全部加载)</span></h2>
  <div class="toolbar">
    <input type="text" id="search-{p['key']}" placeholder="🔍 输入关键词过滤评论..." oninput="renderTable_{p['key']}()">
    <select id="sort-{p['key']}" onchange="renderTable_{p['key']}()">
      <option value="default">默认顺序</option>
      <option value="like">按点赞 ↓</option>
      <option value="time">按时间 ↓</option>
    </select>
    <select id="psize-{p['key']}" onchange="renderTable_{p['key']}()">
      <option value="20">每页 20 条</option>
      <option value="50">每页 50 条</option>
      <option value="100">每页 100 条</option>
    </select>
  </div>
  <div style="overflow-x:auto">
    <table class="data-table">
      <thead><tr>
        <th style="width:44px"></th>
        <th>用户</th>
        <th>评论内容</th>
        <th style="width:140px">所属{p["label1"]}</th>
        <th style="width:60px">点赞</th>
        <th style="width:140px">时间</th>
      </tr></thead>
      <tbody id="tbody-{p['key']}"></tbody>
    </table>
  </div>
  <div class="pagination" id="pgn-{p['key']}"></div>
</div>
''')

    # JS
    parts.append(f'''
<script>
(function() {{
var DATA_{p['key']} = b64ToJson("{comm_b64}");
window.PAGE_{p["key"]} = 1;
var PFOLDER_{p['key']} = "{data_dir}";

window['openFolder_{p['key']}'] = function() {{
    var a = document.createElement('a');
    a.href = "file:///" + PFOLDER_{p['key']}.replace(/\\\\\\\\/g, "/");
    a.target = "_blank"; a.click();
    setTimeout(function(){{ showToast('若未弹出，请手动打开文件夹'); }}, 600);
}};
window['copyPath_{p['key']}'] = function() {{
    var pp = PFOLDER_{p['key']}.replace(/\\\\\\\\/g, '\\\\');
    if (navigator.clipboard) {{
        navigator.clipboard.writeText(pp).then(function(){{ showToast('已复制路径到剪贴板'); }});
    }} else {{ prompt('复制此路径:', pp); }}
}};

window['renderTable_{p['key']}'] = function() {{
    var q = (document.getElementById('search-{p['key']}').value || '').toLowerCase().trim();
    var sort = document.getElementById('sort-{p['key']}').value;
    var ps = parseInt(document.getElementById('psize-{p['key']}').value) || 20;
    var data = DATA_{p['key']}.slice();

    if (q) {{
        data = data.filter(function(c) {{
            return (c["{cmf.get('content','content')}"]||'').toLowerCase().indexOf(q) >= 0 ||
                   (c["{cmf.get('nickname','nickname')}"]||'').toLowerCase().indexOf(q) >= 0 ||
                   (c._content_title||'').toLowerCase().indexOf(q) >= 0;
        }});
    }}

    if (sort === 'like') {{
        data.sort(function(a,b){{ return (parseInt(b["{cmf.get('likes','like_count')}"])||0) - (parseInt(a["{cmf.get('likes','like_count')}"])||0); }});
    }} else if (sort === 'time') {{
        data.sort(function(a,b){{ return (parseInt(b["{cmf.get('time','create_time')}"])||0) - (parseInt(a["{cmf.get('time','create_time')}"])||0); }});
    }}

    var tp = Math.ceil(data.length / ps) || 1;
    if (window.PAGE_{p["key"]} > tp) window.PAGE_{p["key"]} = tp;
    var start = (window.PAGE_{p["key"]} - 1) * ps;
    var pd = data.slice(start, start + ps);

    var rows = [];
    for (var i = 0; i < pd.length; i++) {{
        var c = pd[i];
        var nick = c["{cmf.get('nickname','nickname')}"] || '?';
        var text = escHtml(c["{cmf.get('content','content')}"] || '');
        var likes = parseInt(c["{cmf.get('likes','like_count')}"]) || 0;
        var ts = parseInt(c["{cmf.get('time','create_time')}"]) || 0;
        var tstr = ts ? new Date(ts*1000).toLocaleString('zh-CN') : '-';
        var av = avatarCell(c["{cmf.get('avatar','avatar')}"] || '', nick.charAt(0));
        var sl = srcLinkCell(c._content_title || '', c._content_url || '');

        rows.push('<tr>' +
            '<td class="avatar-cell">' + av + '</td>' +
            '<td style="white-space:nowrap;font-size:13px">' + escHtml(nick) + '</td>' +
            '<td class="text-cell">' + text + '</td>' +
            sl +
            '<td style="text-align:right;white-space:nowrap">' + (likes||'') + '</td>' +
            '<td style="white-space:nowrap;font-size:12px;color:var(--text2)">' + tstr + '</td>' +
            '</tr>');
    }}

    document.getElementById('tbody-{p['key']}').innerHTML = rows.join('') ||
        '<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--text2)">没有匹配的评论</td></tr>';

    var h = '<button '+(window.PAGE_{p["key"]}===1?'disabled':'')+' onclick="window.PAGE_{p["key"]}=window.PAGE_{p["key"]}-1;renderTable_{p['key']}()">上一页</button>';
    var ms = 7;
    var ps2 = Math.max(1, window.PAGE_{p["key"]} - Math.floor(ms/2));
    var pe = Math.min(tp, ps2 + ms - 1);
    if (pe - ps2 < ms - 1) ps2 = Math.max(1, pe - ms + 1);
    for (var j = ps2; j <= pe; j++) {{
        h += '<button class="'+(j===window.PAGE_{p["key"]}?'pg-active':'')+'" onclick="window.PAGE_{p["key"]}='+j+';renderTable_{p['key']}()">'+j+'</button>';
    }}
    h += '<button '+(window.PAGE_{p["key"]}===tp?'disabled':'')+' onclick="window.PAGE_{p["key"]}=window.PAGE_{p["key"]}+1;renderTable_{p['key']}()">下一页</button>';
    h += '<span class="pg-info">共 '+data.length+' 条 / '+tp+' 页</span>';
    document.getElementById('pgn-{p['key']}').innerHTML = h;
}};

renderTable_{p['key']}();
}})();
</script>
''')

    return ''.join(parts)

# ════════════════ 组装完整 HTML ════════════════
parts = []
parts.append(f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MediaCrawler · 多平台数据采集报告</title>
<style>{CSS}</style>
<script>
{JS_COMMON}
</script>
</head>
<body>
<div class="container">

<div class="header">
  <h1>📊 MediaCrawler · 数据采集报告</h1>
  <div class="meta">
    <span>📅 {date_str}</span>
    <span>📁 {DATA_ROOT.replace(chr(92), '/')}</span>
  </div>
</div>
''')

# 按聚焦平台排序（聚焦平台放首位）
if _focus_platform and len(platforms) > 1:
    for i, p in enumerate(platforms):
        if p["key"] == _focus_platform:
            platforms.insert(0, platforms.pop(i))
            break
    print(f"FOCUS={platforms[0]['key']}")

# 平台 tabs
if len(platforms) > 1:
    parts.append('<div class="tabs">')
    for i, p in enumerate(platforms):
        active = ' active' if i == 0 else ''
        parts.append(f'<button class="tab-btn{active}" onclick="switchTab(\'{p["key"]}\')">{p["emoji"]} {p["name"]}</button>')
    parts.append('</div>')

# 每个平台的面板
for i, p in enumerate(platforms):
    active = ' active' if i == 0 else ''
    parts.append(f'<div class="tab-panel{active}" id="panel-{p["key"]}">')
    parts.append(build_platform_tab(p))
    parts.append('</div>')

# 页脚
parts.append(f'''
<div class="footer">
  <p>MediaCrawler · {date_str} · <span style="cursor:pointer;color:var(--accent);text-decoration:underline" onclick="switchTab('{platforms[0]["key"]}')">{DATA_ROOT.replace(chr(92), '/')}</span></p>
</div>
<div class="toast" id="toast"></div>
''')

# Tab 切换 JS
parts.append('''
<script>
function switchTab(key) {
    document.querySelectorAll('.tab-panel').forEach(function(p){ p.classList.remove('active'); });
    document.querySelectorAll('.tab-btn').forEach(function(b){ b.classList.remove('active'); });
    (document.getElementById('panel-'+key)||{}).classList.add('active');
    var btns = document.querySelectorAll('.tab-btn');
    for (var i = 0; i < btns.length; i++) {
        if (btns[i].textContent.indexOf(key.replace('bili','B站').replace('xhs','小红书').replace('dy','抖音').replace('ks','快手').replace('wb','微博').replace('tieba','贴吧').replace('zhihu','知乎').substring(0,2)) >= 0) {
            btns[i].classList.add('active');
        }
    }
}
</script>
''')

# 公共 JS 函数已在 <head> 中定义，这里不需要重复

parts.append('</div></body></html>')

html = ''.join(parts)

# ── 保存 ──
report_dir = os.path.join(PROJECT_DIR, "data", "reports")
os.makedirs(report_dir, exist_ok=True)
report_path = os.path.join(report_dir, f"report_{date_str}.html")
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(html)

desktop_path = os.path.expanduser(f"~/Desktop/MediaCrawler_Report_{date_str}.html")
try:
    shutil.copy(report_path, desktop_path)
except:
    pass

# 自动在浏览器中打开报告（--no-open 时跳过）
if not _no_open:
    try:
        if sys.platform == 'win32':
            os.startfile(desktop_path)
        elif sys.platform == 'darwin':
            subprocess.run(['open', desktop_path])
        else:
            subprocess.run(['xdg-open', desktop_path])
        print(f"OPENED=1")
    except Exception as e:
        print(f"OPEN_ERROR={e}")
else:
    print(f"OPENED=0")

print(f"REPORT_PATH={report_path}")
print(f"DESKTOP_PATH={desktop_path}")
total_v = sum(len(p["contents"]) for p in platforms)
total_c = sum(len(p["comments"]) for p in platforms)
print(f"PLATFORMS={len(platforms)}")
print(f"CONTENTS={total_v}")
print(f"COMMENTS={total_c}")
for p in platforms:
    print(f"  {p['key']}: {len(p['contents'])} contents, {len(p['comments'])} comments")
