# -*- coding: utf-8 -*-
"""
独立脚本：从抖音 CSV 读取评论，按与「2006.9.13」关联度评分排行，生成 HTML。
不修改 generate_report.py，独立运行。
"""
import csv, os, json, html as html_mod, sys, subprocess

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "MediaCrawler", "data", "douyin", "csv")
OUT_PATH = os.path.expanduser("~/Desktop/Douyin_20060913_排行.html")

def read_csv(path):
    if not os.path.isfile(path): return []
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            return list(csv.DictReader(f))
    except:
        return []

def score_comment(comment, content_map):
    """给评论打分，越高越相关"""
    text = (comment.get('content', '') or '').strip()
    score = 0
    reasons = []

    # 核心命中
    if '2006.9.13' in text or '2006.09.13' in text:
        score += 15; reasons.append('精确匹配2006.9.13')
    if '2006年9月13日' in text or '2006年9月13' in text:
        score += 15; reasons.append('精确匹配2006年9月13日')
    if '06913' in text:
        score += 12; reasons.append('包含06913')
    if '06年9月13' in text:
        score += 12; reasons.append('包含06年9月13')

    # 日期模式
    if '9月13日' in text or '9月13' in text:
        if score < 10: score += 8
        reasons.append('包含9月13')
    if re.search(r'(?<!\d)9\.13(?!\d)', text):
        if score < 10: score += 8
        reasons.append('包含9.13')
    sp = text.replace(' ', '').replace('\n', '')
    if '913' in sp and '9.13' not in sp and '9月13' not in sp:
        score += 4; reasons.append('包含913数字')

    # 生日相关
    if '生日' in text: score += 5; reasons.append('提及生日')
    if '出生' in text: score += 4; reasons.append('提及出生')
    if '同年同月同日' in text: score += 6; reasons.append('同年同月同日生')
    if '2006年' in text or '06年' in text: score += 3; reasons.append('提及2006年')

    # 星座
    if '处女座' in text or '处女' in text: score += 3; reasons.append('提及处女座')

    # 点名回答型 (回复别人问日期的)
    if re.match(r'^\d{1,2}[\.月]\d{1,2}', text): score += 3; reasons.append('日期格式回复')
    if text in ('9.13', '913', '9月13', '9月13日', '06913'): score += 5; reasons.append('纯日期回复')

    # 短文本惩罚
    if len(text) < 2: score = max(0, score - 3)
    if len(text) < 1: score = 0

    # 从所属视频标题中提取上下文加分
    aweme_id = comment.get('aweme_id', '')
    cmeta = content_map.get(aweme_id, {})
    ctitle = cmeta.get('title', '')
    if '2006' in ctitle or '06年' in ctitle: score += 1
    if '生日' in ctitle: score += 2
    if '9.13' in ctitle or '913' in ctitle: score += 2

    return score, reasons

import re

def main():
    comments = read_csv(os.path.join(DATA_DIR, "search_comments_2026-06-11.csv"))
    contents = read_csv(os.path.join(DATA_DIR, "search_contents_2026-06-11.csv"))

    if not comments:
        print("No douyin comments found.")
        sys.exit(1)

    # 构建 aweme_id → 视频信息映射
    content_map = {}
    for c in contents:
        aid = c.get('aweme_id', '')
        if aid:
            content_map[aid] = {
                'title': c.get('title', '?'),
                'url': c.get('aweme_url', ''),
                'nickname': c.get('nickname', '?'),
            }

    # 给每条评论评分
    scored = []
    for cmt in comments:
        s, reasons = score_comment(cmt, content_map)
        if s > 0:
            scored.append((s, reasons, cmt))

    scored.sort(key=lambda x: x[0], reverse=True)

    # 统计
    total = len(comments)
    relevant = len(scored)
    top_score = scored[0][0] if scored else 0

    # 生成 HTML
    parts = []
    parts.append(f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>抖音评论 · 2006.9.13 关联度排行</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#f8f9fb;color:#1f2937;line-height:1.6}}
.container{{max-width:1000px;margin:0 auto;padding:24px 20px}}
.header{{background:linear-gradient(135deg,#ef4444,#f97316);color:#fff;padding:32px 40px;border-radius:16px;margin-bottom:24px;box-shadow:0 4px 12px rgba(239,68,68,.25)}}
.header h1{{font-size:26px;font-weight:700;margin-bottom:8px}}
.header .meta{{opacity:.85;font-size:14px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:20px}}
.stat-card{{background:#fff;border-radius:12px;padding:16px 20px;box-shadow:0 1px 3px rgba(0,0,0,.06);border:1px solid #e5e7eb}}
.stat-card .num{{font-size:28px;font-weight:800;color:#ef4444;line-height:1.2}}
.stat-card .label{{font-size:12px;color:#6b7280;margin-top:4px}}
.comment-item{{display:flex;gap:12px;padding:14px 16px;margin:8px 0;background:#fff;border-radius:10px;border-left:4px solid #ef4444;box-shadow:0 1px 3px rgba(0,0,0,.04)}}
.comment-item.gold{{border-left-color:#f59e0b;background:#fffbeb}}
.comment-item.silver{{border-left-color:#94a3b8;background:#f8fafc}}
.comment-item.bronze{{border-left-color:#d97706;background:#fffbeb}}
.rank{{font-size:24px;font-weight:800;color:#ef4444;min-width:44px;text-align:center;flex-shrink:0;line-height:1.2}}
.score-badge{{display:inline-flex;align-items:center;gap:4px;background:#fef2f2;color:#dc2626;padding:2px 10px;border-radius:20px;font-size:13px;font-weight:700;white-space:nowrap}}
.reason-tag{{display:inline-block;background:#eef2ff;color:#4338ca;padding:1px 8px;border-radius:4px;font-size:11px;margin:2px 4px 2px 0}}
.comment-body{{flex:1;min-width:0}}
.comment-text{{font-size:14px;line-height:1.6;word-break:break-word;margin-bottom:6px}}
.comment-meta{{font-size:12px;color:#6b7280;display:flex;align-items:center;gap:10px;flex-wrap:wrap}}
.comment-source{{font-size:11px;color:#9ca3af;margin-top:4px}}
.comment-source a{{color:#6366f1;text-decoration:none}}
.comment-source a:hover{{text-decoration:underline}}
.avatar{{width:36px;height:36px;border-radius:50%;flex-shrink:0;object-fit:cover;background:#e5e7eb}}
.filter-bar{{display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap;align-items:center}}
.filter-bar input{{flex:1;min-width:200px;padding:10px 14px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:14px;outline:none}}
.filter-bar input:focus{{border-color:#ef4444}}
.filter-bar select{{padding:10px 14px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:14px;background:#fff;cursor:pointer}}
.footer{{text-align:center;padding:20px;color:#9ca3af;font-size:12px}}
</style>
</head>
<body>
<div class="container">
<div class="header">
  <h1>🎵 抖音评论 · 「2006.9.13」关联度排行</h1>
  <div class="meta">按与出生日期 2006年9月13日 的语义关联度评分排序 · 共 {total} 条评论，{relevant} 条相关</div>
</div>
<div class="stats">
  <div class="stat-card"><div class="num">{total}</div><div class="label">总评论数</div></div>
  <div class="stat-card"><div class="num">{relevant}</div><div class="label">相关评论</div></div>
  <div class="stat-card"><div class="num">{top_score}</div><div class="label">最高关联分</div></div>
  <div class="stat-card"><div class="num">{len(comments) - relevant}</div><div class="label">无关评论</div></div>
</div>
<div class="filter-bar">
  <input type="text" id="searchBox" placeholder="🔍 在结果中搜索..." oninput="filterComments()">
  <select id="minScore" onchange="filterComments()">
    <option value="0">全部评分</option>
    <option value="5">≥ 5 分</option>
    <option value="8">≥ 8 分</option>
    <option value="10">≥ 10 分</option>
    <option value="12" selected>≥ 12 分</option>
    <option value="15">≥ 15 分（精确匹配）</option>
  </select>
  <span style="font-size:13px;color:#6b7280" id="resultCount"></span>
</div>
<div id="commentList">
''')

    for i, (score, reasons, cmt) in enumerate(scored):
        text = html_mod.escape((cmt.get('content', '') or '')[:500])
        nickname = html_mod.escape(cmt.get('nickname', '?') or '?')
        avatar = cmt.get('avatar', '') or ''
        likes = cmt.get('like_count', '0') or '0'
        aid = cmt.get('aweme_id', '')
        cmeta = content_map.get(aid, {})
        vtitle = html_mod.escape((cmeta.get('title', '?') or '?')[:60])
        vurl = html_mod.escape(cmeta.get('url', '') or '')
        vnick = html_mod.escape(cmeta.get('nickname', '?') or '?')

        tier = ''
        if i == 0: tier = 'gold'
        elif i == 1: tier = 'silver'
        elif i == 2: tier = 'bronze'

        reasons_html = ''.join(f'<span class="reason-tag">{r}</span>' for r in reasons[:5])

        avatar_html = ''
        if avatar:
            avatar_html = f'<img class="avatar" src="{html_mod.escape(avatar)}" alt="" loading="lazy" onerror="this.style.display=\'none\'">'
        else:
            initial = html_mod.escape(nickname[0]) if nickname else '?'
            avatar_html = f'<div class="avatar" style="background:#ef4444;color:#fff;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:bold;flex-shrink:0">{initial}</div>'

        parts.append(f'''
<div class="comment-item {tier}" data-score="{score}" data-text="{html_mod.escape(text.lower())}">
  <div class="rank">#{i+1}</div>
  {avatar_html}
  <div class="comment-body">
    <div class="comment-text">{text}</div>
    <div style="margin:4px 0">{reasons_html}</div>
    <div class="comment-meta">
      <span class="score-badge">⭐ {score}分</span>
      <span>{nickname}</span>
      <span>❤ {likes}</span>
    </div>
    <div class="comment-source">📹 <a href="{vurl}" target="_blank" title="{vtitle}">{vtitle}</a> · {vnick}</div>
  </div>
</div>''')

    parts.append('''
</div>
<div class="footer">MediaCrawler · 2026-06-11 · 关键词关联度排行</div>
</div>
<script>
function filterComments() {
    var q = (document.getElementById('searchBox').value || '').toLowerCase().trim();
    var min = parseInt(document.getElementById('minScore').value) || 0;
    var items = document.querySelectorAll('.comment-item');
    var count = 0;
    items.forEach(function(item) {
        var score = parseInt(item.getAttribute('data-score')) || 0;
        var text = item.getAttribute('data-text') || '';
        var show = score >= min && (!q || text.indexOf(q) >= 0);
        item.style.display = show ? 'flex' : 'none';
        if (show) count++;
    });
    document.getElementById('resultCount').textContent = '显示 ' + count + ' 条';
}
document.getElementById('resultCount').textContent = '显示 ' + document.querySelectorAll('.comment-item').length + ' 条';
</script>
</body>
</html>''')

    html = ''.join(parts)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"SCORED={relevant}")
    print(f"TOP_SCORE={top_score}")
    print(f"OUTPUT={OUT_PATH}")

    # 自动打开
    try:
        if sys.platform == 'win32':
            os.startfile(OUT_PATH)
        elif sys.platform == 'darwin':
            subprocess.run(['open', OUT_PATH])
        else:
            subprocess.run(['xdg-open', OUT_PATH])
        print("OPENED=1")
    except Exception as e:
        print(f"OPEN_ERROR={e}")

if __name__ == '__main__':
    main()
