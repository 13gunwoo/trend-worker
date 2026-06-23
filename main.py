# main.py
# 트렌드 수집 메인 실행 파일

import os
import sys
import json
import subprocess
import tempfile

from collectors import kakaopage
from exporters import to_json, to_excel, to_dashboard
from uploader import gdrive
from notifier import kakao


def parse_options(platform):
    """
    GitHub Actions에서 넘어온 옵션 파싱
    환경변수 COLLECT_OPTIONS_{PLATFORM} 에서 읽음
    예: COLLECT_OPTIONS_KAKAOPAGE={"realtime":true,"genre":true,...}
    """
    key = "COLLECT_OPTIONS_" + platform.upper()
    raw = os.environ.get(key)
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return None  # None이면 기본값(전체) 사용


def run_kakaopage():
    platform = "카카오페이지"
    try:
        options = parse_options("KAKAOPAGE")
        print("[카카오페이지] 수집 시작...")
        data = kakaopage.collect(options)

        output_dir = tempfile.mkdtemp()
        filepaths = []

        # JSON
        json_path = to_json.export(data, output_dir)
        filepaths.append(json_path)
        print("[카카오페이지] JSON 생성 완료:", json_path)

        # Excel
        xlsx_path = to_excel.export(data, output_dir)
        filepaths.append(xlsx_path)
        print("[카카오페이지] Excel 생성 완료:", xlsx_path)

        # HTML 대시보드
        html_path = to_dashboard.export(data, output_dir)
        filepaths.append(html_path)
        print("[카카오페이지] 대시보드 생성 완료:", html_path)

        # Word (Node.js)
        tmp_json = os.path.join(output_dir, "tmp_data.json")
        with open(tmp_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.environ["TEMP_DATA_PATH"] = tmp_json

        word_script = os.path.join(os.path.dirname(__file__), "exporters", "to_word.js")
        result = subprocess.run(
            ["node", word_script, output_dir],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            docx_path = result.stdout.strip()
            filepaths.append(docx_path)
            print("[카카오페이지] Word 생성 완료:", docx_path)
        else:
            print("[카카오페이지] Word 생성 실패:", result.stderr)

        # Google Drive 업로드
        uploaded = gdrive.upload(filepaths, platform)
        print("[카카오페이지] Drive 업로드 완료:", uploaded)

        # 카톡 완료 알림
        kakao.send_complete(platform, uploaded)
        print("[카카오페이지] 완료 알림 전송")

    except Exception as e:
        print("[카카오페이지] 오류:", e)
        kakao.send_error(platform, e)
        raise


def main():
    platforms = os.environ.get("PLATFORMS", "kakaopage").split(",")
    platforms = [p.strip().lower() for p in platforms]

    if "kakaopage" in platforms:
        run_kakaopage()

    # 추후 문피아, 네이버 웹툰 추가 예정
    # if "munpia" in platforms:
    #     run_munpia()
    # if "naver" in platforms:
    #     run_naver()


if __name__ == "__main__":
    main()
