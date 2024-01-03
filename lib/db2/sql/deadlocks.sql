SELECT deadlocks,lock_waits, DOUBLE(elapsed_exec_time_s + elapsed_exec_time_ms / 1000000), DOUBLE(lock_wait_time / 1000) FROM sysibmadm.snapdb

