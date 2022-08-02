import csv

import click
from intermine.webservice import Service

service = Service("https://planmine.mpibpc.mpg.de:443/planmine/service")


@click.command()
@click.option(
    "-c",
    "--contigs",
    required=True,
    type=str,
    help="Specify a comma-separated list of dd_smed_v6 contig to fetch GO terms for.",
)
@click.option(
    "-o",
    "--outfile",
    required=True,
    type=str,
    help="Specify the output path for the results (results are in tab-separated format or .tsv).",
)
def queryContigs(contigs, outfile):
    contigs = contigs.split(",")
    output = [
        queryContig(c)
        if "dd_Smed_v6_" in c
        else [
            {
                "contig": c,
                "name": "",
                "description": "incorrect contig format (need dd_Smed_v6_)",
            }
        ]
        for c in contigs
    ]  # only query correctly formatted IDs (regex would be better)
    header = ["contig", "names", "descriptions"]
    with open(outfile, "w") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(header)
        for terms in output:
            print(terms)
            contig = terms[0]["contig"]
            names = " | ".join([t["name"] for t in terms])
            descriptions = " | ".join([t["description"] for t in terms])
            writer.writerow([contig, names, descriptions])


def queryContig(contig):
    query = service.new_query("Contig")
    query.add_view(
        "primaryIdentifier",
        "domainHits.proteinDomain.goAnnotation.ontologyTerm.identifier",
        "domainHits.proteinDomain.goAnnotation.ontologyTerm.name",
        "domainHits.proteinDomain.goAnnotation.ontologyTerm.description",
    )
    query.add_constraint("Contig", "LOOKUP", contig, code="A")

    terms = []
    for row in query.rows():
        term = {
            "contig": contig,
            "name": row["domainHits.proteinDomain.goAnnotation.ontologyTerm.name"],
            "description": row[
                "domainHits.proteinDomain.goAnnotation.ontologyTerm.description"
            ],
        }
        terms.append(term)
    return terms


if __name__ == "__main__":
    queryContigs()
