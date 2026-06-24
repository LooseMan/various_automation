#!/usr/bin/env python3

import argparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined
import yaml
import sys

def main(template_root: Path, vars_path: Path):
    # すでに Path オブジェクトなのでそのままメソッドが使えます
    if not template_root.is_dir():
        print(f"Error: {template_root} is not a directory", file=sys.stderr)
        sys.exit(1)

    if not vars_path.exists():
        print(f"Error: {vars_path} not found", file=sys.stderr)
        sys.exit(1)

    # 値ファイル読み込み
    with vars_path.open() as f:
        vars_data = yaml.safe_load(f)

    # Jinja 環境（ルート基準）
    env = Environment(
        loader=FileSystemLoader(template_root),
        undefined=StrictUndefined,
        autoescape=False,
        # trim_blocks=True,
        lstrip_blocks=True,
    )

    # 再帰的に .j2 を処理
    for tpl in template_root.rglob("*.j2"):
        rel_path = tpl.relative_to(template_root)
        out_path = tpl.with_suffix("")

        template = env.get_template(str(rel_path))
        rendered = template.render(**vars_data)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered)

        print(f"Rendered: {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Render Jinja2 templates recursively"
    )
    # type=Path を指定することで、引数を Path オブジェクトとして受け取る
    parser.add_argument("template_dir", type=Path, help="Directory containing .j2 templates")
    parser.add_argument("vars_file", type=Path, help="YAML file with variables")
    parser.add_argument(
        "-r", "--remove-source",
        action="store_true",
        help="Remove source .j2 templates after rendering"
    )

    args = parser.parse_args()
    # Path オブジェクトが渡される
    main(args.template_dir, args.vars_file)
