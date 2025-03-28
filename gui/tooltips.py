"""
Tooltip functionality for the Memory Tracker application.
"""
import tkinter as tk

def draw_info_icon(canvas):
    """
    Draw a simple 'i' information icon on the canvas.
    
    Args:
        canvas: Tkinter canvas object
    """
    canvas.create_oval(2, 2, 14, 14, fill="blue", outline="blue")
    canvas.create_text(8, 8, text="i", fill="white", font=("Arial", 10, "bold"))


def bind_tooltip(root, widget, text):
    """
    Bind a tooltip to a widget.
    
    Args:
        root: Tkinter root window
        widget: Widget to bind the tooltip to
        text: Text to display in the tooltip
    """
    tooltip = tk.Toplevel(root, bg="white", padx=5, pady=3)
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
