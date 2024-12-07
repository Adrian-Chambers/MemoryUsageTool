import tkinter as tk
from tkinter import ttk
from plyer import notification

class MemoryTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Memory Tracker")
        self.root.geometry("900x800")

        # Title
        ttk.Label(root, text="Memory Tracker Tool", font=("Arial", 18, "bold")).pack(pady=10)

        # Overall Efficiency Section
        self.score_frame = ttk.LabelFrame(root, text="Overall Efficiency", padding=10)
        self.score_frame.pack(fill="x", padx=10, pady=5)

        self.efficiency_bar = ttk.Progressbar(self.score_frame, orient="horizontal", length=300, mode="determinate")
        self.efficiency_bar["value"] = 85
        self.efficiency_bar.pack(pady=5)
        ttk.Label(self.score_frame, text="Efficiency Score: 85%", font=("Arial", 14)).pack()

        efficiency_status = ttk.Label(self.score_frame, text="Status: Good", font=("Arial", 12, "italic"), foreground="green")
        efficiency_status.pack()

        # Usage Analyzer
        self.usage_frame = ttk.LabelFrame(root, text="Usage Analyzer", padding=10)
        self.usage_frame.pack(fill="x", padx=10, pady=5)
        columns = ("Application", "Usage", "Recommendation")
        self.usage_table = ttk.Treeview(self.usage_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.usage_table.heading(col, text=col)
            self.usage_table.column(col, width=200, anchor="center")
        self.usage_table.pack(fill="both", expand=True)

        # example data
        example_data = [
            ("Browser", "1.2 GB", "Consider closing unused tabs"),
            ("Photo Editor", "800 MB", "Close if not in use"),
            ("Video Player", "1.5 GB", "High usage, monitor"),
            ("Unknown App", "2.0 GB", "Flagged for review")
        ]
        for item in example_data:
            self.usage_table.insert("", "end", values=item)

        # Notifications Section
        self.notifications_frame = ttk.LabelFrame(root, text="Notification Settings", padding=10)
        self.notifications_frame.pack(fill="x", padx=10, pady=5)
        self.notif_options = {
            "Close unused applications": tk.BooleanVar(value=True),
            "Optimize memory usage": tk.BooleanVar(value=True),
            "Flag unusual behavior": tk.BooleanVar(value=False),
        }

        notif_frame = ttk.Frame(self.notifications_frame)
        notif_frame.pack(anchor="w", padx=20)

        for text, var in self.notif_options.items():
            ttk.Checkbutton(notif_frame, text=text, variable=var).pack(anchor="w", pady=2)

        # Trigger Notification Button (Hidden for now)
        # self.notification_button = ttk.Button(self.notifications_frame, text="Trigger Notification", command=self.send_notifications)
        # self.notification_button.pack(pady=5)

        # Flagged Applications
        self.flagged_frame = ttk.LabelFrame(root, text="Flagged Applications", padding=10)
        self.flagged_frame.pack(fill="x", padx=10, pady=5)

        flagged_columns = ("Application", "Usage", "Reason")
        self.flagged_table = ttk.Treeview(self.flagged_frame, columns=flagged_columns, show="headings", height=6)
        for col in flagged_columns:
            self.flagged_table.heading(col, text=col)
            self.flagged_table.column(col, width=200, anchor="center")
        self.flagged_table.pack(fill="both", expand=True)

        # Insert flagged application data
        flagged_data = [
            ("Unknown App", "2.0 GB", "Excessive memory usage"),
            ("Untrusted App", "1.5 GB", "Potential malware activity")
        ]
        for item in flagged_data:
            self.flagged_table.insert("", "end", values=item)

        # Footer
        ttk.Label(root, text="Memory Tracker Tool - Version 1.0", font=("Arial", 10, "italic")).pack(side="bottom", pady=10)

    def send_notifications(self):
        # Check selected options and trigger appropriate notifications
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

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = MemoryTrackerApp(root)
    root.mainloop()
