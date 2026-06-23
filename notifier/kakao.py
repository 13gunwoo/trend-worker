# notifier/kakao.py

import os
import requests


def _refresh_access_token():
    rest_api_key = os.environ.get("KAKAO_REST_API_KEY")
    client_secret = os.environ.get("KAKAO_CLIENT_SECRET")
    refresh_token = os.environ.get("KAKAO_REFRESH_TOKEN")

    resp = requests.post(
        "https://kauth.kakao.com/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": rest_api_key,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def send(message):
    access_token = _refresh_access_token()
    resp = requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        headers={"Authorization": "Bearer " + access_token},
        data={
            "template_object": '{"object_type":"text","text":"' + message + '","link":{"web_url":"","mobile_web_url":""}}'
        },
    )
    resp.raise_for_status()
    return resp.json()


def send_page_link(page_url):
    message = "[웹툰/웹소설 트렌드]\n오늘 수집 설정을 선택해주세요.\n\n" + page_url
    return send(message)


def send_complete(platform, uploaded_files):
    files_str = ", ".join(uploaded_files)
    message = "[완료] " + platform + " 트렌드 수집이 완료됐습니다.\n저장된 파일: " + files_str
    return send(message)


def send_error(platform, error_msg):
    message = "[오류] " + platform + " 트렌드 수집 중 오류가 발생했습니다.\n" + str(error_msg)
    return send(message)
