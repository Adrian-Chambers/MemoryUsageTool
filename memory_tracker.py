import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from ttkthemes import ThemedTk
import psutil
from plyer import notification
from time import time

class MemoryTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Memory Tracker")
        self.root.geometry("900x800")

        # Apply padding for all child widgets
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Default high memory threshold (1/8th of total RAM in MB)
        self.high_memory_threshold = psutil.virtual_memory().total / (1024 * 1024 * 8)

        # Process caching
        self.process_cache = []
        self.last_cache_update = 0
        self.cache_duration = 5  # Update process cache every 5 seconds

        # Sort state for maintaining order across updates
        self.current_sort_column = None
        self.current_sort_reverse = False

        # Store selected process information to handle table refresh
        self.selected_process_info = None

        # Main Frame
        self.main_frame = ttk.Frame(root, padding=10)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ttk.Label(self.main_frame, text="Memory Tracker Tool", font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, pady=10)

        # Overall Efficiency Section
        self.score_frame = ttk.LabelFrame(self.main_frame, text="Overall Efficiency", padding=10)
        self.score_frame.grid(row=1, column=0, sticky="ew", pady=10)

        self.efficiency_bar = ttk.Progressbar(self.score_frame, orient="horizontal", length=300, mode="determinate")
        self.efficiency_bar.pack(fill="x", pady=5)

        self.efficiency_label = ttk.Label(self.score_frame, text="Efficiency Score: Calculating...", font=("Arial", 14))
        self.efficiency_label.pack()

        self.efficiency_status = ttk.Label(self.score_frame, text="Status: Calculating...", font=("Arial", 12, "italic"), foreground="green")
        self.efficiency_status.pack()

        # Call the efficiency bar update AFTER the labels are defined
        self.update_efficiency_bar()

        # Threshold Adjustment
        self.threshold_frame = ttk.LabelFrame(self.main_frame, text="Threshold Adjustment", padding=10)
        self.threshold_frame.grid(row=2, column=0, sticky="ew", pady=10)

        ttk.Label(self.threshold_frame, text="High Memory Threshold (MB):", font=("Arial", 12)).grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.threshold_input = ttk.Entry(self.threshold_frame, font=("Arial", 12), width=10)
        self.threshold_input.grid(row=1, column=0, sticky="w", padx=10)
        self.threshold_input.insert(0, f"{self.high_memory_threshold:.2f}")

        self.update_threshold_button = ttk.Button(self.threshold_frame, text="Update Threshold", command=self.update_threshold)
        self.update_threshold_button.grid(row=1, column=1, sticky="w", padx=10)

        # Usage Analyzer
        self.usage_frame = ttk.LabelFrame(self.main_frame, text="Usage Analyzer", padding=10)
        self.usage_frame.grid(row=3, column=0, sticky="nsew", pady=10)
        self.main_frame.grid_rowconfigure(3, weight=1)

        # Create vertical scrollbar
        scroll_y = ttk.Scrollbar(self.usage_frame, orient="vertical")

        # Add the usage table
        columns = ("Application", "Usage", "Recommendation")
        self.usage_table = ttk.Treeview(self.usage_frame, columns=columns, show="headings", height=8, yscrollcommand=scroll_y.set)

        # Attach scrollbar to the Treeview
        scroll_y.config(command=self.usage_table.yview)
        scroll_y.pack(side="right", fill="y")  # Place scrollbar to the right of the table

        self.usage_table.pack(fill="both", expand=True)

        # Configure column widths and behavior
        self.usage_table.heading("Application", text="Application", command=lambda: self.sort_treeview(self.usage_table, "Application", False))
        self.usage_table.column("Application", width=200, anchor="center", stretch=False)

        self.usage_table.heading("Usage", text="Usage", command=lambda: self.sort_treeview(self.usage_table, "Usage", False))
        self.usage_table.column("Usage", width=100, anchor="center", stretch=False)

        self.usage_table.heading("Recommendation", text="Recommendation", command=lambda: self.sort_treeview(self.usage_table, "Recommendation", False))
        self.usage_table.column("Recommendation", width=400, anchor="w", stretch=True)

        # Add a horizontal scrollbar for the table (optional)
        scroll_x = ttk.Scrollbar(self.usage_frame, orient="horizontal", command=self.usage_table.xview)
        self.usage_table.configure(xscrollcommand=scroll_x.set)
        scroll_x.pack(side="bottom", fill="x")

        # Populate the table
        self.update_usage_table()

        # Context menu for the usage table (right-click actions)
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Kill Process", command=self.kill_selected_process)
        self.context_menu.add_command(label="Open File Location", command=self.open_file_location)
        self.context_menu.add_command(label="View Details", command=self.view_process_details)

        # Bind right-click to show the context menu
        self.usage_table.bind("<Button-3>", self.show_context_menu)

        # Notifications Section
        self.notifications_frame = ttk.LabelFrame(self.main_frame, text="Notification Settings", padding=10)
        self.notifications_frame.grid(row=4, column=0, sticky="ew", pady=10)

        self.notif_options = {
            "Close unused applications": tk.BooleanVar(value=True),
            "Optimize memory usage": tk.BooleanVar(value=True),
            "Flag unusual behavior": tk.BooleanVar(value=False),
        }

        notif_frame = ttk.Frame(self.notifications_frame)
        notif_frame.pack(anchor="w", padx=20)

        for text, var in self.notif_options.items():
            ttk.Checkbutton(notif_frame, text=text, variable=var).pack(anchor="w", pady=2)

        # Flagged Applications
        self.flagged_frame = ttk.LabelFrame(self.main_frame, text="Flagged Applications", padding=10)
        self.flagged_frame.grid(row=5, column=0, sticky="nsew", pady=10)
        self.main_frame.grid_rowconfigure(5, weight=1)

        flagged_columns = ("Application", "Usage", "Reason")
        self.flagged_table = ttk.Treeview(self.flagged_frame, columns=flagged_columns, show="headings", height=6)
        self.flagged_table.pack(fill="both", expand=True)

        # Configure column widths and behavior
        self.flagged_table.heading("Application", text="Application")
        self.flagged_table.column("Application", width=200, anchor="center", stretch=False)

        self.flagged_table.heading("Usage", text="Usage")
        self.flagged_table.column("Usage", width=100, anchor="center", stretch=False)

        self.flagged_table.heading("Reason", text="Reason")
        self.flagged_table.column("Reason", width=400, anchor="w", stretch=True)

        # Add a horizontal scrollbar for the flagged table
        flagged_scroll_x = ttk.Scrollbar(self.flagged_frame, orient="horizontal", command=self.flagged_table.xview)
        self.flagged_table.configure(xscrollcommand=flagged_scroll_x.set)
        flagged_scroll_x.pack(side="bottom", fill="x")

        # Populate the flagged table
        self.update_flagged_table()

        # Footer
        ttk.Label(self.main_frame, text="Memory Tracker Tool - Version 1.0", font=("Arial", 10, "italic")).grid(row=6, column=0, pady=10)


    def get_cached_processes(self):
        """Fetch process data, updating the cache if necessary."""
        if time() - self.last_cache_update > self.cache_duration:
            try:
                self.process_cache = list(psutil.process_iter(['pid', 'name', 'memory_info', 'exe']))
                self.last_cache_update = time()
            except Exception:
                self.process_cache = [] 
        return self.process_cache

    def update_efficiency_bar(self):
        """Update the efficiency bar and calculate status."""
        mem = psutil.virtual_memory()
        free_mem_percent = (mem.available / mem.total) * 100

        self.efficiency_bar['value'] = free_mem_percent
        self.efficiency_label.config(text=f"Efficiency Score: {free_mem_percent:.2f}% Free")

        # Update status based on free memory percentage
        if free_mem_percent > 60:
            self.efficiency_status.config(text="Status: Good", foreground="green")
        elif free_mem_percent > 30:
            self.efficiency_status.config(text="Status: Fair", foreground="orange")
        else:
            self.efficiency_status.config(text="Status: Poor", foreground="red")

        self.root.after(1000, self.update_efficiency_bar)

    def update_threshold(self):
        """Update the high memory threshold based on user input."""
        try:
            # Disable the button and show a loading indicator
            self.update_threshold_button.config(text="Updating...", state="disabled")
            self.root.update_idletasks()

            # Get and validate the new threshold
            new_threshold = float(self.threshold_input.get())
            if new_threshold <= 0:
                raise ValueError("Threshold must be greater than 0.")
            
            # Update the threshold
            self.high_memory_threshold = new_threshold
            print(f"Threshold updated to {self.high_memory_threshold:.2f} MB")
            
            # Refresh the usage table immediately
            self.update_usage_table()

        except ValueError:
            # Show an error and reset the input field to the current threshold
            self.threshold_input.delete(0, tk.END)
            self.threshold_input.insert(0, f"{self.high_memory_threshold:.2f}")
        finally:
            # Re-enable the button and reset its text
            self.update_threshold_button.config(text="Update Threshold", state="normal")


    def is_browser(self, process):
        try:
            browser_keywords = ["chrome", "firefox", "safari", "edge", "opera", "brave"]
            if any(keyword in process.info['name'].lower() for keyword in browser_keywords):
                return True

            exe_path = process.info.get('exe', '')
            if exe_path and any(browser in exe_path.lower() for browser in browser_keywords):
                return True
        except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
            pass

        return False

    def update_usage_table(self):
        """Update the usage table while maintaining the current sort order."""
        # Delete all existing rows
        self.usage_table.delete(*self.usage_table.get_children())

        # Fetch and insert new rows
        for proc in self.get_cached_processes():
            try:
                pinfo = proc.info
                # Ensure 'memory_info' exists in the process info dictionary
                if 'memory_info' not in pinfo:
                    continue

                mem_info = pinfo['memory_info']
                mem_usage_mb = mem_info.vms / (1024 * 1024)

                # Only display processes exceeding the memory threshold
                if mem_usage_mb > self.high_memory_threshold:
                    recommendation = self.generate_recommendation(pinfo['name'], mem_usage_mb)
                    self.usage_table.insert("", "end", values=(pinfo['name'], f"{mem_usage_mb:.2f} MB", recommendation))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue  # Skip processes that are inaccessible
        # Reapply the current sort order
        if self.current_sort_column is not None:
            self.sort_treeview(self.usage_table, self.current_sort_column, self.current_sort_reverse)

        # Schedule the next update
        self.root.after(5000, self.update_usage_table)



    def generate_recommendation(self, app_name, memory_usage):
        """Generate a recommendation based on the application name and memory usage."""
        app_name_lower = app_name.lower()

        # Browser-related recommendations
        if any(keyword in app_name_lower for keyword in ["chrome", "firefox", "safari", "edge", "opera", "brave"]):
            if memory_usage > self.high_memory_threshold:
                return "Consider closing unused tabs or restarting the browser."
            else:
                return "Close unnecessary tabs to reduce memory usage."

        # Development Tools
        elif any(keyword in app_name_lower for keyword in ["code", "pycharm", "intellij", "eclipse"]):
            return "Close unused projects or restart the IDE to free up resources."

        # Streaming Applications
        elif any(keyword in app_name_lower for keyword in ["spotify", "vlc", "netflix", "youtube"]):
            return "Pause the application if not actively using it."

        # Communication Apps
        elif any(keyword in app_name_lower for keyword in ["zoom", "teams", "slack", "discord"]):
            return "Close unused calls or chats to save resources."

        # Gaming Applications
        elif any(keyword in app_name_lower for keyword in ["game", "steam", "epic", "blizzard"]):
            return "Close background apps to improve game performance."

        # File Sharing and Cloud Services
        elif any(keyword in app_name_lower for keyword in ["onedrive", "dropbox", "google drive"]):
            return "Pause syncing to free up memory."

        # Office Applications
        elif any(keyword in app_name_lower for keyword in ["word", "excel", "powerpoint", "office"]):
            return "Close unused documents or spreadsheets."

        # High Memory Usage
        if memory_usage > self.high_memory_threshold:
            return "Restart the application to release unused memory."

        # Default Recommendation
        return "Consider closing the application if not actively using it."

    def show_context_menu(self, event):
        """Show context menu and store selected process details."""
        try:
            # Identify the row under the cursor
            row_id = self.usage_table.identify_row(event.y)
            if row_id:
                self.usage_table.selection_set(row_id)  # Select the row
                # Store the selected process details
                selected_item = self.usage_table.item(row_id, "values")
                app_name = selected_item[0]  # Application name
                self.selected_process_info = self.get_process_info_by_name(app_name)
                # Show the context menu
                self.context_menu.post(event.x_root, event.y_root)
            else:
                self.selected_process_info = None  # Clear selection if no row
        except Exception as e:
            print(f"Error showing context menu: {e}")

    # Show the context menu on right-click
    def get_process_info_by_name(self, app_name):
        """Retrieve process information by name."""
        for proc in self.get_cached_processes():
            if proc.info["name"] == app_name:
                return proc.info  # Return the full process info dictionary
        return None

    # Kill the selected process
    def kill_selected_process(self):
        """Kill all processes with the same name as the selected process."""
        try:
            if self.selected_process_info:
                app_name = self.selected_process_info["name"]  # Get the name of the process
                processes_to_kill = [
                    proc for proc in psutil.process_iter(['name', 'pid'])
                    if proc.info['name'] == app_name
                ]

                if not processes_to_kill:
                    messagebox.showinfo("Process Gone", "The process no longer exists.")
                    return

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
                    except psutil.AccessDenied:
                        failed_to_terminate.append(process)
                    except psutil.TimeoutExpired:
                        failed_to_terminate.append(process)

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

                # Refresh the table to reflect updated process list
                self.refresh_process_cache()
                self.update_usage_table()
            else:
                messagebox.showerror("Error", "No process selected.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not terminate process: {e}")




    def refresh_process_cache(self):
        """Force a refresh of the process cache."""
        try:
            self.process_cache = list(psutil.process_iter(['pid', 'name', 'memory_info', 'exe']))
            self.last_cache_update = time()
        except Exception as e:
            print(f"Error refreshing process cache: {e}")



    # Open the file location of the selected process
    def open_file_location(self):
        """Open the file location of the selected process."""
        try:
            if self.selected_process_info:
                exe_path = self.selected_process_info.get("exe", "")
                if exe_path and os.path.exists(exe_path):
                    os.startfile(os.path.dirname(exe_path))
                else:
                    messagebox.showerror("Error", "Executable path not found.")
            else:
                messagebox.showerror("Error", "No process selected.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file location: {e}")


    # View detailed information about the selected process
    def view_process_details(self):
        """View detailed information about the selected process."""
        try:
            if self.selected_process_info:
                process = psutil.Process(self.selected_process_info["pid"])
                details = (
                    f"Name: {process.name()}\n"
                    f"PID: {process.pid}\n"
                    f"Status: {process.status()}\n"
                    f"CPU Usage: {process.cpu_percent(interval=0.1)}%\n"
                    f"Memory Usage: {process.memory_info().rss / (1024 * 1024):.2f} MB\n"
                    f"Executable: {process.exe()}\n"
                    f"Threads: {process.num_threads()}\n"
                )
                messagebox.showinfo("Process Details", details)
            else:
                messagebox.showerror("Error", "No process selected.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not fetch process details: {e}")


    # Helper function to get the PID of a process by its name
    def get_pid_by_name(self, app_name):
        for proc in self.get_cached_processes():
            if proc.info['name'] == app_name:
                return proc.info['pid']
        return None

    def update_flagged_table(self):
        self.flagged_table.delete(*self.flagged_table.get_children())
        for proc in self.get_cached_processes():
            try:
                pinfo = proc.info
                mem_info = pinfo['memory_info']
                mem_usage_mb = mem_info.vms / (1024 * 1024)
                if mem_usage_mb > 1000:
                    self.flagged_table.insert("", "end", values=(pinfo['name'], f"{mem_usage_mb:.2f} MB", "High memory usage"))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        self.root.after(5000, self.update_flagged_table)

    def send_notifications(self):
        if self.notif_options["Close unused applications"].get():
            notification.notify(
                title="Memory Optimization",
                message="Consider closing unused applications to free up memory.",
                timeout=5
            )
        if self.notif_options["Optimize memory usage"].get():
            notification.notify(
                title="Memory Optimization",
                message="Optimizing memory usage can improve system performance.",
                timeout=5
            )
        if self.notif_options["Flag unusual behavior"].get():
            notification.notify(
                title="Potential Issue Detected",
                message="Unusual behavior detected. Consider reviewing flagged applications.",
                timeout=5
            )

    def sort_treeview(self, treeview, col, reverse):
        """Sort the Treeview by a given column and save the sort state."""
        try:
            # Get all items in the Treeview
            items = [(treeview.set(k, col), k) for k in treeview.get_children('')]

            # Convert numeric columns to float for sorting
            try:
                items.sort(key=lambda t: float(t[0].replace(' MB', '')), reverse=reverse)
            except ValueError:  # Non-numeric sorting
                items.sort(reverse=reverse)

            # Rearrange items in sorted order
            for index, (_, k) in enumerate(items):
                treeview.move(k, '', index)

            # Save the current sort state
            self.current_sort_column = col
            self.current_sort_reverse = reverse

            # Update the heading to allow toggling the sort direction
            treeview.heading(col, command=lambda: self.sort_treeview(treeview, col, not reverse))
        except Exception as e:
            print(f"Error sorting column '{col}': {e}")

# Run the application
if __name__ == "__main__":
    root = ThemedTk(theme="plastik")
    app = MemoryTrackerApp(root)
    root.mainloop()
