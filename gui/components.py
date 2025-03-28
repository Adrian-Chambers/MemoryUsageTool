"""
GUI components for the Memory Tracker application.
Contains classes and functions for building and updating the application interface.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from utils import memory_utils, process_utils, notification_utils
from gui.tooltips import draw_info_icon, bind_tooltip


def configure_table_columns(table, columns_config):
    """
    Configure columns for a Treeview table.
    
    Args:
        table: Treeview widget
        columns_config: Dictionary with column configuration
    """
    for col, config in columns_config.items():
        table.heading(col, text=col, command=lambda _col=col: sort_treeview(table, _col, False))
        table.column(col, **config, stretch=tk.YES)  # Allow resizing of columns


def sort_treeview(treeview, col, reverse):
    """
    Sort the Treeview by a given column.
    
    Args:
        treeview: Treeview widget
        col: Column to sort by
        reverse: Sort in reverse order if True
    """
    items = [(treeview.set(k, col), k) for k in treeview.get_children('')]
    try:
        # Try to convert to float for numeric sorting (e.g., "123.45 MB")
        items.sort(key=lambda t: float(t[0].replace(' MB', '')), reverse=reverse)
    except ValueError:
        # Fall back to string sorting for non-numeric values
        items.sort(reverse=reverse)
    
    # Reorder items in the treeview
    for index, (_, k) in enumerate(items):
        treeview.move(k, '', index)
    
    # Configure heading to sort in the opposite direction next time
    treeview.heading(col, command=lambda: sort_treeview(treeview, col, not reverse))


class EfficiencySection:
    """Component for the overall efficiency section."""
    def __init__(self, parent, root):
        """
        Initialize the efficiency section widget.
        
        Args:
            parent: Parent frame
            root: Root window
        """
        self.parent = parent
        self.root = root
        
        self.score_frame = ttk.LabelFrame(parent, text="Overall Efficiency", padding=10)
        self.score_frame.grid_columnconfigure(0, weight=1)
        
        # Efficiency bar
        self.efficiency_bar = ttk.Progressbar(self.score_frame, orient="horizontal", 
                                               length=300, mode="determinate")
        self.efficiency_bar.grid(row=0, column=0, pady=5, padx=10, sticky="ew")
        
        # Efficiency score label and icon in a nested frame
        efficiency_label_frame = ttk.Frame(self.score_frame)
        efficiency_label_frame.grid(row=1, column=0, pady=(5, 0), sticky="ew")
        efficiency_label_frame.grid_columnconfigure(0, weight=1)  # Center the content
        
        # Add text and icon to the nested frame
        text_and_icon_frame = ttk.Frame(efficiency_label_frame)
        text_and_icon_frame.grid(row=0, column=0)  # Center the text and icon horizontally
        text_and_icon_frame.grid_columnconfigure(0, weight=1)
        
        self.efficiency_label = ttk.Label(text_and_icon_frame, text="Efficiency Score: Calculating...", 
                                           font=("Arial", 12), anchor="center")
        self.efficiency_label.grid(row=0, column=0, padx=(0, 5))
        
        # Add info icon next to the Efficiency Score label
        info_icon = tk.Canvas(text_and_icon_frame, width=16, height=16, 
                               highlightthickness=0, bg=self.root.cget("background"))
        info_icon.grid(row=0, column=1)  # Place the icon next to the text
        draw_info_icon(info_icon)  # Draw the 'i' icon
        
        # Add tooltip to the icon
        bind_tooltip(self.root, info_icon, 
                     "Efficiency Score measures the percentage of free memory relative to total system memory.\n"
                     "Green: >60% free memory\n"
                     "Orange: 30%-60% free memory\n"
                     "Red: <30% free memory")
        
        # Status label
        self.efficiency_status = ttk.Label(self.score_frame, text="Status: Calculating...", 
                                            font=("Arial", 12), anchor="center", foreground="green")
        self.efficiency_status.grid(row=2, column=0, pady=(5, 5), sticky="ew")
    
    def update(self):
        """Update the efficiency bar and status."""
        free_mem_percent, status, color = memory_utils.get_memory_efficiency()
        self.efficiency_bar['value'] = free_mem_percent
        self.efficiency_label.config(text=f"Efficiency Score: {free_mem_percent:.2f}% Free")
        self.efficiency_status.config(text=f"Status: {status}", foreground=color)
        return True


class MemoryTable:
    """Base class for memory usage tables."""
    def __init__(self, parent, title, description, height=15):
        """
        Initialize a memory table component.
        
        Args:
            parent: Parent frame
            title: Table title
            description: Table description
            height: Table height
        """
        self.parent = parent
        self.title = title
        self.frame = ttk.LabelFrame(parent, text=title, padding=10)
        
        # Add description
        description_label = ttk.Label(
            self.frame,
            text=description,
            font=("Arial", 10),
            justify="left",
            anchor="w"
        )
        description_label.pack(pady=(0, 10), padx=5, fill="x")
        
        # Table for applications
        scroll_y = ttk.Scrollbar(self.frame, orient="vertical")
        scroll_x = ttk.Scrollbar(self.frame, orient="horizontal")
        columns = ("Application", "Usage", "Recommendation")
        
        self.table = ttk.Treeview(
            self.frame, columns=columns, show="headings", height=height,
            yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set
        )
        scroll_y.config(command=self.table.yview)
        scroll_x.config(command=self.table.xview)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.table.pack(fill="both", expand=True, padx=5)
        
        configure_table_columns(self.table, {
            "Application": {"width": 150, "anchor": "center"},
            "Usage": {"width": 100, "anchor": "center"},
            "Recommendation": {"width": 500, "anchor": "w"},
        })


class HighestMemoryTable(MemoryTable):
    """Table showing applications with highest memory usage."""
    def __init__(self, parent, root, threshold_callback, context_menu_callback):
        """
        Initialize the highest memory usage table.
        
        Args:
            parent: Parent frame
            root: Root window
            threshold_callback: Callback function for threshold changes
            context_menu_callback: Callback function for context menu
        """
        description = "Displays applications consuming significant memory. Adjust the threshold to control which applications are shown."
        super().__init__(parent, "Highest Memory Applications", description)
        
        self.root = root
        self.threshold_callback = threshold_callback
        
        # Add threshold controls
        threshold_frame = ttk.Frame(self.frame)
        threshold_frame.pack(fill="x", padx=5, pady=(0, 10))
        
        ttk.Label(threshold_frame, text="Threshold (MB):", font=("Arial", 10)).grid(
            row=0, column=0, sticky="w", padx=(0, 5)
        )
        self.threshold_mb = ttk.Entry(threshold_frame, font=("Arial", 10), width=10)
        self.threshold_mb.grid(row=0, column=1, sticky="w", padx=(0, 10))
        
        ttk.Label(threshold_frame, text="or %:", font=("Arial", 10)).grid(
            row=0, column=2, sticky="w", padx=(5, 5)
        )
        self.threshold_percent = ttk.Entry(threshold_frame, font=("Arial", 10), width=10)
        self.threshold_percent.grid(row=0, column=3, sticky="w")
        
        # Reset to Default Button with Info Icon
        reset_frame = ttk.Frame(threshold_frame)
        reset_frame.grid(row=0, column=4, padx=(10, 0))
        
        reset_button = ttk.Button(reset_frame, text="Reset to Default", command=self.reset_threshold)
        reset_button.pack(side="left")
        
        # Add info icon
        info_icon = tk.Canvas(reset_frame, width=16, height=16, 
                               highlightthickness=0, bg=self.root.cget("background"))
        info_icon.pack(side="left", padx=(5, 0))
        draw_info_icon(info_icon)
        bind_tooltip(self.root, info_icon, 
                     "Defaults are calculated as 2% of total memory or 200 MB, whichever is higher, "
                     "to ensure compatibility across different systems.")
        
        # Add notification toggle
        self.notifications_enabled = tk.BooleanVar(value=False)
        notif_checkbox_frame = ttk.Frame(self.frame)
        notif_checkbox_frame.pack(fill="x", padx=5, pady=(0, 10))
        
        notifications_checkbox = ttk.Checkbutton(
            notif_checkbox_frame,
            text="Enable Notifications",
            variable=self.notifications_enabled
        )
        notifications_checkbox.pack(anchor="w", padx=(0, 10))
        
        # Bind context menu
        self.table.bind("<Button-3>", context_menu_callback)
        
        # Bind threshold updates
        self.threshold_mb.bind("<KeyRelease>", self._on_threshold_mb_changed)
        self.threshold_percent.bind("<KeyRelease>", self._on_threshold_percent_changed)
        
        # Initialize with default values
        self.set_default_threshold()
    
    def _on_threshold_mb_changed(self, event):
        """Handle changes to the MB threshold field."""
        try:
            if self.threshold_mb.get():
                mb_value = float(self.threshold_mb.get())
                percent_value = memory_utils.mb_to_percent(mb_value)
                
                self.threshold_percent.delete(0, tk.END)
                self.threshold_percent.insert(0, f"{percent_value:.2f}")
                self.threshold_callback()
        except ValueError:
            pass  # Ignore invalid inputs
    
    def _on_threshold_percent_changed(self, event):
        """Handle changes to the percentage threshold field."""
        try:
            if self.threshold_percent.get():
                percent_value = float(self.threshold_percent.get())
                mb_value = memory_utils.percent_to_mb(percent_value)
                
                self.threshold_mb.delete(0, tk.END)
                self.threshold_mb.insert(0, f"{mb_value:.2f}")
                self.threshold_callback()
        except ValueError:
            pass  # Ignore invalid inputs
    
    def reset_threshold(self):
        """Reset threshold to default values."""
        self.set_default_threshold()
        self.threshold_callback()
    
    def set_default_threshold(self):
        """Set default threshold values."""
        usage_threshold, _ = memory_utils.calculate_default_thresholds()
        percent_value = memory_utils.mb_to_percent(usage_threshold)
        
        self.threshold_mb.delete(0, tk.END)
        self.threshold_mb.insert(0, f"{usage_threshold:.2f}")
        
        self.threshold_percent.delete(0, tk.END)
        self.threshold_percent.insert(0, f"{percent_value:.2f}")
    
    def get_threshold(self):
        """Get the current threshold value in MB."""
        try:
            return float(self.threshold_mb.get())
        except (ValueError, TypeError):
            # Fall back to default if invalid
            usage_threshold, _ = memory_utils.calculate_default_thresholds()
            return usage_threshold
    
    def update_table(self, process_cache):
        """Update the table with process data."""
        try:
            # Get current threshold
            threshold = self.get_threshold()
            
            # Aggregate memory by process name
            aggregated_memory = process_utils.aggregate_memory_by_name(process_cache)
            
            # Filter processes that exceed the threshold
            processes = []
            notified_processes = set()
            
            for name, memory in aggregated_memory.items():
                if memory >= threshold:
                    # Generate recommendations
                    usage_threshold, flagged_threshold = memory_utils.calculate_default_thresholds()
                    recommendation = memory_utils.generate_detailed_recommendation(
                        name, memory, usage_threshold, flagged_threshold)
                    processes.append((name, memory, recommendation))
                    
                    # Trigger notifications if enabled
                    if self.notifications_enabled.get() and name not in notified_processes:
                        notification_utils.send_high_memory_notification(name, memory, recommendation)
                        notified_processes.add(name)
            
            # Update table
            self._populate_table(processes)
            
            return True
        except Exception as e:
            print(f"Error updating usage table: {e}")
            return False
    
    def _populate_table(self, processes):
        """Efficiently update the table with process data."""
        # Get current items in the table
        current_items = {self.table.item(child)['values'][0]: child 
                         for child in self.table.get_children()}
        
        # Prepare new items to add/update
        new_items = {name: (name, f"{mem_usage:.2f} MB", recommendation) 
                     for name, mem_usage, recommendation in processes}
        
        # Update existing rows and add new ones
        for name, values in new_items.items():
            if name in current_items:
                self.table.item(current_items[name], values=values)
            else:
                self.table.insert("", "end", values=values)
        
        # Remove rows that are no longer in the list
        for name in current_items.keys() - new_items.keys():
            self.table.delete(current_items[name])


class FlaggedMemoryTable(MemoryTable):
    """Table showing applications with suspiciously high memory usage."""
    def __init__(self, parent, root, threshold_callback, context_menu_callback):
        """
        Initialize the flagged memory table.
        
        Args:
            parent: Parent frame
            root: Root window
            threshold_callback: Callback function for threshold changes
            context_menu_callback: Callback function for context menu
        """
        description = "Lists applications with unusually high memory usage. Adjust the threshold to detect potential memory leaks or harmful programs."
        super().__init__(parent, "Suspicious Applications", description, height=12)
        
        self.root = root
        self.threshold_callback = threshold_callback
        
        # Add threshold controls
        threshold_frame = ttk.Frame(self.frame)
        threshold_frame.pack(fill="x", padx=5, pady=(0, 10))
        
        ttk.Label(threshold_frame, text="Threshold (MB):", font=("Arial", 10)).grid(
            row=0, column=0, sticky="w", padx=(0, 5)
        )
        self.threshold_mb = ttk.Entry(threshold_frame, font=("Arial", 10), width=10)
        self.threshold_mb.grid(row=0, column=1, sticky="w", padx=(0, 10))
        
        ttk.Label(threshold_frame, text="or %:", font=("Arial", 10)).grid(
            row=0, column=2, sticky="w", padx=(5, 5)
        )
        self.threshold_percent = ttk.Entry(threshold_frame, font=("Arial", 10), width=10)
        self.threshold_percent.grid(row=0, column=3, sticky="w")
        
        # Reset to Default Button with Info Icon
        reset_frame = ttk.Frame(threshold_frame)
        reset_frame.grid(row=0, column=4, padx=(10, 0))
        
        reset_button = ttk.Button(reset_frame, text="Reset to Default", command=self.reset_threshold)
        reset_button.pack(side="left")
        
        # Add info icon
        info_icon = tk.Canvas(reset_frame, width=16, height=16, 
                               highlightthickness=0, bg=self.root.cget("background"))
        info_icon.pack(side="left", padx=(5, 0))
        draw_info_icon(info_icon)
        bind_tooltip(self.root, info_icon, 
                     "Defaults are calculated as 15% of total memory or 1500 MB, whichever is higher, "
                     "to detect unusually high memory usage.")
        
        # Add notification toggle
        self.notifications_enabled = tk.BooleanVar(value=True)  # Default: Enabled
        
        # Notification Setting
        notif_checkbox = ttk.Checkbutton(
            threshold_frame,
            text="Enable Notifications",
            variable=self.notifications_enabled
        )
        notif_checkbox.grid(row=2, column=0, columnspan=5, sticky="w", padx=(0, 10), pady=(5, 0))
        
        # Bind context menu
        self.table.bind("<Button-3>", context_menu_callback)
        
        # Bind threshold updates
        self.threshold_mb.bind("<KeyRelease>", self._on_threshold_mb_changed)
        self.threshold_percent.bind("<KeyRelease>", self._on_threshold_percent_changed)
        
        # Initialize with default values
        self.set_default_threshold()
    
    def _on_threshold_mb_changed(self, event):
        """Handle changes to the MB threshold field."""
        try:
            if self.threshold_mb.get():
                mb_value = float(self.threshold_mb.get())
                percent_value = memory_utils.mb_to_percent(mb_value)
                
                self.threshold_percent.delete(0, tk.END)
                self.threshold_percent.insert(0, f"{percent_value:.2f}")
                self.threshold_callback()
        except ValueError:
            pass  # Ignore invalid inputs
    
    def _on_threshold_percent_changed(self, event):
        """Handle changes to the percentage threshold field."""
        try:
            if self.threshold_percent.get():
                percent_value = float(self.threshold_percent.get())
                mb_value = memory_utils.percent_to_mb(percent_value)
                
                self.threshold_mb.delete(0, tk.END)
                self.threshold_mb.insert(0, f"{mb_value:.2f}")
                self.threshold_callback()
        except ValueError:
            pass  # Ignore invalid inputs
    
    def reset_threshold(self):
        """Reset threshold to default values."""
        self.set_default_threshold()
        self.threshold_callback()
    
    def set_default_threshold(self):
        """Set default threshold values."""
        _, flagged_threshold = memory_utils.calculate_default_thresholds()
        percent_value = memory_utils.mb_to_percent(flagged_threshold)
        
        self.threshold_mb.delete(0, tk.END)
        self.threshold_mb.insert(0, f"{flagged_threshold:.2f}")
        
        self.threshold_percent.delete(0, tk.END)
        self.threshold_percent.insert(0, f"{percent_value:.2f}")
    
    def get_threshold(self):
        """Get the current threshold value in MB."""
        try:
            return float(self.threshold_mb.get())
        except (ValueError, TypeError):
            # Fall back to default if invalid
            _, flagged_threshold = memory_utils.calculate_default_thresholds()
            return flagged_threshold
    
    def update_table(self, process_cache):
        """Update the table with process data."""
        try:
            # Get current threshold
            threshold = self.get_threshold()
            
            # Aggregate memory by process name
            aggregated_memory = process_utils.aggregate_memory_by_name(process_cache)
            
            # Filter processes that exceed the threshold
            processes = []
            notified_processes = set()
            
            for name, memory in aggregated_memory.items():
                if memory >= threshold:
                    # Get thresholds for recommendations
                    usage_threshold, flagged_threshold = memory_utils.calculate_default_thresholds()
                    recommendation = memory_utils.generate_detailed_recommendation(
                        name, memory, usage_threshold, flagged_threshold)
                    
                    processes.append((name, memory, "High Memory Usage"))
                    
                    # Trigger notifications if enabled
                    if self.notifications_enabled.get() and name not in notified_processes:
                        notification_utils.send_flagged_notification(name, memory, recommendation)
                        notified_processes.add(name)
            
            # Update table
            self._populate_table(processes)
            
            return True
        except Exception as e:
            print(f"Error updating flagged table: {e}")
            return False
    
    def _populate_table(self, processes):
        """Efficiently update the table with process data."""
        # Get current items in the table
        current_items = {self.table.item(child)['values'][0]: child 
                         for child in self.table.get_children()}
        
        # Prepare new items to add/update
        new_items = {name: (name, f"{mem_usage:.2f} MB", reason) 
                     for name, mem_usage, reason in processes}
        
        # Update existing rows and add new ones
        for name, values in new_items.items():
            if name in current_items:
                self.table.item(current_items[name], values=values)
            else:
                self.table.insert("", "end", values=values)
        
        # Remove rows that are no longer in the list
        for name in current_items.keys() - new_items.keys():
            self.table.delete(current_items[name])
