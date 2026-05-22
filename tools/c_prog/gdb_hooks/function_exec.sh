#!/bin/bash

main() {
    if [ "$#" -lt 2 ]; then
        echo "Usage: $0 <process_name> <function_name> [args...]"
        echo "Examples:"
        echo "  C関数:       $0 my_program 'my_c_func' 10"
        echo "  C++メソッド: $0 my_program 'sim::Client::Request' 5"
        return 1
    fi

    local process_name="$1"
    local full_func_name="$2"
    shift 2
    # 残りの引数をカンマ区切りの文字列に変換
    local call_args=""
    if [ "$#" -gt 0 ]; then
        local IFS=","
        call_args="$*"
    fi

    local pid=$(pgrep -f "^${process_name}$" | head -n 1)
    if [ -z "$pid" ]; then
        echo "Error: Process '$process_name' not found."
        return 1
    fi
    echo "Found process '$process_name' with PID: $pid"

    # 一時的なGDBスクリプトファイル名を作成
    local gdb_script=$(mktemp /tmp/gdb_call_XXXXXX.gdb)

    # クラス名が含まれているか判定 (例: sim::Client::Request や Client::Request)
    if [[ "$full_func_name" =~ (.*)::([^:]+) ]]; then
        local class_name="${BASH_REMATCH[1]}"
        local method_name="${BASH_REMATCH[2]}"

        echo "Detected C++ Method: Class='$class_name', Method='$method_name'"
        cat << EOF > "$gdb_script"
# メモリを確保してインスタンス化
set \$obj = (${class_name}*) malloc(sizeof(${class_name}))
call ((\$obj)->${class_name}())

# メソッドを実行して戻り値を出力
print (\$obj)->${method_name}(${call_args})

# 後片付け（デストラクタ呼び出しとメモリ解放）
call ((\$obj)->~${class_name}())
call free(\$obj)

detach
quit
EOF
    else
        echo "Detected C/Standard Function: '$full_func_name'"
        cat << EOF > "$gdb_script"
print ${full_func_name}(${call_args})
detach
quit
EOF
    fi

    # GDBをバッチモードで実行（バックグラウンド実行）
    echo "--------------------------------------------------"
    gdb -batch -q -p "$pid" -x "$gdb_script" &
    echo "--------------------------------------------------"

    rm -f "$gdb_script"
}

main "$@"
exit $?
