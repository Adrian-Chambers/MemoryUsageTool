"""
Notification utilities for the Memory Tracker application.
Handles sending system notifications for high memory usage events.
"""
from plyer import notification

def send_high_memory_notification(app_name, memory_mb, recommendation):
    """
    Send a notification about high memory usage.
    
    Args:
        app_name (str): Name of the application
        memory_mb (float): Memory usage in MB
        recommendation (str): Recommendation text
        
    Returns:
        bool: True if notification was sent successfully
    """
    try:
        notification.notify(
            title="High Memory Usage Detected",
            message=f"{app_name} is using {memory_mb:.2f} MB of memory.\n{recommendation}",
            timeout=5,
        )
        return True
    except Exception as e:
        print(f"Error sending high memory notification: {e}")
        return False


def send_flagged_notification(app_name, memory_mb, recommendation):
    """
    Send a notification about suspiciously high memory usage.
    
    Args:
        app_name (str): Name of the application
        memory_mb (float): Memory usage in MB
        recommendation (str): Recommendation text
        
    Returns:
        bool: True if notification was sent successfully
    """
    try:
        notification.notify(
            title="Suspicious Memory Usage Detected",
            message=f"{app_name} is using {memory_mb:.2f} MB of memory.\n{recommendation}",
            timeout=5,
        )
        return True
    except Exception as e:
        print(f"Error sending flagged notification: {e}")
        return False
