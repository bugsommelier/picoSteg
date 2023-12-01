from tkinter import filedialog
from PIL import Image, ImageTk
import os
import tkinter as tk
import cv2

# Declare global variables
global image_path, target_save_path, message_entry, original_image_tk

def load_image():
    global image_path, target_save_path, original_image_tk
    # Get the image path
    image_path = filedialog.askopenfilename()

    # Initialize the target save path with the image directory
    target_save_path = os.path.dirname(image_path)

    if image_path:
        # Open the image without resizing
        image = Image.open(image_path)

        # Resize the image while maintaining the aspect ratio to fit the GUI window
        max_size = (300, 300)
        image.thumbnail(max_size, Image.ANTIALIAS)

        # Convert the image to an ImageTk object
        original_image_tk = ImageTk.PhotoImage(image)

        # Display the image on the GUI
        image_label.configure(image=original_image_tk)
        image_label.image = original_image_tk

        # Clear the message entry and labels
        message_label.configure(text="Message to steg:")
        message_entry.delete(0, tk.END)
        decoded_message_label.configure(text="")
        decoded_image_label.configure(image=None)  # Clear the displayed image
        results_label.configure(text="")

def encode_and_save_message():
    global message_entry
    # Get the message to hide
    message = message_entry.get()

    # Check if an image is loaded
    if not image_path:
        print("No image loaded. Please load an image first.")
        return

    # Open a file dialog to select the target directory
    target_save_path = filedialog.askdirectory()

    if not target_save_path:
        print("No target directory selected. Please choose a directory.")
        return

    # Generate the encoded image filename
    filename = os.path.basename(image_path) + "_encoded.png"

    # Encode the message into the image using pixel modification
    encode_message(image_path, message, target_save_path, filename)

    # Display a success message
    results_label.configure(text="Encoded and saved to:")
    results_label.configure(text=results_label['text'] + " " + os.path.join(target_save_path, filename))

def encode_message(image_path, message, target_save_path, filename):
    # Open the image using OpenCV
    original_image = cv2.imread(image_path)

    # Convert the message to a binary string
    binary_message = ''.join(format(ord(char), '08b') for char in message)

    # Flatten the image
    flat_image = original_image.flatten()

    # Embed the message into the image pixels
    for i in range(len(binary_message)):
        flat_image[i] = (flat_image[i] & 0xFE) | int(binary_message[i])

    # Reshape the flat image back to its original shape
    encoded_image = flat_image.reshape(original_image.shape)

    # Save the encoded image to the specified path
    encoded_image_path = os.path.join(target_save_path, filename)
    cv2.imwrite(encoded_image_path, encoded_image)

def load_decode():
    global decoded_image_label, original_image_tk
    # Get the encoded image path
    encoded_image_path = filedialog.askopenfilename()

    # Decode the message from the encoded image
    hidden_message, decoded_image = decode_message(encoded_image_path)

    # Display the decoded message
    update_results(hidden_message)

    # Convert the NumPy array to a PIL Image
    decoded_image_pil = Image.fromarray(decoded_image)

    # Resize the decoded image while maintaining the aspect ratio to fit the GUI window
    max_size = (300, 300)
    decoded_image_pil.thumbnail(max_size, Image.ANTIALIAS)

    # Convert the decoded image to an ImageTk object
    decoded_image_tk = ImageTk.PhotoImage(decoded_image_pil)

    # Display the decoded image
    image_label.configure(image=decoded_image_tk)
    image_label.image = decoded_image_tk

    # Clear the message entry
    message_entry.delete(0, tk.END)

def decode_message(encoded_image_path):
    # Open the encoded image using OpenCV
    encoded_image = cv2.imread(encoded_image_path)

    # Flatten the encoded image
    flat_encoded_image = encoded_image.flatten()

    # Extract the LSBs to retrieve the binary message
    binary_message = ''.join(str(pixel & 1) for pixel in flat_encoded_image)

    # Convert the binary message to ASCII
    hidden_message = ''.join(chr(int(binary_message[i:i+8], 2)) for i in range(0, len(binary_message), 8))

    # Reshape the flat image back to its original shape
    decoded_image = flat_encoded_image.reshape(encoded_image.shape)

    return hidden_message, decoded_image

def update_results(hidden_message):
    # Update the decoded message label with the decoded message
    decoded_message_label.configure(text="Decoded Message:")
    decoded_message_label.configure(text=decoded_message_label['text'] + "\n" + hidden_message)

# Create the main window and its components
window = tk.Tk()
window.title("picoSteg")

image_label = tk.Label(window)
image_label.pack()

load_image_button = tk.Button(
    window, text="Browse for an image", command=load_image)
load_image_button.pack()

message_label = tk.Label(window, text="Message:")
message_label.pack()

message_entry = tk.Entry(window, width=40)
message_entry.pack()

encode_message_button = tk.Button(
    window, text="Save", command=encode_and_save_message)
encode_message_button.pack()

decode_message_button = tk.Button(
    window, text="Load for decode", command=load_decode)
decode_message_button.pack()

decoded_message_label = tk.Label(window, text="", wraplength=300)
decoded_message_label.pack()

results_label = tk.Label(window, text="", wraplength=300)
results_label.pack()

# Create a label to display the decoded image
decoded_image_label = tk.Label(window)
decoded_image_label.pack()

# Start the main event loop
window.mainloop()
