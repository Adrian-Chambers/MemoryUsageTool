"""
Process management utilities for the Memory Tracker application.
Contains functions to fetch, filter and manipulate process information.
"""
import os
import psutil
from time import time

def refresh_process_cache():
    """
    Fetch and cache process data, excluding system-critical processes.
    
    Returns:
        list: A list of filtered process objects
    """
    try:
        # Define system-critical process names or conditions to exclude
        critical_names = {"System", "Idle", "svchost.exe", "winlogon.exe", "services.exe", "csrss.exe", "smss.exe", "lsass.exe"}

        def is_system_critical(proc):
            """Determine if a process is system-critical."""
            try:
                # Exclude based on process name
                if proc.info.get('name') in critical_names:
                    return True
                # Exclude processes without a name or executable path
                if not proc.info.get('name') or not proc.info.get('exe'):
                    return True
                # Exclude processes owned by the system user (e.g., PID 0 or critical system PIDs)
                if proc.info['pid'] == 0 or proc.info['pid'] == 4:  # PID 4 is commonly "System" on Windows
                    return True
                return False
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                return True  # Exclude inaccessible or zombie processes

        # Fetch and filter processes
        process_cache = [
            proc for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'exe'])
            if not is_system_critical(proc)
        ]
        
        print(f"Process cache updated: {len(process_cache)} processes found (excluding system-critical).")
        return process_cache
    except Exception as e:
        print(f"Error refreshing process cache: {e}")
        return []


def aggregate_memory_by_name(processes):
    """
    Aggregate memory usage by process name.
    
    Args:
        processes (list): List of process objects
        
    Returns:
        dict: Dictionary with process names as keys and memory usage in MB as values
    """
    aggregated = {}
    for proc in processes:
        try:
            name = proc.info.get('name', 'Unknown')
            memory = proc.info['memory_info'].rss / (1024 * 1024)  # Convert to MB
            aggregated[name] = aggregated.get(name, 0) + memory
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return aggregated


def get_process_info_by_name(process_cache, app_name):
    """
    Retrieve process information by process name.
    
    Args:
        process_cache (list): List of process objects
        app_name (str): Name of the process to find
        
    Returns:
        dict or None: Process information dictionary or None if not found
    """
    for proc in process_cache:
        try:
            if proc.info['name'] == app_name:  # Match by process name
                return proc.info  # Return the full process info dictionary
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None  # Return None if no matching process is found


def kill_process_by_name(app_name):
    """
    Kill all processes with the given name.
    
    Args:
        app_name (str): Name of the process to kill
        
    Returns:
        tuple: (successfully_terminated, failed_to_terminate) lists of processes
    """
    processes_to_kill = [
        proc for proc in psutil.process_iter(['name', 'pid'])
        if proc.info['name'] == app_name
    ]
    
    if not processes_to_kill:
        return [], []
        
    # Attempt to terminate all matching processes
    successfully_terminated = []
    failed_to_terminate = []
    
    for process in processes_to_kill:
        try:
            process.terminate()
            process.wait(timeout=3)  # Wait up to 3 seconds for the process to terminate
            successfully_terminated.append(process)
        except psutil.NoSuchProcess:
            continue  # Process already terminated
        except (psutil.AccessDenied, psutil.TimeoutExpired):
            failed_to_terminate.append(process)
            
    return successfully_terminated, failed_to_terminate


def open_file_location(exe_path):
    """
    Open the file location of the given executable path.
    
    Args:
        exe_path (str): Path to the executable
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if exe_path and os.path.exists(exe_path):
            os.startfile(os.path.dirname(exe_path))  # Open the folder containing the executable
            return True
        return False
    except Exception as e:
        print(f"Error opening file location: {e}")
        return False
