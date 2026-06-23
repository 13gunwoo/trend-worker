# collectors/munpia.py
# 문피아 웹소설 트렌드 수집기

import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import date

BASE_URL = "https://www.munpia.com/page/j/view/w/best"

URLS = {
    "free_today"  : BASE_URL + "/today?displayType=GRID",
    "paid_today"  : BASE_URL + "/plsa.eachtoday?displayType=GRID",
    "paid_new"    : BASE_URL + "/plsa.newbie?displayType=GRID",
    "paid_rising" : BASE_URL + "/plsa.soar?displayType=GRID",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.munpia.com/",
}


def _get_soup(url, session):
    resp = session.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return BeautifulSoup(resp.text, "html.parser")


def _parse_top3(soup):
    results = []
    top3_wrap = soup.select_one("div.novel-top3")
    if not top3_wrap:
        return results

    for block in top3_wrap.select(":scope > div"):
        novel_link = block.select_one("a.novel-wrap")
        if not novel_link:
            continue

        rank_span = novel_link.select_one("div.top3-rank span.month")
        rank = ""
        if rank_span:
            outline = rank_span.select_one("span.outline")
            if outline:
                outline.decompose()
            rank = rank_span.get_text(strip=True).replace("위", "").strip()

        title_tag = novel_link.select_one("div.novel-title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        author_tag = novel_link.select_one("div.novel-author")
        author = author_tag.get_text(strip=True) if author_tag else ""

        genre_spans = novel_link.select("div.novel-genre span")
        genre = "".join(s.get_text(strip=True) for s in genre_spans).strip(", ")

        novel_url = novel_link.get("href", "")
        if novel_url and not novel_url.startswith("http"):
            novel_url = "https://novel.munpia.com" + novel_url

        results.append({
            "rank"        : int(rank) if rank.isdigit() else rank,
            "title"       : title,
            "author"      : author,
            "genre"       : genre,
            "url"         : novel_url,
            "description" : None,
        })

    return results


def _parse_list(soup, limit=10):
    results = []
    list_wrap = soup.select_one("div.best-rank-list")
    if not list_wrap:
        return results

    for item in list_wrap.select(":scope > a"):
        if len(results) >= limit - 3:
            break

        num_tag = item.select_one("div.num")
        rank = num_tag.get_text(strip=True) if num_tag else ""

        title_tag = item.select_one("div.title span.title-wrap")
        title = title_tag.get_text(strip=True) if title_tag else ""

        author_tag = item.select_one("div.author")
        author = author_tag.get_text(strip=True) if author_tag else ""

        genre_spans = item.select("div.genre span")
        genre = "".join(s.get_text(strip=True) for s in genre_spans).strip(", ")

        novel_url = item.get("href", "")
        if novel_url and not novel_url.startswith("http"):
            novel_url = "https://novel.munpia.com" + novel_url

        results.append({
            "rank"        : int(rank) if rank.isdigit() else rank,
            "title"       : title,
            "author"      : author,
            "genre"       : genre,
            "url"         : novel_url,
            "description" : None,
        })

    return results


def _fetch_description(novel_url, session):
    try:
        soup = _get_soup(novel_url, session)
        story_tag = soup.select_one("div#STORY-BOX p.story")
        if story_tag:
            for br in story_tag.find_all("br"):
                br.replace_with("\n")
            return story_tag.get_text(strip=True)
    except Exception as e:
        return "[소개글 수집 실패: " + str(e) + "]"
    return ""


def _fetch_best(url, include_description=False, limit=10):
    session = requests.Session()

    try:
        soup = _get_soup(url, session)
    except requests.RequestException as e:
        raise RuntimeError("페이지 요청 실패: " + str(e))

    top3 = _parse_top3(soup)
    rest = _parse_list(soup, limit=limit)
    novels = (top3 + rest)[:limit]

    if not novels:
        raise RuntimeError("작품 목록을 찾을 수 없습니다. 사이트 구조가 변경되었을 수 있습니다.")

    if include_description:
        for novel in novels:
            if novel.get("url"):
                novel["description"] = _fetch_description(novel["url"], session)
                time.sleep(0.7)

    return novels


def collect(options=None):
    """
    options: dict - 수집 범위 설정
      {
        "free_today"        : True,   # 무료 투데이 베스트
        "paid_today"        : True,   # 유료 투데이 베스트
        "paid_new"          : True,   # 유료 신규 베스트
        "paid_rising"       : True,   # 유료 인기급상승 베스트
        "include_description": False, # 소개글 수집 여부
        "limit"             : 10,     # 수집 작품 수 (최대 50)
        "exporters"         : ["json", "excel", "dashboard", "word"]
      }
    """
    if options is None:
        options = {
            "free_today"         : True,
            "paid_today"         : True,
            "paid_new"           : True,
            "paid_rising"        : True,
            "include_description": False,
            "limit"              : 10,
        }

    today = date.today().strftime("%Y-%m-%d")
    include_desc = options.get("include_description", False)
    limit = max(1, min(options.get("limit", 10), 50))

    result = {"날짜": today, "플랫폼": "문피아"}

    if options.get("free_today", True):
        result["무료투데이베스트"] = _fetch_best(URLS["free_today"], include_desc, limit)

    if options.get("paid_today", True):
        result["유료투데이베스트"] = _fetch_best(URLS["paid_today"], include_desc, limit)

    if options.get("paid_new", True):
        result["유료신규베스트"] = _fetch_best(URLS["paid_new"], include_desc, limit)

    if options.get("paid_rising", True):
        result["유료인기급상승"] = _fetch_best(URLS["paid_rising"], include_desc, limit)

    return result
