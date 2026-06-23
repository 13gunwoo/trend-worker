# exporters/comparison.py
# 순위 변동 비교 HTML 생성 및 파싱 (공통 모듈)

import json
import re
from datetime import date, timedelta


COLORS = [
    "#e6194b","#3cb44b","#ffe119","#4363d8","#f58231","#911eb4",
    "#42d4f4","#f032e6","#bfef45","#fabed4","#469990","#dcbeff",
    "#9A6324","#800000","#aaffc3","#808000","#ffd8b1","#000075",
    "#a9a9a9","#80aaff","#ff9999","#99ffcc","#ffcc99","#c0392b",
    "#2980b9","#8e44ad","#27ae60","#d35400","#1abc9c","#e74c3c",
    "#3498db","#f39c12","#2ecc71","#9b59b6","#e67e22","#1a5276",
    "#117a65","#7d6608","#5d6d7e","#a93226","#1f618d","#1e8449",
    "#d4ac0d","#6c3483","#ba4a00","#148f77","#4a235a","#154360",
    "#0b5345","#a04000",
]


def get_week_label(d=None):
    """
    날짜 기준 'n월 x주차' 문자열 반환.
    주차는 해당 월의 첫 번째 월요일을 1주차로 계산.
    """
    if d is None:
        d = date.today()

    month = d.month
    # 해당 월 1일
    first_day = date(d.year, d.month, 1)
    # 해당 월 첫 번째 월요일
    days_until_monday = (7 - first_day.weekday()) % 7
    first_monday = first_day + timedelta(days=days_until_monday)

    # 1일이 월요일이면 바로 1주차, 아니면 1일~첫월요일 전날은 1주차
    if d < first_monday:
        week_num = 1
    else:
        week_num = (d - first_monday).days // 7 + 2

    return str(month) + "월 " + str(week_num) + "주차"


def get_comparison_filename(label):
    """비교 HTML 파일명 반환. 예: '실시간랭킹 비교 6월 4주차.html'"""
    week_label = get_week_label()
    return label + " 비교 " + week_label + ".html"


def _hex_distance(c1, c2):
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    return ((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2) ** 0.5


def _assign_color(color_map):
    used = set(color_map.values())
    for c in COLORS:
        if c not in used and all(_hex_distance(c, u) >= 30 for u in used):
            return c
    for c in COLORS:
        if c not in used:
            return c
    return "#cccccc"


def parse_existing_html(html_content):
    """기존 비교 HTML에서 누적 데이터 추출. 없으면 빈 구조 반환."""
    if not html_content:
        return {"runs": [], "events": [], "color_map": {}}
    try:
        m = re.search(
            r'<script id="chart-data" type="application/json">(.*?)</script>',
            html_content, re.DOTALL
        )
        if m:
            return json.loads(m.group(1))
    except Exception:
        pass
    return {"runs": [], "events": [], "color_map": {}}


def get_prev_ranks(existing_data):
    """직전 회차 순위 딕셔너리 {제목: 순위} 반환."""
    runs = existing_data.get("runs", [])
    if not runs:
        return {}
    return dict(runs[-1].get("ranks", {}))


def calc_change(current_rank, prev_rank):
    """순위 변동 문자열 반환."""
    if prev_rank is None:
        return "NEW"
    try:
        diff = int(prev_rank) - int(current_rank)
    except (ValueError, TypeError):
        return "-"
    if diff > 0:
        return "▲" + str(diff)
    elif diff < 0:
        return "▼" + str(abs(diff))
    return "-"


def build_updated_html(existing_data, current_results, chart_title, title_key="제목", rank_key="순위"):
    """
    기존 데이터에 이번 회차를 추가하고 새 비교 HTML 생성.
    current_results: [{"순위": 1, "제목": "...", ...}, ...]
    title_key: 제목 필드명 (플랫폼마다 다를 수 있음)
    rank_key: 순위 필드명
    """
    runs      = existing_data.get("runs", [])
    events    = existing_data.get("events", [])
    color_map = existing_data.get("color_map", {})

    today = date.today().strftime("%Y-%m-%d")
    current_ranks = {
        item[title_key]: item[rank_key]
        for item in current_results
        if item.get(title_key)
    }
    run_num = len(runs) + 1
    runs.append({"run": run_num, "date": today, "ranks": current_ranks})

    # 색상 배정
    for title in current_ranks:
        if title not in color_map:
            color_map[title] = _assign_color(color_map)

    # IN/OUT 이벤트 감지
    if len(runs) >= 2:
        prev_set = set(runs[-2]["ranks"].keys())
        curr_set = set(current_ranks.keys())
        for title in (curr_set - prev_set):
            events.append({"type": "IN",  "title": title, "date": today, "run": run_num})
        for title in (prev_set - curr_set):
            events.append({"type": "OUT", "title": title, "date": today, "run": run_num})

    data_json = json.dumps(
        {"runs": runs, "events": events, "color_map": color_map},
        ensure_ascii=False, indent=2
    )

    week_label = get_week_label()

    html = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>""" + chart_title + """ 순위 추이 (""" + week_label + """)</title>
<style>
  body { font-family: 'Malgun Gothic', sans-serif; background: #fff; margin: 20px; }
  h2 { color: #333; }
  #chart-wrap { position: relative; overflow-x: auto; }
  canvas { display: block; }
  .events { margin-top: 24px; padding: 12px 16px; background: #f9f9f9; border-left: 4px solid #aaa; }
  .events h3 { margin: 0 0 8px; font-size: 14px; color: #555; cursor: pointer; user-select: none; }
  .event-item { font-size: 13px; margin: 4px 0; }
  .event-in  { color: #2a7ae2; }
  .event-out { color: #c0392b; }
</style>
</head>
<body>
<h2>""" + chart_title + """ 순위 추이 (""" + week_label + """)</h2>
<div id="chart-wrap"><canvas id="myChart"></canvas></div>
<div class="events">
  <h3 id="events-toggle" onclick="toggleEvents()">▶ 변동 사항 <span style="font-size:11px;color:#888">(클릭하여 펼치기)</span></h3>
  <div id="event-list" style="display:none;"></div>
</div>
<script id="chart-data" type="application/json">""" + data_json + """</script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
(function() {
  var raw    = JSON.parse(document.getElementById("chart-data").textContent);
  var runs   = raw.runs;
  var events = raw.events;
  var cmap   = raw.color_map;

  var labels = runs.map(function(r) { return r.date; });

  var allTitles = [];
  var seenT = {};
  runs.forEach(function(r) {
    Object.keys(r.ranks).forEach(function(t) {
      if (!seenT[t]) { allTitles.push(t); seenT[t] = true; }
    });
  });

  var datasets = allTitles.map(function(title) {
    var data = runs.map(function(r) {
      return r.ranks[title] !== undefined ? r.ranks[title] : null;
    });
    return {
      label: title,
      data: data,
      borderColor: cmap[title] || "#999",
      backgroundColor: cmap[title] || "#999",
      borderWidth: 2,
      pointRadius: 4,
      pointHoverRadius: 6,
      tension: 0,
      spanGaps: false,
    };
  });

  var ctx = document.getElementById("myChart").getContext("2d");
  new Chart(ctx, {
    type: "line",
    data: { labels: labels, datasets: datasets },
    options: {
      responsive: true,
      scales: {
        y: {
          reverse: true,
          min: 1,
          max: 20,
          ticks: { stepSize: 1 },
          title: { display: true, text: "순위" },
        },
        x: { title: { display: true, text: "날짜" } },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(ctx) { return ctx.dataset.label + ": " + ctx.parsed.y + "위"; }
          }
        }
      }
    }
  });

  window.toggleEvents = function() {
    var el = document.getElementById("event-list");
    var h3 = document.getElementById("events-toggle");
    var isHidden = el.style.display === "none";
    el.style.display = isHidden ? "block" : "none";
    h3.innerHTML = (isHidden ? "▼" : "▶") + " 변동 사항 <span style='font-size:11px;color:#888'>" + (isHidden ? "(클릭하여 접기)" : "(클릭하여 펼치기)") + "</span>";
  };

  var el = document.getElementById("event-list");
  if (events.length === 0) {
    el.innerHTML = "<span style='color:#999'>없음</span>";
  } else {
    events.forEach(function(ev) {
      var div = document.createElement("div");
      div.className = "event-item " + (ev.type === "IN" ? "event-in" : "event-out");
      if (ev.type === "IN") {
        div.textContent = "• \"" + ev.title + "\" 이(가) 새로 진입했습니다. (" + ev.date + " 기준)";
      } else {
        div.textContent = "• \"" + ev.title + "\" 이(가) 순위 밖으로 벗어났습니다. (" + ev.date + " 기준)";
      }
      el.appendChild(div);
    });
  }
})();
</script>
</body>
</html>"""

    return html
