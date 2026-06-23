# collectors/naver.py
# 네이버 웹툰 트렌드 수집기

from datetime import date
from collectors import naver_webtoon_crawler as crawler


def collect(options=None):
    """
    options: dict - 수집 범위 설정
      {
        "ranking"        : True,        # 전체/남성/여성 랭킹
        "ranking_limit"  : 20,          # 랭킹 수집 개수
        "genre"          : True,        # 장르별 목록
        "genre_list"     : [...],       # 수집할 장르 목록 (기본: 전체 9개)
        "genre_limit"    : 10,          # 장르별 수집 개수
        "day"            : True,        # 요일별 목록
        "day_list"       : [...],       # 수집할 요일 (기본: 전 요일)
        "search"         : False,       # 검색 (query 필요)
        "search_query"   : "",          # 검색어
        "search_limit"   : 20,          # 검색 결과 수
        "trend_analysis" : True,        # 트렌드 분석
        "trend_top_n"    : 10,          # 트렌드 분석 기준 상위 N개
        "full_dashboard" : False,       # 전체 통합 수집 (모든 항목 한번에)
        "exporters"      : ["json", "excel", "dashboard", "word"]
      }

    full_dashboard=True 이면 나머지 옵션 무시하고 전체 수집.
    """
    if options is None:
        options = {
            "ranking"        : True,
            "ranking_limit"  : 20,
            "genre"          : True,
            "genre_limit"    : 10,
            "day"            : True,
            "trend_analysis" : True,
            "trend_top_n"    : 10,
            "full_dashboard" : False,
        }

    today = date.today().strftime("%Y-%m-%d")
    result = {"날짜": today, "플랫폼": "네이버웹툰"}

    # full_dashboard 모드: 전체 통합 수집
    if options.get("full_dashboard", False):
        dashboard = crawler.get_full_dashboard()
        result["요일별랭킹"]  = dashboard.get("dayRankings", {})
        result["장르별랭킹"]  = dashboard.get("genreRankings", {})
        result["랭킹"]        = dashboard.get("rankings", {})
        result["트렌드태그"]  = dashboard.get("trendTags", [])
        result["인기작"]      = dashboard.get("popularByFavorite", [])
        return result

    # 랭킹
    if options.get("ranking", True):
        limit = options.get("ranking_limit", 20)
        result["랭킹"] = {
            "전체": crawler.get_ranking(gender="all",    limit=limit),
            "남성": crawler.get_ranking(gender="male",   limit=limit),
            "여성": crawler.get_ranking(gender="female", limit=limit),
        }

    # 장르별 목록
    if options.get("genre", True):
        genre_list = options.get("genre_list", crawler.DASHBOARD_GENRES)
        genre_limit = options.get("genre_limit", 10)
        result["장르별랭킹"] = {}
        for genre in genre_list:
            result["장르별랭킹"][genre] = crawler.get_webtoon_by_genre(genre=genre, limit=genre_limit)

    # 요일별 목록
    if options.get("day", True):
        day_list = options.get("day_list", ["월", "화", "수", "목", "금", "토", "일"])
        result["요일별랭킹"] = {}
        for day in day_list:
            result["요일별랭킹"][day] = crawler.get_webtoon_by_day(day=day)

    # 검색
    if options.get("search", False):
        query = options.get("search_query", "")
        if query:
            search_limit = options.get("search_limit", 20)
            result["검색결과"] = {
                "검색어": query,
                "목록": crawler.search_webtoon(query=query, limit=search_limit),
            }

    # 트렌드 분석
    if options.get("trend_analysis", True):
        top_n = options.get("trend_top_n", 10)
        trend = crawler.get_trend_analysis(top_n=top_n)
        result["트렌드분석"] = {
            "트렌드태그": trend.get("trendTags", []),
            "인기작"    : trend.get("popularByFavorite", []),
        }

    return result
