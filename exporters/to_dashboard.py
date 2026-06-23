# exporters/to_dashboard.py
# 수집 데이터를 HTML 대시보드로 변환

import os
import json
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

    # 탭 목록 구성
    tabs = []
    contents = []

    if "실시간랭킹" in data:
        tabs.append(("realtime", "실시간랭킹"))
        contents.append(("realtime", _ranking_table(data["실시간랭킹"])))

    if "장르별랭킹" in data:
        for genre_name, items in data["장르별랭킹"].items():
            tab_id = "genre_" + genre_name
            tabs.append((tab_id, genre_name))
            contents.append((tab_id, _ranking_table(items)))

    if "신작" in data:
        tabs.append(("new", "신작"))
        contents.append(("new", _new_table(data["신작"])))

    if "작품상세" in data:
        tabs.append(("detail", "작품상세"))
        contents.append(("detail", _detail_table(data["작품상세"])))

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
  .up { color: #e53935; }
  .down { color: #1e88e5; }
  .new-badge { background: #ff6b35; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; }
  .adult-badge { background: #c62828; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; }
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
  for (var i = 0; i < contents.length; i++) {
    contents[i].style.display = 'none';
  }
  for (var i = 0; i < buttons.length; i++) {
    buttons[i].classList.remove('active');
  }
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
        변동 = item.get("변동", "")
        if "▲" in 변동:
            변동_html = '<span class="up">' + 변동 + '</span>'
        elif "▼" in 변동:
            변동_html = '<span class="down">' + 변동 + '</span>'
        elif 변동 == "신규":
            변동_html = '<span class="new-badge">신규</span>'
        else:
            변동_html = 변동

        연령 = item.get("연령등급", "")
        adult_html = '<span class="adult-badge">성인</span>' if 연령 == "성인" else ""

        rows += "<tr>"
        rows += '<td class="rank">' + str(item.get("순위", "")) + "</td>"
        rows += "<td>" + 변동_html + "</td>"
        rows += "<td>" + item.get("작품명", "") + " " + adult_html + "</td>"
        rows += "<td>" + item.get("작가", "") + "</td>"
        rows += "<td>" + item.get("장르", "") + "</td>"
        rows += "<td>" + item.get("조회수", "") + "</td>"
        rows += "<td>" + item.get("연재상태", "") + "</td>"
        rows += "</tr>"

    return """<table>
<thead><tr>
<th>순위</th><th>변동</th><th>작품명</th><th>작가</th><th>장르</th><th>조회수</th><th>연재상태</th>
</tr></thead>
<tbody>""" + rows + "</tbody></table>"


def _new_table(day_groups):
    if not day_groups:
        return "<p>데이터 없음</p>"

    rows = ""
    for group in day_groups:
        date_label = group.get("날짜", "")
        for item in group.get("작품목록", []):
            연령 = item.get("연령등급", "")
            adult_html = '<span class="adult-badge">성인</span>' if 연령 == "성인" else ""
            rows += "<tr>"
            rows += "<td>" + date_label + "</td>"
            rows += "<td>" + item.get("작품명", "") + " " + adult_html + "</td>"
            rows += "<td>" + item.get("장르", "") + "</td>"
            rows += "<td>" + item.get("조회수", "") + "</td>"
            rows += "</tr>"

    return """<table>
<thead><tr>
<th>날짜</th><th>작품명</th><th>장르</th><th>조회수</th>
</tr></thead>
<tbody>""" + rows + "</tbody></table>"


def _detail_table(items):
    if not items:
        return "<p>데이터 없음</p>"

    rows = ""
    for item in items:
        rows += "<tr>"
        rows += "<td>" + item.get("작품명", "") + "</td>"
        rows += "<td>" + item.get("작가", "") + "</td>"
        rows += "<td>" + item.get("장르", "") + "</td>"
        rows += "<td>" + item.get("연재상태", "") + "</td>"
        rows += "<td>" + str(item.get("조회수", "")) + "</td>"
        rows += "<td>" + item.get("별점", "") + "</td>"
        rows += "<td>" + item.get("결제방식", "") + "</td>"
        rows += "<td>" + item.get("키워드", "") + "</td>"
        rows += "</tr>"

    return """<table>
<thead><tr>
<th>작품명</th><th>작가</th><th>장르</th><th>연재상태</th><th>조회수</th><th>별점</th><th>결제방식</th><th>키워드</th>
</tr></thead>
<tbody>""" + rows + "</tbody></table>"
