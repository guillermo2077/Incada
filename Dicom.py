import pydicom
import numpy as np
import os
import h5py


# Function called to import a new study, creates a new directory for said study inside "study data", inside that
# new directory writes a hdf5 file that will contain all pixel data from each ct scan slice.
# The hdf5 file format is indicated when large amounts of data need to be stored.
def create_study(read_path, name, open_f=False):
    # pixel data, here all pixels from the dicom file will be saved
    pixel_data = []

    # Count number of valid dicom files, file_count is the number of slices in the ct scan
    file_count = 0
    for file in os.scandir(read_path):
        file_count += 1

    # For each slice gets their pixel data, in the first one gets pixel spacing, slice thickness and image shape (size)
    parameters_obtained = False

    # Count is only used to print the number of images that have been read
    count = 0

    for i, filename in enumerate(os.scandir(read_path)):
        ds = pydicom.dcmread(filename)

        if not parameters_obtained:
            shape = [file_count, ds[0x0028, 0x0010].value, ds[0x0028, 0x0011].value]
            shape = tuple(shape)
            # print("Niveles, filas, columnas" + str(shape))
            pixel_data = np.empty(shape=shape)

            spacing = list(ds[0x0028, 0x0030].value)
            try:
                spacing.append(ds[0x0018, 0x0088].value)
            except:
                try:
                    spacing.append(ds[0x0018, 0x0050].value / 2)
                except:
                    spacing.append(spacing[0])

            print(spacing)

            parameters_obtained = True
            # print(ds.pixel_array.itemsize)
            print(ds)

        # Pixel data in position [i] is filled with the pixel array of the current slice
        pixel_data[i] = ds.pixel_array
        if open_f:
            pass
        else:
            pixel_data[i] = ds.pixel_array

        # + 1 to the number of files and print number of files
        count += 1

    # now, the data from this study will be saved to the relative path indicated by write_path
    write_path = "study_data/" + name

    # if the path is empty, a new directory is created and study data is saved inside
    # !!! if the path is not empty, nothing will be saved !!!
    if not os.path.exists(write_path):
        os.mkdir(write_path)
        os.mkdir(write_path + "/visualizations")
        with h5py.File(write_path + "/study.hdf5", "w") as f:
            dset_pixel = f.create_dataset("pixel_data", data=pixel_data)
            dset_spacing = f.create_dataset("spacing_data", data=spacing, dtype="float32")


def volume_threshold(vol, val_1, val_2):
    # remove open f
    # val1_bigger allows any threshold to be the upper or lower, instead of dedicated to either
    val1_bigger = val_1 > val_2

    if val1_bigger:
        vol_threshold = (vol <= val_1) * (vol >= val_2)
    else:
        vol_threshold = (vol <= val_2) * (vol >= val_1)

    return vol_threshold


# This function is called to create a new visualization file, that file will contain an XYZ point cloud, which is
# what is needed for the opengl representation
def generate_volume_xyz(vol, spacing, val_1, val_2, study_path, name):
    vol_threshold = volume_threshold(vol, val_1, val_2)

    # each point gets added to an array with their xyz coordinates in the format [x1, y1, z1, x2, y2, ...]
    xyz_data = np.argwhere(vol_threshold > 0).flatten().astype('float32')

    # the point cloud is centered on [0,0,0]
    mean_z = min(xyz_data[0::3]) + max(xyz_data[0::3]) / 2
    z = (xyz_data[0::3] - mean_z) / 18
    mean_x = min(xyz_data[1::3]) + max(xyz_data[1::3]) / 2
    x = (xyz_data[1::3] - mean_x) / 18
    mean_y = min(xyz_data[2::3]) + max(xyz_data[2::3]) / 2
    y = (xyz_data[2::3] - mean_y) / 18

    # proper order for xyz
    xyz_data[0::3] = x * spacing[0]
    xyz_data[1::3] = y * spacing[1]
    xyz_data[2::3] = z * spacing[2]

    # save the new visualization
    with h5py.File(study_path + "/visualizations" + "/" + name + ".hdf5", "w") as f:
        dset_xyz = f.create_dataset("xyz_data", data=xyz_data, dtype="float32")
