#include <tunables/global>

profile recipe-box flags=(attach_disconnected,mediate_deleted) inherits docker-default {
  # Log-friendly identifier for diagnostics
  audit deny /proc/sysrq-trigger rw,

  # Extra read/write allowances for application layout
  /app/** r,
  /opt/venv/** r,
  owner /tmp/** rwk,
  owner /var/tmp/** rwk,

  # Networking (uvicorn binds high ports only)
  network inet,
  network inet6,
  deny network raw,

  # Deny kernel-manipulation capabilities that are never needed
  deny capability sys_admin,
  deny capability sys_module,
  deny capability sys_ptrace,
  deny capability sys_time,
  deny capability sys_tty_config,
  deny capability mac_admin,
  deny capability mac_override,
  deny capability perfmon,

  # Block namespace/file-system escape attempts
  deny mount,
  deny umount,
  deny pivot_root,
  deny signal (receive) peer=unconfined,
  deny signal (send) peer=unconfined,
  deny ptrace,

  # Guard sensitive kernel interfaces
  deny /dev/mem rw,
  deny /dev/kmem rw,
  deny /sys/** w,
  deny /proc/kcore r,
}
