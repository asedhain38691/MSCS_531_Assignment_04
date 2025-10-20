#include <stdio.h>

int main() {
    int a = 5, b = 10, c;
    c = a + b;
    for (int i = 0; i < 5; i++) {
        c += i;
    }
    printf("Result: %d\n", c);
    return 0;
}