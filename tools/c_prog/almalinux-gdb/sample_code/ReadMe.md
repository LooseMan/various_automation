gcc -g -O0 function_server.c -o function_server

g++ -g -O0 function_server.cpp -o function_server_cpp

VSCodeデバッグノウハウ
ブレークポイント設置後、編集から以下の式を入力しEnter
cmd == 4 && (cmd = 0)
cmdが4の状態でブレークポイントに入ると、ブレークなしでcmdに0が設定される。
→特定の条件でのみ戻り値を変えるなどが可能になる！
（GDBスクリプトより柔軟ではないが、簡単なテストでは十分使える）

# C++の場合 (C言語なら gcc)
g++ -fsanitize=address -g main.cpp -o myapp

# ① 普通にバックグラウンド、またはサービスとして実行
./myapp &

# ② PIDを確認してgdbでアタッチ
PID=$(pidof myapp)
sudo gdb -p $PID

# ③ gdb内でリークチェックをコール
(gdb) call __lsan_do_leak_check()
(gdb) detach
(gdb) quit

    dnf -y install \
        libasan \

=================================================================
==40==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 16 byte(s) in 1 object(s) allocated from:
    #0 0x7ffb641e4a07 in __interceptor_malloc (/lib64/libasan.so.6+0xb4a07)
    #1 0x40129c in func_leak /workspace/sample_code/func_server.c:31
    #2 0x401451 in main /workspace/sample_code/func_server.c:81
    #3 0x7ffb63f5060f in __libc_start_call_main (/lib64/libc.so.6+0x2a60f)

SUMMARY: AddressSanitizer: 16 byte(s) leaked in 1 allocation(s).
[root@98fd2880a5d1 sample_code]# ./func_server
