#include <iostream>
#include <map>
#include <cmath> // std::abs に必要

double getInterpolatedSpeed(const std::map<double, double>& m, double target_v) {
    if (m.empty()) return 0.0;
    if (m.size() == 1) return m.begin()->second;
    
    std::map<double, double>::const_iterator it_upper = m.lower_bound(target_v);
    if (it_upper == m.begin()) return it_upper->second;
    if (it_upper == m.end()) return (--it_upper)->second;
    
    std::map<double, double>::const_iterator it_lower = it_upper;
    --it_lower;
    return it_lower->second + (target_v - it_lower->first) * (it_upper->second - it_lower->second) / (it_upper->first - it_lower->first);
}

// 【メイン】すべての条件（逆転・マイナス・誤差）をクリアしたループ制御
void runLoop(const std::map<double, double>& m, double start_v, double end_v, double step_v) {
    // 向き（符号）を自動判定
    const double sign = (start_v <= end_v) ? 1.0 : -1.0;

    // 誤差を吸収して総ステップ数を計算（植木算の +1 を含む）
    const size_t total_steps = static_cast<size_t>((std::abs(end_v - start_v) / step_v) + 0.5) + 1;

    for (size_t i = 0; i < total_steps; ++i) {
        double current_v;
        
        // 最終回だけ誤差を完全排除して、確実に終了にする
        if (i == total_steps - 1) {
            current_v = end_v;
        } else {
            current_v = start_v + (sign * i * step_v);
        }

        double speed = getInterpolatedSpeed(m, current_v);
    }
}

int main() {
    // デフォルトのマップ（追加は順不同、内部で自動昇順ソート）
    std::map<double, double> m;
    m[0.0] = 0.0;
    m[2.0] = 50.0;
    m[-2.0] = -50.0; // マイナス値も自動で正しい位置にソートされる

    runLoop(m, 5.0, -2.0, 0.5);

    return 0;
}
