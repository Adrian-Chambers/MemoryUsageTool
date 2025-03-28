# Memory Tracker Tool

A Python application for monitoring memory usage of running processes. This tool helps identify memory-intensive applications and provides recommendations to optimize system performance.

## Features

- Real-time memory efficiency monitoring
- Tracking of applications with high memory usage
- Detection of suspicious applications that may be causing memory leaks
- Customizable memory thresholds for alerts
- Desktop notifications for high memory usage
- Process management (view details, kill processes, open file locations)

## Project Structure

The application has been refactored into a modular structure:

```
memory_tracker/
├── main.py                  # Entry point for the application
├── requirements.txt         # Dependencies
├── gui/                     # GUI-related modules
│   ├── __init__.py
│   ├── app.py               # Main application class
│   ├── components.py        # GUI components and tables
│   └── tooltips.py          # Tooltip functionality
└── utils/                   # Utility functions
    ├── __init__.py
    ├── memory_utils.py      # Memory analysis utilities
    ├── notification_utils.py # Notification handling
    └── process_utils.py     # Process management utilities
```

## Installation

1. Clone the repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the application with:

```
python main.py
```

## Dependencies

- psutil: Process and system utilities
- plyer: Cross-platform notifications
- ttkthemes: Themed Tkinter widgets

## Customizing Thresholds

- **Usage Analyzer Threshold**: Controls which applications are shown in the "Highest Memory Applications" table. Default: 2% of total memory or 200 MB, whichever is higher.
  
- **Flagged Applications Threshold**: Controls which applications are considered suspicious. Default: 15% of total memory or 1500 MB, whichever is higher.

Both thresholds can be adjusted using either MB values or percentages.
