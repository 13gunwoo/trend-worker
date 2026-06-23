# exporters/munpia_to_dashboard.py

import os
from datetime import date


def export(data, output_dir):
    today = date.today().strftime("%Y%m%d")
    platform = data.get("플랫폼", "unknown")
    filename = platform + "_" + today + ".html"
    filepath = os.path.join(output_dir, filename)

    os.makedirs(output_dir, exist_ok=True)

    html = _build_html(data)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return filepath


def _build_html(data):
    today = data.get("날짜", date.today().strftime("%Y-%m-%d"))
    platform = data.get("플랫폼", "")

    category_map = {
        "무료투데이베스트": "무료 투데이",
        "유료투데이베스트": "유료 투데이",
        "유료신규베스트"  : "유료 신규",
        "유료인기급상승"  : "유료 급상승",
    }

    tabs = []
    contents = []

    for key, label in category_map.items():
        if key in data:
            tab_id = key
            tabs.append((tab_id, label))
            contents.append((tab_id, _ranking_table(data[key])))

    tab_buttons = ""
    for i, (tab_id, tab_name) in enumerate(tabs):
        active = " active" if i == 0 else ""
        tab_buttons += '<button class="tab-btn' + active + '" onclick="showTab(\'' + tab_id + '\')" id="btn_' + tab_id + '">' + tab_name + '</button>'

    tab_contents = ""
    for i, (tab_id, content) in enumerate(contents):
        display = "block" if i == 0 else "none"
        tab_contents += '<div id="tab_' + tab_id + '" class="tab-content" style="display:' + display + '">' + content + '</div>'

    html = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>""" + platform + """ 트렌드 """ + today + """</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Arial, sans-serif; background: #f5f7fa; color: #333; }
  .header { background: #2E75B6; color: white; padding: 20px 30px; }
  .header h1 { font-size: 22px; }
  .header p { font-size: 13px; opacity: 0.85; margin-top: 4px; }
  .tab-bar { background: white; padding: 0 30px; border-bottom: 2px solid #e0e0e0; display: flex; gap: 4px; flex-wrap: wrap; }
  .tab-btn { padding: 12px 18px; border: none; background: none; cursor: pointer; font-size: 14px; color: #666; border-bottom: 3px solid transparent; transition: all 0.2s; }
  .tab-btn:hover { color: #2E75B6; }
  .tab-btn.active { color: #2E75B6; border-bottom-color: #2E75B6; font-weight: bold; }
  .container { padding: 24px 30px; }
  table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.08); font-size: 13px; }
  th { background: #2E75B6; color: white; padding: 10px 12px; text-align: left; font-weight: 600; }
  td { padding: 9px 12px; border-bottom: 1px solid #f0f0f0; }
  tr:hover td { background: #f8f9ff; }
  .rank { font-weight: bold; color: #2E75B6; text-align: center; }
  .desc { color: #666; font-size: 12px; max-width: 400px; }
</style>
</head>
<body>
<div class="header">
  <h1>""" + platform + """ 트렌드 리포트</h1>
  <p>수집일: """ + today + """</p>
</div>
<div class="tab-bar">""" + tab_buttons + """</div>
<div class="container">""" + tab_contents + """</div>
<script>
function showTab(id) {
  var contents = document.querySelectorAll('.tab-content');
  var buttons = document.querySelectorAll('.tab-btn');
  for (var i = 0; i < contents.length; i++) { contents[i].style.display = 'none'; }
  for (var i = 0; i < buttons.length; i++) { buttons[i].classList.remove('active'); }
  document.getElementById('tab_' + id).style.display = 'block';
  document.getElementById('btn_' + id).classList.add('active');
}
</script>
</body>
</html>"""

    return html


def _ranking_table(items):
    if not items:
        return "<p>데이터 없음</p>"

    rows = ""
    for item in items:
        desc = item.get("description") or ""
        desc_html = '<span class="desc">' + desc[:100] + ("..." if len(desc) > 100 else "") + '</span>' if desc else ""

        rows += "<tr>"
        rows += '<td class="rank">' + str(item.get("rank", "")) + "</td>"
        rows += "<td>" + item.get("title", "") + "</td>"
        rows += "<td>" + item.get("author", "") + "</td>"
        rows += "<td>" + item.get("genre", "") + "</td>"
        rows += "<td>" + desc_html + "</td>"
        rows += "</tr>"

    return """<table>
<thead><tr>
<th>순위</th><th>제목</th><th>작가</th><th>장르</th><th>소개글</th>
</tr></thead>
<tbody>""" + rows + "</tbody></table>"
