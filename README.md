# Memory Tracker Tool

## Description
The Memory Tracker Tool is a Python application built using `tkinter` for the graphical user interface (GUI) and `plyer` for system notifications. It provides a visual interface to monitor system memory usage, analyze application behavior, and receive notifications based on user preferences.

## Features
- **Overall Efficiency**: Displays the system memory usage and efficiency score.
- **Usage Analyzer**: Lists applications consuming memory with recommendations.
- **Notification Settings**: Allows users to set up notifications based on memory usage patterns.
- **Flagged Applications**: Displays applications that are flagged for high memory usage or unusual behavior.

## Requirements

- Python 3.x
- Required Python libraries:
  - `tkinter`
  - `plyer` (for system notifications)

You can install the required libraries with the following command:

```bash
pip install plyer
```

## Running the Application

### Step 1: Clone the repository
First, clone the GitHub repository to your local machine:

```bash
git clone https://github.com/Adrian-Chambers/MemoryUsageTool.git
```

### Step 2: Install dependencies
Navigate to the project folder and install the required dependencies using `pip`:

```bash
cd MemoryUsageTool
```

**Note**: If `requirements.txt` is not available, manually install `plyer` with the command mentioned earlier.

### Step 3: Run the application
Once all dependencies are installed, you can run the application with the following command:

```bash
python memory_tracker.py
```

This will open the Memory Tracker Tool GUI, and you can start using it to track system memory usage and receive notifications.
