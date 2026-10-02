#include <stddef.h>
#include <stdint.h>
#include <string.h>

int process_input(const uint8_t *data, size_t size)
{
    char input[256];
    char buffer[16];

    if (size >= sizeof(buffer))
        return 0;

    memcpy(input, data, size);
    input[size] = '\0';

    strcpy(buffer, input);

    return 1;
}