# trend-worker

웹툰/웹소설 트렌드 자동 수집기

## 구조

```
trend-worker/
├── .github/workflows/collect.yml   # GitHub Actions
├── collectors/
│   └── kakaopage.py                # 카카오페이지 수집
├── exporters/
│   ├── to_json.py                  # JSON 출력
│   ├── to_excel.py                 # Excel 출력
│   ├── to_dashboard.py             # HTML 대시보드 출력
│   └── to_word.js                  # Word 출력 (Node.js)
├── uploader/
│   └── gdrive.py                   # Google Drive 업로드
├── notifier/
│   └── kakao.py                    # 카카오톡 알림
├── main.py                         # 메인 실행
└── requirements.txt
```

## GitHub Secrets 설정

| Key | 설명 |
|-----|------|
| `KAKAO_REST_API_KEY` | 카카오 REST API 키 |
| `KAKAO_CLIENT_SECRET` | 카카오 클라이언트 시크릿 |
| `KAKAO_REFRESH_TOKEN` | 카카오 리프레시 토큰 |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Google 서비스 계정 JSON 전체 |
| `GDRIVE_FOLDER_ID` | Google Drive 루트 폴더 ID |

## Google Drive 폴더 구조

```
웹툰_웹소설_트렌드/
├── 웹소설/
│   ├── 카카오페이지/
│   └── 문피아/
└── 웹툰/
    └── 네이버웹툰/
```

## 수동 실행

GitHub → Actions → 트렌드 수집 → Run workflow
