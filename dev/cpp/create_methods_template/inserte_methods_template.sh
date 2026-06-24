main() {
    set -e  # エラーで即終了
    local method_list="$1"
    local insert_dst="$2"

    # 拡張子小文字抽出
    local ext_lower="${insert_dst##*.}"
    ext_lower="${ext_lower,,}"

    # 関数宣言行を配列に格納
    if [[ "$ext_lower" == "h" || "$ext_lower" == "hpp" ]]; then
        # ヘッダ用
        mapfile -t FUNC_LINES < <(
            awk -F'\t' '{
                print "";
                print "    /**";
                printf "     * @brief %s\n", $3;
                print "     */";
                printf "    %s %s;\n", $1, $2;
            }' "$method_list"
        )
    else
        # ソース用
        local namespace
        namespace="$(basename "$insert_dst" | sed 's/\.[^.]*$//')"
        mapfile -t FUNC_LINES < <(
            awk -F'\t' -v classname="$namespace" '{
                print "";
                print "/**";
                printf " * @brief %s\n", $3;
                print " */";
                printf "%s %s::%s\n", $1, classname, $2;
                print "{";
                print "    // TBD";
                print "";
                print "    return;";
                print "}";
            }' "$method_list"
        )
    fi

    # クラス定義情報抽出
    python tree_sitter_cpp_sample.py "$insert_dst" > tmp_classlist.tsv
    command -v dos2unix >/dev/null && dos2unix tmp_classlist.tsv

    # 挿入位置の決定
    local TARGET_LINES
    if [[ "$ext_lower" == "h" || "$ext_lower" == "hpp" ]]; then
        mapfile -t TARGET_LINES < <(
            awk -F'\t' '$3=="Class"{print $2-1}' tmp_classlist.tsv | sort -nr
        )
    else
        TARGET_LINES=( "$(wc -l < "$insert_dst")" )
    fi

    # 一時ファイル作成・バックアップ
    local TMPFILE="${insert_dst}.tmp"
    cp "$insert_dst" "$TMPFILE"
    cp "$insert_dst" "${insert_dst}.bak"

    # 後ろから挿入（行ずれ防止）
    for line in "${TARGET_LINES[@]}"; do
        (
            head -n "$line" "$TMPFILE"
            printf '%s\n' "${FUNC_LINES[@]}"
            tail -n +"$((line + 1))" "$TMPFILE"
        ) > "${TMPFILE}.new"
        mv "${TMPFILE}.new" "$TMPFILE"
    done

    mv "$TMPFILE" "${insert_dst}.new"

    # 一時ファイル自動削除
    trap 'rm -f tmp_classlist.tsv' EXIT

    echo -e "\033[32mメソッドを挿入しました: $insert_dst\033[0m"
}

main "$@"
