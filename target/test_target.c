#include <assert.h>
#include <stddef.h>

int process_input(const unsigned char *data, size_t size);

int main(void){
    unsigned char data[17] = {0};

    assert(process_input(data, 0) == 1);
    assert(process_input(data, 15) == 1);
    assert(process_input(data, 16) == 0);

    return 0;
}