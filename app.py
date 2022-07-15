import ctypes
import tkinter as tk
import os
import tkinter.ttk
import tkinter.font as font
import numpy as np

import h5py

import Dicom
from PIL import Image, ImageTk
import ogl_represent

# imports from other modules

# Dicom

# imports from other modules end

# global variables

pixel_data_new_visualization = None
pixel_data_for_display = None
spacing_data = None
pixel_data_threshold = None
threshold = False

left_panel = None
studies = None

second_study_frame = None
second_visu_frame = None
right_frame = None

img_canvas = None
image_container = None
width = None
height = None

slider_slice = None
slider_1 = None
slider_2 = None

threshold_button = None

new_visu_name_entry = None

visu_type = False
visu_type_label = None

study_btt_dict = {}
visu_btt_dict = {}


# button callbacks

def size(call):
    print(root.winfo_screenwidth(), root.winfo_screenheight())
    print(call)
    root.after(3000, size, call + 1)


def clear_right_frame():
    for widget in right_frame.winfo_children():
        widget.destroy()


def update_image_canvas_with_array(a):
    # print(pixel_data_new_visualization.shape)
    # print(pixel_data_new_visualization[16])
    # print(n_slice)
    global slider_1, slider_2, slider_slice, width, height
    n_slice = slider_slice.get()
    # print(n_slice)
    w, h = int(width), int(height)
    if threshold:
        val1, val2 = slider_1.get(), slider_2.get()
        val1_bigger = val1 > val2

        current_slice = pixel_data_new_visualization[int(n_slice)]
        if val1_bigger:
            slice_threshold = (current_slice <= val1) * (current_slice >= val2)
        else:
            slice_threshold = (current_slice <= val2) * (current_slice >= val1)

        new_img = Image.fromarray(slice_threshold)
        # new_img = Image.frombytes('L', slice_threshold.shape, slice_threshold)

    else:
        # new_img = Image.fromarray(pixel_data_new_visualization[int(n_slice)])
        new_img = Image.fromarray(pixel_data_for_display[n_slice])

    new_img = new_img.resize((w, h), Image.ANTIALIAS)

    new_img = ImageTk.PhotoImage(image=new_img)
    root.new_img = new_img
    img_canvas.itemconfig(image_container, image=new_img)

    # print()


def change_visu_mode():
    global threshold, slider_slice, width, height

    # if threshold mode was activated, activate normal mode and change button text accordingly
    if threshold:
        threshold_button.config(text="You are in normal\n view mode")
    else:
        threshold_button.config(text="You are in threshold\n view mode")

    threshold = not threshold
    update_image_canvas_with_array(1)


def populate_right_frame_new_visu(study_path):
    clear_right_frame()

    f = h5py.File(study_path + "/study.hdf5", 'r')

    global pixel_data_new_visualization, spacing_data, pixel_data_for_display, threshold

    # reset view to normal view
    threshold = False

    # set global variable to the pixel data that we get from the file
    pixel_data_new_visualization = f.get('pixel_data')[...]

    # this pixel data will be used to display in normal view, it has less color depth
    pixel_data_for_display = pixel_data_new_visualization.astype(np.uint8)

    # get spacing data from file
    spacing_data = f.get('spacing_data')[...]

    # close the file
    f.close()

    # get shape of volume of pixel data
    vol_shape = list(pixel_data_new_visualization.shape)

    # create a canvas with the shape of the image, add image object inside, it is empty at this stage
    global img_canvas, width, height
    width, height = vol_shape[1] * 2, vol_shape[2] * 2
    img_canvas = tk.Canvas(right_frame, width=width, height=height)
    img_canvas.pack(side="left", anchor="n")

    global image_container
    image_container = img_canvas.create_image(0, 0, anchor="nw")

    # create the sliders
    sliders_frame = tk.Frame(right_frame)
    sliders_frame.pack(side="left", anchor="nw", fill="x", expand=True)

    # global variables
    global slider_1, slider_2, slider_slice, threshold_button, new_visu_name_entry

    label_slice = tk.Label(sliders_frame, text="Slice selector")
    label_slice.pack(side="top", anchor="nw", padx=5, pady=5, fill="x")
    slider_slice = tk.Scale(sliders_frame, from_=0, to=vol_shape[0] - 1,
                            orient="horizontal", tickinterval=vol_shape[0] / 4,
                            command=lambda a=1: update_image_canvas_with_array(a))
    slider_slice.pack(side="top", anchor="nw", padx=5, pady=5, fill="x")

    # calculate number of colors / shades
    shades = pixel_data_new_visualization.itemsize * 256

    # threshold slider 1
    label_1 = tk.Label(sliders_frame, text="Threshold 1")
    label_1.pack(side="top", anchor="nw", padx=5, pady=5, fill="x")
    slider_1 = tk.Scale(sliders_frame, from_=0, to=shades - 1,
                        orient="horizontal", tickinterval=shades / 4,
                        command=lambda a=1: update_image_canvas_with_array(a))
    slider_1.pack(side="top", anchor="nw", padx=5, pady=5, fill="x")

    # threshold slider 2
    label_2 = tk.Label(sliders_frame, text="Threshold 2")
    label_2.pack(side="top", anchor="nw", padx=5, pady=5, fill="x")
    slider_2 = tk.Scale(sliders_frame, from_=0, to=shades - 1,
                        orient="horizontal", tickinterval=shades / 4,
                        command=lambda a=1: update_image_canvas_with_array(a))
    slider_2.pack(side="top", anchor="nw", padx=5, pady=5, fill="x")

    # theshold mode button
    threshold_button = tk.Button(sliders_frame, text="You are in normal\n view mode",
                                 command=lambda: change_visu_mode())
    threshold_button.pack(padx=5, pady=5)

    # new visu name entry
    new_visu_name_entry = tk.Entry(sliders_frame)
    new_visu_name_entry.pack(padx=5, pady=5)

    # generate visu button
    generate_button = tk.Button(sliders_frame, text="Generate\nvisualization",
                                command=lambda i=new_visu_name_entry.get(), j=study_path: [
                                    Dicom.generate_volume_xyz(pixel_data_new_visualization,
                                                              spacing_data,
                                                              slider_1.get(), slider_2.get(), j,
                                                              new_visu_name_entry.get()),
                                    update_visu_frame_with_files(j)
                                ])
    generate_button.pack(padx=5, pady=5)

    # initially the first image is displayed
    update_image_canvas_with_array(1)


def update_visu_type_label():
    global visu_type, visu_type_label
    if visu_type_label is None:
        if not visu_type:
            visu_type_label = tk.Label(right_frame, text="Normal visualization", font=my_font)
        else:
            visu_type_label = tk.Label(right_frame, text="Active shutter visualization", font=my_font)
    else:
        if not visu_type:
            visu_type_label.config(text="Normal visualization")
        else:
            visu_type_label.config(text="Active shutter visualization")

    visu_type_label.pack(pady=(60, 0))


def change_visu_type():
    global visu_type
    # true = shutter false = normal
    visu_type = not visu_type

    print(visu_type)

    update_visu_type_label()


def get_visu_type():
    global visu_type
    return visu_type


def populate_right_frame_visu_type(filename, study_path):
    global visu_type, visu_type_label

    clear_right_frame()

    visu_type = None
    visu_type_label = None

    update_visu_type_label()

    change_mode = tk.Button(right_frame, text="Change visualization type", width=20, anchor="n", font=my_font,
                            command=change_visu_type)
    change_mode.pack(pady=(20, 0))

    start_visu_btt = tk.Button(right_frame, text="Start visualization", width=20, anchor="n", font=my_font,
                               command=lambda i=study_path, j=filename, k=visu_type: [ogl_represent.start_visualization(
                                   i + "/visualizations" + "/" + j, get_visu_type())])

    start_visu_btt.pack(pady=(20, 0))


def select_visu(filename):
    global visu_btt_dict
    for i in visu_btt_dict:
        visu_btt_dict[i].configure(bg="white")
    visu_btt_dict[filename].configure(bg="grey")


# needs to add a command to each of its buttons
def update_visu_frame_with_files(study_path):
    for widget in second_visu_frame.winfo_children():
        widget.destroy()

    global visu_btt_dict
    visu_btt_dict = {}

    clear_right_frame()

    new_visu_btt = tk.Button(second_visu_frame, text="+ new visualization", width=20, anchor="w", font=my_font,
                             command=lambda i=study_path: [populate_right_frame_new_visu(i),
                                                           select_visu("new_visu_btt")])
    new_visu_btt.pack(fill="x")

    visu_btt_dict["new_visu_btt"] = new_visu_btt

    global root
    for filename in os.listdir(study_path + "/visualizations"):
        new_btt = tk.Button(second_visu_frame, text=filename, width=20, anchor="w", font=my_font,
                            command=lambda i=filename, j=study_path:
                            [populate_right_frame_visu_type(i, j),
                             select_visu(i)])
        new_btt.pack(fill="x")
        visu_btt_dict[filename] = new_btt


def select_study(filename):
    global study_btt_dict
    for i in study_btt_dict:
        study_btt_dict[i].configure(bg="white")
    study_btt_dict[filename].configure(bg="grey")


def update_study_frame_with_files(all_studies_path):
    for widget in second_study_frame.winfo_children():
        widget.destroy()

    global study_btt_dict
    study_btt_dict = {}
    for filename in os.listdir(all_studies_path):
        new_btt = tk.Button(second_study_frame, text=filename, width=20, anchor="w", font=my_font,
                            command=lambda i=filename: [update_visu_frame_with_files("study_data/" + i),
                                                        select_study(i)])
        new_btt.pack(fill="x")

        study_btt_dict[filename] = new_btt


def add_update_study(read_path, name):
    Dicom.create_study(read_path, name)
    update_study_frame_with_files("study_data")


# create permanent elements
# Create the root window
root = tk.Tk()

# Set root title
root.title('Incada')

# Dpi awareness, set a common Dpi awareness between windows
ctypes.windll.shcore.SetProcessDpiAwareness(1)

# Set root size
root.geometry("2000x1100")
root.resizable(True, True)

# Set root background color
root.config(background="white")

# Create font
my_font = font.Font(size=15)

# LEFT PANEL
left_panel = tk.Frame(root, bg="black", width=600)
left_panel.pack(side="left", fill="y")

# IMPORTATION FRAME
import_frame = tk.Frame(left_panel, bg="grey", height=100)
import_frame.pack(pady=(3, 0), padx=3, fill="x")

# IMPORT PATH LABEL
import_frame_label = tk.Label(import_frame, background="white", text="Insert study path", width=16, font=my_font)
import_frame_label.pack(pady=(5, 0))

# READ PATH ENTRY
read_path_entry = tk.Entry(import_frame, background="white", font=my_font)
read_path_entry.pack(fill="x", pady=(5, 0), padx=10)

# IMPORT NAME LABEL
import_name_label = tk.Label(import_frame, background="white", text="Name for study", width=12, font=my_font)
import_name_label.pack(pady=(5, 0))

# IMPORT NAME ENTRY

import_name_entry = tk.Entry(import_frame, background="white", font=my_font)
import_name_entry.pack(fill="x", pady=(5, 0), padx=10)

# IMPORT STUDY BUTTON
import_study_btt = tk.Button(import_frame, text="IMPORT",
                             height=2, bg="white", fg="black", font=my_font,
                             command=lambda i=read_path_entry.get():
                             add_update_study(read_path_entry.get(), import_name_entry.get()))
import_study_btt.pack(pady=5)

# STUDY LIST
studies = tk.Frame(left_panel, bg="white", width=200)
studies.pack(fill="both", expand=True, side="left", pady=3, padx=3)

# Canvas
study_canvas = tk.Canvas(studies, width=250)
study_canvas.pack(side="left", fill="both")

# Add scrollbar to study_canvas
scrollbar_study = tkinter.ttk.Scrollbar(studies, orient="vertical",
                                        command=study_canvas.yview)
scrollbar_study.pack(side="right", fill="y")

# Configure study_canvas
study_canvas.configure(yscrollcommand=scrollbar_study.set)
study_canvas.bind('<Configure>', lambda e: study_canvas.configure(scrollregion=study_canvas.bbox("all")))

# New frame inside study_canvas
second_study_frame = tk.Frame(study_canvas)
second_study_frame.pack(fill="x")

# Add new frame to root in study_canvas
study_canvas.create_window((0, 0), window=second_study_frame, anchor="nw")

# VISUALIZATION LIST
visualizations = tk.Frame(root, width=150, bg="black")
visualizations.pack(fill="both", expand=False, side="left")

# Canvas
visu_canvas = tk.Canvas(visualizations, width=250)
visu_canvas.pack(side="left", fill="both", pady=3)

# Add scrollbar to visu_canvas
scrollbar_visu = tkinter.ttk.Scrollbar(visualizations, orient="vertical",
                                       command=visu_canvas.yview)
scrollbar_visu.pack(side="right", fill="y", pady=3, padx=(0, 3))

# Configure study_canvas
visu_canvas.configure(yscrollcommand=scrollbar_visu.set)
visu_canvas.bind('<Configure>', lambda e: visu_canvas.configure(scrollregion=visu_canvas.bbox("all")))

# New frame inside study_canvas
second_visu_frame = tk.Frame(visu_canvas)
second_visu_frame.pack(fill="x")

# Add new frame to root in study_canvas
visu_canvas.create_window((0, 0), window=second_visu_frame, anchor="nw")

# RIGHT FRAME
right_frame = tk.Frame(root, bg="grey")
right_frame.pack(fill="both", expand=True)

# first update
update_study_frame_with_files("study_data")

# main loop of application
root.mainloop()
