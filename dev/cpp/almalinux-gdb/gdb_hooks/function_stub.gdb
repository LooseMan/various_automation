# ============================================================
# GDB one-shot hook script
#
# 用途:
#   特定関数が呼ばれたタイミングで処理をフックし、
#   任意の値をreturnしてGDBを終了する。
#
# 実行例:
#   gdb -batch -q -p <PID> -x hook.gdb &
#
# 注意:
#   - C++関数は demangle名 を指定する
#   - demangle名は、GDBでプロセスにattach後、`info functions`コマンドで確認可能
# ============================================================

# ビルド環境と実行環境が異なる場合、下記コマンドでパスのマッピングがが必要（実行環境にSRCを配置しておく必要がある）
# set substitute-path <from(ビルド環境上のパス)> <to(動作環境上のパス)>

# 構造体などを綺麗に見たいなら以下を有効か
# set printpretty on

# 一回だけ有効なbreakpoint
# 一覧はi bで、無効化はd <Num>で
tbreak sim::Client::Request(int)

# breakpointヒット時の自動実行処理、複数ある場合はIDをつける（"commands 1"など）
commands
    # break時の説明を省略し画面表示を圧縮
    silent

    # 関数本体を実行せず即return
    return 0

    # 変数の内容を表示
    # printf "%s\n", var

    # 対象プロセスからdetach
    detach

    # GDB終了
    quit
end

# attach後に停止している対象プロセスを再開
continue
