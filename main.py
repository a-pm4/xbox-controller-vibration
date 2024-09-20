import ctypes
import time
import threading
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

xinput = ctypes.windll.xinput1_4
XINPUT_GAMEPAD_A = 0x1000
XINPUT_GAMEPAD_X = 0x4000
XINPUT_GAMEPAD_LEFT_SHOULDER = 0x0100  
XINPUT_GAMEPAD_RIGHT_SHOULDER = 0x0200  

class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [("wButtons", ctypes.c_ushort),
                ("bLeftTrigger", ctypes.c_ubyte),
                ("bRightTrigger", ctypes.c_ubyte),
                ("sThumbLX", ctypes.c_short),
                ("sThumbLY", ctypes.c_short),
                ("sThumbRX", ctypes.c_short),
                ("sThumbRY", ctypes.c_short)]

class XINPUT_STATE(ctypes.Structure):
    _fields_ = [("dwPacketNumber", ctypes.c_ulong),
                ("Gamepad", XINPUT_GAMEPAD)]

def get_state(controller):
    state = XINPUT_STATE()
    result = xinput.XInputGetState(controller, ctypes.byref(state))
    if result == 0:  
        return state
    else:
        return None

class XINPUT_VIBRATION(ctypes.Structure):
    _fields_ = [("wLeftMotorSpeed", ctypes.c_ushort),
                ("wRightMotorSpeed", ctypes.c_ushort)]

def set_vibration(controller, left_motor, right_motor):
    vibration = XINPUT_VIBRATION(int(left_motor * 65535), int(right_motor * 65535))
    xinput.XInputSetState(controller, ctypes.byref(vibration))

class XboxControllerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Xbox Controller Vibration")
        self.root.geometry('800x400')

        self.controller = 0
        self.vibration_running = False
        self.a_button_pressed = False  
        self.x_button_pressed = False  
        self.left_trigger_pressed = False
        self.right_trigger_pressed = False
        self.left_shoulder_pressed = False
        self.right_shoulder_pressed = False
        self.left_motor_enabled = ttk.BooleanVar(value=True)
        self.right_motor_enabled = ttk.BooleanVar(value=True)
        self.left_motor_intensity = ttk.DoubleVar(value=0.0)
        self.right_motor_intensity = ttk.DoubleVar(value=0.0)

        self.mainframe = ttk.Frame(root, padding=20)
        self.mainframe.pack(expand=True)

        self.toggle_button = ttk.Button(self.mainframe, text="Start Vibration", command=self.toggle_vibration, bootstyle='success-outline', width=20)
        self.toggle_button.pack(pady=20)

        self.motors_frame = ttk.Frame(self.mainframe)
        self.motors_frame.pack(pady=10)

        self.left_motor_frame = ttk.Frame(self.motors_frame)
        self.left_motor_frame.grid(column=0, row=0, padx=30)

        self.left_motor_checkbox = ttk.Checkbutton(self.left_motor_frame, text="Left Motor", variable=self.left_motor_enabled, command=self.update_vibration, bootstyle='primary')
        self.left_motor_checkbox.pack(anchor=CENTER, pady=5)

        ttk.Label(self.left_motor_frame, text="Intensity", bootstyle='info').pack(anchor=CENTER)
        self.left_motor_slider = ttk.Scale(self.left_motor_frame, from_=0, to=1, orient=HORIZONTAL, length=250, variable=self.left_motor_intensity, command=lambda val: self.update_vibration(), bootstyle='info')
        self.left_motor_slider.pack(pady=10)
        
        self.left_intensity_label = ttk.Label(self.left_motor_frame, text="0%", bootstyle='info')
        self.left_intensity_label.pack(anchor=CENTER)

        self.right_motor_frame = ttk.Frame(self.motors_frame)
        self.right_motor_frame.grid(column=1, row=0, padx=30)

        self.right_motor_checkbox = ttk.Checkbutton(self.right_motor_frame, text="Right Motor", variable=self.right_motor_enabled, command=self.update_vibration, bootstyle='primary')
        self.right_motor_checkbox.pack(anchor=CENTER, pady=5)

        ttk.Label(self.right_motor_frame, text="Intensity", bootstyle='info').pack(anchor=CENTER)
        self.right_motor_slider = ttk.Scale(self.right_motor_frame, from_=0, to=1, orient=HORIZONTAL, length=250, variable=self.right_motor_intensity, command=lambda val: self.update_vibration(), bootstyle='info')
        self.right_motor_slider.pack(pady=10)
        
        self.right_intensity_label = ttk.Label(self.right_motor_frame, text="0%", bootstyle='info')
        self.right_intensity_label.pack(anchor=CENTER)

        self.vibration_thread = None
        self.controller_thread = threading.Thread(target=self.listen_to_controller)
        self.controller_thread.daemon = True
        self.controller_thread.start()

    def toggle_vibration(self):
        if self.vibration_running:
            self.stop_vibration()
        else:
            self.start_vibration()

    def start_vibration(self):
        self.vibration_running = True
        self.toggle_button.config(text="Stop Vibration")
        self.vibration_thread = threading.Thread(target=self.vibrate_controller)
        self.vibration_thread.start()

    def stop_vibration(self):
        self.vibration_running = False
        self.toggle_button.config(text="Start Vibration")
        if self.vibration_thread is not None:
            self.vibration_thread.join()
        set_vibration(self.controller, 0, 0)

    def vibrate_controller(self):
        while self.vibration_running:
            left_motor_value = self.left_motor_intensity.get() if self.left_motor_enabled.get() else 0
            right_motor_value = self.right_motor_intensity.get() if self.right_motor_enabled.get() else 0
            set_vibration(self.controller, left_motor_value, right_motor_value)
            time.sleep(0.1)

    def update_vibration(self):
        if self.vibration_running:
            left_motor_value = self.left_motor_intensity.get() if self.left_motor_enabled.get() else 0
            right_motor_value = self.right_motor_intensity.get() if self.right_motor_enabled.get() else 0
            set_vibration(self.controller, left_motor_value, right_motor_value)
        self.left_intensity_label.config(text="{:.0f}%".format(self.left_motor_intensity.get() * 100))
        self.right_intensity_label.config(text="{:.0f}%".format(self.right_motor_intensity.get() * 100))

    def listen_to_controller(self):
        while True:
            state = get_state(self.controller)
            if state:
                if state.Gamepad.wButtons & XINPUT_GAMEPAD_A:
                    if not self.a_button_pressed:  
                        self.a_button_pressed = True
                        self.toggle_vibration()
                else:
                    self.a_button_pressed = False  
                
                if state.Gamepad.wButtons & XINPUT_GAMEPAD_X:
                    if not self.x_button_pressed:
                        self.x_button_pressed = True
                        self.left_motor_intensity.set(0.1)
                        self.right_motor_intensity.set(0.1)
                        self.update_vibration()
                else:
                    self.x_button_pressed = False  
                
                if state.Gamepad.bLeftTrigger > 0:
                    if not self.left_trigger_pressed:
                        self.left_trigger_pressed = True
                        new_left_intensity = min(self.left_motor_intensity.get() + 0.1, 1.0)
                        self.left_motor_intensity.set(new_left_intensity)
                        self.update_vibration()
                else:
                    self.left_trigger_pressed = False  
                
                if state.Gamepad.bRightTrigger > 0:
                    if not self.right_trigger_pressed:
                        self.right_trigger_pressed = True
                        new_right_intensity = min(self.right_motor_intensity.get() + 0.1, 1.0)
                        self.right_motor_intensity.set(new_right_intensity)
                        self.update_vibration()
                else:
                    self.right_trigger_pressed = False  
                
                if state.Gamepad.wButtons & XINPUT_GAMEPAD_LEFT_SHOULDER:
                    if not self.left_shoulder_pressed:
                        self.left_shoulder_pressed = True
                        new_left_intensity = max(self.left_motor_intensity.get() - 0.1, 0.0)
                        self.left_motor_intensity.set(new_left_intensity)
                        self.update_vibration()
                else:
                    self.left_shoulder_pressed = False  
                
                if state.Gamepad.wButtons & XINPUT_GAMEPAD_RIGHT_SHOULDER:
                    if not self.right_shoulder_pressed:
                        self.right_shoulder_pressed = True
                        new_right_intensity = max(self.right_motor_intensity.get() - 0.1, 0.0)
                        self.right_motor_intensity.set(new_right_intensity)
                        self.update_vibration()
                else:
                    self.right_shoulder_pressed = False  
            time.sleep(0.1)

if __name__ == "__main__":
    root = ttk.Window(themename='darkly')
    app = XboxControllerApp(root)
    root.mainloop()