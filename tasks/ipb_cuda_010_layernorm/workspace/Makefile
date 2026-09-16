NVCC = nvcc
NVCC_FLAGS = -O3 -arch=sm_80 -std=c++17
INCLUDES = -I./src

SRC_DIR = src
TEST_DIR = test
BUILD_DIR = build

SOURCES = $(SRC_DIR)/layernorm.cu
TEST_SOURCES = $(TEST_DIR)/test_main.cu

TARGET = layernorm_test

all: $(TARGET)

$(TARGET): $(SOURCES) $(TEST_SOURCES)
	$(NVCC) $(NVCC_FLAGS) $(INCLUDES) $(SOURCES) $(TEST_SOURCES) -o $(TARGET)

clean:
	rm -f $(TARGET)

.PHONY: all clean
