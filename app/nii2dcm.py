"""
Make DICOM from isotropic reconstruction nifti data.
Use axial DICOM as the reference dicom

See README.md for usage & license
"""

import pydicom as pyd
import nibabel as nib
import matplotlib.pyplot as plt
import numpy as np

def nii2dcm(nii_in, dcm_in, dcm_out, series_num=None, series_description=None):
    
    FLYWHEEL_BASE = "/flywheel/v0"
    INPUT_DIR = (FLYWHEEL_BASE + "/input/input/")
    OUTPUT_DIR = (FLYWHEEL_BASE + "/output")
    WORK = (FLYWHEEL_BASE + "/work")
    dcm_out = OUTPUT_DIR + '/' + dcm_out + '.dcm'

    dcm = pyd.read_file(dcm_in)
    dcm2 = dcm.copy()
    
    nii = nib.load(nii_in)
    nii_img = np.transpose(nii.get_fdata(), [2,1,0])
    nii_img = np.flip(nii_img, axis=[1,2])

    c_img = nii_img.copy(order='C')

    dcm2.NumberOfFrames = c_img.shape[0]
    dcm2.Rows = c_img.shape[1]
    dcm2.Columns = c_img.shape[2]

    c_img = c_img.astype(np.float16)
    c_img /= np.max(c_img) * 2**16 # Scale to DICOM max range
    dcm2.PixelData = c_img.tobytes()

    # Change UUIDs for a lot of tags...
    dcm2.PixelSpacing
    dcm2.PixelSpacing = list(nii.header['pixdim'][1:3])
    dcm2.SliceThickness = nii.header['pixdim'][3]
    imgtype = dcm2.ImageType 
    imgtype[0] = 'DERIVED'
    dcm2.ImageType = imgtype

    # (0018, 0050) Slice Thickness
    dcm2[0x5200, 0x9229][0][0x0028, 0x9110][0][0x0018, 0x0050].value = dcm2.SliceThickness
    # (0028, 0030) Pixel Spacing
    dcm2[0x5200, 0x9229][0][0x0028, 0x9110][0][0x0028, 0x0030].value = dcm2.PixelSpacing

    nslices = dcm2.NumberOfFrames
    FOV_max = nslices * dcm2.SliceThickness

    nframes = len(dcm2.PerFrameFunctionalGroupsSequence)
    nadd = nslices - nframes

    frame_ref = dcm2.PerFrameFunctionalGroupsSequence[0].to_json()
    for i in range(nadd):
        dcm2.PerFrameFunctionalGroupsSequence.append(pyd.Dataset.from_json(frame_ref))

    # Check orientation
    pat_orient = None
    orient = dcm2[0x5200, 0x9229][0][0x0020, 0x9116][0][0x0020, 0x0037].value
    orient = [round(x) for x in orient]
    if orient == [1,0,0,0,1,0]:
        pat_orient = 'Axi'
    elif orient == [1,0,0,0,0,-1]:
        pat_orient = 'Cor'
    elif orient == [0,1,0,0,0,-1]:
        pat_orient = 'Sag'

    
    for i in range(nslices):
        # (0020, 9057) In-Stack Position Number
        dcm2.PerFrameFunctionalGroupsSequence[i][0x0020, 0x9111][0][0x0020, 0x9057].value = i+1

        # (0020, 9157) Dimension Index Values
        dcm2.PerFrameFunctionalGroupsSequence[i][0x0020, 0x9111][0][0x0020, 0x9157].value = [1,i+1]

        # (0020, 0032) Image Position (Patient)
        if pat_orient == 'Axi':
            pos = [0,0, dcm2.SliceThickness*i - FOV_max]
        elif pat_orient == 'Cor':
            pos = [0, dcm2.SliceThickness*i, 0]
        elif pat_orient == 'Sag':
            pos = [dcm2.SliceThickness*i, 0, 0]

        dcm2.PerFrameFunctionalGroupsSequence[i][0x0020, 0x9113][0][0x0020, 0x0032].value = pos
        
    new_uid = pyd.uid.generate_uid()
    dcm2.SOPInstanceUID = new_uid
    dcm2.file_meta[0x0002, 0x0003].value = new_uid

    if series_num:
        dcm2.SeriesNumber = series_num
    else:
        dcm2.SeriesNumber = str(dcm2.SeriesNumber) + '001'

    if series_description:
        dcm2.SeriesDescription = series_description


    dcm2.SeriesInstanceUID = pyd.uid.generate_uid()

    dcm2.save_as(dcm_out)

