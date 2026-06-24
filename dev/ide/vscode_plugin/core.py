import json
import os
import urllib.request

API_URL = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
HEADERS = {
    "Accept": "application/json;api-version=3.0-preview.1",
    "Content-Type": "application/json",
    "User-Agent": "vscode-plugin-downloader"
}

def fetch_extension_info(ext_id: str) -> dict:
    """マーケットプレイスAPIからプラグイン情報を取得"""
    payload = {"filters": [{"criteria": [{"filterType": 7, "value": ext_id}]}], "flags": 914}
    req = urllib.request.Request(API_URL, data=json.dumps(payload).encode(), headers=HEADERS, method="POST")
    
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode())
    
    extensions = data.get("results", [{}])[0].get("extensions", [])
    if not extensions:
        raise ValueError(f"プラグイン '{ext_id}' が見見つかりませんでした。")
    return extensions[0]

def parse_metadata(ext: dict) -> dict:
    """必要なメタデータ（ライセンス、リポジトリ等）を抽出"""
    latest = ext["versions"][0]
    props = {p["key"]: p["value"] for p in latest.get("properties", [])}
    
    return {
        "id": f"{ext['publisher']['publisherName']}.{ext['extensionName']}",
        "version": latest["version"],
        "publisher": ext["publisher"]["displayName"],
        "license": props.get("Microsoft.VisualStudio.Services.Links.License", "未特定"),
        "repo": props.get("Microsoft.VisualStudio.Services.Links.Repository", "未特定"),
        "download_url": next((f["source"] for f in latest["files"] if f["assetType"] == "Microsoft.VisualStudio.Services.VSIXPackage"), None)
    }

def download_vsix(url: str, filepath: str):
    """VSIXパッケージをローカルに保存"""
    os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
    urllib.request.urlretrieve(url, filepath)
