#include <stddef.h>
#include <stdint.h>

int process_input(const unsigned char *data, size_t size);

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
    process_input(data, size);

    return 0;
}