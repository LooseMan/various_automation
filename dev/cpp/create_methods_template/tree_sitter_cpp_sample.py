import argparse
import sys
import csv
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_cpp as tscpp

def get_node_text(node, code_bytes):
    return code_bytes[node.start_byte:node.end_byte].decode("utf-8")

def extract_base_classes(node, code_bytes):
    base_classes = []
    for child in node.children:
        if child.type == "base_class_clause":
            for grandchild in child.children:
                if grandchild.type in ["type_identifier", "qualified_identifier"]:
                    base_classes.append(get_node_text(grandchild, code_bytes))
    return ", ".join(base_classes) if base_classes else "None"

def extract_function_prototype(node, code_bytes):
    body_node = node.child_by_field_name("body")
    proto_end = body_node.start_byte if body_node else node.end_byte
    proto_text = code_bytes[node.start_byte:proto_end].decode("utf-8").strip()
    return " ".join(proto_text.split())

def find_parent_class(start_row, classes_info):
    for c in classes_info:
        if c["start"] <= start_row <= c["end"]:
            return c["name"]
    return "Global"

def analyze_cpp_file(file_path):
    cpp_lang = Language(tscpp.language())
    parser = Parser(cpp_lang)

    try:
        with open(file_path, "rb") as f:
            code_bytes = f.read()
    except FileNotFoundError:
        print(f"Error: {file_path} not found", file=sys.stderr)
        return

    tree = parser.parse(code_bytes)

    # クエリは基本要素のみ
    query_string = """
    (class_specifier) @class
    (function_definition) @function
    (
      field_declaration
        declarator: (function_declarator
          declarator: (field_identifier) @func_name)
    ) @function
    """
    query = Query(cpp_lang, query_string)
    cursor = QueryCursor(query)
    
    captures_dict = cursor.captures(tree.root_node)
    
    flattened_list = []
    for tag_name, nodes in captures_dict.items():
        for node in nodes:
            flattened_list.append((node, tag_name))
    
    # 修正: x[0] が Node オブジェクトなので x[0].start_byte でソート
    sorted_items = sorted(flattened_list, key=lambda x: x[0].start_byte)

    classes_info = []
    processed_nodes = set()

    for node, tag in sorted_items:
        node_id = (node.start_byte, node.end_byte)
        if node_id in processed_nodes:
            continue

        # fieldノードの場合、中に "virtual" があれば関数として扱う
        if tag == "field":
            if b"virtual" not in code_bytes[node.start_byte:node.end_byte]:
                continue
            tag = "function"

        processed_nodes.add(node_id)
        start_row = node.start_point.row + 1
        end_row = node.end_point.row + 1

        if tag == "class":
            name_node = node.child_by_field_name("name")
            name = get_node_text(name_node, code_bytes) if name_node else "Anonymous"
            base_info = extract_base_classes(node, code_bytes)
            
            classes_info.append({"name": name, "start": start_row, "end": end_row})
            # typeを"Class"に、順序を維持
            yield [start_row, end_row, "Class", name, base_info]

        elif tag == "function":
            prototype = extract_function_prototype(node, code_bytes)
            parent_class = find_parent_class(start_row, classes_info)
            # typeを"Func"に変更
            yield [start_row, end_row, "Func", prototype, parent_class]

def main():
    arg_parser = argparse.ArgumentParser(description="C++ Source Analyzer")
    arg_parser.add_argument("file_path", help="Path to C++ source file")
    args = arg_parser.parse_args()

    writer = csv.writer(sys.stdout, delimiter='\t')
    writer.writerow(["START", "END", "TYPE", "NAME/PROTOTYPE", "BASE/PARENT"])

    for row in analyze_cpp_file(args.file_path):
        writer.writerow(row)

if __name__ == "__main__":
    main()
