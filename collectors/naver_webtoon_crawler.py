"""
네이버 웹툰 크롤러
확인된 내부 API만 사용 (폴백 없음)
"""

import sys
import time
import random
import requests
from typing import Optional


def _log(msg: str):
    """stderr로 디버그 로그 출력 (Claude Desktop 로그에서 확인 가능)"""
    print(f"[naver_webtoon] {msg}", file=sys.stderr, flush=True)

# ───────────────────────────────────────────────
# 공통 설정
# ───────────────────────────────────────────────

BASE_URL = "https://comic.naver.com"
API_BASE = "https://comic.naver.com/api"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://comic.naver.com/",
}

GENDER_MAP = {
    "male": "male", "female": "female", "all": "all",
    "남성": "male", "여성": "female", "전체": "all",
}

DAY_MAP = {
    "mon": "MONDAY", "tue": "TUESDAY", "wed": "WEDNESDAY",
    "thu": "THURSDAY", "fri": "FRIDAY", "sat": "SATURDAY", "sun": "SUNDAY",
    "월": "MONDAY", "화": "TUESDAY", "수": "WEDNESDAY",
    "목": "THURSDAY", "금": "FRIDAY", "토": "SATURDAY", "일": "SUNDAY",
}

GENRE_MAP = {
    # 영문 입력
    "romance": "PURE", "action": "ACTION", "fantasy": "FANTASY",
    "daily": "DAILY", "thriller": "THRILL", "gag": "COMIC",
    "drama": "DRAMA", "emotion": "SENSIBILITY", "sports": "SPORTS",
    "historical": "HISTORICAL", "school": "SCHOOL", "game": "GAME", "horror": "HORROR",
    # 한글 입력
    "로맨스": "PURE", "액션": "ACTION", "판타지": "FANTASY",
    "일상": "DAILY", "스릴러": "THRILL", "개그": "COMIC",
    "드라마": "DRAMA", "감성": "SENSIBILITY", "스포츠": "SPORTS",
    "무협/사극": "HISTORICAL", "학원": "SCHOOL", "게임판타지": "GAME", "공포": "HORROR",
    "드라마&영화 원작웹툰": "드라마&영화 원작",
    "먼치킨": "먼치킨",
    "요즘핫한추천작": "요즘핫한추천작",
    "학원로맨스": "학원로맨스",
    "로판": "로판",
    "동양풍판타지": "동양풍판타지",
    "로맨스코미디": "로맨스코미디",
    "역사물": "역사물",
    "현대판타지": "현대판타지",
    "연예계": "연예계",
}


# ───────────────────────────────────────────────
# 공통 requests GET
# ───────────────────────────────────────────────

def _get(url: str, params: dict = None) -> Optional[requests.Response]:
    try:
        time.sleep(random.uniform(0.3, 0.8))
        _log(f"GET {url} params={params}")
        resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
        _log(f"응답 상태: {resp.status_code}")
        resp.raise_for_status()
        return resp
    except requests.exceptions.HTTPError as e:
        _log(f"HTTP 오류: {e} | URL: {url}")
        return None
    except requests.exceptions.ConnectionError as e:
        _log(f"연결 오류: {e} | URL: {url}")
        return None
    except requests.exceptions.Timeout:
        _log(f"타임아웃 | URL: {url}")
        return None
    except Exception as e:
        _log(f"알 수 없는 오류: {e} | URL: {url}")
        return None


# ───────────────────────────────────────────────
# 1. 랭킹 조회
# ───────────────────────────────────────────────

def get_ranking(gender: str = "all", limit: int = 20) -> list[dict]:
    """
    네이버 웹툰 랭킹 조회.
    - gender="all" : realtime/ranking/list API, limit 적용 (최대 100)
    - gender="male/female" : 동일 API 응답의 성별 리스트 슬라이싱, 최대 5개 고정
    """
    gender_key = GENDER_MAP.get(gender.lower(), "all")

    resp = _get(f"{API_BASE}/realtime/ranking/list", {"rankTabType": "DEFAULT"})
    if not resp:
        _log("get_ranking: API 응답 없음")
        return []

    try:
        data = resp.json()
    except Exception as e:
        _log(f"get_ranking: JSON 파싱 실패 - {e}")
        return []

    if gender_key == "male":
        items = data.get("maleRankingTitleList", [])
    elif gender_key == "female":
        items = data.get("femaleRankingTitleList", [])
    else:
        items = data.get("totalRankingTitleList", [])
        # 전체는 5개뿐이므로 더 많이 필요하면 추가 페이지 없음 — limit만 적용
        # (API 자체가 5개 고정이므로 min 처리)

    return [_normalize_ranking_item(i) for i in items[:limit]]


def _normalize_ranking_item(item: dict) -> dict:
    title_id = str(item.get("titleId", ""))
    return {
        "rank": item.get("rank"),
        "titleId": title_id,
        "title": item.get("titleName"),
        "author": item.get("displayAuthor"),
        "thumbnail": item.get("thumbnailUrl"),
        "isUp": item.get("up", False),
        "isRest": item.get("rest", False),
        "badges": item.get("thumbnailBadgeList", []),
        "url": f"{BASE_URL}/webtoon/list?titleId={title_id}",
    }


# ───────────────────────────────────────────────
# 2. 작품 상세정보
# ───────────────────────────────────────────────

def get_webtoon_detail(title_id: str) -> dict:
    resp = _get(f"{API_BASE}/article/list/info", {"titleId": title_id})
    if not resp:
        _log(f"get_webtoon_detail: API 응답 없음 | titleId={title_id}")
        return {"error": "API 요청 실패"}

    try:
        data = resp.json()
    except Exception as e:
        _log(f"get_webtoon_detail: JSON 파싱 실패 - {e}")
        return {"error": "응답 파싱 실패"}

    if not data.get("titleId"):
        return {"error": f"titleId={title_id} 작품을 찾을 수 없습니다."}

    # 작가 정보
    artists = data.get("communityArtists", [])
    author = ", ".join(
        a.get("name", "") for a in artists if a.get("name")
    ) or data.get("author")

    # 장르/태그
    tags = [t.get("tagName") for t in data.get("curationTagList", []) if t.get("tagName")]

    return {
        "titleId": str(data.get("titleId")),
        "title": data.get("titleName"),
        "author": author,
        "synopsis": data.get("synopsis"),
        "thumbnail": data.get("thumbnailUrl"),
        "favoriteCount": data.get("favoriteCount"),
        "publishDays": data.get("publishDayOfWeekList", []),
        "isFinished": data.get("finished", False),
        "ageGrade": data.get("age", {}).get("description"),
        "tags": tags,
        "url": f"{BASE_URL}/webtoon/list?titleId={title_id}",
    }


# ───────────────────────────────────────────────
# 3. 장르별 목록
# ───────────────────────────────────────────────

def get_webtoon_by_genre(genre: str, limit: int = 20) -> list[dict]:
    genre_key = GENRE_MAP.get(genre.lower(), genre.upper())
    limit = min(limit, 50)
    _log(f"get_webtoon_by_genre: genre_key={genre_key}, limit={limit}")

    results = []
    page = 1
    page_size = min(limit, 25)

    while len(results) < limit:
        resp = _get(f"{API_BASE}/webtoon/titlelist/genre", {
            "type": "GENRE",
            "genre": genre_key,
            "page": page,
            "pageSize": page_size,
            "order": "USER",
        })
        if not resp:
            _log(f"get_webtoon_by_genre: API 응답 없음 | genre={genre_key}, page={page}")
            break

        try:
            raw = resp.json()
        except Exception as e:
            _log(f"get_webtoon_by_genre: JSON 파싱 실패 - {e}")
            break

        _log(f"get_webtoon_by_genre: 응답 타입={type(raw).__name__}, 키={list(raw.keys()) if isinstance(raw, dict) else 'list'}")

        # 응답이 배열인 경우 vs 객체로 래핑된 경우 모두 처리
        if isinstance(raw, list):
            items = raw
        elif isinstance(raw, dict):
            # titleList, items, data, list 등 가능한 키 순서대로 시도
            items = (
                raw.get("titleList")
                or raw.get("items")
                or raw.get("data")
                or raw.get("list")
                or []
            )
        else:
            _log(f"get_webtoon_by_genre: 예상치 못한 응답 형태 - {str(raw)[:200]}")
            break

        if not items:
            _log(f"get_webtoon_by_genre: 빈 결과 | genre={genre_key}, page={page}")
            break

        for item in items:
            if len(results) >= limit:
                break
            results.append(_normalize_list_item(item, len(results) + 1))

        if len(items) < page_size:
            break  # 마지막 페이지
        page += 1

    return results


# ───────────────────────────────────────────────
# 4. 요일별 목록
# ───────────────────────────────────────────────

def get_webtoon_by_day(day: str) -> list[dict]:
    day_key = DAY_MAP.get(day.strip().lower(), day.upper())

    resp = _get(f"{API_BASE}/webtoon/titlelist/weekday", {"order": "user"})
    if not resp:
        _log(f"get_webtoon_by_day: API 응답 없음 | day={day}")
        return []

    try:
        data = resp.json()
    except Exception as e:
        _log(f"get_webtoon_by_day: JSON 파싱 실패 - {e}")
        return []

    items = data.get("titleListMap", {}).get(day_key, [])
    return [_normalize_list_item(item, idx + 1) for idx, item in enumerate(items)]


# ───────────────────────────────────────────────
# 5. 검색
# ───────────────────────────────────────────────

def search_webtoon(query: str, limit: int = 20) -> list[dict]:
    limit = min(limit, 50)

    resp = _get(f"{API_BASE}/search/all", {"keyword": query})
    if not resp:
        _log(f"search_webtoon: API 응답 없음 | query={query}")
        return []

    try:
        raw = resp.json()
    except Exception as e:
        _log(f"search_webtoon: JSON 파싱 실패 - {e}")
        return []

    _log(f"search_webtoon: 응답 키={list(raw.keys()) if isinstance(raw, dict) else 'list'}")

    # 실제 응답 구조: searchNbooksComicResult.searchViewList
    items = raw.get("searchNbooksComicResult", {}).get("searchViewList", [])
    _log(f"search_webtoon: 결과 {len(items)}개")

    results = []
    for idx, item in enumerate(items[:limit]):
        content_id = str(item.get("contentId", ""))
        artists = item.get("communityArtists", [])
        author = ", ".join(a.get("name", "") for a in artists if a.get("name"))
        genres = [g.get("description", "") for g in item.get("genreList", []) if g.get("description")]

        results.append({
            "rank": idx + 1,
            "titleId": content_id,
            "title": item.get("titleName"),
            "author": author,
            "genres": genres,
            "isFinished": item.get("finished", False),
            "isAdult": item.get("adult", False),
            "isNew": item.get("new", False),
            "articleCount": item.get("articleTotalCount"),
            "lastUpdate": item.get("lastArticleServiceDate"),
            "url": f"{BASE_URL}/webtoon/list?titleId={content_id}",
        })

    return results


# ───────────────────────────────────────────────
# 6. 트렌드 분석
# ───────────────────────────────────────────────

def get_trend_analysis(top_n: int = 10) -> dict:
    """
    전체 요일 상위 작품을 수집하고 공통 태그/장르를 분석해 트렌드를 반환.
    - 7개 요일 × top_n개 수집 → 중복 제거 → 상세정보 일괄 조회
    - 태그/장르 집계 → 트렌드 키워드 추출
    """
    from collections import Counter

    _log(f"get_trend_analysis: 시작 | top_n={top_n}")

    # 1단계: 요일별 상위 작품 수집
    days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    seen_ids = set()
    candidates = []  # {"titleId", "title", "dayRanks": [...]}

    resp = _get(f"{API_BASE}/webtoon/titlelist/weekday", {"order": "user"})
    if not resp:
        _log("get_trend_analysis: 요일별 API 응답 없음")
        return {"error": "요일별 API 요청 실패"}

    try:
        weekday_data = resp.json()
    except Exception as e:
        _log(f"get_trend_analysis: 요일별 JSON 파싱 실패 - {e}")
        return {"error": "요일별 응답 파싱 실패"}

    title_map = {}  # titleId → {title, dayRanks}
    day_labels = {
        "MONDAY": "월", "TUESDAY": "화", "WEDNESDAY": "수",
        "THURSDAY": "목", "FRIDAY": "금", "SATURDAY": "토", "SUNDAY": "일"
    }

    for day_key, label in day_labels.items():
        items = weekday_data.get("titleListMap", {}).get(day_key, [])
        for rank, item in enumerate(items[:top_n], 1):
            title_id = str(item.get("titleId", ""))
            if not title_id:
                continue
            if title_id not in title_map:
                title_map[title_id] = {
                    "titleId": title_id,
                    "title": item.get("titleName"),
                    "dayRanks": []
                }
            title_map[title_id]["dayRanks"].append(f"{label}요일 {rank}위")

    candidates = list(title_map.values())
    _log(f"get_trend_analysis: 중복 제거 후 {len(candidates)}개 작품")

    # 2단계: 상세정보 일괄 조회
    tag_counter = Counter()
    genre_counter = Counter()
    favorite_list = []

    for item in candidates:
        detail = get_webtoon_detail(item["titleId"])
        if detail.get("error"):
            _log(f"get_trend_analysis: 상세정보 실패 | titleId={item['titleId']}")
            continue

        tags = detail.get("tags", [])
        for tag in tags:
            tag_counter[tag] += 1

        publish_days = detail.get("publishDays", [])
        for day in publish_days:
            genre_counter[day] += 1

        favorite_count = detail.get("favoriteCount") or 0
        favorite_list.append({
            "titleId": item["titleId"],
            "title": item["title"],
            "favoriteCount": favorite_count,
            "tags": tags,
            "dayRanks": item["dayRanks"],
            "url": detail.get("url"),
        })

    # 3단계: 집계
    favorite_list.sort(key=lambda x: x["favoriteCount"], reverse=True)

    _log(f"get_trend_analysis: 완료 | 분석 작품 수={len(favorite_list)}")

    return {
        "analyzedCount": len(favorite_list),
        "topN": top_n,
        "trendTags": [
            {"tag": tag, "count": count}
            for tag, count in tag_counter.most_common(20)
        ],
        "popularByFavorite": favorite_list[:20],
    }


# ───────────────────────────────────────────────
# 7. 대시보드 (트렌드 분석 통합)
# ───────────────────────────────────────────────

DASHBOARD_GENRES = ["판타지", "액션", "일상", "무협/사극", "로맨스", "드라마", "스릴러", "스포츠", "개그"]
DAY_LABEL_MAP = {
    "MONDAY": "월", "TUESDAY": "화", "WEDNESDAY": "수",
    "THURSDAY": "목", "FRIDAY": "금", "SATURDAY": "토", "SUNDAY": "일"
}

def get_full_dashboard() -> dict:
    """
    트렌드 분석 대시보드 데이터 한 번에 수집:
    - 요일별 TOP 10 (전 요일)
    - 대표 장르 9개 × TOP 10
    - 전체/남성/여성 랭킹 (각 5개)
    - 트렌드 태그 집계
    """
    from collections import Counter
    _log("get_full_dashboard: 시작")

    # 1. 요일별 TOP 10
    day_rankings = {}
    resp = _get(f"{API_BASE}/webtoon/titlelist/weekday", {"order": "user"})
    if resp:
        try:
            weekday_data = resp.json()
            title_map = {}
            for day_key, label in DAY_LABEL_MAP.items():
                items = weekday_data.get("titleListMap", {}).get(day_key, [])
                day_rankings[label] = [_normalize_list_item(item, idx + 1) for idx, item in enumerate(items[:10])]
                for rank, item in enumerate(items[:10], 1):
                    title_id = str(item.get("titleId", ""))
                    if title_id and title_id not in title_map:
                        title_map[title_id] = {"titleId": title_id, "title": item.get("titleName")}
        except Exception as e:
            _log(f"get_full_dashboard: 요일별 파싱 실패 - {e}")
            title_map = {}
    else:
        _log("get_full_dashboard: 요일별 API 실패")
        title_map = {}

    # 2. 장르별 TOP 10
    genre_rankings = {}
    for genre in DASHBOARD_GENRES:
        results = get_webtoon_by_genre(genre=genre, limit=10)
        genre_rankings[genre] = results

    # 3. 전체/성별 랭킹
    ranking_resp = _get(f"{API_BASE}/realtime/ranking/list", {"rankTabType": "DEFAULT"})
    rankings = {"전체": [], "남성": [], "여성": []}
    if ranking_resp:
        try:
            rdata = ranking_resp.json()
            rankings["전체"] = [_normalize_ranking_item(i) for i in rdata.get("totalRankingTitleList", [])]
            rankings["남성"] = [_normalize_ranking_item(i) for i in rdata.get("maleRankingTitleList", [])]
            rankings["여성"] = [_normalize_ranking_item(i) for i in rdata.get("femaleRankingTitleList", [])]
        except Exception as e:
            _log(f"get_full_dashboard: 랭킹 파싱 실패 - {e}")

    # 4. 트렌드 태그 집계 (요일별 수집 작품 기반)
    tag_counter = Counter()
    favorite_list = []
    for item in list(title_map.values()):
        detail = get_webtoon_detail(item["titleId"])
        if detail.get("error"):
            continue
        for tag in detail.get("tags", []):
            tag_counter[tag] += 1
        favorite_list.append({
            "titleId": item["titleId"],
            "title": item["title"],
            "favoriteCount": detail.get("favoriteCount") or 0,
            "tags": detail.get("tags", []),
            "url": detail.get("url"),
        })

    favorite_list.sort(key=lambda x: x["favoriteCount"], reverse=True)
    _log(f"get_full_dashboard: 완료")

    return {
        "dayRankings": day_rankings,
        "genreRankings": genre_rankings,
        "rankings": rankings,
        "trendTags": [{"tag": t, "count": c} for t, c in tag_counter.most_common(20)],
        "popularByFavorite": favorite_list[:20],
    }


# ───────────────────────────────────────────────
# 8. 더 보기
# ───────────────────────────────────────────────

def get_more_webtoons(category: str, value: str, offset: int = 10, limit: int = 10) -> list[dict]:
    """
    더 보기 요청 처리.
    - category="day"    : value=요일 한글(월/화/수/목/금/토/일)
    - category="genre"  : value=장르명(한글/영문)
    - category="ranking": value=전체/남성/여성 (5개 고정이라 추가 없음)
    """
    limit = min(limit, 50)
    _log(f"get_more_webtoons: category={category}, value={value}, offset={offset}, limit={limit}")

    if category == "day":
        day_key = DAY_MAP.get(value.strip(), value.upper())
        resp = _get(f"{API_BASE}/webtoon/titlelist/weekday", {"order": "user"})
        if not resp:
            return []
        try:
            data = resp.json()
        except Exception:
            return []
        items = data.get("titleListMap", {}).get(day_key, [])
        return [_normalize_list_item(item, offset + idx + 1) for idx, item in enumerate(items[offset:offset + limit])]

    elif category == "genre":
        genre_key = GENRE_MAP.get(value.lower(), value)
        page = (offset // 25) + 1
        page_offset = offset % 25
        resp = _get(f"{API_BASE}/webtoon/titlelist/genre", {
            "type": "GENRE",
            "genre": genre_key,
            "page": page,
            "pageSize": 25,
            "order": "USER",
        })
        if not resp:
            return []
        try:
            raw = resp.json()
        except Exception:
            return []
        items = raw if isinstance(raw, list) else (raw.get("titleList") or raw.get("items") or raw.get("data") or [])
        return [_normalize_list_item(item, offset + idx + 1) for idx, item in enumerate(items[page_offset:page_offset + limit])]

    else:
        _log(f"get_more_webtoons: 지원하지 않는 category={category}")
        return []


# ───────────────────────────────────────────────
# 공통 아이템 정규화 (랭킹 제외 목록용)
# ───────────────────────────────────────────────

def _normalize_list_item(item: dict, rank: int) -> dict:
    title_id = str(item.get("titleId", ""))
    return {
        "rank": rank,
        "titleId": title_id,
        "title": item.get("titleName"),
        "author": item.get("author"),
        "thumbnail": item.get("thumbnailUrl"),
        "starScore": item.get("starScore"),
        "isAdult": item.get("adult", False),
        "isFinished": item.get("finish", False),
        "isNew": item.get("new", False),
        "isUp": item.get("up", False),
        "url": f"{BASE_URL}/webtoon/list?titleId={title_id}",
    }
