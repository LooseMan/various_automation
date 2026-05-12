
main() {
    local method_list="$1"
    local insert_dst="$2"

    while IFS=$'\t' read type signature description; do
        # echo $type $signature $description
        :
    done < "$method_list"

    python tree_sitter_cpp_sample.py $insert_dst > tmp
    while IFS=$'\t' read -r start end type name parent; do
        if [ $type == 'Class' ]; then
            # end=$(end - 1)
            target_line=$((end - 1))
            sed -e "${target_line}a\\
            hogehoge" $insert_dst
        fi
    done < <(sort -k1,1n tmp)

}

main "$@"
