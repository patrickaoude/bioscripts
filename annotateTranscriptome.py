import csv
import json
import re
import os
import requests
import time
import subprocess
import multiprocessing as mp
from tqdm import tqdm
from collections import Counter

import click
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from orffinder import orffinder

# python annotateTranscriptome -i /lab/solexa_reddien/Patrick/10X_Pharynx_scRNAseq/dd_Smed_v6_trimmed_custom.fasta -o dd_smed_v6.tsv

HMMSEARCHPATT = re.compile(
    "b'\s+(?P<full_e>[\de\-\.]+)\s+(?P<full_score>[\de\-\.]+)\s+(?P<full_bias>[\de\-\.]+)\s+(?P<best_domain_e>[\de\-\.]+)\s+(?P<best_domain_score>[\de\-\.]+)\s+(?P<best_domain_bias>[\de\-\.]+)\s+(?P<exp>[\de\-\.]+)\s+(?P<N>[\de\-\.]+)\s+(?P<model>[A-Za-z0-9-_]+)\s+(?P<description>[A-Za-z0-9\s_\-\(\)]+)"
)
HMMSEARCHPATTKEY = [
    "full_e",
    "full_score",
    "full_bias",
    "best_domain_e",
    "best_domain_score",
    "best_domain_bias",
    "exp",
    "N",
    "model",
    "description",
]
TMPDIR = "tmp"


@click.command()
@click.option(
    "-i",
    "--infile",
    required=True,
    type=str,
    help="Specify the fasta file containing sequences to annotate.",
)
@click.option(
    "-o",
    "--outfile",
    required=True,
    type=str,
    help="Specify the name of the tsv output file containing all annotations.",
)
@click.option(
    "-h",
    "--hmmerbin",
    type=str,
    default="/lab/solexa_reddien/Patrick/tools/hmmer-3.3.2/bin",
    help="Specify the path to hmmer's bin directory.",
)
@click.option(
    "-m",
    "--model",
    type=str,
    default="/lab/solexa_reddien/Patrick/tools/annotations/pfamIndexFiles/Pfam-A.hmm",
    help="Specify the path to the hmm model to use for annotations.",
)
@click.option(
    "-c",
    "--cores",
    type=int,
    default=mp.cpu_count(),
    help="Specify the number of CPUs or cores for parallel processing.",
)
@click.option(
    "-p",
    "--save_protein",
    type=bool,
    default=False,
    help="Also output a protein fasta file with all translated ORFs.",
)
def annotateSequences(infile, outfile, hmmerbin, model, cores, save_protein):
    sequences = SeqIO.parse(infile, "fasta")
    numSeqs = 0
    if save_protein:
        proteins = []
    if not os.path.exists(TMPDIR):
        os.mkdir(TMPDIR)
    with open(infile, "r") as f:
        numSeqs = f.read().count(">")
    with open(outfile, "w") as f:
        header = [
            "contig ID",
            "features",
            "descriptions",
            "no orf found",
            "no domains, repeats, motifs, or features found",
            "contig sequence",
            "translated sequence (orffinder)",
        ]
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(header)
        pool = mp.Pool(cores)
        results = []
        for result in tqdm(
            pool.imap_unordered(processSequence, sequences), total=numSeqs
        ):
            results.append(result)
        for r in results:
            writer.writerow(r)
            if save_protein:
                contig = r[0]
                sequence = r[6]
                if sequence is not None:
                    protein = SeqRecord(sequence, id=contig, name="", description="")
                    proteins.append(protein)
        pool.close()
    if save_protein:
        baseName = outfile.split(".")[0]
        SeqIO.write(proteins, f"{baseName}_protein.fasta", "fasta-2line")
    os.rmdir(TMPDIR)


def findDomains(record):
    c = click.get_current_context()
    hmmfile = c.params["model"]
    hmmerbin = c.params["hmmerbin"]
    scanPath = os.path.join(hmmerbin, "hmmscan")
    # make a temporary ORF sequence file
    orf = f"{record.id}.fasta"
    orfPath = os.path.join(TMPDIR, orf)
    with open(orfPath, "w") as f:
        SeqIO.write(record, f, "fasta")
    # run hmmscan with protein sequence against HMM file
    hmmscan = subprocess.Popen(
        f"{scanPath} --notextw {hmmfile} {orfPath}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        hmmscan.wait(timeout=120)  # wait for hmmscan to complete
        os.remove(orfPath)  # remove temporary ORF sequence file
    except subprocess.TimeoutExpired:
        hmmscan.kill()
        os.remove(orfPath)  # remove temporary ORF sequence file
        return None
    # grab results from scan
    results = hmmscan.stdout.readlines()
    allResults = []
    start = 16
    if "No hits detected that satisfy reporting thresholds" in str(results[start]):
        return None
    else:
        # determine the number of results returned (# of lines after line 15 that are not just a carriage return)
        counter = start
        m = HMMSEARCHPATT.search(str(results[counter]))
        while m:
            counter += 1
            m = HMMSEARCHPATT.search(str(results[counter]))
        for i in range(start, counter):
            m = HMMSEARCHPATT.search(str(results[i]))
            formattedMatches = {}
            for key in HMMSEARCHPATTKEY:
                formattedMatches[key] = m[key]
            allResults.append(formattedMatches)
        return allResults


def processSequence(sequence):
    orfs = orffinder.getORFNucleotides(sequence)
    noORF = False
    noFeatures = False
    result = None
    names = None
    descriptions = None
    translatedSequence = None
    if len(orfs):
        translatedSequence = orfs[0].translate()
        contig = sequence.id
        orfRecord = SeqRecord(translatedSequence, id=contig, name=contig)
        result = findDomains(orfRecord)
        if result is None:
            noFeatures = True
        else:
            allNames = [x["model"] for x in result]
            allDescriptions = [x["description"] for x in result]
            if allNames:
                names = [f"{k} ({v})" for k, v in Counter(allNames).items()]
                if len(names) > 1:
                    names = " / ".join(names)
                else:
                    names = names[0]
            else:
                names = None
            if allDescriptions:
                descriptions = [
                    f"{k} ({v})" for k, v in Counter(allDescriptions).items()
                ]
                if len(descriptions) > 1:
                    descriptions = " / ".join(descriptions)
                else:
                    descriptions = descriptions[0]
            else:
                descriptions = None
    else:
        noORF = True
    row = [
        sequence.id,
        names,
        descriptions,
        noORF,
        noFeatures,
        str(sequence.seq),
        translatedSequence,
    ]
    return row


if __name__ == "__main__":
    annotateSequences()
