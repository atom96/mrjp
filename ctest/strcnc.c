#include <string.h>
#include <stdlib.h>
#include <stdio.h>

char* _str_concat(char* str1, char* str2) {
    char * new_str = malloc(strlen(str1) + strlen(str2) + 1);
    strcpy(new_str, str1);
    strcat(new_str, str2);
    return new_str;
}


void top_error() {
    printf("runtime error\n");
    exit(1);
}

int top_readInt() {
    int d;
    scanf("%d", &d);
    return d;
}

char* top_readString() {

    size_t size = 64;
    char* b = malloc(size);

    getline(&b,&size,stdin);
    return b;
}
