#!/bin/bash

main() {
    if [ "$#" -ne 3 ]; then
        echo "Usage: $0 <process_name> <function_name> <return_value>"
        echo "Example: $0 my_program 'sim::Client::Request(int)' 0"
        return 1
    fi

    local process_name="$1"
    local function_name="$2"
    local return_value="$3"

    local pid=$(pgrep -f "^${process_name}$" | head -n 1)
    if [ -z "$pid" ]; then
        echo "Error: Process '$process_name' not found."
        return 1
    fi
    echo "Found process '$process_name' with PID: $pid"

    # 一時的なGDBスクリプトファイル名を作成
    local gdb_script=$(mktemp /tmp/gdb_hook_XXXXXX.gdb)

    # ヒアドキュメントでGDBスクリプトを生成
    cat << EOF > "$gdb_script"
tbreak '${function_name}'
commands
    return ${return_value}
    detach
    quit
end
continue
EOF

    echo "Running GDB hook against PID $pid..."

    # GDBをバッチモードで実行（バックグラウンド実行）
    gdb -batch -q -p "$pid" -x "$gdb_script" &

    # GDBの起動完了をわずかに待ってからスクリプトファイルを削除
    sleep 1
    rm -f "$gdb_script"

    echo "GDB is running in background. Temporary script removed."
}

main "$@"
exit $?
