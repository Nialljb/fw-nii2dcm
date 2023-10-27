"""Parser module to parse gear config.json."""

import flywheel
from typing import Tuple
from flywheel_gear_toolkit import GearToolkitContext
import json
import os
from utils.parser import get_dicom


def parse_config(
    gear_context: GearToolkitContext,
) -> Tuple[str, bool, bool, bool, bool, bool]:
    """Parses the config info.
    Args:
        gear_context: Context.

    Returns:
        Tuple of input, dcm, out, series, desc
    """
    input = gear_context.get_input_path("input")
    dcm = gear_context.config.get("dcm")
    out = gear_context.config.get("prefix")
    series = gear_context.config.get("series")
    desc = gear_context.config.get("desc")

    if dcm is None:
        # raise Exception("dcm is required")
        print("No dcm file provided. Will look for T2w AXI as default")
        dcm = get_dicom()

    return input, dcm, out, series, desc

# If no reference DICOM is provided, use the T2w AXI DICOM as default
def get_dicom():
    # Read config.json file
    p = open('/flywheel/v0/config.json')
    config = json.loads(p.read())
    # Read API key in config file
    api_key = (config['inputs']['api-key']['key'])
    fw = flywheel.Client(api_key=api_key)

    # Get the input file id
    input_file_id = (config['inputs']['input']['hierarchy']['id'])
    print("input_file_id is : ", input_file_id)
    input_container = fw.get(input_file_id)

    # Get the session id from the input file id
    # & extract the session container
    session_id = input_container.parents['session']
    session_container = fw.get(session_id)
    session = session_container.reload()
    print("subject label: ", session.subject.label)
    print("session label: ", session.label)

    # Get the acquisition id from the session container
    for acq in session_container.acquisitions.iter():
        # print(acq.label)
        acq = acq.reload()
        if 'T2' in acq.label and 'AXI' in acq.label and 'Segmentation' not in acq.label: 
            for file_obj in acq.files: # get the files in the acquisition
                # Screen file object information & download the desired file
                if file_obj['type'] == 'dicom':
                    download_dir = ('/flywheel/v0/input/input/')
                    if not os.path.exists(download_dir):
                        os.mkdir(download_dir)
                    download_path = download_dir + '/' + file_obj.name
                    file_obj.download(download_path)

    dcm = download_path
    return dcm


# import argparse

# def read_args():
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--dcm', help='Reference dicom', required=True)
#     parser.add_argument('--nii', help='Nifti image', required=True)
#     parser.add_argument('--series', help='Series number. Default will append to ref dcm 001', required=False)
#     parser.add_argument('--desc', help='Series description. Default is to append "fromNII"', required=False, type=str)
#     parser.add_argument('--out', help='Output dicom', required=True)
#     args = parser.parse_args()
#     return args