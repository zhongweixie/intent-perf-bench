NVCC = nvcc
NVCCFLAGS = -O3 -std=c++11 -arch=sm_80 -I. -Iinclude

TARGET = l2norm_benchmark
SOURCES = main.cu solve.cu

all: $(TARGET)

$(TARGET): $(SOURCES)
	$(NVCC) $(NVCCFLAGS) $(SOURCES) -o $(TARGET)

clean:
	rm -f $(TARGET)

.PHONY: all clean
