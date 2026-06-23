# exporters/naver_series_to_dashboard.py

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
    ranking_data = data.get("랭킹데이터", {})

    # 탭: 기간별
    tabs = []
    contents = []

    for period_ko, categories in ranking_data.items():
        tab_id = "period_" + period_ko
        tabs.append((tab_id, period_ko))
        contents.append((tab_id, _category_section(categories, period_ko)))

    tab_buttons = ""
    for i, (tab_id, tab_name) in enumerate(tabs):
        active = " active" if i == 0 else ""
        tab_buttons += '<button class="tab-btn' + active + '" onclick="showTab(\'' + tab_id + '\')" id="btn_' + tab_id + '">' + tab_name + '</button>'

    tab_contents = ""
    for i, (tab_id, content) in enumerate(contents):
        display = "block" if i == 0 else "none"
        tab_contents += '<div id="tab_' + tab_id + '" class="tab-content" style="display:' + display + '">' + content + '</div>'

    return """<!DOCTYPE html>
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
  .tab-btn { padding: 12px 18px; border: none; background: none; cursor: pointer; font-size: 14px; color: #666; border-bottom: 3px solid transparent; }
  .tab-btn.active { color: #2E75B6; border-bottom-color: #2E75B6; font-weight: bold; }
  .container { padding: 24px 30px; }
  .sub-tab-bar { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 16px; }
  .sub-tab-btn { padding: 6px 14px; border: 1px solid #ddd; background: white; border-radius: 20px; cursor: pointer; font-size: 13px; color: #666; }
  .sub-tab-btn.active { background: #2E75B6; color: white; border-color: #2E75B6; }
  table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.08); font-size: 13px; margin-bottom: 20px; }
  th { background: #2E75B6; color: white; padding: 10px 12px; text-align: left; font-weight: 600; }
  td { padding: 9px 12px; border-bottom: 1px solid #f0f0f0; }
  tr:hover td { background: #f8f9ff; }
  .rank { font-weight: bold; color: #2E75B6; text-align: center; }
  .up { color: #e53935; }
  .down { color: #1e88e5; }
  .new-badge { background: #ff6b35; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; }
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
  document.querySelectorAll('.tab-content').forEach(function(el) { el.style.display = 'none'; });
  document.querySelectorAll('.tab-btn').forEach(function(el) { el.classList.remove('active'); });
  document.getElementById('tab_' + id).style.display = 'block';
  document.getElementById('btn_' + id).classList.add('active');
}
function showSubTab(groupId, subId) {
  var group = document.getElementById(groupId);
  group.querySelectorAll('.sub-content').forEach(function(el) { el.style.display = 'none'; });
  group.querySelectorAll('.sub-tab-btn').forEach(function(el) { el.classList.remove('active'); });
  document.getElementById(subId).style.display = 'block';
  document.getElementById('sbtn_' + subId).classList.add('active');
}
</script>
</body>
</html>"""


def _category_section(categories, period_ko):
    if not categories:
        return "<p>데이터 없음</p>"

    keys = list(categories.keys())
    group_id = "grp_" + period_ko

    sub_btns = ""
    sub_contents = ""
    for i, cat_ko in enumerate(keys):
        sub_id = period_ko + "_cat_" + str(i)
        active_btn     = " active" if i == 0 else ""
        active_content = "block"   if i == 0 else "none"
        sub_btns     += '<button class="sub-tab-btn' + active_btn + '" id="sbtn_' + sub_id + '" onclick="showSubTab(\'' + group_id + '\',\'' + sub_id + '\')">' + cat_ko + '</button>'
        sub_contents += '<div id="' + sub_id + '" class="sub-content" style="display:' + active_content + '">' + _ranking_table(categories[cat_ko]) + '</div>'

    return '<div id="' + group_id + '"><div class="sub-tab-bar">' + sub_btns + '</div>' + sub_contents + '</div>'


def _ranking_table(items):
    if not items:
        return "<p>데이터 없음</p>"

    rows = ""
    for item in items:
        변동 = item.get("변동", "") or ""
        if "▲" in 변동:
            변동_html = '<span class="up">' + 변동 + '</span>'
        elif "▼" in 변동:
            변동_html = '<span class="down">' + 변동 + '</span>'
        elif 변동 == "NEW":
            변동_html = '<span class="new-badge">NEW</span>'
        else:
            변동_html = 변동

        rows += "<tr>"
        rows += '<td class="rank">' + str(item.get("순위", "")) + "</td>"
        rows += "<td>" + 변동_html + "</td>"
        rows += "<td>" + (item.get("제목") or "") + "</td>"
        rows += "<td>" + (item.get("작가") or "") + "</td>"
        rows += "<td>" + (item.get("출판사") or "") + "</td>"
        rows += "<td>" + (item.get("총화수") or "") + "</td>"
        rows += "<td>" + (item.get("별점") or "") + "</td>"
        rows += "<td>" + (item.get("전체다운로드수") or "") + "</td>"
        rows += "<td>" + (item.get("전체댓글수") or "") + "</td>"
        rows += "</tr>"

    return """<table>
<thead><tr>
<th>순위</th><th>변동</th><th>제목</th><th>작가</th><th>출판사</th><th>총화수</th><th>별점</th><th>다운로드</th><th>댓글</th>
</tr></thead>
<tbody>""" + rows + "</tbody></table>"
