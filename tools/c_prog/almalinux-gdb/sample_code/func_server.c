// file: function_server.c

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void func_hello(void)
{
    printf("[func_hello] Hello\n");
}

void func_add(void)
{
    int a = 10;
    int b = 20;

    printf("[func_add] %d + %d = %d\n", a, b, a + b);
}

void func_sleep(void)
{
    printf("[func_sleep] sleeping 5 sec...\n");
    sleep(5);
    printf("[func_sleep] wake up\n");
}

void show_menu(void)
{
    printf("\n");
    printf("==== Function Menu ====\n");
    printf("1 : func_hello\n");
    printf("2 : func_add\n");
    printf("3 : func_sleep\n");
    printf("0 : exit\n");
    printf("> ");
    fflush(stdout);
}

int main(void)
{
    char buf[64];

    printf("Function server started. pid=%d\n", getpid());

    while (1)
    {
        show_menu();

        if (fgets(buf, sizeof(buf), stdin) == NULL)
        {
            continue;
        }

        int cmd = atoi(buf);

        switch (cmd)
        {
            case 1:
                func_hello();
                break;

            case 2:
                func_add();
                break;

            case 3:
                func_sleep();
                break;

            case 0:
                printf("exit\n");
                return 0;

            default:
                printf("unknown command\n");
                break;
        }
    }

    return 0;
}
