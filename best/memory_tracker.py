import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from ttkthemes import ThemedTk
import psutil
from plyer import notification
from time import time
from threading import Thread

class MemoryTrackerApp:
    def __init__(self, root):
        """Initialize the Memory Tracker App."""
        self.root = root
        self.root.title("Memory Tracker")
        self.root.geometry("900x800")

        # Global Configurations
        self.high_memory_threshold = psutil.virtual_memory().total / (1024 * 1024 * 8)
        self.process_cache = []
        self.last_cache_update = 0
        self.cache_duration = 5  # Refresh every 5 seconds
        self.current_sort_column = None
        self.current_sort_reverse = False
        self.selected_process_info = None

        # Main Frame
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Setup GUI Sections
        self.setup_title()
        self.setup_efficiency_section()
        self.setup_threshold_adjustment()
        self.setup_usage_analyzer()
        self.setup_notifications()
        self.setup_flagged_applications()
        self.setup_footer()

    # --- GUI Setup Methods ---
    def setup_title(self):
        """Setup the title section."""
        title_label = ttk.Label(self.main_frame, text="Memory Tracker Tool", font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, pady=10)

    def setup_efficiency_section(self):
        """Setup the overall efficiency section."""
        self.score_frame = ttk.LabelFrame(self.main_frame, text="Overall Efficiency", padding=10)
        self.score_frame.grid(row=1, column=0, sticky="ew", pady=10)

        self.efficiency_bar = ttk.Progressbar(self.score_frame, orient="horizontal", length=300, mode="determinate")
        self.efficiency_bar.pack(fill="x", pady=5)

        self.efficiency_label = ttk.Label(self.score_frame, text="Efficiency Score: Calculating...", font=("Arial", 14))
        self.efficiency_label.pack()

        self.efficiency_status = ttk.Label(self.score_frame, text="Status: Calculating...", font=("Arial", 12, "italic"), foreground="green")
        self.efficiency_status.pack()

        self.update_efficiency_bar()

    def setup_threshold_adjustment(self):
        """Setup the threshold adjustment section."""
        self.threshold_frame = ttk.LabelFrame(self.main_frame, text="Threshold Adjustment", padding=10)
        self.threshold_frame.grid(row=2, column=0, sticky="ew", pady=10)

        ttk.Label(self.threshold_frame, text="High Memory Threshold (MB):", font=("Arial", 12)).grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.threshold_input = ttk.Entry(self.threshold_frame, font=("Arial", 12), width=10)
        self.threshold_input.grid(row=1, column=0, sticky="w", padx=10)
        self.threshold_input.insert(0, f"{self.high_memory_threshold:.2f}")

        self.update_threshold_button = ttk.Button(self.threshold_frame, text="Update Threshold", command=self.update_threshold)
        self.update_threshold_button.grid(row=1, column=1, sticky="w", padx=10)

    def setup_usage_analyzer(self):
        """Setup the Usage Analyzer table."""
        self.usage_frame = ttk.LabelFrame(self.main_frame, text="Usage Analyzer", padding=10)
        self.usage_frame.grid(row=3, column=0, sticky="nsew", pady=10)
        self.main_frame.grid_rowconfigure(3, weight=1)

        # Scrollbars
        scroll_y = ttk.Scrollbar(self.usage_frame, orient="vertical")

        # Table
        columns = ("Application", "Usage", "Recommendation")
        self.usage_table = ttk.Treeview(
            self.usage_frame, columns=columns, show="headings", height=8, yscrollcommand=scroll_y.set
        )
        scroll_y.config(command=self.usage_table.yview)
        scroll_y.pack(side="right", fill="y")
        self.usage_table.pack(fill="both", expand=True)

        # Configure Columns
        self.configure_table_columns(self.usage_table, {
            "Application": {"width": 200, "anchor": "center"},
            "Usage": {"width": 100, "anchor": "center"},
            "Recommendation": {"width": 400, "anchor": "w"},
        })

        # Context Menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Kill Process", command=self.kill_selected_process)
        self.context_menu.add_command(label="Open File Location", command=self.open_file_location)
        self.context_menu.add_command(label="View Details", command=self.view_process_details)
        self.usage_table.bind("<Button-3>", self.show_context_menu)

        self.update_usage_table()

    def setup_notifications(self):
        """Setup the Notifications section."""
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

    def setup_flagged_applications(self):
        """Setup the Flagged Applications table."""
        self.flagged_frame = ttk.LabelFrame(self.main_frame, text="Flagged Applications", padding=10)
        self.flagged_frame.grid(row=5, column=0, sticky="nsew", pady=10)
        self.main_frame.grid_rowconfigure(5, weight=1)

        # Scrollbars
        scroll_y = ttk.Scrollbar(self.flagged_frame, orient="vertical")

        # Table
        columns = ("Application", "Usage", "Reason")
        self.flagged_table = ttk.Treeview(
            self.flagged_frame, columns=columns, show="headings", height=6, yscrollcommand=scroll_y.set
        )
        scroll_y.config(command=self.flagged_table.yview)
        scroll_y.pack(side="right", fill="y")
        self.flagged_table.pack(fill="both", expand=True)

        # Configure Columns
        self.configure_table_columns(self.flagged_table, {
            "Application": {"width": 200, "anchor": "center"},
            "Usage": {"width": 100, "anchor": "center"},
            "Reason": {"width": 400, "anchor": "w"},
        })

        self.update_flagged_table()

    def setup_footer(self):
        """Setup the footer section."""
        ttk.Label(self.main_frame, text="Memory Tracker Tool - Version 1.0", font=("Arial", 10, "italic")).grid(row=6, column=0, pady=10)

    # --- Helper Methods ---
    def configure_table_columns(self, table, columns_config):
        """Configure columns for a Treeview table."""
        for col, config in columns_config.items():
            table.heading(col, text=col, command=lambda _col=col: self.sort_treeview(table, _col, False))
            table.column(col, **config)


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
        """Update the usage table with processes exceeding the threshold or the top 5 highest memory usage."""
        self.usage_table.delete(*self.usage_table.get_children())

        processes_above_threshold = []
        all_processes = []

        for proc in self.get_cached_processes():
            try:
                pinfo = proc.info
                if 'memory_info' not in pinfo or 'pid' not in pinfo:
                    continue

                process = psutil.Process(pinfo['pid'])
                mem_usage_mb = process.memory_info().rss / (1024 * 1024)  # Convert to MB

                # Track all processes for sorting later
                all_processes.append((pinfo['name'], mem_usage_mb))

                # Only display processes exceeding the memory threshold
                if mem_usage_mb > self.high_memory_threshold:
                    recommendation = self.generate_recommendation(pinfo['name'], mem_usage_mb)
                    processes_above_threshold.append((pinfo['name'], f"{mem_usage_mb:.2f} MB", recommendation))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Show processes exceeding the threshold or top 5 highest memory usage
        if processes_above_threshold:
            for row in processes_above_threshold:
                self.usage_table.insert("", "end", values=row)
        else:
            # Sort all processes by memory usage in descending order and show the top 5
            all_processes.sort(key=lambda x: x[1], reverse=True)
            for proc in all_processes[:5]:
                recommendation = self.generate_recommendation(proc[0], proc[1])
                self.usage_table.insert("", "end", values=(proc[0], f"{proc[1]:.2f} MB", recommendation))

        # Reapply sorting if necessary
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
        """Force a refresh of the process cache in a separate thread."""
        def worker():
            try:
                self.process_cache = list(psutil.process_iter(['pid', 'name', 'memory_info', 'exe']))
                self.last_cache_update = time()
            except Exception as e:
                print(f"Error refreshing process cache: {e}")

        Thread(target=worker, daemon=True).start()


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
        """Update the flagged applications table with highly suspicious processes."""
        self.flagged_table.delete(*self.flagged_table.get_children())

        # Define thresholds for suspicious behavior
        high_memory_threshold = 1500  # MB
        high_cpu_threshold = 90  # %
        excessive_child_processes = 20
        idle_resource_threshold = 500  # MB (idle process using >500MB)

        # List of known suspicious executables or behaviors
        suspicious_names = {"cryptominer.exe", "malware.exe", "suspicious_app.exe"}
        flagged_processes = []

        for proc in self.get_cached_processes():
            try:
                pinfo = proc.info
                if 'memory_info' not in pinfo or 'pid' not in pinfo:
                    continue

                process = psutil.Process(pinfo['pid'])
                mem_usage_mb = process.memory_info().rss / (1024 * 1024)  # Convert to MB
                cpu_percent = process.cpu_percent(interval=0.0)  # Non-blocking
                thread_count = process.num_threads()
                child_count = len(process.children())
                process_status = process.status()
                exe_path = process.exe()

                # Known suspicious executables
                if process.name().lower() in suspicious_names:
                    flagged_processes.append((process.name(), f"{mem_usage_mb:.2f} MB", "Known Suspicious Application"))

                # Memory leak detection (High memory, low CPU)
                elif mem_usage_mb > high_memory_threshold and cpu_percent < 5:
                    flagged_processes.append((process.name(), f"{mem_usage_mb:.2f} MB", "Potential Memory Leak"))

                # High CPU usage
                elif cpu_percent > high_cpu_threshold:
                    flagged_processes.append((process.name(), f"{mem_usage_mb:.2f} MB", "High CPU Usage"))

                # Excessive child processes
                elif child_count > excessive_child_processes:
                    flagged_processes.append((process.name(), f"{mem_usage_mb:.2f} MB", "Excessive Child Processes"))

                # Idle process using high resources
                elif process_status == "idle" and mem_usage_mb > idle_resource_threshold:
                    flagged_processes.append((process.name(), f"{mem_usage_mb:.2f} MB", "Idle Process Using High Resources"))

                # Suspicious file paths
                elif "system32" not in exe_path.lower() and process.name().lower() in {"svchost.exe", "explorer.exe"}:
                    flagged_processes.append((process.name(), f"{mem_usage_mb:.2f} MB", "Suspicious File Path"))

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue  # Ignore inaccessible processes

        # Populate the flagged table
        for process in flagged_processes:
            self.flagged_table.insert("", "end", values=process)

        # Schedule the next update
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
