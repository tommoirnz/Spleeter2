# main.py

import os
import sys
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from pathlib import Path
import warnings

# ===============================
# Suppress TensorFlow and Python Warnings
# ===============================

# Suppress TensorFlow logging before importing it
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress INFO, WARNING, and ERROR messages

# Import TensorFlow after setting the environment variable
import tensorflow as tf
tf.get_logger().setLevel('ERROR')  # Set TensorFlow logger to ERROR
logging.getLogger('tensorflow').setLevel(logging.ERROR)  # Further suppress TensorFlow logs

# Suppress Python deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ===============================
# Configure Application Logging
# ===============================
logging.basicConfig(
    filename='audio_separator.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# ===============================
# Define Utility Functions
# ===============================

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.

    Args:
        relative_path (str): Relative path to the resource.

    Returns:
        str: Absolute path to the resource.
    """
    try:
        # PyInstaller creates a temporary folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# ===============================
# Set Up Local Cache Directory for Spleeter
# ===============================

from spleeter.separator import Separator

# Define the local cache directory relative to the executable or script
CACHE_DIR_NAME = 'spleeter_models'
CACHE_DIR = resource_path(CACHE_DIR_NAME)

# Ensure the cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

# Set the Spleeter cache directory environment variable
os.environ['Spleeter_CACHE_DIR'] = CACHE_DIR  # Corrected environment variable name

# ===============================
# Define Core Functionality
# ===============================

# Global flag to indicate if separation is in progress
separation_in_progress = False

def separate_audio(audio_path, output_directory, stems):
    """
    Separates the audio file into the specified number of stems using Spleeter.
    This function runs in a separate thread to keep the GUI responsive.
    """
    global separation_in_progress
    try:
        progress.start()  # Start the progress bar
        logging.info(f"Starting separation: {audio_path} into {stems} stems.")

        # Determine the Spleeter model based on selected stems
        if stems == 2:
            model = 'spleeter:2stems'
        elif stems == 4:
            model = 'spleeter:4stems'
        elif stems == 5:
            model = 'spleeter:5stems'
        else:
            raise ValueError("Unsupported number of stems. Please choose between 2, 4, or 5.")

        # Initialize the separator with the chosen model
        separator = Separator(model)  # Removed cache_dir argument

        # Perform the separation
        separator.separate_to_file(audio_path, output_directory)

        logging.info("Separation completed successfully.")
        messagebox.showinfo("Success", f"Separation into {stems} stems complete!\nCheck the output directory for results.")
    except Exception as e:
        logging.error(f"Separation failed: {e}")
        messagebox.showerror("Error", f"An error occurred during separation:\n{e}")
    finally:
        progress.stop()  # Stop the progress bar
        separation_in_progress = False
        # Re-enable the separation button in the main thread
        root.after(0, lambda: separate_button.config(state='normal'))

def browse_input_file():
    """
    Opens a file dialog for the user to select an input audio file.
    """
    file_path = filedialog.askopenfilename(
        title="Select Audio File",
        filetypes=(("Audio Files", "*.mp3 *.wav *.flac *.m4a"), ("All Files", "*.*"))
    )
    if file_path:
        input_entry.delete(0, tk.END)
        input_entry.insert(0, file_path)

def browse_output_directory():
    """
    Opens a directory dialog for the user to select an output folder.
    """
    directory_path = filedialog.askdirectory(title="Select Output Directory")
    if directory_path:
        output_entry.delete(0, tk.END)
        output_entry.insert(0, directory_path)

def start_separation():
    """
    Validates user inputs and initiates the audio separation process in a separate thread.
    Prevents multiple separation processes from running simultaneously.
    """
    global separation_in_progress
    if separation_in_progress:
        messagebox.showwarning("Separation In Progress", "A separation task is already running. Please wait until it finishes.")
        return

    audio_path = input_entry.get()
    output_directory = output_entry.get()
    stems = stem_var.get()

    # Input Validation
    if not audio_path:
        messagebox.showwarning("Input Needed", "Please select an audio file to separate.")
        return
    if not output_directory:
        messagebox.showwarning("Output Needed", "Please select an output directory.")
        return
    if stems not in [2, 4, 5]:
        messagebox.showwarning("Invalid Selection", "Please select a valid number of stems (2, 4, or 5).")
        return

    # User Confirmation
    confirm = messagebox.askyesno(
        "Confirm Separation",
        f"Separate '{Path(audio_path).name}' into {stems} stems and save to '{output_directory}'?"
    )
    if confirm:
        separation_in_progress = True
        separate_button.config(state='disabled')  # Disable the button to prevent multiple clicks
        # Start separation in a new thread to keep GUI responsive
        threading.Thread(
            target=separate_audio,
            args=(audio_path, output_directory, stems),
            daemon=True
        ).start()

# ===============================
# Initialize the Main Window
# ===============================
if __name__ == "__main__":
    # Initialize the main window
    root = tk.Tk()
    root.title("Audio Separator with Spleeter")
    root.geometry("600x300")  # Increased height to accommodate new widgets
    root.resizable(False, False)

    # Configure grid layout
    root.columnconfigure(1, weight=1, minsize=400)

    # ===============================
    # Input File Selection
    # ===============================
    input_label = tk.Label(root, text="Input Audio File:")
    input_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")

    input_entry = tk.Entry(root, width=50)
    input_entry.grid(row=0, column=1, padx=10, pady=10, sticky="we")

    browse_input_button = tk.Button(root, text="Browse...", command=browse_input_file)
    browse_input_button.grid(row=0, column=2, padx=10, pady=10)

    # ===============================
    # Output Directory Selection
    # ===============================
    output_label = tk.Label(root, text="Output Directory:")
    output_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")

    output_entry = tk.Entry(root, width=50)
    output_entry.grid(row=1, column=1, padx=10, pady=10, sticky="we")

    browse_output_button = tk.Button(root, text="Browse...", command=browse_output_directory)
    browse_output_button.grid(row=1, column=2, padx=10, pady=10)

    # ===============================
    # Stem Selection
    # ===============================
    stem_label = tk.Label(root, text="Number of Stems:")
    stem_label.grid(row=2, column=0, padx=10, pady=10, sticky="e")

    stem_var = tk.IntVar(value=2)  # Default to 2 stems
    stem_options = [2, 4, 5]  # Supported options

    stem_menu = tk.OptionMenu(root, stem_var, *stem_options)
    stem_menu.config(width=10)
    stem_menu.grid(row=2, column=1, padx=10, pady=10, sticky="w")

    # ===============================
    # Separation Button
    # ===============================
    separate_button = tk.Button(
        root,
        text="Separate Audio",
        command=start_separation,
        bg="#4CAF50",
        fg="white",
        font=("Helvetica", 12, "bold")
    )
    separate_button.grid(row=3, column=1, pady=20)

    # ===============================
    # Progress Bar
    # ===============================
    progress = ttk.Progressbar(root, orient='horizontal', length=400, mode='indeterminate')
    progress.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

    # ===============================
    # Run the Application
    # ===============================
    root.mainloop()
