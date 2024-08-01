from tkinter import ttk, messagebox, filedialog
import pyautogui
from pynput import mouse, keyboard
import time
import json
import threading
import keyboard as kk
import ttkbootstrap as tb
import webbrowser


def open_github():
    webbrowser.open('https://github.com/hemuba')

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tb.Canvas(self)
        scrollbar = tb.Scrollbar(self, orient="vertical", command=self.canvas.yview, bootstyle='light-round')
        self.scrollable_frame = tb.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class AutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EET v3.0")
        self.steps = []
        self.recording = False
        self.mouse_listener = None
        self.keyboard_listener = None
        self.automation_thread = None
        self.paused = False
        self.stop_requested = False

        self.main_frame = ScrollableFrame(self.root)
        self.main_frame.pack(side='left', fill="both", expand=True, padx=5, pady=5)

        self.step_frame = tb.Frame(self.main_frame.scrollable_frame)
        self.step_frame.pack(pady=10)

        self.property = tb.Label(self.main_frame.scrollable_frame, 
                                 text="""EASY-ENTRY TOOL - V3.0""", font=('Consolas', 12))
        self.property.pack(pady=5, padx=5)

        self.add_step_button = tb.Button(self.main_frame.scrollable_frame, text="Add Step", command=self.add_step, bootstyle='success')
        self.add_step_button.pack(pady=10)

        self.run_button = tb.Button(self.main_frame.scrollable_frame, text="Run Automation", command=self.toggle_automation, bootstyle='success')
        self.run_button.pack(pady=10)

        self.clear_all_button = tb.Button(self.main_frame.scrollable_frame, text="Clear All Steps", command=self.clear_all_steps, bootstyle='danger')
        self.clear_all_button.pack(pady=5)

        self.save_button = tb.Button(self.main_frame.scrollable_frame, text="Save Steps", command=self.save_steps, bootstyle='info')
        self.save_button.pack(pady=5)

        self.load_button = tb.Button(self.main_frame.scrollable_frame, text="Load Steps", command=self.load_steps, bootstyle='info')
        self.load_button.pack(pady=5)

        self.listen_button = tb.Button(self.main_frame.scrollable_frame, text="Start Listening", command=self.toggle_listening, bootstyle='warning')
        self.listen_button.pack(pady=5)

        delay_frame = tb.Frame(self.main_frame.scrollable_frame)
        delay_frame.pack(pady=5, padx=5)
        tb.Label(delay_frame, text="delay between steps (seconds):", font=('Consolas', 10, 'bold')).pack(side="left")
        self.delay_entry = tb.Entry(delay_frame, width=5)
        self.delay_entry.pack(side="left")
        self.delay_entry.insert(0, "2")  # Default delay is 2 second
        self.mouse_press_time = None

        self.side_frame = tb.Frame(self.root)  
        self.side_frame.pack(side='right', fill='y')  

        
        ttk.Label(self.side_frame, text="EET v3.0 - Easy Entry Tool", font=('Consolas', 10, 'bold')).pack(pady=(5, 0), padx=5)


        
        how_to = """



## How to use Easy Entry Tool (EET v3.0)

EET v3.0 automates tasks using simple steps. 

Quick start guide:


### 1. Add Automation Step
- **Add Step**: Click `Add Step` to define a new action (mouse clicks, keyboard inputs).


### 2. Run Automation
- **Run**: Click `Run Automation` after setting your steps to execute them.


### 3. Save and Load Configurations
- **Save Steps**: Click `Save Steps` to save your configurations to a JSON file.
- **Load Steps**: Click `Load Steps` to reload and execute saved configurations.


### 4. Start Listening
- **Listen**: Click `Start Listening` to automatically record actions for automation.


## Quick Tips
- **Plan Ahead**: Strategize your steps before starting.
- **Test**: Always run a test after setting new steps.
- **Backup**: Regularly back up your configurations to avoid data loss.



Utilize these features to boost efficiency by automating repetitive tasks.
        """
        tb.Label(self.side_frame, text=how_to, font=('Consolas', 9, 'bold')).pack(padx=5, pady=5)


        
        credit_text = "Credits: Alessandro De Vincenti - GitHub"
        credit_label = tb.Label(self.side_frame, text=credit_text, cursor='hand2', font=('Consolas', 10, 'underline'), foreground='lightblue')
        credit_label.pack(pady=20, padx=5, side='bottom')

        
        credit_label.bind("<Button-1>", lambda e: open_github()) 



    def add_step(self, step_type=None, step_value=None):
        step_frame = tb.Frame(self.step_frame)
        step_frame.pack(pady=5)

        step_type_combobox = tb.Combobox(step_frame, values=["Mouse Click", "Mouse Right Click", "Keyboard Arrow Key", "Keyboard Input", "Keyboard Special Key"])
        step_type_combobox.pack(side="left", padx=5)
        if step_type:
            step_type_combobox.set(step_type)
        else:
            step_type_combobox.set("Mouse Click")

        step_entry = tb.Entry(step_frame)
        step_entry.pack(side="left", padx=5)
        if step_value:
            step_entry.insert(0, step_value)

        copy_button = tb.Button(step_frame, text="Copy", command=lambda: self.add_step(step_type_combobox.get(), step_entry.get()), bootstyle='info')
        copy_button.pack(side="left", padx=5)

        remove_button = tb.Button(step_frame, text="X", command=lambda: self.remove_step(step_frame), bootstyle='danger-outline')
        remove_button.pack(side="left", padx=5)

        move_up_button = tb.Button(step_frame, text="↑", command=lambda: self.move_step(step_frame, 'up'), bootstyle='light-outline')
        move_up_button.pack(side="left", padx=5)

        move_down_button = tb.Button(step_frame, text="↓", command=lambda: self.move_step(step_frame, 'down'), bootstyle='light-outline')
        move_down_button.pack(side="left", padx=5)


        self.steps.append((step_type_combobox, step_entry, step_frame))


    def remove_step(self, step_frame):
        for step in self.steps:
            if step[2] == step_frame:
                step_frame.destroy()
                self.steps.remove(step)
                break

    def move_step(self, step_frame, direction):
        index = next((i for i, step in enumerate(self.steps) if step[2] == step_frame), None)
        if index is not None:
            new_index = index + (1 if direction == 'down' else -1)
            if 0 <= new_index < len(self.steps):
                self.steps[index], self.steps[new_index] = self.steps[new_index], self.steps[index]
                for step in self.steps:
                    step[2].pack_forget()  
                for _, _, frame in self.steps:
                    frame.pack(pady=5)  

    def toggle_automation(self):
        if self.automation_thread and self.automation_thread.is_alive():
            self.stop_requested = True
        else:
            self.stop_requested = False
            self.paused = False
            self.automation_thread = threading.Thread(target=self.run_automation)
            self.automation_thread.start()

    def run_automation(self):
        try:
            delay = float(self.delay_entry.get()) 
        except ValueError:
            messagebox.showerror("Error", "Delay must be a number")
            return

        for step_type_combobox, step_entry, _ in self.steps:
            if kk.is_pressed('esc'):
                messagebox.showinfo('Info', 'Automation Stopped!')
                break  

            while self.paused:
                time.sleep(0.1) 

            action_type = step_type_combobox.get()
            action_value = step_entry.get()

            if action_value:  
                self.execute_step(action_type, action_value, delay)  
                time.sleep(delay)  
            else:
                messagebox.showerror("Error", "All steps must be filled out")
                break  
            

    def execute_step(self, action_type, action_value, delay):
        keyboard_controller = keyboard.Controller()
        if action_type == "Mouse Click":
            try:
                x, y = map(int, action_value.split(','))
                pyautogui.click(x, y)
            except ValueError:
                messagebox.showerror("Error", "Mouse Click must have format 'x,y'")
        elif action_type == "Mouse Right Click":
            try:
                x, y = map(int, action_value.split(','))
                pyautogui.rightClick(x, y)
            except ValueError:
                messagebox.showerror("Error", "Mouse Right Click must have format 'x,y'")
        elif action_type == "Keyboard Arrow Key" or action_type == "Keyboard Special Key":
            key = getattr(keyboard.Key, action_value)
            keyboard_controller.press(key)
            keyboard_controller.release(key)
        elif action_type == "Keyboard Input":
            for char in action_value:
                keyboard_controller.type(char)
        elif action_type in ["Mouse Drag", "Mouse Right Drag"]:
            try:
                start_coords, end_coords = action_value.split(' to ')
                start_x, start_y = map(int, start_coords.split(','))
                end_x, end_y = map(int, end_coords.split(','))
                pyautogui.moveTo(start_x, start_y)
                pyautogui.dragTo(end_x, end_y, button=('left' if action_type == "Mouse Drag" else 'right'), duration=1)  # Ensure the drag lasts enough
            except ValueError:
                messagebox.showerror("Error", f"{action_type} must have format 'start_x,start_y to end_x,end_y'")
        else:
            messagebox.showerror("Error", f"Unknown action type: {action_type}")

    def save_steps(self):
        steps_to_save = []
        for step_type_combobox, step_entry, _ in self.steps:
            action_type = step_type_combobox.get()
            action_value = step_entry.get()
            steps_to_save.append({"type": action_type, "value": action_value})

        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "w") as file:
                json.dump(steps_to_save, file)
            messagebox.showinfo("Success", "Steps saved successfully")

    def load_steps(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "r") as file:
                loaded_steps = json.load(file)

            for step in self.steps:
                step[2].destroy()
            self.steps.clear()

            for step in loaded_steps:
                self.add_step(step["type"], step["value"])

    def toggle_listening(self):
        if not self.recording:
            self.recording = True
            self.listen_button.config(text="Stop Listening")
            self.mouse_listener = mouse.Listener(on_click=self.on_click)
            self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
            try:
                self.mouse_listener.start()
                self.keyboard_listener.start()
            except Exception as e:
                messagebox.showerror('Error', f"Failed to start listeners: {e}") 
        else:
            self.recording = False
            self.listen_button.config(text="Start Listening")
            if self.mouse_listener:
                try:
                    self.mouse_listener.stop()
                except Exception as e:
                    messagebox.showerror('Error', f"Failed to start listeners: {e}") 
                self.mouse_listener = None
            if self.keyboard_listener:
                try:
                    self.keyboard_listener.stop()
                except Exception as e:
                    messagebox.showerror('Error', f"Failed to start listeners: {e}") 
                self.keyboard_listener = None


    def on_click(self, x, y, button, pressed):
        if self.recording:
            window_x1 = self.root.winfo_rootx()
            window_y1 = self.root.winfo_rooty()
            window_x2 = window_x1 + self.root.winfo_width()
            window_y2 = window_y1 + self.root.winfo_height()

            
            if window_x1 <= x <= window_x2 and window_y1 <= y <= window_y2:
                return  

            if pressed:
                # Record starting mouse position and time
                self.mouse_press_time = time.time()
                self.start_x, self.start_y = x, y
            else:
                # Check how long the mouse was pressed
                if time.time() - self.mouse_press_time > 0.5:
                    # It's a drag
                    end_x, end_y = x, y
                    if button == mouse.Button.left:
                        drag_action = f"{self.start_x},{self.start_y} to {end_x},{end_y}"
                        self.add_step("Mouse Drag", drag_action)
                    elif button == mouse.Button.right:
                        drag_action = f"{self.start_x},{self.start_y} to {end_x},{end_y}"
                        self.add_step("Mouse Right Drag", drag_action)
                else:
                    # It's a click
                    if button == mouse.Button.left:
                        self.add_step("Mouse Click", f"{x},{y}")
                    elif button == mouse.Button.right:
                        self.add_step("Mouse Right Click", f"{x},{y}")

    def on_press(self, key):
        if self.recording:
            try:
                if hasattr(key, 'char') and key.char:
                    self.add_step("Keyboard Input", key.char)
                else:
                    self.add_step("Keyboard Special Key", key.name)
            except AttributeError:
                pass

        if key == keyboard.Key.esc:
            self.paused = not self.paused
            self.root.after(0, lambda: messagebox.showinfo('Info', 'Automation paused/resumed!'))

    def clear_all_steps(self):
        for _, _, step_frame in self.steps:
            step_frame.destroy()
        self.steps.clear()


        self.main_frame.canvas.update_idletasks()
        self.main_frame.canvas.configure(scrollregion=self.main_frame.canvas.bbox("all"))

if __name__ == "__main__":
    root = tb.Window(themename='darkly')
    root.geometry('1200x800')
    app = AutomationApp(root)
    root.mainloop()
