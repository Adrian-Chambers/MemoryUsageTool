"""
Entry point for the Memory Tracker application.
Run this file to start the application.
"""
import tkinter as tk
from ttkthemes import ThemedTk
from gui.app import MemoryTrackerApp


def main():
    """Main entry point for the application."""
    # Create the root window with a theme
    root = ThemedTk(theme="plastik")
    
    # Initialize the application
    app = MemoryTrackerApp(root)
    
    # Start the main loop
    root.mainloop()


if __name__ == "__main__":
    main()
