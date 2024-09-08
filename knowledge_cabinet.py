import tkinter as tk
import subprocess

# Function to run file_to_anki.py
def open_the_flap():
    subprocess.run(["python", "file_to_anki.py"])

# Function to run masterdeck.py
def forage_for_info():
    subprocess.run(["python", "masterdeck.py"])

# Create the main window
root = tk.Tk()
root.title("The Knowledge Cabinet")
root.geometry("400x300")  # Set the size of the window

# Add a title label
title_label = tk.Label(root, text="The Knowledge Cabinet", font=("Arial", 18, "bold"))
title_label.pack(pady=20)

# Add the subtitle
subtitle_label = tk.Label(root, text="What information will squeeze through today?", font=("Arial", 12))
subtitle_label.pack(pady=10)

# Add a button to run file_to_anki.py
open_flap_button = tk.Button(root, text="Open the Flap", font=("Arial", 14), command=open_the_flap)
open_flap_button.pack(pady=20)

# Add a button to run masterdeck.py
forage_info_button = tk.Button(root, text="Forage for Info", font=("Arial", 14), command=forage_for_info)
forage_info_button.pack(pady=20)

# Run the Tkinter event loop
root.mainloop()
