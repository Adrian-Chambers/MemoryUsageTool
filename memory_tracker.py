import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from ttkthemes import ThemedTk
import psutil
from plyer import notification
from time import time
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

class MemoryTrackerApp:
    def __init__(self, root):
        """Initialize the Memory Tracker App."""
        self.root = root
        self.root.title("Memory Tracker")
        self.root.geometry("900x1000")

        # Global Configurations
        total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
        self.usage_analyzer_threshold = max(200, total_memory_mb * 0.02)  # Default: 2% of total memory or 200 MB
        self.flagged_applications_threshold = max(1500, total_memory_mb * 0.15)  # Default: 15% of total memory or 1500 MB
        self.process_cache = []
        self.last_cache_update = 0
        self.cache_duration = 15  # Refresh every 15 seconds
        self.current_sort_column = None
        self.current_sort_reverse = False
        self.selected_process_info = None
        self.executor = ThreadPoolExecutor(max_workers=4)  # Thread pool for background tasks
        self.highest_memory_notifications = tk.BooleanVar(value=False)  # Default: Notifications are off
        self.flagged_memory_notifications = tk.BooleanVar(value=True)  # Default: Enabled

        # Main Frame
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Setup GUI Sections
        self.setup_title()  # Title
        self.setup_efficiency_section()  # Efficiency Bar
        self.setup_highest_memory_applications()  # Includes Usage Analyzer Threshold
        self.setup_flagged_applications()  # Includes Flagged Applications Threshold
        self.setup_footer()  # Footer
        self.setup_context_menus()  # Setup context menus for both tables

        # Initialize Process Cache and Populate Tables
        self.initialize_process_data()

        # Start background updates
        self.schedule_background_updates()
        self.update_efficiency_bar()

    def initialize_process_data(self):
        """Refresh the process cache and populate the tables."""
        self.refresh_process_cache()
        self.update_usage_table()
        self.update_flagged_table()

    def refresh_process_cache(self):
        """Fetch and cache process data, excluding system-critical processes."""
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
            self.process_cache = [
                proc for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'exe'])
                if not is_system_critical(proc)
            ]
            self.last_cache_update = time()
            print(f"Process cache updated: {len(self.process_cache)} processes found (excluding system-critical).")  # Debug
        except Exception as e:
            print(f"Error refreshing process cache: {e}")


    # --- GUI Setup Methods ---
    def setup_title(self):
        """Setup the title section."""
        title_label = ttk.Label(self.main_frame, text="Memory Tracker Tool", font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, pady=10)

    def setup_efficiency_section(self):
        """Setup the overall efficiency section."""
        self.score_frame = ttk.LabelFrame(self.main_frame, text="Overall Efficiency", padding=10)
        self.score_frame.grid(row=1, column=0, sticky="ew", pady=15)

        # Configure the frame to center all contents
        self.score_frame.grid_columnconfigure(0, weight=1)

        # Efficiency bar
        self.efficiency_bar = ttk.Progressbar(self.score_frame, orient="horizontal", length=300, mode="determinate")
        self.efficiency_bar.grid(row=0, column=0, pady=5, padx=10, sticky="ew")

        # Efficiency score label and icon in a nested frame
        efficiency_label_frame = ttk.Frame(self.score_frame)
        efficiency_label_frame.grid(row=1, column=0, pady=(5, 0), sticky="ew")
        efficiency_label_frame.grid_columnconfigure(0, weight=1)  # Center the content

        # Add text and icon to the nested frame
        text_and_icon_frame = ttk.Frame(efficiency_label_frame)
        text_and_icon_frame.grid(row=0, column=0)  # Center the text and icon horizontally
        text_and_icon_frame.grid_columnconfigure(0, weight=1)

        self.efficiency_label = ttk.Label(text_and_icon_frame, text="Efficiency Score: Calculating...", font=("Arial", 12), anchor="center")
        self.efficiency_label.grid(row=0, column=0, padx=(0, 5))

        # Add info icon next to the Efficiency Score label
        info_icon = tk.Canvas(text_and_icon_frame, width=16, height=16, highlightthickness=0, bg=self.root.cget("background"))
        info_icon.grid(row=0, column=1)  # Place the icon next to the text
        self.draw_info_icon(info_icon)  # Draw the 'i' icon

        # Add tooltip to the icon
        self.bind_tooltip(info_icon, "Efficiency Score measures the percentage of free memory relative to total system memory.\n"
                                    "Green: >60% free memory\n"
                                    "Orange: 30%-60% free memory\n"
                                    "Red: <30% free memory")

        # Status label
        self.efficiency_status = ttk.Label(self.score_frame, text="Status: Calculating...", font=("Arial", 12), anchor="center", foreground="green")
        self.efficiency_status.grid(row=2, column=0, pady=(5, 5), sticky="ew")  # Center the status label horizontally



    def update_percentage_from_mb(self, event=None):
        """Update percentage fields based on MB input."""
        try:
            total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)

            # Update Usage Analyzer Threshold Percentage
            if self.usage_threshold_mb.get():
                usage_mb = float(self.usage_threshold_mb.get())
                usage_percent = (usage_mb / total_memory_mb) * 100
                self.usage_threshold_percent.delete(0, tk.END)
                self.usage_threshold_percent.insert(0, f"{usage_percent:.2f}")

            # Update Flagged Applications Threshold Percentage
            if self.flagged_threshold_mb.get():
                flagged_mb = float(self.flagged_threshold_mb.get())
                flagged_percent = (flagged_mb / total_memory_mb) * 100
                self.flagged_threshold_percent.delete(0, tk.END)
                self.flagged_threshold_percent.insert(0, f"{flagged_percent:.2f}")

        except ValueError:
            pass  # Ignore invalid inputs


    def update_mb_from_percentage(self, event=None):
        """Update MB fields based on percentage input."""
        try:
            total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)

            # Update Usage Analyzer Threshold MB
            if self.usage_threshold_percent.get():
                usage_percent = float(self.usage_threshold_percent.get())
                usage_mb = (usage_percent / 100) * total_memory_mb
                self.usage_threshold_mb.delete(0, tk.END)
                self.usage_threshold_mb.insert(0, f"{usage_mb:.2f}")

            # Update Flagged Applications Threshold MB
            if self.flagged_threshold_percent.get():
                flagged_percent = float(self.flagged_threshold_percent.get())
                flagged_mb = (flagged_percent / 100) * total_memory_mb
                self.flagged_threshold_mb.delete(0, tk.END)
                self.flagged_threshold_mb.insert(0, f"{flagged_mb:.2f}")

        except ValueError:
            pass  # Ignore invalid inputs
        

    def setup_highest_memory_applications(self):
        """Setup the Highest Memory Applications table with threshold inputs."""
        self.usage_frame = ttk.LabelFrame(self.main_frame, text="Highest Memory Applications", padding=10)
        self.usage_frame.grid(row=3, column=0, sticky="nsew", pady=15)
        self.main_frame.grid_rowconfigure(3, weight=1)

        # Add description label
        description_label = ttk.Label(
            self.usage_frame,
            text="Displays applications consuming significant memory. Adjust the threshold to control which applications are shown.",
            font=("Arial", 10),
            justify="left",
            anchor="w" 
        )
        description_label.pack(pady=(0, 10), padx=5, fill="x") 

        # Threshold inputs for Highest Memory Applications
        threshold_frame = ttk.Frame(self.usage_frame)
        threshold_frame.pack(fill="x", padx=5, pady=(0, 10))

        ttk.Label(threshold_frame, text="Threshold (MB):", font=("Arial", 10)).grid(
            row=0, column=0, sticky="w", padx=(0, 5)
        )
        self.usage_threshold_mb = ttk.Entry(threshold_frame, font=("Arial", 10), width=10)
        self.usage_threshold_mb.grid(row=0, column=1, sticky="w", padx=(0, 10))
        self.usage_threshold_mb.insert(0, f"{self.usage_analyzer_threshold:.2f}")

        ttk.Label(threshold_frame, text="or %:", font=("Arial", 10)).grid(
            row=0, column=2, sticky="w", padx=(5, 5)
        )
        self.usage_threshold_percent = ttk.Entry(threshold_frame, font=("Arial", 10), width=10)
        self.usage_threshold_percent.grid(row=0, column=3, sticky="w")
        self.usage_threshold_percent.insert(0, f"{(self.usage_analyzer_threshold / (psutil.virtual_memory().total / (1024 * 1024))) * 100:.2f}")

        # Reset to Default Button with Info Icon
        reset_frame = ttk.Frame(threshold_frame)
        reset_frame.grid(row=0, column=4, padx=(10, 0))

        reset_button = ttk.Button(reset_frame, text="Reset to Default", command=self.reset_usage_threshold)
        reset_button.pack(side="left")

        # Add info icon next to the button
        info_icon = tk.Canvas(reset_frame, width=16, height=16, highlightthickness=0, bg=self.root.cget("background"))
        info_icon.pack(side="left", padx=(5, 0))
        self.draw_info_icon(info_icon)  # Draw the icon
        self.bind_tooltip(info_icon, "Defaults are calculated as 2% of total memory or 200 MB, whichever is higher, to ensure compatibility across different systems.")

        # Bind the syncing function to both fields
        self.usage_threshold_mb.bind("<KeyRelease>", lambda e: self.sync_threshold_fields(
            self.usage_threshold_mb, self.usage_threshold_percent, self.update_usage_table, source="mb"))
        self.usage_threshold_percent.bind("<KeyRelease>", lambda e: self.sync_threshold_fields(
            self.usage_threshold_mb, self.usage_threshold_percent, self.update_usage_table, source="percent"))

        # Add notification toggle
        notif_checkbox_frame = ttk.Frame(self.usage_frame)
        notif_checkbox_frame.pack(fill="x", padx=5, pady=(0, 10))  # Adjusted padding to match "Suspicious Applications"

        notifications_checkbox = ttk.Checkbutton(
            notif_checkbox_frame,
            text="Enable Notifications",
            variable=self.highest_memory_notifications
        )
        notifications_checkbox.pack(anchor="w", padx=(0, 10))  # Align to the left and add padding to match the other section

        # Table for applications
        scroll_y = ttk.Scrollbar(self.usage_frame, orient="vertical")
        scroll_x = ttk.Scrollbar(self.usage_frame, orient="horizontal")
        columns = ("Application", "Usage", "Recommendation")

        self.usage_table = ttk.Treeview(
            self.usage_frame, columns=columns, show="headings", height=15,
            yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set
        )
        scroll_y.config(command=self.usage_table.yview)
        scroll_x.config(command=self.usage_table.xview)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.usage_table.pack(fill="both", expand=True, padx=5)
        self.usage_table.bind("<Button-3>", self.show_usage_context_menu)

        self.configure_table_columns(self.usage_table, {
            "Application": {"width": 150, "anchor": "center"},
            "Usage": {"width": 100, "anchor": "center"},
            "Recommendation": {"width": 500, "anchor": "w"},
        })



    def show_usage_context_menu(self, event):
        """Show the context menu for the Usage Analyzer table."""
        try:
            # Identify the row under the cursor
            row_id = self.usage_table.identify_row(event.y)
            if row_id:
                self.usage_table.selection_set(row_id)  # Select the row
                selected_item = self.usage_table.item(row_id, "values")
                if selected_item:
                    app_name = selected_item[0]  # Application name from the table
                    self.selected_process_info = self.get_process_info_by_name(app_name)
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
            row_id = self.flagged_table.identify_row(event.y)
            if row_id:
                self.flagged_table.selection_set(row_id)  # Select the row
                selected_item = self.flagged_table.item(row_id, "values")
                if selected_item:
                    app_name = selected_item[0]  # Application name from the table
                    self.selected_process_info = self.get_process_info_by_name(app_name)
                    self.flagged_context_menu.post(event.x_root, event.y_root)
                else:
                    self.selected_process_info = None
            else:
                self.selected_process_info = None
        except Exception as e:
            print(f"Error showing flagged context menu: {e}")




    def get_process_info_by_name(self, app_name):
        """Retrieve process information by process name."""
        for proc in self.process_cache:
            try:
                if proc.info['name'] == app_name:  # Match by process name
                    return proc.info  # Return the full process info dictionary
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return None  # Return None if no matching process is found

    def update_usage_threshold(self):
        """Update the Usage Analyzer threshold based on the input fields and refresh the table."""
        try:
            total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)

            if self.usage_threshold_mb.get():
                self.usage_analyzer_threshold = float(self.usage_threshold_mb.get())
                self.usage_threshold_percent.delete(0, tk.END)
                self.usage_threshold_percent.insert(0, f"{(self.usage_analyzer_threshold / total_memory_mb) * 100:.2f}")

            elif self.usage_threshold_percent.get():
                percent_value = float(self.usage_threshold_percent.get())
                self.usage_analyzer_threshold = (percent_value / 100) * total_memory_mb
                self.usage_threshold_mb.delete(0, tk.END)
                self.usage_threshold_mb.insert(0, f"{self.usage_analyzer_threshold:.2f}")

            self.update_usage_table()
        except ValueError:
            messagebox.showerror("Error", "Invalid input in Usage Analyzer threshold fields. Please enter valid numbers.")


    def update_flagged_threshold(self):
        """Update the Flagged Applications threshold based on the input fields and refresh the table."""
        try:
            total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)

            if self.flagged_threshold_mb.get():
                self.flagged_applications_threshold = float(self.flagged_threshold_mb.get())
                self.flagged_threshold_percent.delete(0, tk.END)
                self.flagged_threshold_percent.insert(0, f"{(self.flagged_applications_threshold / total_memory_mb) * 100:.2f}")

            elif self.flagged_threshold_percent.get():
                percent_value = float(self.flagged_threshold_percent.get())
                self.flagged_applications_threshold = (percent_value / 100) * total_memory_mb
                self.flagged_threshold_mb.delete(0, tk.END)
                self.flagged_threshold_mb.insert(0, f"{self.flagged_applications_threshold:.2f}")

            self.update_flagged_table()
        except ValueError:
            messagebox.showerror("Error", "Invalid input in Flagged Applications threshold fields. Please enter valid numbers.")

    def setup_flagged_applications(self):
        """Setup the Suspicious Applications table with threshold inputs."""
        self.flagged_frame = ttk.LabelFrame(self.main_frame, text="Suspicious Applications", padding=10)
        self.flagged_frame.grid(row=5, column=0, sticky="nsew", pady=15)
        self.main_frame.grid_rowconfigure(5, weight=1)

        # Add description label
        description_label = ttk.Label(
            self.flagged_frame,
            text="Lists applications with unusually high memory usage. Adjust the threshold to detect potential memory leaks or harmful programs.",
            font=("Arial", 10),
            justify="left",  # Align text to the left
            anchor="w"      # Align within the container to the left
        )
        description_label.pack(pady=(0, 10), padx=5, fill="x")  # Added fill to ensure it spans the frame

        # Threshold inputs for Suspicious Applications
        threshold_frame = ttk.Frame(self.flagged_frame)
        threshold_frame.pack(fill="x", padx=5, pady=(0, 10))

        ttk.Label(threshold_frame, text="Threshold (MB):", font=("Arial", 10)).grid(
            row=0, column=0, sticky="w", padx=(0, 5)
        )
        self.flagged_threshold_mb = ttk.Entry(threshold_frame, font=("Arial", 10), width=10)
        self.flagged_threshold_mb.grid(row=0, column=1, sticky="w", padx=(0, 10))
        self.flagged_threshold_mb.insert(0, f"{self.flagged_applications_threshold:.2f}")

        ttk.Label(threshold_frame, text="or %:", font=("Arial", 10)).grid(
            row=0, column=2, sticky="w", padx=(5, 5)
        )
        self.flagged_threshold_percent = ttk.Entry(threshold_frame, font=("Arial", 10), width=10)
        self.flagged_threshold_percent.grid(row=0, column=3, sticky="w")
        self.flagged_threshold_percent.insert(0, f"{(self.flagged_applications_threshold / (psutil.virtual_memory().total / (1024 * 1024))) * 100:.2f}")

        # Reset to Default Button with Info Icon
        reset_frame = ttk.Frame(threshold_frame)
        reset_frame.grid(row=0, column=4, padx=(10, 0))

        reset_button = ttk.Button(reset_frame, text="Reset to Default", command=self.reset_flagged_threshold)
        reset_button.pack(side="left")

        # Add info icon next to the button
        info_icon = tk.Canvas(reset_frame, width=16, height=16, highlightthickness=0, bg=self.root.cget("background"))
        info_icon.pack(side="left", padx=(5, 0))
        self.draw_info_icon(info_icon)  # Draw the icon
        self.bind_tooltip(info_icon, "Defaults are calculated as 15% of total memory or 1500 MB, whichever is higher, to detect unusually high memory usage.")

        # Bind the syncing function to both fields
        self.flagged_threshold_mb.bind("<KeyRelease>", lambda e: self.sync_threshold_fields(
            self.flagged_threshold_mb, self.flagged_threshold_percent, self.update_flagged_table, source="mb"))
        self.flagged_threshold_percent.bind("<KeyRelease>", lambda e: self.sync_threshold_fields(
            self.flagged_threshold_mb, self.flagged_threshold_percent, self.update_flagged_table, source="percent"))

        # Notification Setting
        notif_checkbox = ttk.Checkbutton(
            threshold_frame,
            text="Enable Notifications",
            variable=self.flagged_memory_notifications
        )
        notif_checkbox.grid(row=2, column=0, columnspan=5, sticky="w", padx=(0, 10), pady=(5, 0))

        # Table for flagged applications
        scroll_y = ttk.Scrollbar(self.flagged_frame, orient="vertical")
        scroll_x = ttk.Scrollbar(self.flagged_frame, orient="horizontal")
        columns = ("Application", "Usage", "Reason")

        self.flagged_table = ttk.Treeview(
            self.flagged_frame, columns=columns, show="headings", height=12,
            yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set
        )
        scroll_y.config(command=self.flagged_table.yview)
        scroll_x.config(command=self.flagged_table.xview)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.flagged_table.pack(fill="both", expand=True, padx=5)
        self.flagged_table.bind("<Button-3>", self.show_flagged_context_menu)

        self.configure_table_columns(self.flagged_table, {
            "Application": {"width": 150, "anchor": "center"},
            "Usage": {"width": 100, "anchor": "center"},
            "Reason": {"width": 500, "anchor": "w"},
        })



    def draw_info_icon(self, canvas):
        """Draw a simple 'i' information icon on the canvas."""
        canvas.create_oval(2, 2, 14, 14, fill="blue", outline="blue")
        canvas.create_text(8, 8, text="i", fill="white", font=("Arial", 10, "bold"))


    def bind_tooltip(self, widget, text):
        """Bind a tooltip to a widget."""
        tooltip = tk.Toplevel(self.root, bg="white", padx=5, pady=3)
        tooltip.wm_overrideredirect(True)  # Remove window decorations
        tooltip.withdraw()  # Hide by default
        tooltip_label = tk.Label(tooltip, text=text, font=("Arial", 9), bg="white", justify="left")
        tooltip_label.pack()

        def show_tooltip(event):
            x, y, _, _ = widget.bbox("all")  # Get widget's bounding box
            x += widget.winfo_rootx() + 20  # Adjust tooltip position
            y += widget.winfo_rooty() + 10
            tooltip.geometry(f"+{x}+{y}")
            tooltip.deiconify()

        def hide_tooltip(event):
            tooltip.withdraw()

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)


    
    def reset_usage_threshold(self):
        """Reset the Usage Analyzer threshold to its default value."""
        total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
        self.usage_analyzer_threshold = max(200, total_memory_mb * 0.02)
        self.usage_threshold_mb.delete(0, tk.END)
        self.usage_threshold_mb.insert(0, f"{self.usage_analyzer_threshold:.2f}")
        self.usage_threshold_percent.delete(0, tk.END)
        self.usage_threshold_percent.insert(0, f"{(self.usage_analyzer_threshold / total_memory_mb) * 100:.2f}")
        self.update_usage_table()


    def reset_flagged_threshold(self):
        """Reset the Flagged Applications threshold to its default value."""
        total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
        self.flagged_applications_threshold = max(1500, total_memory_mb * 0.15)
        self.flagged_threshold_mb.delete(0, tk.END)
        self.flagged_threshold_mb.insert(0, f"{self.flagged_applications_threshold:.2f}")
        self.flagged_threshold_percent.delete(0, tk.END)
        self.flagged_threshold_percent.insert(0, f"{(self.flagged_applications_threshold / total_memory_mb) * 100:.2f}")
        self.update_flagged_table()


    def show_flagged_context_menu(self, event):
        """Show the context menu for the flagged applications table."""
        try:
            row_id = self.flagged_table.identify_row(event.y)
            if row_id:
                self.flagged_table.selection_set(row_id)
                selected_item = self.flagged_table.item(row_id, "values")
                if selected_item:
                    app_name = selected_item[0]  # Application name from the table
                    self.selected_process_info = self.get_process_info_by_name(app_name)
                    self.flagged_context_menu.post(event.x_root, event.y_root)
                else:
                    self.selected_process_info = None
            else:
                self.selected_process_info = None
        except Exception as e:
            print(f"Error showing context menu: {e}")

    def setup_context_menus(self):
        """Setup context menus for both tables."""
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


    def kill_selected_process(self):
        """Kill all processes with the same name as the selected process."""
        try:
            if self.selected_process_info:
                app_name = self.selected_process_info.get("name")  # Get the name of the process
                if not app_name:
                    messagebox.showerror("Error", "No process name found.")
                    return

                # Find all processes with the same name
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
                self.update_flagged_table()
            else:
                messagebox.showerror("Error", "No process selected.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not terminate process: {e}")


    def open_file_location(self):
        """Open the file location of the selected process."""
        try:
            if self.selected_process_info:
                exe_path = self.selected_process_info.get("exe", None)
                if exe_path and os.path.exists(exe_path):
                    os.startfile(os.path.dirname(exe_path))  # Open the folder containing the executable
                else:
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



    def setup_footer(self):
        """Setup the footer section."""
        footer_label = ttk.Label(
            self.main_frame,
            text="Memory Tracker Tool - Version 1.0",
            font=("Arial", 10, "italic"),
            anchor="center"
        )
        footer_label.grid(row=7, column=0, pady=10)  # Moved to row 7



    # --- Helper Methods ---
    def configure_table_columns(self, table, columns_config):
        """Configure columns for a Treeview table."""
        for col, config in columns_config.items():
            table.heading(col, text=col, command=lambda _col=col: self.sort_treeview(table, _col, False))
            table.column(col, **config, stretch=tk.YES)  # Allow resizing of columns


    def schedule_background_updates(self):
        """Schedule background updates for process data."""
        self.executor.submit(self.refresh_process_cache)
        self.root.after(10000, self.schedule_background_updates)

    def update_efficiency_bar(self):
        """Update the efficiency bar and status."""
        mem = psutil.virtual_memory()
        free_mem_percent = (mem.available / mem.total) * 100
        self.efficiency_bar['value'] = free_mem_percent
        self.efficiency_label.config(text=f"Efficiency Score: {free_mem_percent:.2f}% Free")
        status_color = "green" if free_mem_percent > 60 else "orange" if free_mem_percent > 30 else "red"
        self.efficiency_status.config(text=f"Status: {'Good' if status_color == 'green' else 'Fair' if status_color == 'orange' else 'Poor'}", foreground=status_color)
        self.root.after(2000, self.update_efficiency_bar)

    def update_usage_table(self):
        """Update the Usage Analyzer table with processes exceeding the usage threshold."""
        try:
            # Refresh the process cache to ensure up-to-date data
            self.refresh_process_cache()
            
            # Aggregate memory usage by process name
            aggregated_memory = self.aggregate_memory_by_name(self.process_cache)

            # Filter processes that exceed the usage threshold
            total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
            self.usage_analyzer_threshold = float(self.usage_threshold_mb.get() or self.usage_analyzer_threshold)

            notified_processes = set()  # Track processes already notified
            processes = []

            for name, memory in aggregated_memory.items():
                if memory >= self.usage_analyzer_threshold:
                    # Generate recommendations
                    recommendation = self.generate_detailed_recommendation(name, memory, total_memory_mb)
                    processes.append((name, memory, recommendation))

                    # Trigger notifications if enabled
                    if self.highest_memory_notifications.get() and name not in notified_processes:
                        notification.notify(
                            title="High Memory Usage Detected",
                            message=f"{name} is using {memory:.2f} MB of memory.\n{recommendation}",
                            timeout=5,
                        )
                        notified_processes.add(name)

            # Populate the table with the filtered processes
            self.populate_usage_table(processes)
        except ValueError as e:
            print(f"Error in update_usage_table: {e}")
        except Exception as e:
            print(f"Unexpected error in update_usage_table: {e}")




    def populate_usage_table(self, processes):
        """Efficiently update the usage table."""
        print(f"Populating table with {len(processes)} processes.")
        current_items = {self.usage_table.item(child)['values'][0]: child for child in self.usage_table.get_children()}
        new_items = {name: (name, f"{mem_usage:.2f} MB", recommendation) for name, mem_usage, recommendation in processes}

        for name, values in new_items.items():
            if name in current_items:
                self.usage_table.item(current_items[name], values=values)
            else:
                self.usage_table.insert("", "end", values=values)

        for name in current_items.keys() - new_items.keys():
            self.usage_table.delete(current_items[name])



    def update_flagged_table(self):
        """Update the Flagged Applications table with processes exceeding the flagged threshold."""
        try:
            # Refresh the process cache to ensure up-to-date data
            self.refresh_process_cache()
            
            # Aggregate memory usage by process name
            aggregated_memory = self.aggregate_memory_by_name(self.process_cache)

            # Filter processes that exceed the flagged threshold
            total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
            self.flagged_applications_threshold = float(self.flagged_threshold_mb.get() or self.flagged_applications_threshold)

            notified_processes = set()  # Track processes already notified
            flagged_processes = []

            for name, memory in aggregated_memory.items():
                if memory >= self.flagged_applications_threshold:
                    flagged_processes.append((name, memory, "High Memory Usage"))
                    recommendation = self.generate_detailed_recommendation(name, memory, total_memory_mb)

                    # Trigger notifications if enabled
                    if self.flagged_memory_notifications.get() and name not in notified_processes:
                        notification.notify(
                            title="Suspicious Memory Usage Detected",
                            message=f"{name} is using {memory:.2f} MB of memory.\n{recommendation}",
                            timeout=5,
                        )
                        notified_processes.add(name)

            # Populate the table with the flagged processes
            self.populate_flagged_table(flagged_processes)
        except ValueError as e:
            print(f"Error in update_flagged_table: {e}")
        except Exception as e:
            print(f"Unexpected error in update_flagged_table: {e}")


    def populate_flagged_table(self, flagged_processes):
        """Efficiently update the flagged applications table."""
        print(f"Populating flagged table with {len(flagged_processes)} processes.")  # Debug
        current_items = {self.flagged_table.item(child)['values'][0]: child for child in self.flagged_table.get_children()}
        new_items = {name: (name, f"{mem_usage:.2f} MB", reason) for name, mem_usage, reason in flagged_processes}

        # Update existing rows and add new ones
        for name, values in new_items.items():
            if name in current_items:
                self.flagged_table.item(current_items[name], values=values)
            else:
                self.flagged_table.insert("", "end", values=values)

        # Remove rows that are no longer in the list
        for name in current_items.keys() - new_items.keys():
            self.flagged_table.delete(current_items[name])


    def generate_recommendation(self, app_name, memory_usage):
        """Generate a recommendation based on the application name and memory usage."""
        app_name_lower = app_name.lower()

        # Browser-related recommendations
        if any(keyword in app_name_lower for keyword in ["chrome", "firefox", "safari", "edge", "opera", "brave"]):
            if memory_usage > self.usage_analyzer_threshold:  # Use the threshold to determine the recommendation
                return "Consider closing unused tabs or restarting the browser."
            else:
                return "Close unnecessary tabs to reduce memory usage."

        # Development Tools
        elif any(keyword in app_name_lower for keyword in ["code", "pycharm", "intellij", "eclipse", "visual studio"]):
            return "Close unused projects or restart the IDE to free up resources."

        # Streaming Applications
        elif any(keyword in app_name_lower for keyword in ["spotify", "vlc", "netflix", "youtube", "prime video"]):
            return "Pause the application if not actively using it."

        # Communication Apps
        elif any(keyword in app_name_lower for keyword in ["zoom", "teams", "slack", "discord", "skype"]):
            return "Close unused calls or chats to save resources."

        # Gaming Applications
        elif any(keyword in app_name_lower for keyword in ["game", "steam", "epic", "blizzard", "riot"]):
            return "Close background apps to improve game performance."

        # File Sharing and Cloud Services
        elif any(keyword in app_name_lower for keyword in ["onedrive", "dropbox", "google drive", "icloud"]):
            return "Pause syncing to free up memory."

        # Office Applications
        elif any(keyword in app_name_lower for keyword in ["word", "excel", "powerpoint", "outlook", "office"]):
            return "Close unused documents or spreadsheets."

        # Video Editing or Graphic Tools
        elif any(keyword in app_name_lower for keyword in ["premiere", "photoshop", "after effects", "final cut", "lightroom"]):
            return "Close unused projects or export completed work to free up resources."

        # High Memory Usage
        if memory_usage > self.usage_analyzer_threshold:
            return "Restart the application to release unused memory."

        # Default Recommendation
        return "Consider closing the application if not actively using it."

    def aggregate_memory_by_name(self, processes):
        """Aggregate memory usage by process name."""
        aggregated = {}
        for proc in processes:
            try:
                name = proc.info.get('name', 'Unknown')
                memory = proc.info['memory_info'].rss / (1024 * 1024)  # Convert to MB
                aggregated[name] = aggregated.get(name, 0) + memory
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return aggregated

    def generate_detailed_recommendation(self, app_name, memory_mb, total_memory_mb):
        """Generate a detailed recommendation based on memory usage patterns."""
        app_name_lower = app_name.lower()
        memory_percent = (memory_mb / total_memory_mb) * 100  # Calculate memory usage as a percentage of total

        # Base recommendation levels
        if memory_percent > 50:
            base_recommendation = "CRITICAL: Process consuming over 50% of system memory. "
        elif memory_mb > self.flagged_applications_threshold:
            base_recommendation = "WARNING: High memory usage detected. "
        elif memory_mb > self.usage_analyzer_threshold * 3:
            base_recommendation = "High Usage: "
        elif memory_mb > self.usage_analyzer_threshold * 2:
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
            if memory_mb > self.usage_analyzer_threshold * 2:
                recommendation = base_recommendation + "Restart the application to release unused memory."
            else:
                recommendation = base_recommendation + "Consider closing the application if not actively using it."

        return recommendation

    
    def sync_threshold_fields(self, mb_entry, percent_entry, update_table_callback, source="mb"):
        """Synchronize MB and percentage threshold fields with debounce."""
        total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)

        # Cancel any previously scheduled update
        if hasattr(self, "debounce_timer") and self.debounce_timer:
            self.root.after_cancel(self.debounce_timer)

        try:
            if source == "mb" and mb_entry.get():
                mb_value = float(mb_entry.get())
                percent_value = (mb_value / total_memory_mb) * 100
                percent_entry.delete(0, tk.END)
                percent_entry.insert(0, f"{percent_value:.2f}")
            elif source == "percent" and percent_entry.get():
                percent_value = float(percent_entry.get())
                mb_value = (percent_value / 100) * total_memory_mb
                mb_entry.delete(0, tk.END)
                mb_entry.insert(0, f"{mb_value:.2f}")
            
            # Schedule the table update after 500ms
            self.debounce_timer = self.root.after(2000, update_table_callback)
        except ValueError:
            pass  # Ignore invalid inputs


    def sync_usage_thresholds(self, event=None):
        total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
        try:
            if event.widget == self.usage_threshold_mb and self.usage_threshold_mb.get():
                mb_value = float(self.usage_threshold_mb.get())
                percent_value = (mb_value / total_memory_mb) * 100
                self.usage_threshold_percent.delete(0, tk.END)
                self.usage_threshold_percent.insert(0, f"{percent_value:.2f}")
                print(f"Updated usage threshold: {mb_value} MB ({percent_value:.2f}%)")  # Debug
            elif event.widget == self.usage_threshold_percent and self.usage_threshold_percent.get():
                percent_value = float(self.usage_threshold_percent.get())
                mb_value = (percent_value / 100) * total_memory_mb
                self.usage_threshold_mb.delete(0, tk.END)
                self.usage_threshold_mb.insert(0, f"{mb_value:.2f}")
                print(f"Updated usage threshold: {percent_value:.2f}% ({mb_value} MB)")  # Debug
            self.update_usage_table()
        except ValueError:
            pass

    def restore_defaults(self):
        """Restore default thresholds."""
        total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
        self.usage_analyzer_threshold = max(200, total_memory_mb * 0.02)
        self.flagged_applications_threshold = max(1500, total_memory_mb * 0.15)
        self.update_threshold_inputs()  # Update inputs dynamically
        self.update_usage_table()
        self.update_flagged_table()
        print("Thresholds restored to default values.")


    def sort_treeview(self, treeview, col, reverse):
        """Sort the Treeview by a given column."""
        items = [(treeview.set(k, col), k) for k in treeview.get_children('')]
        try:
            items.sort(key=lambda t: float(t[0].replace(' MB', '')), reverse=reverse)
        except ValueError:
            items.sort(reverse=reverse)
        for index, (_, k) in enumerate(items):
            treeview.move(k, '', index)
        treeview.heading(col, command=lambda: self.sort_treeview(treeview, col, not reverse))


# Run the application
if __name__ == "__main__":
    root = ThemedTk(theme="plastik")
    app = MemoryTrackerApp(root)
    root.mainloop()
