import tkinter as tk
from tkinter import ttk
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

        columns = ("Application", "Usage", "Recommendation")
        self.usage_table = ttk.Treeview(self.usage_frame, columns=columns, show="headings", height=8)
        self.usage_table.pack(fill="both", expand=True)

        for col in columns:
            self.usage_table.heading(
                col, text=col,
                command=lambda _col=col: self.sort_treeview(self.usage_table, _col, False)
            )
            self.usage_table.column(col, width=200, anchor="center")
        self.update_usage_table()

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

        for col in flagged_columns:
            self.flagged_table.heading(col, text=col)
            self.flagged_table.column(col, width=200, anchor="center")
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
                self.process_cache = []  # Handle error gracefully
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
                mem_info = pinfo['memory_info']
                mem_usage_mb = mem_info.vms / (1024 * 1024)

                # Only display processes exceeding the memory threshold
                if mem_usage_mb > self.high_memory_threshold:
                    recommendation = self.generate_recommendation(pinfo['name'], mem_usage_mb)
                    self.usage_table.insert("", "end", values=(pinfo['name'], f"{mem_usage_mb:.2f} MB", recommendation))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

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



    def update_flagged_table(self):
        self.flagged_table.delete(*self.flagged_table.get_children())
        for proc in self.get_cached_processes():
            try:
                pinfo = proc.info
                mem_info = pinfo['memory_info']
                mem_usage_mb = mem_info.vms / (1024 * 1024)
                if mem_usage_mb > 1000:  # Flag processes using more than 1000 MB
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
