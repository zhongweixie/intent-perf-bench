# Existing native CUDA helpers used by this derived vLLM MoE block.
import ctypes
from pathlib import Path

lib = ctypes.CDLL(str(Path(__file__).resolve().parent / 'native' / 'kernels.so'))
P = ctypes.c_void_p
I = ctypes.c_int
lib.route.argtypes = [P,P,P,P,P,I,I,I,P]
lib.route.restype = I
lib.align.argtypes = [P,P,P,P,P,I,I,I,I,I,P]
lib.align.restype = I
lib.reduce8.argtypes = [P,P,I,I,P]
lib.reduce8.restype = I

def check(code):
    if code:
        raise RuntimeError(f'CUDA launch error {code}')
