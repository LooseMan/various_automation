#!/usr/bin/env python3

import argparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import csv
import sys

from render_template import render_template

def render_templates_in_folder(
    template_dir: Path,
    vars_path: Path,
    output_dir: Path = None
):
    """指定フォルダ内のj2ファイル全部を一括レンダリング"""
    template_dir = template_dir.resolve()
    if output_dir is None:
        output_dir = template_dir
    else:
        output_dir = Path(output_dir).resolve()

    # テンプレート一覧
    j2_files = list(template_dir.glob("*.j2"))
    if not j2_files:
        print(f"{template_dir}に .j2 ファイルがありません。")
        return

    # env = Environment(loader=FileSystemLoader(str(template_dir)))

    # CSV読み込み
    # with vars_path.open(encoding='utf-8') as f:
    #     reader = csv.DictReader(f, delimiter='\t')
    #     rows = list(reader)  # まとめて読んでおく

    for j2f in j2_files:
        # template = env.get_template(j2f.name)
        out_name = j2f.stem  # .j2を除いたファイル名
        rendered_file = output_dir / out_name

        # 出力先ディレクトリ作成
        # rendered_file.parent.mkdir(parents=True, exist_ok=True)
        # rendered_file.write_text("", encoding='utf-8')

        # レンダリングして追記
        # with rendered_file.open(mode='a', encoding='utf-8') as out_f:
        #     for row in rows:
        #         rendered = template.render(**row)
        #         out_f.write(rendered + "\n")
        render_template(j2f, vars_path, rendered_file)

        print(f"{j2f.name} → {rendered_file.name} 保存完了")

    # 出力先ディレクトリ直下のレンダリング結果（.j2以外）を昇順でall.txtに結合
    merged_files = sorted([
        f for f in output_dir.iterdir()
        if f.is_file() and f.suffix != '.j2' and f.name != 'all.txt'
    ], key=lambda x: x.name)

    all_txt_path = output_dir / "all.txt"
    with all_txt_path.open('w', encoding='utf-8') as fw:
        for mf in merged_files:
            fw.write(f"=== {mf.name} ===\n")
            fw.write(mf.read_text(encoding='utf-8'))
            fw.write('\n')  # ファイル間の区切り（必要なければ削除）

    print(f"{len(merged_files)} ファイルを {all_txt_path.name} にマージしました。")

    # 元ファイルを削除
    for mf in merged_files:
        mf.unlink()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Render all Jinja2 templates in a folder and save without .j2 extension"
    )
    parser.add_argument("template_dir", type=Path, help="テンプレートフォルダ")
    parser.add_argument("vars_file", type=Path, help="タブ区切りCSVファイル")
    parser.add_argument("-o", "--output_dir", type=Path, help="出力先フォルダ（未指定時はテンプレートフォルダ）")

    args = parser.parse_args()
    render_templates_in_folder(args.template_dir, args.vars_file, args.output_dir)
