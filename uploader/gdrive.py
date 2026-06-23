# uploader/gdrive.py

import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]

# 폴더 구조 매핑
FOLDER_MAP = {
    "카카오페이지": ["웹소설", "카카오페이지"],
    "문피아":       ["웹소설", "문피아"],
    "네이버웹툰":   ["웹툰", "네이버웹툰"],
}

MIME_MAP = {
    ".json": "application/json",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".html": "text/html",
}


def _get_service():
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON 환경변수가 없습니다.")
    sa_info = json.loads(sa_json)
    creds = service_account.Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def _get_or_create_folder(service, name, parent_id):
    query = (
        "mimeType='application/vnd.google-apps.folder'"
        " and name='" + name + "'"
        " and '" + parent_id + "' in parents"
        " and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def _resolve_folder(service, platform, root_folder_id):
    path_parts = FOLDER_MAP.get(platform, [platform])
    current_id = root_folder_id
    for part in path_parts:
        current_id = _get_or_create_folder(service, part, current_id)
    return current_id


def upload(filepaths, platform):
    service = _get_service()
    root_folder_id = os.environ.get("GDRIVE_FOLDER_ID")
    if not root_folder_id:
        raise ValueError("GDRIVE_FOLDER_ID 환경변수가 없습니다.")

    target_folder_id = _resolve_folder(service, platform, root_folder_id)

    uploaded = []
    for filepath in filepaths:
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()
        mime_type = MIME_MAP.get(ext, "application/octet-stream")

        # 같은 이름 파일 있으면 삭제
        query = (
            "name='" + filename + "'"
            " and '" + target_folder_id + "' in parents"
            " and trashed=false"
        )
        existing = service.files().list(q=query, fields="files(id)").execute().get("files", [])
        for f in existing:
            service.files().delete(fileId=f["id"]).execute()

        metadata = {"name": filename, "parents": [target_folder_id]}
        media = MediaFileUpload(filepath, mimetype=mime_type)
        file = service.files().create(body=metadata, media_body=media, fields="id, name").execute()
        uploaded.append(file.get("name"))

    return uploaded
