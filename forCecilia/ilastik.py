import os
import glob
import subprocess

import h5py
import click
import numpy as np
from readlif.reader import LifFile
import tifffile

# python ilastik.py --name EdU --ilastik "C:\Program Files\ilastik-1.3.3post3\ilastik.exe" --project C:\Users\Patrick\Desktop\Cecilia2Patrick\UTI_EPI_plusNTcData_EdU_Pixel_Classifier_06302022.ilp --directory C:\Users\Patrick\Desktop\Cecilia2Patrick --channel 2
# python ilastik.py --name 17258 --ilastik "C:\Program Files\ilastik-1.3.3post3\ilastik.exe" --project C:\Users\Patrick\Desktop\Cecilia2Patrick\MyProject17258_Classifier_Train_NTc_06292022.ilp --directory C:\Users\Patrick\Desktop\Cecilia2Patrick --channel 1


@click.command()
@click.option(
    "-n",
    "--name",
    required=True,
    type=str,
    help="Name to append to probability maps (Ex. EdU).",
)
@click.option(
    "-i",
    "--ilastik",
    required=True,
    type=str,
    help="Specify the path to ilastik (ex.C:\Program Files\ilastik-1.3.3post3\ilastik.exe).",
)
@click.option(
    "-p",
    "--project",
    required=True,
    type=str,
    help="Specify which ilastik project to process images with.",
)
@click.option(
    "-d",
    "--directory",
    required=True,
    type=str,
    help="Directory containing 'h5' folder. A subdirectory 'probability_maps' will be created to store output files.",
)
@click.option(
    "-c",
    "--channel",
    required=True,
    type=int,
    help="Specify which image channel to use with the trained ilastik project.",
)
def createProbabilityMaps(name, ilastik, directory, project, channel):
    # raise an exception if the h5 input folder does not exist
    h5Dir = os.path.join(directory, "h5")
    if not os.path.exists(h5Dir):
        raise Exception(f"Expected a folder called 'h5' within {directory}")
    tiffDir = os.path.join(directory, "tiff_probability_maps")
    if not os.path.exists(tiffDir):
        os.mkdir(tiffDir)
    h5List = glob.glob(f"{h5Dir}/*_{channel}.h5")
    h5Files = " ".join(h5List)
    # run ilastik in headless mode and provide all h5 files as input
    outputFormat = os.path.join(
        tiffDir, f"{{nickname}}_{{slice_index}}_{name}_probability.tiff"
    )
    cmd = f'{ilastik} --headless --project={project} --output_format="tiff sequence" --output_filename_format="{outputFormat}" {h5Files}'
    proc = subprocess.Popen(
        cmd
    )  # , shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.wait()
    print("done creating probability maps!")
    # removeBackgroundProbability(directory, tiffDir, channel, name)
    # print('done removing background from tiffs!')


def removeBackgroundProbability(directory, tiffDir, channel, name):
    fmtTiffDir = os.path.join(directory, "fmt_tiff_probability_maps")
    if not os.path.exists(fmtTiffDir):
        os.mkdir(fmtTiffDir)  # get all h5 files
    tiffList = glob.glob(f"{tiffDir}/*_{channel}_*_{name}_probability.tiff")
    for tiffPath in tiffList:
        tiff = tifffile.imread(tiffPath)
        tiff = tiff[:, :, 0]
        fileName = tiffPath.split("\\")[-1].split(".tiff")[0] + "_singlechannel.tiff"
        filePath = os.path.join(fmtTiffDir, fileName)
        tifffile.imwrite(filePath, tiff)


if __name__ == "__main__":
    createProbabilityMaps()
