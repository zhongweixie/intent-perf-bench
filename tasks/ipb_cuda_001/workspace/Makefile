NVCC = nvcc
NVCCFLAGS = -O3 -std=c++17 -arch=sm_90

TARGET = huffman_decode

.PHONY: all clean

all: $(TARGET)

$(TARGET): main.cu solve.cu stream_manager.cu solve.h stream_manager.h
	$(NVCC) $(NVCCFLAGS) -o $@ main.cu solve.cu stream_manager.cu

clean:
	rm -f $(TARGET)
