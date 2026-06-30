# main.py
# 트렌드 수집 메인 실행 파일

import os
import json
import subprocess
import tempfile

from exporters import to_json, to_excel, to_dashboard
from exporters import munpia_to_excel, munpia_to_dashboard
from exporters import naver_to_excel, naver_to_dashboard
from exporters import naver_series_to_excel, naver_series_to_dashboard
from exporters import comparison
from uploader import gdrive
from notifier import kakao

DEFAULT_EXPORTERS = ["json", "excel", "dashboard", "word"]


def parse_options(platform):
    """
    GitHub Actions에서 넘어온 옵션 파싱
    환경변수 COLLECT_OPTIONS_{PLATFORM} 에서 읽음
    예: COLLECT_OPTIONS_KAKAOPAGE={"realtime":true,"genre":true,"exporters":["json","excel"]}
    """
    key = "COLLECT_OPTIONS_" + platform.upper()
    raw = os.environ.get(key)
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return None  # None이면 기본값(전체) 사용


def run_exporters(data, options, output_dir, label, platform_key="kakaopage"):
    """
    options의 exporters 키에 따라 선택적으로 파일 생성.
    exporters 키 없으면 전체 생성.
    platform_key로 플랫폼별 익스포터 분기.
    """
    exporters = options.get("exporters", DEFAULT_EXPORTERS) if options else DEFAULT_EXPORTERS
    filepaths = []

    if "json" in exporters:
        path = to_json.export(data, output_dir)
        filepaths.append(path)
        print("[" + label + "] JSON 생성 완료:", path)

    if "excel" in exporters:
        if platform_key == "munpia":
            path = munpia_to_excel.export(data, output_dir)
        elif platform_key == "naver":
            path = naver_to_excel.export(data, output_dir)
        elif platform_key == "naver_series":
            path = naver_series_to_excel.export(data, output_dir)
        else:
            path = to_excel.export(data, output_dir)
        filepaths.append(path)
        print("[" + label + "] Excel 생성 완료:", path)

    if "dashboard" in exporters:
        if platform_key == "munpia":
            path = munpia_to_dashboard.export(data, output_dir)
        elif platform_key == "naver":
            path = naver_to_dashboard.export(data, output_dir)
        elif platform_key == "naver_series":
            path = naver_series_to_dashboard.export(data, output_dir)
        else:
            path = to_dashboard.export(data, output_dir)
        filepaths.append(path)
        print("[" + label + "] 대시보드 생성 완료:", path)

    if "word" in exporters:
        tmp_json = os.path.join(output_dir, "tmp_data.json")
        with open(tmp_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.environ["TEMP_DATA_PATH"] = tmp_json

        if platform_key == "munpia":
            word_script = os.path.join(os.path.dirname(__file__), "exporters", "munpia_to_word.js")
        elif platform_key == "naver":
            word_script = os.path.join(os.path.dirname(__file__), "exporters", "naver_to_word.js")
        elif platform_key == "naver_series":
            word_script = os.path.join(os.path.dirname(__file__), "exporters", "naver_series_to_word.js")
        else:
            word_script = os.path.join(os.path.dirname(__file__), "exporters", "to_word.js")

        result = subprocess.run(
            ["node", word_script, output_dir],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            docx_path = result.stdout.strip()
            filepaths.append(docx_path)
            print("[" + label + "] Word 생성 완료:", docx_path)
        else:
            print("[" + label + "] Word 생성 실패:", result.stderr)

    return filepaths


def run_kakaopage():
    from collectors import kakaopage
    platform = "카카오페이지"
    try:
        options = parse_options("KAKAOPAGE")
        print("[카카오페이지] 수집 시작...")
        data = kakaopage.collect(options)

        # 실시간랭킹 비교
        if "실시간랭킹" in data:
            filename = comparison.get_comparison_filename("실시간랭킹")
            existing_html = gdrive.download_comparison_html(platform, filename)
            existing_data = comparison.parse_existing_html(existing_html)
            prev_ranks    = comparison.get_prev_ranks(existing_data)

            for item in data["실시간랭킹"]:
                item["변동"] = comparison.calc_change(
                    item["순위"], prev_ranks.get(item["작품명"])
                )

            new_html = comparison.build_updated_html(
                existing_data, data["실시간랭킹"], "카카오페이지 실시간랭킹",
                title_key="작품명", rank_key="순위"
            )
            gdrive.upload_comparison_html(platform, filename, new_html)
            print("[카카오페이지] 실시간랭킹 비교 파일 업데이트 완료")

        output_dir = tempfile.mkdtemp()
        filepaths = run_exporters(data, options, output_dir, platform, platform_key="kakaopage")

        uploaded = gdrive.upload(filepaths, platform)
        print("[카카오페이지] Drive 업로드 완료:", uploaded)

        kakao.send_complete(platform, uploaded)
        print("[카카오페이지] 완료 알림 전송")

    except Exception as e:
        print("[카카오페이지] 오류:", e)
        kakao.send_error(platform, e)
        raise


def run_munpia():
    from collectors import munpia
    platform = "문피아"
    try:
        options = parse_options("MUNPIA")
        print("[문피아] 수집 시작...")
        data = munpia.collect(options)

        # 무료투데이베스트, 유료투데이베스트 비교
        for key, label, subfolder in [
            ("무료투데이베스트", "무료투데이베스트", "무료"),
            ("유료투데이베스트", "유료투데이베스트", "유료"),
        ]:
            if key in data:
                filename = comparison.get_comparison_filename(label)
                existing_html = gdrive.download_comparison_html(platform, filename, subfolder=subfolder)
                existing_data = comparison.parse_existing_html(existing_html)
                prev_ranks    = comparison.get_prev_ranks(existing_data)

                for item in data[key]:
                    item["변동"] = comparison.calc_change(
                        item["rank"], prev_ranks.get(item["title"])
                    )

                new_html = comparison.build_updated_html(
                    existing_data, data[key], "문피아 " + label,
                    title_key="title", rank_key="rank"
                )
                gdrive.upload_comparison_html(platform, filename, new_html, subfolder=subfolder)
                print("[문피아]", label, "비교 파일 업데이트 완료")

        output_dir = tempfile.mkdtemp()
        filepaths = run_exporters(data, options, output_dir, platform, platform_key="munpia")

        uploaded = gdrive.upload(filepaths, platform)
        print("[문피아] Drive 업로드 완료:", uploaded)

        kakao.send_complete(platform, uploaded)
        print("[문피아] 완료 알림 전송")

    except Exception as e:
        print("[문피아] 오류:", e)
        kakao.send_error(platform, e)
        raise


def run_naver():
    from collectors import naver
    platform = "네이버웹툰"
    try:
        options = parse_options("NAVER")
        print("[네이버웹툰] 수집 시작...")
        data = naver.collect(options)

        output_dir = tempfile.mkdtemp()
        filepaths = run_exporters(data, options, output_dir, platform, platform_key="naver")

        uploaded = gdrive.upload(filepaths, platform)
        print("[네이버웹툰] Drive 업로드 완료:", uploaded)

        kakao.send_complete(platform, uploaded)
        print("[네이버웹툰] 완료 알림 전송")

    except Exception as e:
        print("[네이버웹툰] 오류:", e)
        kakao.send_error(platform, e)
        raise


def run_naver_series():
    from collectors import naver_series
    platform = "네이버시리즈"
    try:
        options = parse_options("NAVER_SERIES")
        print("[네이버시리즈] 수집 시작...")
        data = naver_series.collect(options)

        # 순위 변동 비교 처리 (기간/카테고리 폴더 구조)
        period_ko_to_key = {"실시간": "realtime", "일간": "daily", "주간": "weekly", "월간": "monthly"}

        ranking_data = data.get("랭킹데이터", {})
        for period_ko, categories in ranking_data.items():
            period_key = period_ko_to_key.get(period_ko, "daily")
            for category_ko, items in categories.items():
                filename = comparison.get_naver_series_comparison_filename(period_ko, period_key, category_ko)
                subfolder = [period_ko, category_ko]

                existing_html = gdrive.download_comparison_html(platform, filename, subfolder=subfolder)
                existing_data = comparison.parse_existing_html(existing_html)
                prev_ranks    = comparison.get_prev_ranks(existing_data)

                for item in items:
                    item["변동"] = comparison.calc_change(
                        item["순위"], prev_ranks.get(item["제목"])
                    )

                new_html = comparison.build_updated_html(
                    existing_data, items, "네이버시리즈 " + period_ko + " " + category_ko,
                    title_key="제목", rank_key="순위"
                )
                gdrive.upload_comparison_html(platform, filename, new_html, subfolder=subfolder)
                print("[네이버시리즈] 비교 파일 업데이트:", period_ko, category_ko)

        output_dir = tempfile.mkdtemp()
        filepaths = run_exporters(data, options, output_dir, platform, platform_key="naver_series")

        uploaded = gdrive.upload(filepaths, platform)
        print("[네이버시리즈] Drive 업로드 완료:", uploaded)

        kakao.send_complete(platform, uploaded)
        print("[네이버시리즈] 완료 알림 전송")

    except Exception as e:
        print("[네이버시리즈] 오류:", e)
        kakao.send_error(platform, e)
        raise


def main():
    platforms = os.environ.get("PLATFORMS", "kakaopage").split(",")
    platforms = [p.strip().lower() for p in platforms]

    if "kakaopage" in platforms:
        run_kakaopage()

    if "munpia" in platforms:
        run_munpia()

    if "naver" in platforms:
        run_naver()

    if "naver_series" in platforms:
        run_naver_series()


if __name__ == "__main__":
    main()
