#ifndef ANIMAL_HPP
#define ANIMAL_HPP

#include <iostream>
#include <string>

// ベースクラス
class Animal {
public:
    virtual void make_sound() = 0; // 純粋仮想関数
    virtual void sleep();          // 仮想関数
};

// 派生クラス
class Dog : public Animal {
public:
    void make_sound() override;    // 実装は別ファイル
    void bark();                   // 通常のメソッド
    
    // クラス内実装
    void eat() {
        std::cout << "Dog is eating" << std::endl;
    }
};

#endif
