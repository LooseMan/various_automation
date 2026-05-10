from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_cpp as tscpp

# 1. セットアップ
CPP_LANGUAGE = Language(tscpp.language())
parser = Parser(CPP_LANGUAGE)

code_bytes = b"""
class MyClass {
    void methodA(int x) { 
        // code
    }
};

void topLevelFunc() {
}
"""
tree = parser.parse(code_bytes)

# 2. クエリの定義
# クラスと、トップレベルまたはメソッドとしての関数を定義
query_string = """
(class_specifier) @class
(function_definition) @function
"""
query = Query(CPP_LANGUAGE, query_string)
cursor = QueryCursor(query)
captures = cursor.captures(tree.root_node)

print(f"{'TYPE':<10} | {'NAME / PROTOTYPE':<40} | {'RANGE':<12} | {'PARENT CLASS'}")
print("-" * 90)

# 3. データの抽出
# クラスの範囲を記録しておくためのリスト
classes_info = []

# まずクラスの位置情報を収集
if "class" in captures:
    for node in captures["class"]:
        name_node = node.child_by_field_name("name")
        name = code_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8") if name_node else "Anonymous"
        classes_info.append({
            "name": name,
            "start": node.start_point.row + 1,
            "end": node.end_point.row + 1
        })
        print(f"{'Class':<10} | {name:<40} | {node.start_point.row+1:>4}-{node.end_point.row+1:<4} | ---")

# 関数を抽出し、どのクラスに属するか判定
if "function" in captures:
    for node in captures["function"]:
        # プロトタイプ（bodyの前まで）を取得
        body_node = node.child_by_field_name("body")
        proto_end = body_node.start_byte if body_node else node.end_byte
        prototype = code_bytes[node.start_byte:proto_end].decode("utf-8").strip() + ";"
        
        start_row = node.start_point.row + 1
        end_row = node.end_point.row + 1
        
        # どのクラスの行範囲内にあるかチェック
        parent_class = "Global"
        for c in classes_info:
            if c["start"] <= start_row <= c["end"]:
                parent_class = c["name"]
                break
        
        print(f"{'Function':<10} | {prototype[:40]:<40} | {start_row:>4}-{end_row:<4} | {parent_class}")
