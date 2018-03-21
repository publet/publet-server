import multiprocessing


bind = "127.0.0.1:8888"
daemon = False                   # Whether work in the background
debug = False                    # Some extra logging
logfile = ".gunicorn.log"        # Name of the log file
loglevel = "info"                # The level at which to log
pidfile = ".gunicorn.pid"        # Path to a PID file
umask = 0                        # Umask to set when daemonizing
user = None                      # Change process owner to user
group = None                     # Change process group to group
proc_name = "gunicorn-publet"    # Change the process name
tmp_upload_dir = None            # Set path used to store temporary uploads


workers = multiprocessing.cpu_count() * 2 + 1
