import os

import pandas as pd

# RLCD location on wi-files2: /lab/reddien_lab/databases/RLCD/
# genesFile is a csv containing all genes to check in the RLCD
# the csv must contain a 'ddID' column formatted like: "dd-Smed-v6-659-0-1" --> "659"
# a second column, 'Name' can be used in placed of the dd ID: "dd-Smed-v6-659-0-1" --> "smedwi-1" in Name column, dd ID can be left out
genesFile = 'genes.tsv'
genes = pd.read_csv(genesFile, sep='\t')
dbFile = 'RLCD_20210730.xlsx'
db = pd.read_excel(dbFile)
# get dbinfo corresponding to geneinfo and combine
geneInfo = ['Label', 'dd ID', 'Name']
dbInfo = ['Reddien Lab Construct Database Index Name', 'Location', 'Plasmid Backbone',
	'Date Record Created', 'Date Record Modified', 'Associated Contig', 'Forward Primer', 'Reverse Primer']
out = pd.DataFrame()
for i, g in genes.iterrows():
    matches1 = db['Associated Contig'].str.contains(str(g['dd ID']), na=False)
    if g.get('Name') and pd.isna(g["dd ID"]): # search by Name if no dd ID is given
        matches2 = db['Gene Name'].str.contains(g['Name'], na=False)
    else:
        matches2 = []
    matches = matches1
    for j, m in db.loc[matches, ].iterrows():
        x = g[geneInfo]
        y = m[dbInfo]
        merge = pd.concat([x, y], ignore_index=True).to_frame().T
        out = pd.concat([out, merge], ignore_index=True)
    matches = matches2
    for j, m in db.loc[matches, ].iterrows():
        x = g[geneInfo]
        y = m[dbInfo]
        merge = pd.concat([x, y], ignore_index=True).to_frame().T
        out = pd.concat([out, merge], ignore_index=True)

# use short names for dbInfo in output
shortNames = {
'Reddien Lab Construct Database Index Name': 'RLCD',
'Plasmid Backbone': 'Backbone',
'Date Record Created': 'Created',
'Date Record Modified': 'Modified',
'Associated Contig': 'Contig',
}
dbInfoShort = [shortNames.get(x, x) for x in dbInfo]
out.to_csv('output.tsv', sep='\t', header=(geneInfo+dbInfoShort), index=False)
