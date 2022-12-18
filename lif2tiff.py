import os
import glob

import click
import numpy as np
from readlif.reader import LifFile
from tifffile import imwrite, imshow, TiffWriter


@click.command()
@click.option(
    "--directory",
    required=True,
    help="""Directory containing 'lif' folder. A subdirectory 'tiff' will be created to store output files.""",
)
def convertLifs(directory):
    # raise an exception if the lif input folder does not exist
    lifDir = os.path.join(directory, "lif")
    if not os.path.exists(lifDir):
        raise Exception(f"Expected a folder called 'lif' within {directory}")
    # create output hdf5 folder if it does not exist
    tiffDir = os.path.join(directory, "tiff")
    if not os.path.exists(tiffDir):
        os.mkdir(tiffDir)
    # get all lif files
    lifList = glob.glob(f"{lifDir}/*.lif")
    # iterate over each lif and split/store channels in tiff format
    for lifPath in lifList:
        lif = LifFile(lifPath)
        lifName = os.path.basename(lifPath).split(".")[0]
        # img 1 seems to be the merged image for the file I tested, this assumption might be wrong.
        img = lif.get_image(1)
        nZ = img.dims.z
        nC = img.channels
        zStacks = []
        for z in range(0, nZ):
            zStacks.append(
                np.array(
                    [
                        np.array(img.get_frame(z=z, c=0)),
                        np.array(img.get_frame(z=z, c=1)),
                        np.array(img.get_frame(z=z, c=2)),
                    ]
                )
            )
        tifPath = os.path.join(tiffDir, f"{lifName}.tif")
        imwrite(tifPath, np.array(zStacks), shape=np.shape(zStacks))


if __name__ == "__main__":
    convertLifs()
