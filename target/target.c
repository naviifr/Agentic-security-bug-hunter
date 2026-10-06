#include <stddef.h>
#include <stdint.h>
#include <string.h>

static int helper_check(size_t size)
{
    if (size > 200)
    {
        return 0;
    }

    return 1;
}

static int helper_transform(const uint8_t *data, size_t size)
{
    int result = 0;

    if (data != NULL)
    {
        for (size_t index = 0; index < size; index++)
        {
            if (data[index] == 'A')
            {
                result++;
            }
        }
    }

    return result;
}

int process_input(const uint8_t *data, size_t size)
{
    char input[256];
    char buffer[16];

    if (!helper_check(size))
        return 0;

    helper_transform(data, size);

    if (size >= sizeof(input))
        return 0;

    memcpy(input, data, size);
    input[size] = '\0';

    strcpy(buffer, input);

    return 1;
}

static int final_helper(void)
{
    return 42;
}