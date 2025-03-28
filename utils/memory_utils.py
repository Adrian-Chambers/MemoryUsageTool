"""
Memory analysis utilities for the Memory Tracker application.
Contains functions to analyze and provide recommendations for memory usage.
"""
import psutil

def calculate_default_thresholds():
    """
    Calculate default thresholds based on total system memory.
    
    Returns:
        tuple: (usage_analyzer_threshold, flagged_applications_threshold) in MB
    """
    total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
    usage_threshold = max(200, total_memory_mb * 0.02)  # Default: 2% of total memory or 200 MB
    flagged_threshold = max(1500, total_memory_mb * 0.15)  # Default: 15% of total memory or 1500 MB
    return usage_threshold, flagged_threshold


def get_memory_efficiency():
    """
    Calculate the memory efficiency score.
    
    Returns:
        tuple: (free_memory_percentage, status)
    """
    mem = psutil.virtual_memory()
    free_mem_percent = (mem.available / mem.total) * 100
    
    if free_mem_percent > 60:
        status = "Good"
        color = "green"
    elif free_mem_percent > 30:
        status = "Fair"
        color = "orange"
    else:
        status = "Poor"
        color = "red"
        
    return free_mem_percent, status, color


def mb_to_percent(mb_value):
    """
    Convert a memory value in MB to a percentage of total memory.
    
    Args:
        mb_value (float): Memory value in MB
        
    Returns:
        float: Memory value as a percentage of total memory
    """
    total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
    return (mb_value / total_memory_mb) * 100


def percent_to_mb(percent_value):
    """
    Convert a memory percentage to a value in MB.
    
    Args:
        percent_value (float): Memory percentage
        
    Returns:
        float: Memory value in MB
    """
    total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
    return (percent_value / 100) * total_memory_mb


def generate_detailed_recommendation(app_name, memory_mb, usage_threshold, flagged_threshold):
    """
    Generate a detailed recommendation based on memory usage patterns.
    
    Args:
        app_name (str): Name of the application
        memory_mb (float): Memory usage in MB
        usage_threshold (float): Usage analyzer threshold in MB
        flagged_threshold (float): Flagged applications threshold in MB
        
    Returns:
        str: Detailed recommendation
    """
    app_name_lower = app_name.lower()
    total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
    memory_percent = (memory_mb / total_memory_mb) * 100  # Calculate memory usage as a percentage of total

    # Base recommendation levels
    if memory_percent > 50:
        base_recommendation = "CRITICAL: Process consuming over 50% of system memory. "
    elif memory_mb > flagged_threshold:
        base_recommendation = "WARNING: High memory usage detected. "
    elif memory_mb > usage_threshold * 3:
        base_recommendation = "High Usage: "
    elif memory_mb > usage_threshold * 2:
        base_recommendation = "Moderate Usage: "
    else:
        base_recommendation = "Usage is within acceptable limits. "

    # Application-specific recommendations
    if any(keyword in app_name_lower for keyword in ["chrome", "firefox", "safari", "edge", "opera", "brave"]):
        recommendation = base_recommendation + "Consider closing unused tabs or restarting the browser."
    elif any(keyword in app_name_lower for keyword in ["code", "pycharm", "intellij", "eclipse", "visual studio"]):
        recommendation = base_recommendation + "Close unused projects or restart the IDE to free up resources."
    elif any(keyword in app_name_lower for keyword in ["spotify", "vlc", "netflix", "youtube", "prime"]):
        recommendation = base_recommendation + "Pause the application if not actively using it."
    elif any(keyword in app_name_lower for keyword in ["zoom", "teams", "slack", "discord", "skype"]):
        recommendation = base_recommendation + "Close unused calls or chats to save resources."
    elif any(keyword in app_name_lower for keyword in ["game", "steam", "epic", "blizzard", "riot"]):
        recommendation = base_recommendation + "Close background apps to improve game performance."
    elif any(keyword in app_name_lower for keyword in ["onedrive", "dropbox", "google drive", "icloud"]):
        recommendation = base_recommendation + "Pause syncing to free up memory."
    elif any(keyword in app_name_lower for keyword in ["word", "excel", "powerpoint", "outlook", "office"]):
        recommendation = base_recommendation + "Close unused documents or spreadsheets."
    elif any(keyword in app_name_lower for keyword in ["premiere", "photoshop", "after effects", "final cut", "lightroom", "gimp"]):
        recommendation = base_recommendation + "Close unused projects or export completed work to free up resources."
    elif any(keyword in app_name_lower for keyword in ["svchost", "system", "winlogon", "lsass"]):
        recommendation = "System Process: Normal Windows service. Leave running."
    else:
        # Default recommendation
        if memory_mb > usage_threshold * 2:
            recommendation = base_recommendation + "Restart the application to release unused memory."
        else:
            recommendation = base_recommendation + "Consider closing the application if not actively using it."

    return recommendation
