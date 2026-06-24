// file: function_server.cpp

#include <iostream>
#include <string>
#include <thread>
#include <chrono>
#include <unistd.h>

class FunctionServer
{
public:
    void funcHello()
    {
        std::cout << "[funcHello] Hello" << std::endl;
    }

    void funcAdd()
    {
        int a = 100;
        int b = 200;

        std::cout
            << "[funcAdd] "
            << a
            << " + "
            << b
            << " = "
            << (a + b)
            << std::endl;
    }

    void funcSleep()
    {
        std::cout << "[funcSleep] sleeping 5 sec..." << std::endl;

        std::this_thread::sleep_for(std::chrono::seconds(5));

        std::cout << "[funcSleep] wake up" << std::endl;
    }

    void showMenu()
    {
        std::cout << std::endl;
        std::cout << "==== Function Menu ====" << std::endl;
        std::cout << "1 : funcHello" << std::endl;
        std::cout << "2 : funcAdd" << std::endl;
        std::cout << "3 : funcSleep" << std::endl;
        std::cout << "0 : exit" << std::endl;
        std::cout << "> ";
    }
};

int main()
{
    FunctionServer server;

    std::string line;

    std::cout
        << "Function server started. pid="
        << getpid()
        << std::endl;

    while (true)
    {
        server.showMenu();

        if (!std::getline(std::cin, line))
        {
            continue;
        }

        int cmd = std::stoi(line);

        switch (cmd)
        {
            case 1:
                server.funcHello();
                break;

            case 2:
                server.funcAdd();
                break;

            case 3:
                server.funcSleep();
                break;

            case 0:
                std::cout << "exit" << std::endl;
                return 0;

            default:
                std::cout << "unknown command" << std::endl;
                break;
        }
    }

    return 0;
}
