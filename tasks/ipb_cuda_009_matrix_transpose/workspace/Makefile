NVCC = nvcc
CXXFLAGS = -I./include -arch=sm_80 -O3
TARGET = transpose_test

all: $(TARGET)

$(TARGET): solution.cu test/test_main.cu
	$(NVCC) $(CXXFLAGS) -o $(TARGET) solution.cu test/test_main.cu

clean:
	rm -f $(TARGET)

.PHONY: all clean
