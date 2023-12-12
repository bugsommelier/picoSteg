import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import cv2
import threading

class PicoStegApp:
    def __init__(self, root):
        self.root = root
        self.root.title("picoSteg")

        # Initialize variables
        self.image_path = ""
        self.target_save_path = ""
        self.original_image_tk = None
        self.decoded_image_tk = None

        # User Interface Setup
        self.setup_ui()

    def setup_ui(self):
        self.image_label = tk.Label(self.root)
        self.image_label.pack()

        self.load_image_button = tk.Button(self.root, text="Browse for an image", command=self.load_image)
        self.load_image_button.pack()

        self.message_label = tk.Label(self.root, text="Message:")
        self.message_label.pack()

        self.message_entry = tk.Entry(self.root, width=40)
        self.message_entry.pack()

        self.encode_message_button = tk.Button(self.root, text="Save", command=self.encode_and_save_message)
        self.encode_message_button.pack()

        self.decode_message_button = tk.Button(self.root, text="Load for decode", command=self.load_decode)
        self.decode_message_button.pack()

        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=200, mode='indeterminate')
        self.progress.pack()

        self.decoded_message_label = tk.Label(self.root, text="", wraplength=300)
        self.decoded_message_label.pack()

        self.results_label = tk.Label(self.root, text="", wraplength=300)
        self.results_label.pack()

        self.decoded_image_label = tk.Label(self.root)
        self.decoded_image_label.pack()

    def load_image(self):
        self.image_path = filedialog.askopenfilename()
        if self.image_path:
            self.process_and_display_image(self.image_path, True)

    def process_and_display_image(self, image_path, is_original):
        image = Image.open(image_path)
        max_size = (300, 300)
        image.thumbnail(max_size, Image.ANTIALIAS)

        image_tk = ImageTk.PhotoImage(image)
        if is_original:
            self.original_image_tk = image_tk
            self.image_label.configure(image=self.original_image_tk)
            self.image_label.image = self.original_image_tk
        else:
            self.decoded_image_tk = image_tk
            self.decoded_image_label.configure(image=self.decoded_image_tk)
            self.decoded_image_label.image = self.decoded_image_tk

        self.message_entry.delete(0, tk.END)
        self.decoded_message_label.configure(text="")
        self.results_label.configure(text="")

    def encode_and_save_message(self):
        threading.Thread(target=self._encode_and_save).start()

    def _encode_and_save(self):
        self.progress.start()
        message = self.message_entry.get()
        if not self.image_path:
            messagebox.showerror("Error", "No image loaded. Please load an image first.")
            self.progress.stop()
            return

        target_save_path = filedialog.askdirectory()
        if not target_save_path:
            messagebox.showerror("Error", "No target directory selected. Please choose a directory.")
            self.progress.stop()
            return

        filename = os.path.basename(self.image_path) + "_encoded.png"
        self.encode_message(self.image_path, message, target_save_path, filename)

        self.progress.stop()
        # Update the UI in the main thread
        self.root.after(0, self.update_encode_results, os.path.join(target_save_path, filename))

    def update_encode_results(self, encoded_image_path):
        self.results_label.configure(text="Encoded and saved to: " + encoded_image_path)
        self.progress.pack_forget()  # Hide the progress bar

    def encode_message(self, image_path, message, target_save_path, filename):
        # Read the original image
        original_image = cv2.imread(image_path)

        # Convert the message to binary, and append the end-of-message marker
        end_marker = "\x00\x00\x00"  # Three null bytes to signify the end of the message
        binary_message = ''.join(format(ord(char), '08b') for char in message) + ''.join(format(ord(char), '08b') for char in end_marker)

        # Check if the image can store the binary message
        if len(binary_message) > original_image.size:
            messagebox.showerror("Error", "The message is too long for the selected image.")
            return

        # Flatten the image array and embed the binary message
        flat_image = original_image.flatten()
        for i in range(len(binary_message)):
            flat_image[i] = (flat_image[i] & 0xFE) | int(binary_message[i])

        # Reshape the array back to the original image shape
        encoded_image = flat_image.reshape(original_image.shape)

        # Save the encoded image
        encoded_image_path = os.path.join(target_save_path, filename)
        cv2.imwrite(encoded_image_path, encoded_image)

    def load_decode(self):
        threading.Thread(target=self._load_decode).start()

    def _load_decode(self):
        self.progress.start()
        encoded_image_path = filedialog.askopenfilename()
        if encoded_image_path:
            hidden_message, decoded_image = self.decode_message(encoded_image_path)
            # Schedule UI updates in the main thread
            self.root.after(0, self.update_decode_results, hidden_message)
        self.progress.stop()

    def update_decode_results(self, hidden_message):
        self.update_results(hidden_message)
        self.progress.pack_forget()  # Hide the progress bar

    def decode_message(self, encoded_image_path):
        encoded_image = cv2.imread(encoded_image_path)
        flat_encoded_image = encoded_image.flatten()

        binary_message = "".join(str(pixel & 1) for pixel in flat_encoded_image)
        hidden_message = ""
        end_marker = "00000000" * 3  # Assuming end-of-message is marked by three consecutive null bytes

        for i in range(0, len(binary_message), 8):
            byte = binary_message[i:i+8]
            if binary_message[i:i+24] == end_marker:  # Check for end marker
                break
            hidden_message += chr(int(byte, 2))

        return hidden_message, encoded_image


    def update_results(self, hidden_message):
        self.decoded_message_label.configure(text="Decoded Message:\n" + hidden_message)

# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    app = PicoStegApp(root)
    root.mainloop()
