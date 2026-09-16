NVCC = nvcc
NVCCFLAGS = -I./include -arch=sm_80 -O3
TARGET = kmeans_test

all: $(TARGET)

$(TARGET): solution.cu test/test_main.cu
	$(NVCC) $(NVCCFLAGS) -o $(TARGET) solution.cu test/test_main.cu

clean:
	rm -f $(TARGET)

.PHONY: all clean
