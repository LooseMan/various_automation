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

# 一回だけ有効なbreakpoint
tbreak sim::Client::Request(int)

# breakpointヒット時の自動実行処理
commands
    # 関数本体を実行せず即return
    return 0

    # 対象プロセスからdetach
    detach

    # GDB終了
    quit
end

# attach後に停止している対象プロセスを再開
continue
