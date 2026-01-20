import tkinter as tk
import sys

def main():
    # Settings
    box_width = 600
    box_height = 600
    thickness = 2
    color = 'red'

    # Hidden root to get screen info
    base = tk.Tk()
    base.withdraw()
    screen_width = base.winfo_screenwidth()
    screen_height = base.winfo_screenheight()
    base.destroy()

    center_x = screen_width // 2
    center_y = screen_height // 2

    # Calculate coordinates
    # x, y are top-left corners
    
    # Top Bar
    x_top = center_x - (box_width // 2)
    y_top = center_y - (box_height // 2)
    geo_top = f"{box_width}x{thickness}+{x_top}+{y_top}"

    # Bottom Bar
    x_bot = x_top
    y_bot = center_y + (box_height // 2) - thickness
    geo_bot = f"{box_width}x{thickness}+{x_bot}+{y_bot}"

    # Left Bar
    x_left = x_top
    y_left = y_top
    geo_left = f"{thickness}x{box_height}+{x_left}+{y_left}"

    # Right Bar
    x_right = center_x + (box_width // 2) - thickness
    y_right = y_top
    geo_right = f"{thickness}x{box_height}+{x_right}+{y_right}"

    # Create windows
    # Main root is Top Bar
    root = tk.Tk()
    root.overrideredirect(True) # No window decorations
    root.geometry(geo_top)
    root.configure(bg=color)
    root.attributes('-topmost', True)

    # Others are Toplevels
    for geo in [geo_bot, geo_left, geo_right]:
        win = tk.Toplevel(root)
        win.overrideredirect(True)
        win.geometry(geo)
        win.configure(bg=color)
        win.attributes('-topmost', True)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        root.destroy()

if __name__ == "__main__":
    main()
