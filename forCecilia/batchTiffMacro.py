import os
import re

import click


@click.command()
@click.option(
    "--exec",
    required=True,
    help="""Path to ImageJ exec.""",
)
@click.option(
    "--macro",
    required=True,
    help="""Path to the ImageJ/Fiji macro to be run in batch.""",
)
@click.option(
    "--directory",
    required=True,
    help="""Directory containing 'tiff' folder.""",
)
def runMacro(exec, macro, directory):
    # raise an exception if the tiff input folder does not exist
    tiffDir = os.path.join(directory, "tiff")
    if not os.path.exists(tiffDir):
        raise Exception(f"Expected a folder called 'tiff' within {directory}")
    # get all tiff files
    files = os.listdir(tiffDir)
    tiffFilesEdu = list(glob_re(r".*2_00_EdU_probability.tiff", files))
    tiffFilesGene = list(glob_re(r".*1_00_17258_probability.tiff", files))
    # get the file "prefix" without the variable ending
    eduPrefixes = [
        eduTiff.split("_2_00_EdU_probability.tiff")[0] for eduTiff in tiffFilesEdu
    ]
    genePrefixes = [
        geneTiff.split("_1_00_17258_probability.tiff")[0] for geneTiff in tiffFilesGene
    ]
    # build a list of complete 17258 and EdU pairs - their common prefix will be passed to the macro
    pathPrefixes = []
    for eduPrefix in eduPrefixes:
        for genePrefix in genePrefixes:
            if eduPrefix == genePrefix:
                pathPrefix = os.path.join(tiffDir, eduPrefix)
                pathPrefixes.append(pathPrefix)
    for pathPrefix in pathPrefixes:
        cmd = f"{exec} -macro {macro} {pathPrefix}"
        print(cmd)
        os.system(cmd)


def glob_re(pattern, strings):
    return filter(re.compile(pattern).match, strings)


if __name__ == "__main__":
    runMacro()
