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
        self.usage_analyzer_threshold = 200  # Default lower threshold (in MB)
        self.flagged_applications_threshold = 1500  # Default higher threshold (in MB)
        self.process_cache = []
        self.last_cache_update = 0
        self.cache_duration = 15  # Refresh every 15 seconds
        self.current_sort_column = None
        self.current_sort_reverse = False
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
        self.setup_threshold_adjustment()
        self.setup_usage_analyzer()
        self.setup_notifications()
        self.setup_flagged_applications()
        self.setup_footer()

        # Start background updates
        self.schedule_background_updates()
        self.update_efficiency_bar()

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

    def setup_threshold_adjustment(self):
        """Setup the threshold adjustment section."""
        self.threshold_frame = ttk.LabelFrame(self.main_frame, text="Threshold Adjustment", padding=10)
        self.threshold_frame.grid(row=2, column=0, sticky="ew", pady=10)

        ttk.Label(self.threshold_frame, text="Usage Analyzer Threshold (MB):", font=("Arial", 12)).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.usage_threshold_input = ttk.Entry(self.threshold_frame, font=("Arial", 12), width=10)
        self.usage_threshold_input.grid(row=0, column=1, sticky="w", padx=10)
        self.usage_threshold_input.insert(0, f"{self.usage_analyzer_threshold:.2f}")

        ttk.Label(self.threshold_frame, text="Flagged Applications Threshold (MB):", font=("Arial", 12)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.flagged_threshold_input = ttk.Entry(self.threshold_frame, font=("Arial", 12), width=10)
        self.flagged_threshold_input.grid(row=1, column=1, sticky="w", padx=10)
        self.flagged_threshold_input.insert(0, f"{self.flagged_applications_threshold:.2f}")

        self.update_threshold_button = ttk.Button(self.threshold_frame, text="Update Thresholds", command=self.update_thresholds)
        self.update_threshold_button.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=5)

    def update_thresholds(self):
        """Update the memory thresholds for usage analyzer and flagged applications."""
        try:
            new_usage_threshold = float(self.usage_threshold_input.get())
            new_flagged_threshold = float(self.flagged_threshold_input.get())
            if new_usage_threshold <= 0 or new_flagged_threshold <= 0:
                raise ValueError("Thresholds must be greater than 0.")
            self.usage_analyzer_threshold = new_usage_threshold
            self.flagged_applications_threshold = new_flagged_threshold
            print(f"Updated Usage Analyzer Threshold: {self.usage_analyzer_threshold:.2f} MB")
            print(f"Updated Flagged Applications Threshold: {self.flagged_applications_threshold:.2f} MB")
            self.update_usage_table()
            self.update_flagged_table()
        except ValueError:
            messagebox.showerror("Error", "Invalid threshold values. Please enter positive numbers.")

    def setup_usage_analyzer(self):
        """Setup the Usage Analyzer table."""
        self.usage_frame = ttk.LabelFrame(self.main_frame, text="Usage Analyzer", padding=10)
        self.usage_frame.grid(row=3, column=0, sticky="nsew", pady=10)
        self.main_frame.grid_rowconfigure(3, weight=1)

        scroll_y = ttk.Scrollbar(self.usage_frame, orient="vertical")
        columns = ("Application", "Usage", "Recommendation")
        
        # Increased the height of the table
        self.usage_table = ttk.Treeview(self.usage_frame, columns=columns, show="headings", height=12, yscrollcommand=scroll_y.set)
        scroll_y.config(command=self.usage_table.yview)
        scroll_y.pack(side="right", fill="y")
        self.usage_table.pack(fill="both", expand=True)

        self.configure_table_columns(self.usage_table, {
            "Application": {"width": 200, "anchor": "center"},
            "Usage": {"width": 100, "anchor": "center"},
            "Recommendation": {"width": 400, "anchor": "w"},
        })

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

        scroll_y = ttk.Scrollbar(self.flagged_frame, orient="vertical")
        columns = ("Application", "Usage", "Reason")

        # Increased the height of the table
        self.flagged_table = ttk.Treeview(self.flagged_frame, columns=columns, show="headings", height=10, yscrollcommand=scroll_y.set)
        scroll_y.config(command=self.flagged_table.yview)
        scroll_y.pack(side="right", fill="y")
        self.flagged_table.pack(fill="both", expand=True)

        self.configure_table_columns(self.flagged_table, {
            "Application": {"width": 200, "anchor": "center"},
            "Usage": {"width": 100, "anchor": "center"},
            "Reason": {"width": 400, "anchor": "w"},
        })


    def setup_footer(self):
        """Setup the footer section."""
        ttk.Label(self.main_frame, text="Memory Tracker Tool - Version 1.0", font=("Arial", 10, "italic")).grid(row=6, column=0, pady=10)

    # --- Helper Methods ---
    def configure_table_columns(self, table, columns_config):
        """Configure columns for a Treeview table."""
        for col, config in columns_config.items():
            table.heading(col, text=col, command=lambda _col=col: self.sort_treeview(table, _col, False))
            table.column(col, **config)

    def schedule_background_updates(self):
        """Schedule background updates for process data."""
        self.executor.submit(self.refresh_process_cache)
        self.root.after(10000, self.schedule_background_updates)

    def refresh_process_cache(self):
        """Fetch and cache process data."""
        try:
            self.process_cache = list(psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'exe']))
            self.last_cache_update = time()
        except Exception as e:
            print(f"Error refreshing process cache: {e}")

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
        """Update the usage analyzer table."""
        processes = [
            (p.info['name'], p.info['memory_info'].rss / (1024 * 1024), self.generate_recommendation(p.info['name'], p.info['memory_info'].rss / (1024 * 1024)))
            for p in self.process_cache
            if p.info.get('memory_info') and p.info['memory_info'].rss / (1024 * 1024) > self.usage_analyzer_threshold
        ]
        self.populate_usage_table(processes)

    def populate_usage_table(self, processes):
        """Efficiently update the usage table."""
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
        """Update the flagged applications table."""
        flagged_processes = []
        for proc in self.process_cache:
            try:
                mem_usage_mb = proc.info['memory_info'].rss / (1024 * 1024)
                if mem_usage_mb > self.flagged_applications_threshold:
                    flagged_processes.append((proc.info['name'], f"{mem_usage_mb:.2f} MB", "High Memory Usage"))
            except Exception:
                continue
        self.populate_flagged_table(flagged_processes)

    def populate_flagged_table(self, flagged_processes):
        """Populate the flagged table."""
        self.flagged_table.delete(*self.flagged_table.get_children())
        for process in flagged_processes:
            self.flagged_table.insert("", "end", values=process)

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
