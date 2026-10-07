"""Linux Landlock filesystem allowlist for the DeepSpeed evaluator."""
import ctypes,errno,os,sys
from pathlib import Path

def enter(root,vendor,extra=()):
 c=ctypes.CDLL(None,use_errno=True)
 class Ruleset(ctypes.Structure):_fields_=[('handled_access_fs',ctypes.c_uint64)]
 class PathRule(ctypes.Structure):
  _pack_=1
  _fields_=[('allowed_access',ctypes.c_uint64),('parent_fd',ctypes.c_int32)]
 abi=c.syscall(444,0,0,1)
 if abi<3:raise RuntimeError('Landlock ABI >=3 required')
 mask=(1<<15)-1
 r=Ruleset(mask);fd=c.syscall(444,ctypes.byref(r),ctypes.sizeof(r),0)
 if fd<0:raise OSError(ctypes.get_errno(),'landlock create')
 def allow(p,write=False):
  p=Path(p)
  if not p.exists():return
  rights=mask if write else ((1<<0)|(1<<2)|(1<<3))
  if not p.is_dir():rights &= (1<<0)|(1<<1)|(1<<2)|(1<<14)
  pathfd=os.open(p,os.O_PATH|os.O_CLOEXEC)
  a=PathRule(rights,pathfd)
  rv=c.syscall(445,fd,1,ctypes.byref(a),0);os.close(pathfd)
  if rv<0:raise OSError(ctypes.get_errno(),'landlock rule '+str(p))
 for p in ['/usr','/lib','/lib64','/bin','/etc/ld.so.cache','/etc/ld.so.conf','/etc/ld.so.conf.d','/etc/localtime','/proc/driver/nvidia','/proc/cpuinfo','/proc/meminfo','/sys/devices','/sys/bus/pci',vendor]:allow(p)
 allow('/proc/sys/vm/mmap_min_addr')
 for p in extra:allow(p)
 allow('/proc/devices')
 allow('/proc/self',True)
 allow('/dev',True)
 allow(root,True)
 if c.prctl(38,1,0,0,0)!=0:raise RuntimeError('no_new_privs failed')
 if c.syscall(446,fd,0)<0:raise OSError(ctypes.get_errno(),'landlock restrict')
 os.close(fd)
 return
 sec=ctypes.CDLL('libseccomp.so.2')
 sec.seccomp_init.argtypes=[ctypes.c_uint32];sec.seccomp_init.restype=ctypes.c_void_p
 sec.seccomp_syscall_resolve_name.argtypes=[ctypes.c_char_p]
 sec.seccomp_rule_add.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint]
 sec.seccomp_load.argtypes=[ctypes.c_void_p]
 ctx=sec.seccomp_init(0x7fff0000)
 for name in ['ptrace','process_vm_readv','process_vm_writev','mount','bpf']:
  number=sec.seccomp_syscall_resolve_name(name.encode())
  if number>=0 and sec.seccomp_rule_add(ctx,0x50000|errno.EPERM,number,0):raise RuntimeError('seccomp rule')
 # CUDA UVM uses AF_UNIX sockets. Deny other socket families rather than
 # blocking bind/connect indiscriminately and breaking the NVIDIA driver.
 class ArgCmp(ctypes.Structure):
  _fields_=[('arg',ctypes.c_uint),('op',ctypes.c_int),('a',ctypes.c_uint64),('b',ctypes.c_uint64)]
 sec.seccomp_rule_add_array.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint,ctypes.POINTER(ArgCmp)]
 cmp=ArgCmp(0,1,1,0)
 if sec.seccomp_rule_add_array(ctx,0x50000|errno.EPERM,sec.seccomp_syscall_resolve_name(b'socket'),1,ctypes.byref(cmp)):raise RuntimeError('socket rule')
 if sec.seccomp_load(ctx):raise RuntimeError('seccomp load')

if __name__=='__main__':
 root,venv,site=sys.argv[1:4]
 enter(root,venv,extra=(site,os.environ.get('IPB_BASE_PREFIX',sys.base_prefix)))
 os.execvpe(sys.argv[4],sys.argv[4:],os.environ)
