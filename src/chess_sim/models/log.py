import os
from datetime import datetime

class logger:
    def __init__(self, log_name="log"):
        log_dir="logs" # pls dont change
        os.makedirs(log_dir, exist_ok=True)

        
        # Generate filename with date and time
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = os.path.join(log_dir, f"{log_name}_{timestamp}.txt")
        with open(self.log_file, "a") as f:
            f.write(f"{datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")} --- Start of Log ---\n")
        self._cleanup_old_logs(log_dir, keep=10)

    def _cleanup_old_logs(self, log_dir, keep=10):
        log_files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith(".txt")]
        log_files.sort(key=os.path.getmtime, reverse=True)
        for old_file in log_files[(keep-1):]:
            os.remove(old_file)

    def log(self, message):
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        with open(self.log_file, "a") as f:
            f.write(f"{timestamp} {message}\n")
    
    def end_log(self):
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        with open(self.log_file, "a") as f:
            f.write(f"{timestamp} --- End of Log ---\n")
