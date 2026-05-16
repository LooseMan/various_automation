#!/usr/bin/env python3

import argparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import csv
import sys

# 独自フィルタ
def first_upper(value):
    return value[:1].upper() + value[1:]
def pascalize(value: str):
    return ''.join(word.lower().capitalize() for word in value.split('_'))

def render_template(template_file: Path, vars_path: Path, rendered_file: Path):
    env = Environment(
        loader=FileSystemLoader(template_file.parent),
    )

    # 独自フィルタ登録
    # - 1文字目を大文字化
    env.filters['first_upper'] = first_upper
    # - Snake to Camel(False指定で1文字目を大文字化)
    env.filters['pascalize'] = pascalize

    template = env.get_template(template_file.name)
    
    # 出力先ディレクトリの作成
    rendered_file.parent.mkdir(parents=True, exist_ok=True)

    # 最初にファイルを新規作成（中身を空にする）
    rendered_file.write_text("", encoding='utf-8')

    # CSV（タブ区切り）読み込み
    with vars_path.open(encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        # 追記モード ('a') でファイルを開く
        with rendered_file.open(mode='a', encoding='utf-8') as out_f:
            for row in reader:
                rendered = template.render(**row)
                
                # 1行分の結果を書き込み（最後に改行を入れると繋がらない）
                out_f.write(rendered + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Render Jinja2 template and append all to a single file"
    )
    parser.add_argument("template_file", type=Path)
    parser.add_argument("vars_file", type=Path)
    parser.add_argument("rendered_file", type=Path)

    args = parser.parse_args()
    render_template(args.template_file, args.vars_file, args.rendered_file)
