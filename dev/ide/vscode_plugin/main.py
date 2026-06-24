import sys
import os
import core as core

def main():
    # 引数チェック
    if len(sys.argv) < 2:
        print("使用方法: python main.py <プラグインID>")
        sys.exit(1)
        
    ext_id = sys.argv[1]
    save_dir = "./vscode_packages"

    try:
        # 情報の取得と解析
        print(f"【検索中】{ext_id} の情報を取得しています...")
        raw_data = core.fetch_extension_info(ext_id)
        info = core.parse_metadata(raw_data)
        
        # 調査結果の表示
        print("-" * 50)
        print(f"ID        : {info['id']}\nバージョン: {info['version']}\n開発元    : {info['publisher']}\nライセンス: {info['license']}\nソースRepo: {info['repo']}")
        print("-" * 50)
        
        # ダウンロード処理
        if info["download_url"]:
            filename = f"{info['id']}-{info['version']}.vsix"
            filepath = os.path.join(save_dir, filename)
            
            print(f"【DL開始】オフライン用パッケージをダウンロード中...")
            core.download_vsix(info["download_url"], filepath)
            print(f"【完了】保存先: {filepath}")
        else:
            print("【警告】ダウンロードURLが見つかりませんでした。")
            
    except Exception as e:
        print(f"【エラー】{e}")

if __name__ == "__main__":
    main()
