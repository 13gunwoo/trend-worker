# collectors/naver_series.py
# 네이버 시리즈 웹소설 트렌드 수집기 (requests + BeautifulSoup)

import re
import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import date

BASE_URL = "https://series.naver.com/novel/top100List.series"
DETAIL_URL = "https://series.naver.com/novel/detail.series"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://series.naver.com/",
}

PERIODS = {
    "realtime" : "HOURLY",
    "daily"    : "DAILY",
    "weekly"   : "WEEKLY",
    "monthly"  : "MONTHLY",
}

PERIOD_KO = {
    "realtime" : "실시간",
    "daily"    : "일간",
    "weekly"   : "주간",
    "monthly"  : "월간",
}

CATEGORIES = {
    "fantasy" : "202",
    "modern"  : "208",
    "martial" : "206",
}

CATEGORY_KO = {
    "fantasy" : "판타지",
    "modern"  : "현대판타지",
    "martial" : "무협",
}


def _get(url, params=None):
    time.sleep(random.uniform(0.5, 1.2))
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        return resp
    except Exception as e:
        print("[naver_series] 요청 실패:", str(e))
        return None


def _get_soup(url, params=None):
    resp = _get(url, params)
    if not resp:
        return None
    return BeautifulSoup(resp.text, "html.parser")


def _fetch_ranking_list(period_code, category_code, limit=20):
    """랭킹 목록 페이지에서 작품 목록 파싱."""
    soup = _get_soup(BASE_URL, {"rankingTypeCode": period_code, "categoryCode": category_code})
    if not soup:
        return []

    results = []
    items = soup.select("ul.comic_top_lst > li")

    for idx, item in enumerate(items[:limit], 1):
        title_tag = item.select_one("a.pic")
        title = ""
        product_no = None

        if title_tag:
            # 제목
            title_text = item.select_one("span.title, strong.title, .tit")
            title = title_text.get_text(strip=True) if title_text else title_tag.get("title", "")

            # 작품 ID 추출
            href = title_tag.get("href", "")
            m = re.search(r"productNo=(\d+)", href)
            if m:
                product_no = m.group(1)

        results.append({
            "rank"      : idx,
            "title"     : title,
            "product_no": product_no,
        })

    return results


def _fetch_detail(product_no):
    """작품 상세 페이지에서 상세 정보 파싱."""
    if not product_no:
        return {}

    soup = _get_soup(DETAIL_URL, {"productNo": product_no})
    if not soup:
        return {}

    # 제목
    title_tag = soup.select_one("div.end_head h2, h2.tit_area")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # 작가/출판사
    # 실제 페이지에서 정보가 담긴 <ul>은 클래스가 없는 경우가 있어
    # 전체 li를 순회하며 <span>라벨</span> 패턴으로 식별한다.
    author = ""
    publisher = ""
    for li in soup.select("li"):
        label = li.find("span", recursive=False)
        if not label:
            continue
        label_text = label.get_text(strip=True)
        if label_text not in ["글", "작가", "출판사"]:
            continue
        value_tag = li.select_one("a, em")
        value = value_tag.get_text(strip=True) if value_tag else ""
        if label_text in ["글", "작가"] and not author:
            author = value
        elif label_text == "출판사" and not publisher:
            publisher = value

    # 총 화수
    ep_tag = soup.select_one("h5.end_total_episode strong, .total_episode strong")
    total_episodes = ep_tag.get_text(strip=True) + "화" if ep_tag else "0화"

    # 별점
    score = ""
    for sel in ["em.score_num", "em.score", "div.end_head em", "span.score_num"]:
        tag = soup.select_one(sel)
        if tag:
            val = tag.get_text(strip=True)
            if val and val.replace(".", "", 1).isdigit():
                score = val
                break

    # 다운로드 수
    dl_tag = soup.select_one("a.btn_download span, .btn_download span, .download_count")
    download_count = dl_tag.get_text(strip=True) if dl_tag else "0"

    # 댓글 수 (정적 HTML 기준)
    comment_tag = soup.select_one("#commentCount, .comment_count, .u_cbox_count")
    comment_count = comment_tag.get_text(strip=True) if comment_tag else "0"

    return {
        "title"         : title,
        "author"        : author or "작가 정보 없음",
        "publisher"     : publisher or "출판사 정보 없음",
        "total_episodes": "총 " + total_episodes,
        "score"         : score or "0.0",
        "download_count": download_count,
        "comment_count" : comment_count,
    }


def _fetch_category(period_code, category_code, period_ko, category_ko, limit=20):
    """기간+카테고리 조합 수집."""
    items = _fetch_ranking_list(period_code, category_code, limit)
    results = []

    for item in items:
        detail = _fetch_detail(item["product_no"])
        title = detail.get("title") or item["title"]

        results.append({
            "순위"          : item["rank"],
            "제목"          : title,
            "작가"          : detail.get("author", ""),
            "출판사"        : detail.get("publisher", ""),
            "총화수"        : detail.get("total_episodes", ""),
            "별점"          : detail.get("score", ""),
            "전체다운로드수": detail.get("download_count", ""),
            "전체댓글수"    : detail.get("comment_count", ""),
            "변동"          : None,  # 비교 후 채워짐
            "product_no"    : item["product_no"],
        })

    return results


def collect(options=None):
    """
    options: dict
      {
        "periods"    : ["realtime", "daily", "weekly", "monthly"],
        "categories" : ["fantasy", "modern", "martial"],
        "limit"      : 20,
        "exporters"  : ["json", "excel", "dashboard", "word"]
      }
    """
    if options is None:
        options = {
            "periods"   : ["daily"],
            "categories": ["fantasy", "modern", "martial"],
            "limit"     : 20,
        }

    today = date.today().strftime("%Y-%m-%d")
    periods    = options.get("periods",    ["daily"])
    categories = options.get("categories", list(CATEGORIES.keys()))
    limit      = min(options.get("limit", 20), 20)

    result = {
        "날짜"    : today,
        "플랫폼"  : "네이버시리즈",
        "랭킹데이터": {},
    }

    for period_key in periods:
        period_code = PERIODS.get(period_key)
        period_ko   = PERIOD_KO.get(period_key, period_key)
        if not period_code:
            continue

        result["랭킹데이터"][period_ko] = {}

        for cat_key in categories:
            cat_code  = CATEGORIES.get(cat_key)
            cat_ko    = CATEGORY_KO.get(cat_key, cat_key)
            if not cat_code:
                continue

            print("[네이버시리즈] 수집 중:", period_ko, cat_ko)
            items = _fetch_category(period_code, cat_code, period_ko, cat_ko, limit)
            result["랭킹데이터"][period_ko][cat_ko] = items

    return result
