"""
Main application class for the Memory Tracker tool.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
from time import time
from concurrent.futures import ThreadPoolExecutor

from utils import process_utils, memory_utils
from gui.components import EfficiencySection, HighestMemoryTable, FlaggedMemoryTable


class MemoryTrackerApp:
    def __init__(self, root):
        """
        Initialize the Memory Tracker App.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Memory Tracker")
        self.root.geometry("900x1000")
        
        # Global state
        self.process_cache = []
        self.last_cache_update = 0
        self.cache_duration = 15  # Refresh every 15 seconds
        self.selected_process_info = None
        self.executor = ThreadPoolExecutor(max_workers=4)  # Thread pool for background tasks
        
        # Main Frame
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Setup GUI Sections
        self.setup_title()
        self.setup_efficiency_section()
        self.setup_memory_tables()
        self.setup_footer()
        self.setup_context_menus()
        
        # Initialize Process Cache and Populate Tables
        self.refresh_process_cache()
        self.update_tables()
        
        # Start background updates
        self.schedule_background_updates()
    
    def setup_title(self):
        """Setup the title section."""
        title_label = ttk.Label(
            self.main_frame,
            text="Memory Tracker Tool",
            font=("Arial", 18, "bold")
        )
        title_label.grid(row=0, column=0, pady=10)
    
    def setup_efficiency_section(self):
        """Setup the overall efficiency section."""
        self.efficiency_section = EfficiencySection(self.main_frame, self.root)
        self.efficiency_section.score_frame.grid(row=1, column=0, sticky="ew", pady=15)
        # Schedule regular updates
        self.update_efficiency_bar()
    
    def setup_memory_tables(self):
        """Setup memory usage tables."""
        # Setup highest memory usage table
        self.highest_memory_table = HighestMemoryTable(
            self.main_frame,
            self.root,
            threshold_callback=lambda: self.update_tables(),
            context_menu_callback=self.show_usage_context_menu
        )
        self.highest_memory_table.frame.grid(row=3, column=0, sticky="nsew", pady=15)
        self.main_frame.grid_rowconfigure(3, weight=1)
        
        # Setup flagged applications table
        self.flagged_memory_table = FlaggedMemoryTable(
            self.main_frame,
            self.root,
            threshold_callback=lambda: self.update_tables(),
            context_menu_callback=self.show_flagged_context_menu
        )
        self.flagged_memory_table.frame.grid(row=5, column=0, sticky="nsew", pady=15)
        self.main_frame.grid_rowconfigure(5, weight=1)
    
    def setup_footer(self):
        """Setup the footer section."""
        footer_label = ttk.Label(
            self.main_frame,
            text="Memory Tracker Tool - Version 1.0",
            font=("Arial", 10, "italic"),
            anchor="center"
        )
        footer_label.grid(row=7, column=0, pady=10)
    
    def setup_context_menus(self):
        """Setup context menus for the tables."""
        # Usage Table Context Menu
        self.usage_context_menu = tk.Menu(self.root, tearoff=0)
        self.usage_context_menu.add_command(label="Kill Process", command=self.kill_selected_process)
        self.usage_context_menu.add_command(label="Open File Location", command=self.open_file_location)
        self.usage_context_menu.add_command(label="View Details", command=self.view_process_details)
        
        # Flagged Table Context Menu
        self.flagged_context_menu = tk.Menu(self.root, tearoff=0)
        self.flagged_context_menu.add_command(label="Kill Process", command=self.kill_selected_process)
        self.flagged_context_menu.add_command(label="Open File Location", command=self.open_file_location)
        self.flagged_context_menu.add_command(label="View Details", command=self.view_process_details)
    
    def refresh_process_cache(self):
        """Refresh the process cache if needed."""
        current_time = time()
        if current_time - self.last_cache_update > self.cache_duration:
            self.process_cache = process_utils.refresh_process_cache()
            self.last_cache_update = current_time
            return True
        return False
    
    def update_efficiency_bar(self):
        """Update the efficiency bar regularly."""
        self.efficiency_section.update()
        self.root.after(2000, self.update_efficiency_bar)
    
    def update_tables(self):
        """Update both tables with current process data."""
        # Make sure cache is updated
        if self.refresh_process_cache():
            print("Process cache refreshed before updating tables")
        
        # Update highest memory usage table
        self.highest_memory_table.update_table(self.process_cache)
        
        # Update flagged applications table
        self.flagged_memory_table.update_table(self.process_cache)
    
    def schedule_background_updates(self):
        """Schedule background updates for process data."""
        self.executor.submit(self.refresh_process_cache)
        self.root.after(10000, self.schedule_background_updates)
        # Refresh tables every 10 seconds
        self.root.after(10000, self.update_tables)
    
    # --- Context menu handlers ---
    def show_usage_context_menu(self, event):
        """Show the context menu for the Usage Analyzer table."""
        try:
            # Identify the row under the cursor
            row_id = self.highest_memory_table.table.identify_row(event.y)
            if row_id:
                self.highest_memory_table.table.selection_set(row_id)  # Select the row
                selected_item = self.highest_memory_table.table.item(row_id, "values")
                if selected_item:
                    app_name = selected_item[0]  # Application name from the table
                    self.selected_process_info = process_utils.get_process_info_by_name(self.process_cache, app_name)
                    self.usage_context_menu.post(event.x_root, event.y_root)
                else:
                    self.selected_process_info = None
            else:
                self.selected_process_info = None
        except Exception as e:
            print(f"Error showing usage context menu: {e}")
    
    def show_flagged_context_menu(self, event):
        """Show the context menu for the Flagged Applications table."""
        try:
            # Identify the row under the cursor
            row_id = self.flagged_memory_table.table.identify_row(event.y)
            if row_id:
                self.flagged_memory_table.table.selection_set(row_id)  # Select the row
                selected_item = self.flagged_memory_table.table.item(row_id, "values")
                if selected_item:
                    app_name = selected_item[0]  # Application name from the table
                    self.selected_process_info = process_utils.get_process_info_by_name(self.process_cache, app_name)
                    self.flagged_context_menu.post(event.x_root, event.y_root)
                else:
                    self.selected_process_info = None
            else:
                self.selected_process_info = None
        except Exception as e:
            print(f"Error showing flagged context menu: {e}")
    
    def kill_selected_process(self):
        """Kill all processes with the same name as the selected process."""
        try:
            if self.selected_process_info:
                app_name = self.selected_process_info.get("name")  # Get the name of the process
                if not app_name:
                    messagebox.showerror("Error", "No process name found.")
                    return
                
                # Kill all processes with the same name
                successfully_terminated, failed_to_terminate = process_utils.kill_process_by_name(app_name)
                
                # Handle results
                if successfully_terminated:
                    unique_names = set([p.info['name'] for p in successfully_terminated])
                    if len(unique_names) == 1:
                        # All terminated processes share the same name
                        terminated_name = next(iter(unique_names))
                        messagebox.showinfo("Success", f"Terminated: {terminated_name} and all subprocesses.")
                    else:
                        # Multiple process names were terminated
                        terminated_names = ", ".join(unique_names)
                        messagebox.showinfo("Success", f"Terminated: {terminated_names}")
                
                if failed_to_terminate:
                    failed_names = ", ".join(set([p.info['name'] for p in failed_to_terminate]))
                    messagebox.showerror("Error", f"Failed to terminate: {failed_names}")
                
                # Refresh the tables to reflect updated process list
                self.refresh_process_cache()
                self.update_tables()
            else:
                messagebox.showerror("Error", "No process selected.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not terminate process: {e}")
    
    def open_file_location(self):
        """Open the file location of the selected process."""
        try:
            if self.selected_process_info:
                exe_path = self.selected_process_info.get("exe", None)
                result = process_utils.open_file_location(exe_path)
                
                if not result:
                    messagebox.showerror("Error", "Executable path not found or inaccessible.")
            else:
                messagebox.showerror("Error", "No process selected.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file location: {e}")
    
    def view_process_details(self):
        """View detailed information about the selected process."""
        try:
            if self.selected_process_info:
                app_name = self.selected_process_info.get("name")
                
                # Aggregate memory usage for all processes with the same name
                total_memory_mb = 0
                process_details = []  # Store details for all matching processes
                for proc in self.process_cache:
                    try:
                        if proc.info['name'] == app_name:
                            memory_mb = proc.info['memory_info'].rss / (1024 * 1024)  # Convert to MB
                            total_memory_mb += memory_mb
                            process_details.append({
                                "PID": proc.info['pid'],
                                "Memory": f"{memory_mb:.2f} MB",
                                "Executable": proc.info.get('exe', 'N/A'),
                                "Status": proc.status(),
                                "Threads": proc.num_threads(),
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Generate the details message
                details_message = f"Name: {app_name}\n" \
                                f"Total Memory Usage: {total_memory_mb:.2f} MB\n\n"
                
                for details in process_details:
                    details_message += f"PID: {details['PID']}\n" \
                                    f"Memory: {details['Memory']}\n" \
                                    f"Executable: {details['Executable']}\n" \
                                    f"Status: {details['Status']}\n" \
                                    f"Threads: {details['Threads']}\n\n"
                
                # Show the aggregated details
                messagebox.showinfo("Process Details", details_message)
            else:
                messagebox.showerror("Error", "No process selected.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not fetch process details: {e}")
