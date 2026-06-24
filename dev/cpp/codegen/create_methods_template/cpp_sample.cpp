#include "Animal.hpp"

// クラス外での実装 (Animal::)
void Animal::sleep() {
    std::cout << "Animal is sleeping" << std::endl;
}

// クラス外での実装 (Dog::)
void Dog::make_sound() {
    std::cout << "Woof! Woof!" << std::endl;
}

void Dog::bark() {
    std::cout << "Bow wow!" << std::endl;
}

// グローバル関数
void notify_status() {
    std::cout << "Status: OK" << std::endl;
}

int main() {
    Dog myDog;
    myDog.make_sound();
    myDog.eat();
    return 0;
}
