# uploader/gdrive.py

import os
import json
from datetime import date
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]

# 폴더 구조 매핑: [장르, 플랫폼]
FOLDER_MAP = {
    "카카오페이지": ["웹소설", "카카오페이지"],
    "문피아":       ["웹소설", "문피아"],
    "네이버시리즈": ["웹소설", "네이버시리즈"],
    "네이버웹툰":   ["웹툰",   "네이버웹툰"],
}

MIME_MAP = {
    ".json": "application/json",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".html": "text/html",
}


def _get_service():
    client_id     = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        raise ValueError("GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN 환경변수가 필요합니다.")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("drive", "v3", credentials=creds)


def _get_or_create_folder(service, name, parent_id):
    query = (
        "mimeType='application/vnd.google-apps.folder'"
        " and name='" + name + "'"
        " and '" + parent_id + "' in parents"
        " and trashed=false"
    )
    results = service.files().list(
        q=query, fields="files(id, name)",
        supportsAllDrives=True
    ).execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(
        body=metadata, fields="id"
    ).execute()
    return folder["id"]


def _resolve_folder(service, platform, root_folder_id):
    """
    장르 → 플랫폼 → 장르_플랫폼_날짜 폴더 순으로 생성.
    예: 웹소설 → 카카오페이지 → 웹소설_카카오페이지_2025-06-23
    """
    path_parts = FOLDER_MAP.get(platform, [platform])
    genre = path_parts[0] if len(path_parts) > 0 else platform
    platform_name = path_parts[1] if len(path_parts) > 1 else platform
    today = date.today().strftime("%Y-%m-%d")
    date_folder = genre + "_" + platform_name + "_" + today

    current_id = root_folder_id
    for part in path_parts:
        current_id = _get_or_create_folder(service, part, current_id)

    # 날짜 폴더 (장르_플랫폼_날짜)
    current_id = _get_or_create_folder(service, date_folder, current_id)
    return current_id


def _build_filename(original_filename, platform):
    """
    파일명을 플랫폼_장르_날짜.확장자 형태로 변환.
    예: 카카오페이지_20250623.xlsx → 카카오페이지_웹소설_20250623.xlsx
    """
    path_parts = FOLDER_MAP.get(platform, [platform])
    genre = path_parts[0] if len(path_parts) > 0 else ""
    today = date.today().strftime("%Y%m%d")
    ext = os.path.splitext(original_filename)[1].lower()
    return platform + "_" + genre + "_" + today + ext


def upload(filepaths, platform):
    service = _get_service()
    root_folder_id = os.environ.get("GDRIVE_FOLDER_ID")
    if not root_folder_id:
        raise ValueError("GDRIVE_FOLDER_ID 환경변수가 없습니다.")

    target_folder_id = _resolve_folder(service, platform, root_folder_id)

    uploaded = []
    for filepath in filepaths:
        original_filename = os.path.basename(filepath)
        filename = _build_filename(original_filename, platform)
        ext = os.path.splitext(filename)[1].lower()
        mime_type = MIME_MAP.get(ext, "application/octet-stream")

        # 같은 이름 파일 있으면 삭제
        query = (
            "name='" + filename + "'"
            " and '" + target_folder_id + "' in parents"
            " and trashed=false"
        )
        existing = service.files().list(
            q=query, fields="files(id)",
            supportsAllDrives=True
        ).execute().get("files", [])
        for f in existing:
            service.files().delete(fileId=f["id"]).execute()

        metadata = {"name": filename, "parents": [target_folder_id]}
        media = MediaFileUpload(filepath, mimetype=mime_type)
        file = service.files().create(
            body=metadata, media_body=media, fields="id, name"
        ).execute()
        uploaded.append(file.get("name"))

    return uploaded


def _get_or_create_comparison_folder(service, platform, root_folder_id):
    """
    비교 파일 전용 폴더 경로 생성.
    예: 웹소설 → 카카오페이지 → 비교
    """
    path_parts = FOLDER_MAP.get(platform, [platform])
    current_id = root_folder_id
    for part in path_parts:
        current_id = _get_or_create_folder(service, part, current_id)
    current_id = _get_or_create_folder(service, "비교", current_id)
    return current_id


def download_comparison_html(platform, filename, subfolder=None):
    """
    Drive에서 비교 HTML 파일을 다운로드해서 내용을 문자열로 반환.
    파일이 없으면 None 반환.
    subfolder: 비교 폴더 안에 추가 하위 폴더명. 문자열 또는 리스트(예: ["일간","판타지"])
    """
    service = _get_service()
    root_folder_id = os.environ.get("GDRIVE_FOLDER_ID")
    if not root_folder_id:
        return None

    comp_folder_id = _get_or_create_comparison_folder(service, platform, root_folder_id)
    if subfolder:
        sub_parts = subfolder if isinstance(subfolder, list) else [subfolder]
        for part in sub_parts:
            comp_folder_id = _get_or_create_folder(service, part, comp_folder_id)

    query = (
        "name='" + filename + "'"
        " and '" + comp_folder_id + "' in parents"
        " and trashed=false"
    )
    results = service.files().list(
        q=query, fields="files(id)",
        supportsAllDrives=True
    ).execute()
    files = results.get("files", [])
    if not files:
        return None

    file_id = files[0]["id"]
    content = service.files().get_media(fileId=file_id).execute()
    return content.decode("utf-8")


def upload_comparison_html(platform, filename, html_content, subfolder=None):
    """
    비교 HTML 파일을 Drive에 업로드 (같은 이름 있으면 덮어씀).
    subfolder: 비교 폴더 안에 추가 하위 폴더명. 문자열 또는 리스트(예: ["일간","판타지"])
    """
    import tempfile as _tempfile

    service = _get_service()
    root_folder_id = os.environ.get("GDRIVE_FOLDER_ID")
    if not root_folder_id:
        raise ValueError("GDRIVE_FOLDER_ID 환경변수가 없습니다.")

    comp_folder_id = _get_or_create_comparison_folder(service, platform, root_folder_id)
    if subfolder:
        sub_parts = subfolder if isinstance(subfolder, list) else [subfolder]
        for part in sub_parts:
            comp_folder_id = _get_or_create_folder(service, part, comp_folder_id)

    # 기존 파일 삭제
    query = (
        "name='" + filename + "'"
        " and '" + comp_folder_id + "' in parents"
        " and trashed=false"
    )
    existing = service.files().list(
        q=query, fields="files(id)",
        supportsAllDrives=True
    ).execute().get("files", [])
    for f in existing:
        service.files().delete(fileId=f["id"]).execute()

    with _tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".html", delete=False) as tmp:
        tmp.write(html_content)
        tmp_path = tmp.name

    metadata = {"name": filename, "parents": [comp_folder_id]}
    media = MediaFileUpload(tmp_path, mimetype="text/html")
    service.files().create(
        body=metadata, media_body=media, fields="id"
    ).execute()
    os.remove(tmp_path)
