import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import json
import os
import threading
import queue
import winsound

import sounddevice as sd
import pyttsx3
from vosk import Model, KaldiRecognizer
from plyer import notification


# ---------- VOICE ----------

tts = pyttsx3.init()

def speak(text):
    tts.say(text)
    tts.runAndWait()


model = Model(r"D:\model")

recognizer = KaldiRecognizer(
    model,
    16000
)

audio_queue = queue.Queue()

listening = False



def audio_callback(indata, frames, time, status):
    audio_queue.put(bytes(indata))



# ---------- DATA ----------

FILE = "medicines.json"

medicines = []

triggered = set()



def load_data():

    global medicines

    if os.path.exists(FILE):

        with open(FILE,"r") as f:
            medicines = json.load(f)



def save_data():

    with open(FILE,"w") as f:
        json.dump(
            medicines,
            f,
            indent=4
        )



# ---------- UI ----------

root = tk.Tk()

root.title(
    "💊 Smart Medicine Assistant"
)

root.geometry(
    "700x800"
)

root.configure(
    bg="#0b1220"
)



# ---------- HEADER ----------

tk.Label(
    root,
    text="💊 Smart Medicine Assistant",
    font=("Arial",24,"bold"),
    fg="white",
    bg="#0b1220"
).pack(pady=15)



clock = tk.Label(
    root,
    font=("Arial",16),
    fg="#4ade80",
    bg="#0b1220"
)

clock.pack()



def update_clock():

    clock.config(
        text="🕒 "+datetime.now().strftime("%H:%M:%S")
    )

    root.after(
        1000,
        update_clock
    )



# ---------- INPUT ----------

box=tk.Frame(
    root,
    bg="#172033",
    padx=20,
    pady=15
)

box.pack(
    padx=30,
    pady=20,
    fill="x"
)



name=tk.Entry(
    box,
    font=("Arial",12)
)

name.pack(
    fill="x",
    pady=5
)

name.insert(
    0,
    "Medicine name"
)



time=tk.Entry(
    box,
    font=("Arial",12)
)

time.pack(
    fill="x",
    pady=5
)

time.insert(
    0,
    "HH:MM"
)



# ---------- LIST ----------

list_frame=tk.Frame(
    root,
    bg="#0b1220"
)

list_frame.pack(
    fill="both",
    expand=True
)



def show_list():

    for w in list_frame.winfo_children():
        w.destroy()



    for i,m in enumerate(medicines):


        card=tk.Frame(
            list_frame,
            bg="#1e293b",
            padx=15,
            pady=12
        )

        card.pack(
            fill="x",
            padx=30,
            pady=6
        )



        tk.Label(
            card,
            text="💊 "+m["name"],
            fg="white",
            bg="#1e293b",
            font=("Arial",14,"bold")
        ).pack(anchor="w")



        tk.Label(
            card,
            text="⏰ "+m["time"],
            fg="white",
            bg="#1e293b"
        ).pack(anchor="w")



        tk.Label(
            card,
            text=m["status"],
            fg="#facc15" if m["status"]=="Pending" else "#4ade80",
            bg="#1e293b"
        ).pack(anchor="w")



        tk.Button(
            card,
            text="Done ✓",
            command=lambda x=i:complete(x)
        ).pack(side="left")



        tk.Button(
            card,
            text="Delete",
            command=lambda x=i:delete(x)
        ).pack(side="left")



def complete(i):

    medicines[i]["status"]="Completed"

    save_data()

    show_list()



def delete(i):

    medicines.pop(i)

    save_data()

    show_list()



# ---------- ADD ----------


def add():

    medicines.append(
        {
        "name":name.get(),
        "time":time.get(),
        "status":"Pending"
        }
    )

    save_data()

    show_list()

    speak(
        "Medicine added"
    )



# ---------- VOICE ----------


def voice_process():

    global listening

    listening=True


    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=audio_callback
    ):

        step=0


        while listening:


            data=audio_queue.get()


            if recognizer.AcceptWaveform(data):

                result=json.loads(
                    recognizer.Result()
                )


                text=result.get(
                    "text",
                    ""
                )


                if text:


                    if step==0:

                        name.delete(
                            0,
                            tk.END
                        )

                        name.insert(
                            0,
                            text
                        )

                        step=1



                    else:

                        time.delete(
                            0,
                            tk.END
                        )

                        time.insert(
                            0,
                            text
                        )

                        break




def start_voice():

    threading.Thread(
        target=voice_process,
        daemon=True
    ).start()



# ---------- ALARM ----------


def check_alarm():

    now=datetime.now().strftime("%H:%M")


    for m in medicines:


        key=m["name"]+m["time"]


        if (
            m["time"]==now
            and m["status"]=="Pending"
            and key not in triggered
        ):


            triggered.add(key)


            winsound.Beep(
                1200,
                1000
            )


            notification.notify(
                title="💊 Medicine Reminder",
                message="Take "+m["name"],
                timeout=5
            )


            popup=tk.Toplevel(root)

            popup.title(
                "Reminder"
            )


            tk.Label(
                popup,
                text="💊 Take "+m["name"],
                font=("Arial",18)
            ).pack(
                padx=40,
                pady=30
            )



            tk.Button(
                popup,
                text="Taken ✓",
                command=lambda:popup.destroy()
            ).pack(pady=10)



    root.after(
        1000,
        check_alarm
    )



# ---------- BUTTONS ----------


tk.Button(
    root,
    text="➕ Add Medicine",
    command=add,
    width=20
).pack(pady=5)



tk.Button(
    root,
    text="🎤 Voice Assistant",
    command=start_voice,
    width=20
).pack()



# ---------- START ----------

load_data()

show_list()

update_clock()

check_alarm()


speak(
    "Assistant started"
)


root.mainloop()