import os
import glob

import h5py
import click
import numpy as np
from readlif.reader import LifFile


@click.command()
@click.option(
    "--directory",
    required=True,
    help="""Directory containing 'lif' folder. A subdirectory 'h5' will be created to store output files.""",
)
def convertLifs(directory):
    # raise an exception if the lif input folder does not exist
    lifDir = os.path.join(directory, "lif")
    if not os.path.exists(lifDir):
        raise Exception(f"Expected a folder called 'lif' within {directory}")
    # create output hdf5 folder if it does not exist
    h5Dir = os.path.join(directory, "h5")
    if not os.path.exists(h5Dir):
        os.mkdir(h5Dir)
    # get all lif files
    lifList = glob.glob(f"{lifDir}/*.lif")
    # iterate over each lif and split/store channels in h5fd format
    for lifPath in lifList:
        lif = LifFile(lifPath)
        lifName = os.path.basename(lifPath).split(".")[0]
        # img 1 seems to be the merged image for the file I tested, this assumption might be wrong.
        img = lif.get_image(1)
        nZ = img.dims.z
        nC = img.channels
        # iterate over each channel to save all Z layers together as an h5ad file
        for c in range(0, nC):
            zStack = []
            for z in range(0, nZ):
                zStack.append(np.array(img.get_frame(z=z, c=c)))
            channel = np.array(zStack)
            h5Name = f"{lifName}_{c}.h5"
            h5Path = os.path.join(h5Dir, h5Name)
            with h5py.File(h5Path, "w") as f:
                grp = f.create_group("t0")
                dset = grp.create_dataset(
                    f"channel{c}", channel.shape, dtype="i", chunks=True
                )
                dset[...] = channel


if __name__ == "__main__":
    convertLifs()
