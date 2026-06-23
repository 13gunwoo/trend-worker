# exporters/naver_to_dashboard.py

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

    tabs = []
    contents = []

    # 랭킹
    if "랭킹" in data:
        tabs.append(("ranking", "랭킹"))
        contents.append(("ranking", _ranking_section(data["랭킹"])))

    # 요일별 랭킹
    if "요일별랭킹" in data:
        tabs.append(("day", "요일별"))
        contents.append(("day", _tab_section(data["요일별랭킹"], "day", _list_table)))

    # 장르별 랭킹
    if "장르별랭킹" in data:
        tabs.append(("genre", "장르별"))
        contents.append(("genre", _tab_section(data["장르별랭킹"], "genre", _list_table)))

    # 검색결과
    if "검색결과" in data:
        query = data["검색결과"].get("검색어", "")
        tabs.append(("search", "검색: " + query))
        contents.append(("search", _search_table(data["검색결과"].get("목록", []))))

    # 트렌드 분석
    if "트렌드분석" in data:
        tabs.append(("trend", "트렌드분석"))
        contents.append(("trend", _trend_section(data["트렌드분석"])))

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
  .badge { padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-left: 4px; }
  .badge-up { background: #e8f5e9; color: #2e7d32; }
  .badge-new { background: #fff3e0; color: #e65100; }
  .badge-adult { background: #fce4ec; color: #c62828; }
  .badge-finish { background: #e3f2fd; color: #1565c0; }
  .cols2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  .tag-list { display: flex; flex-wrap: wrap; gap: 8px; padding: 16px 0; }
  .tag-item { background: white; border: 1px solid #ddd; border-radius: 20px; padding: 4px 12px; font-size: 13px; }
  .tag-count { color: #2E75B6; font-weight: bold; margin-left: 4px; }
  h3 { font-size: 15px; margin-bottom: 12px; color: #444; }
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


def _ranking_section(rankings):
    html = '<div class="cols2">'
    for label, items in rankings.items():
        html += '<div><h3>' + label + ' 랭킹</h3>'
        html += _ranking_table(items)
        html += '</div>'
    html += '</div>'
    return html


def _tab_section(data_dict, prefix, table_fn):
    if not data_dict:
        return "<p>데이터 없음</p>"

    keys = list(data_dict.keys())
    group_id = "grp_" + prefix

    sub_btns = ""
    sub_contents = ""
    for i, key in enumerate(keys):
        sub_id = prefix + "_" + str(i)
        active_btn = " active" if i == 0 else ""
        active_content = "block" if i == 0 else "none"
        sub_btns += '<button class="sub-tab-btn' + active_btn + '" id="sbtn_' + sub_id + '" onclick="showSubTab(\'' + group_id + '\',\'' + sub_id + '\')">' + key + '</button>'
        sub_contents += '<div id="' + sub_id + '" class="sub-content" style="display:' + active_content + '">' + table_fn(data_dict[key]) + '</div>'

    return '<div id="' + group_id + '"><div class="sub-tab-bar">' + sub_btns + '</div>' + sub_contents + '</div>'


def _ranking_table(items):
    if not items:
        return "<p>데이터 없음</p>"
    rows = ""
    for item in items:
        badges = ""
        if item.get("isUp"):
            badges += '<span class="badge badge-up">↑</span>'
        rows += "<tr>"
        rows += '<td class="rank">' + str(item.get("rank", "")) + "</td>"
        rows += "<td>" + (item.get("title") or "") + badges + "</td>"
        rows += "<td>" + (item.get("author") or "") + "</td>"
        rows += '<td><a href="' + (item.get("url") or "") + '" target="_blank">보기</a></td>'
        rows += "</tr>"
    return "<table><thead><tr><th>순위</th><th>제목</th><th>작가</th><th>링크</th></tr></thead><tbody>" + rows + "</tbody></table>"


def _list_table(items):
    if not items:
        return "<p>데이터 없음</p>"
    rows = ""
    for item in items:
        badges = ""
        if item.get("isNew"):
            badges += '<span class="badge badge-new">NEW</span>'
        if item.get("isFinished"):
            badges += '<span class="badge badge-finish">완결</span>'
        if item.get("isAdult"):
            badges += '<span class="badge badge-adult">성인</span>'
        rows += "<tr>"
        rows += '<td class="rank">' + str(item.get("rank", "")) + "</td>"
        rows += "<td>" + (item.get("title") or "") + badges + "</td>"
        rows += "<td>" + (item.get("author") or "") + "</td>"
        rows += "<td>" + str(item.get("starScore") or "") + "</td>"
        rows += '<td><a href="' + (item.get("url") or "") + '" target="_blank">보기</a></td>'
        rows += "</tr>"
    return "<table><thead><tr><th>순위</th><th>제목</th><th>작가</th><th>별점</th><th>링크</th></tr></thead><tbody>" + rows + "</tbody></table>"


def _search_table(items):
    if not items:
        return "<p>검색 결과 없음</p>"
    rows = ""
    for item in items:
        badges = ""
        if item.get("isNew"):
            badges += '<span class="badge badge-new">NEW</span>'
        if item.get("isFinished"):
            badges += '<span class="badge badge-finish">완결</span>'
        genres = ", ".join(item.get("genres", []))
        rows += "<tr>"
        rows += '<td class="rank">' + str(item.get("rank", "")) + "</td>"
        rows += "<td>" + (item.get("title") or "") + badges + "</td>"
        rows += "<td>" + (item.get("author") or "") + "</td>"
        rows += "<td>" + genres + "</td>"
        rows += '<td><a href="' + (item.get("url") or "") + '" target="_blank">보기</a></td>'
        rows += "</tr>"
    return "<table><thead><tr><th>순위</th><th>제목</th><th>작가</th><th>장르</th><th>링크</th></tr></thead><tbody>" + rows + "</tbody></table>"


def _trend_section(trend):
    html = ""

    tags = trend.get("트렌드태그", [])
    if tags:
        html += "<h3>트렌드 태그 TOP 20</h3><div class='tag-list'>"
        for t in tags:
            html += '<span class="tag-item">' + t.get("tag", "") + '<span class="tag-count">' + str(t.get("count", 0)) + '</span></span>'
        html += "</div>"

    popular = trend.get("인기작", [])
    if popular:
        html += "<h3 style='margin-top:20px'>구독자수 기준 인기작 TOP 20</h3>"
        rows = ""
        for item in popular:
            tags_str = ", ".join(item.get("tags", []))
            rows += "<tr>"
            rows += "<td>" + (item.get("title") or "") + "</td>"
            rows += "<td>" + str(item.get("favoriteCount") or 0) + "</td>"
            rows += "<td>" + tags_str + "</td>"
            rows += '<td><a href="' + (item.get("url") or "") + '" target="_blank">보기</a></td>'
            rows += "</tr>"
        html += "<table><thead><tr><th>제목</th><th>구독자수</th><th>태그</th><th>링크</th></tr></thead><tbody>" + rows + "</tbody></table>"

    return html
