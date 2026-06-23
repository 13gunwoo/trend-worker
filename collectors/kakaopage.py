# collectors/kakaopage.py
# 카카오페이지 웹소설 트렌드 수집기

import json
import re
import requests
from datetime import date

BASE_URL = "https://page.kakao.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://page.kakao.com/",
}

SCREEN_MAP = {
    "realtime":  94,
    "fantasy":   91,
    "martial":   70,
    "modern":    64,
    "romance_f": 92,
    "romance":   68,
    "new":       101,
}

GENRE_KO = {
    "fantasy":   "판타지",
    "martial":   "무협",
    "modern":    "현판",
    "romance_f": "로판",
    "romance":   "로맨스",
}


def _fetch_next_data(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        resp.text,
        re.DOTALL,
    )
    if not match:
        raise ValueError("__NEXT_DATA__ 를 찾을 수 없습니다.")
    return json.loads(match.group(1))


def _get_sections(data):
    try:
        return (
            data["props"]["pageProps"]["initialProps"]
            ["dehydratedState"]["queries"][0]["state"]["data"]["sections"]
        )
    except (KeyError, IndexError):
        return []


def _extract_series_id(item):
    sid = item.get("seriesId")
    if sid:
        return sid
    scheme = item.get("scheme", "")
    m = re.search(r"series_id=(\d+)", scheme)
    if m:
        return int(m.group(1))
    return None


def _parse_ranking_items(data, limit):
    sections = _get_sections(data)
    items = None
    for sec in sections:
        if sec.get("type") == "LandingRanking":
            try:
                items = sec["groups"][0]["items"]
            except (KeyError, IndexError):
                pass
            break

    if not items:
        return []

    results = []
    for item in items:
        if item.get("type") != "RankingPosterView":
            continue
        rank = item.get("rank")
        if rank is None:
            continue
        try:
            rank_int = int(rank)
        except (ValueError, TypeError):
            continue
        if rank_int > limit:
            continue

        meta = item.get("eventLog", {}).get("eventMeta", {})
        subtitle = item.get("subtitleList", [])

        variation = item.get("rankVariation")
        if variation is None:
            variation_str = "신규"
        elif variation == 0:
            variation_str = "-"
        elif variation > 0:
            variation_str = "▲" + str(variation)
        else:
            variation_str = "▼" + str(abs(variation))

        results.append({
            "순위": rank_int,
            "변동": variation_str,
            "작품명": item.get("title", ""),
            "작가": subtitle[2] if len(subtitle) > 2 else "",
            "장르": meta.get("subcategory", ""),
            "조회수": subtitle[0] if len(subtitle) > 0 else "",
            "연재상태": subtitle[1] if len(subtitle) > 1 else "",
            "연령등급": "성인" if item.get("ageGrade") == "Nineteen" else "전체",
            "series_id": _extract_series_id(item),
        })

    results.sort(key=lambda x: x["순위"])
    return results


def _parse_today_new(data, days):
    sections = _get_sections(data)
    groups = None
    for sec in sections:
        if sec.get("type") == "LandingTodayNew":
            groups = sec.get("groups", [])
            break

    if not groups:
        return []

    target_groups = groups[:days]
    results = []
    for grp in target_groups:
        meta = grp.get("meta", {})
        date_label = meta.get("title", "")
        count = meta.get("count", 0)
        items = grp.get("items", [])

        day_items = []
        for item in items:
            meta2 = item.get("eventLog", {}).get("eventMeta", {})
            subtitle = item.get("subtitleList", [])
            day_items.append({
                "작품명": item.get("title", ""),
                "장르": meta2.get("subcategory", ""),
                "조회수": subtitle[0] if subtitle else "",
                "연령등급": "성인" if item.get("ageGrade") == "Nineteen" else "전체",
                "series_id": _extract_series_id(item),
            })

        results.append({
            "날짜": date_label,
            "신작수": count,
            "작품목록": day_items,
        })

    return results


def _fetch_series_detail(series_id):
    url = BASE_URL + "/content/" + str(series_id) + "?tab_type=about"
    data = _fetch_next_data(url)

    try:
        content = (
            data["props"]["pageProps"]["initialProps"]
            ["dehydratedState"]["queries"][0]
            ["state"]["data"]["contentHomeOverview"]["content"]
        )
    except (KeyError, IndexError):
        return None

    svc = content.get("serviceProperty", {})

    rating_count = svc.get("ratingCount", 0)
    rating_sum = svc.get("ratingSum", 0)
    if rating_count > 0:
        rating = round(rating_sum / rating_count, 2)
        rating_str = str(rating) + " (" + str(rating_count) + "명)"
    else:
        rating_str = "정보 없음"

    bm = content.get("bm", "")
    free_count = content.get("freeSlideCount", 0)
    waitfree_block = content.get("waitfreeBlockCount", 0)
    waitfree_min = content.get("waitfreePeriodByMinute", 0)
    waitfree_hours = waitfree_min // 60

    if bm == "PayWaitfree":
        if waitfree_hours == 24:
            bm_str = "기다무 (매일 " + str(waitfree_block) + "화 무료)"
        elif waitfree_hours == 3:
            bm_str = "삼다무 (3시간마다 " + str(waitfree_block) + "화 무료)"
        else:
            bm_str = "기다무 (" + str(waitfree_hours) + "시간마다 " + str(waitfree_block) + "화 무료)"
    elif bm == "Free":
        bm_str = "전체 무료"
    else:
        bm_str = bm if bm else "유료"

    keywords_raw = (
        data["props"]["pageProps"]
        .get("initialProps", {})
        .get("metaInfo", {})
        .get("keywords", "")
    )
    keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]

    on_issue = content.get("onIssue", "")

    return {
        "series_id": series_id,
        "작품명": content.get("title", ""),
        "작가": content.get("authors", ""),
        "장르": content.get("subcategory", ""),
        "연령등급": "성인" if content.get("ageGrade") == "Nineteen" else "전체",
        "연재상태": "완결" if on_issue == "End" else "연재중",
        "연재주기": content.get("pubPeriod", ""),
        "조회수": svc.get("viewCount", 0),
        "댓글수": svc.get("commentCount", 0),
        "별점": rating_str,
        "무료회차": free_count,
        "결제방식": bm_str,
        "키워드": ", ".join(keywords),
    }


def collect(options=None):
    """
    options: dict - 수집 범위 설정
      {
        "realtime": True,         # 실시간 랭킹
        "genre": True,            # 장르별 랭킹
        "new": True,              # 신작
        "detail": True,           # 작품 상세
        "extended": True,         # Top30 (False면 Top10)
        "new_days": 3             # 신작 조회 일수
      }
    """
    if options is None:
        options = {
            "realtime": True,
            "genre": True,
            "new": True,
            "detail": True,
            "extended": True,
            "new_days": 3,
        }

    today = date.today().strftime("%Y-%m-%d")
    limit = 30 if options.get("extended", True) else 10
    result = {"날짜": today, "플랫폼": "카카오페이지"}

    # 실시간 랭킹
    if options.get("realtime", True):
        url = BASE_URL + "/menu/10011/screen/" + str(SCREEN_MAP["realtime"])
        data = _fetch_next_data(url)
        result["실시간랭킹"] = _parse_ranking_items(data, limit)

    # 장르별 랭킹
    if options.get("genre", True):
        result["장르별랭킹"] = {}
        for genre_code, genre_name in GENRE_KO.items():
            url = BASE_URL + "/menu/10011/screen/" + str(SCREEN_MAP[genre_code])
            data = _fetch_next_data(url)
            result["장르별랭킹"][genre_name] = _parse_ranking_items(data, limit)

    # 신작
    if options.get("new", True):
        days = options.get("new_days", 3)
        url = BASE_URL + "/menu/10011/screen/" + str(SCREEN_MAP["new"])
        data = _fetch_next_data(url)
        result["신작"] = _parse_today_new(data, days)

    # 작품 상세
    if options.get("detail", True):
        series_ids = set()
        if "실시간랭킹" in result:
            for item in result["실시간랭킹"]:
                if item.get("series_id"):
                    series_ids.add(item["series_id"])
        if "장르별랭킹" in result:
            for items in result["장르별랭킹"].values():
                for item in items:
                    if item.get("series_id"):
                        series_ids.add(item["series_id"])

        details = []
        for sid in series_ids:
            detail = _fetch_series_detail(sid)
            if detail:
                details.append(detail)
        result["작품상세"] = details

    return result
