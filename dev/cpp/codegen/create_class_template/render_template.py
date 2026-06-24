#!/usr/bin/env python3

import argparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import csv
import sys

# argparseで「key=val」の形式をパースするためのカスタムアクション
class ParseDict(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        d = getattr(namespace, self.dest) or {}
        for val in values:
            if '=' not in val:
                raise argparse.ArgumentError(self, f"Invalid format: '{val}'. Must be 'key=value'.")
            k, v = val.split('=', 1)
            d[k] = v
        setattr(namespace, self.dest, d)

# 独自フィルタ
def first_upper(value):
    return value[:1].upper() + value[1:]
def pascalize(value: str):
    return ''.join(word.lower().capitalize() for word in value.split('_'))
def camel_to_snake(value: str) -> str:
    import re
    # 大文字の前に _ を挿入し、小文字化
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', value)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()

def emvedd_tsv_vars(vars_path: Path):
    """TSV変数ファイルを辞書リストで返す"""
    with vars_path.open(encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        return [row for row in reader]

def embedd_yaml_vars(vars_path: Path):
    """YAML変数ファイルを辞書リストで返す"""
    import yaml
    with vars_path.open(encoding='utf-8') as f:
        var_rows = yaml.safe_load(f)
        if isinstance(var_rows, dict):
            var_rows = [var_rows]
        return var_rows

# レンダリング（変数ファイルはCSV or YAMLで指定可能）
def render_template(template_file: Path, vars_path: Path, rendered_file: Path, extra_vars: dict = {}):
    env = Environment(
        loader=FileSystemLoader(template_file.parent),
    )

    # 独自フィルタ登録
    # - 1文字目を大文字化
    env.filters['first_upper'] = first_upper
    # - Snake to Camel(False指定で1文字目を大文字化)
    env.filters['pascalize'] = pascalize
    # - Camel to Snake(大文字の前に _ を挿入し、小文字化)
    env.filters['camel_to_snake'] = camel_to_snake

    # 1. テンプレートファイルを文字列として読み込み、'---' の行で分割
    template_content = template_file.read_text(encoding='utf-8')
    blocks = [block.rstrip() for block in template_content.replace('\r\n', '\n').split('\n---\n')]
    
    # 2. 各ブロックからJinja2のTemplateオブジェクトを作成
    template_blocks = [env.from_string(block) for block in blocks if block]

    # 出力先ディレクトリの作成
    rendered_file.parent.mkdir(parents=True, exist_ok=True)

    # 最初にファイルを新規作成（中身を空にする）
    rendered_file.write_text("", encoding='utf-8')

    # ファイル形式ごとに読み出し関数を呼び分け
    if vars_path.suffix.lower() in ['.yaml', '.yml']:
        var_rows = embedd_yaml_vars(vars_path)
    else:
        var_rows = emvedd_tsv_vars(vars_path)

    with rendered_file.open(mode='a', encoding='utf-8') as out_f:
        # ブロックごとに処理を行う
        for t_block in template_blocks:
            for row in var_rows:
                # コマンドライン引数から渡された環境変数をマージ（コマンドライン引数を優先）
                merged_vars = {**row, **extra_vars}
                
                rendered = t_block.render(**merged_vars)
                # レンダリング結果を書き込み
                out_f.write(rendered + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Render Jinja2 template and append all to a single file"
    )
    parser.add_argument("template_file", type=Path)
    parser.add_argument("vars_file", type=Path)
    parser.add_argument("rendered_file", type=Path)
    parser.add_argument(
        "-e", "--extra-vars",
        action=ParseDict,
        nargs="+",
        metavar="KEY=VALUE",
        default={},
        help="Additional variables as key=value pairs. Can be used multiple times."
    )

    args = parser.parse_args()
    render_template(args.template_file, args.vars_file, args.rendered_file, args.extra_vars)
