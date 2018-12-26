#include <string.h>
#include <stdlib.h>

char* _str_concat(char* str1, char* str2) {
    char * new_str = malloc(strlen(str1) + strlen(str2));
    strcpy(new_str, str1);
    strcat(new_str, str2);
    return new_str;
}
