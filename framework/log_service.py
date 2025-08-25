import os
from datetime import datetime

def log(message: str) -> None:
    """Simple logging function that writes to /log/{datetime}.txt"""
    
    # Create log directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Generate filename with current date
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{today}.txt")
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Append message to log file
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
