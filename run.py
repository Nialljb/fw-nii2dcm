#!/usr/bin/env python
"""The run script"""
import logging
from flywheel_gear_toolkit import GearToolkitContext
from utils.parser import parse_config
from app.nii2dcm import nii2dcm

# Set up logging
log = logging.getLogger(__name__)

# Define main function
def main(context: GearToolkitContext) -> None:

    # Get the input files
    input, dcm, out, series, desc = parse_config()
    # Run the nii2dcm function
    nii2dcm(input, dcm, out, series, desc)

# Only execute if file is run as main, not when imported by another module
if __name__ == "__main__":  # pragma: no cover
    # Get access to gear config, inputs, and sdk client if enabled.
    with GearToolkitContext() as gear_context:
        # Initialize logging, set logging level based on `debug` configuration
        # key in gear config.
        gear_context.init_logging()
        # Pass the gear context into main function defined above.
        main(gear_context)