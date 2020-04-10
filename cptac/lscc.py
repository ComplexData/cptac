#   Copyright 2018 Samuel Payne sam_payne@byu.edu
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#       http://www.apache.org/licenses/LICENSE-2.0
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import pandas as pd
import numpy as np
import os
import warnings
from .dataset import DataSet
from .dataframe_tools import *
from .exceptions import FailedReindexWarning, ReindexMapError

class Lscc(DataSet):

    def __init__(self, version="latest", no_internet=False):
        """Load all of the lscc dataframes as values in the self._data dict variable, with names as keys, and format them properly.

        Parameters:
        version (str, optional): The version number to load, or the string "latest" to just load the latest building. Default is "latest".
        no_internet (bool, optional): Whether to skip the index update step because it requires an internet connection. This will be skipped automatically if there is no internet at all, but you may want to manually skip it if you have a spotty internet connection. Default is False.
        """

        # Set some needed variables, and pass them to the parent DataSet class __init__ function

        valid_versions = ["1.0"] # This keeps a record of all versions that the code is equipped to handle. That way, if there's a new data release but they didn't update their package, it won't try to parse the new data version it isn't equipped to handle.

        data_files = {
            "1.0": [
                "lscc-v1.0-cnv-gene-level-log2.gct.gz", 
                "lscc-v1.0-cptac3-lscc-rna-seq-fusion-v2.2-y2.all-20190807.txt.gz", 
                "lscc-v1.0-cptac3-lscc-wxs-somatic-variant-sw-v1.5-lscc.y2-20191211.maf.gz",
                "lscc-v1.0-mirna-mature-tpm-log2.gct.gz",
                "lscc-v1.0-phosphoproteome-ratio-norm-NArm.gct.gz", 
                "lscc-v1.0-proteome-ratio-norm-NArm.gct.gz", 
                "lscc-v1.0-rnaseq-uq-fpkm-log2-NArm.gct.gz",
                "lscc-v1.0-sample-annotation.csv.gz"] 
        }

        super().__init__(cancer_type="lscc", version=version, valid_versions=valid_versions, data_files=data_files, no_internet=no_internet)

        # Load the data into dataframes in the self._data dict
        loading_msg = f"Loading {self.get_cancer_type()} v{self.version()}"
        for file_path in self._data_files_paths: # Loops through files variable

            # Print a loading message. We add a dot every time, so the user knows it's not frozen.
            loading_msg = loading_msg + "."
            print(loading_msg, end='\r')

            path_elements = file_path.split(os.sep) # Get a list of the levels of the path
            file_name = path_elements[-1] # The last element will be the name of the file

            if file_name == "lscc-v1.0-cnv-gene-level-log2.gct.gz": 
                df = pd.read_csv(file_path, sep="\t", skiprows=2, dtype=object)
                gene_filter = df['geneSymbol'] != 'na' #Filter out rows of metadata
                df = df[gene_filter]
                df = df.set_index("id")
                cols_to_drop = ["chrom","geneSymbol","chr_end","chr_start"]
                df = df.drop(columns = cols_to_drop)
                df = df.apply(pd.to_numeric)
                df = df.sort_index()
                df = df.transpose()
                df = df.sort_index()
                df.index.name="Patient_ID"
                self._data["CNV"] = df

            elif file_name == "lscc-v1.0-phosphoproteome-ratio-norm-NArm.gct.gz": 
                df = pd.read_csv(file_path, sep="\t", skiprows=2, dtype=object)
                gene_filter = df['geneSymbol'] != 'na' #Drop rows of metadata
                df = df[gene_filter]

                # Prepare some columns we'll need later for the multiindex
                df["variableSites"] = df["variableSites"].str.replace(r"[a-z\s]", "") # Get rid of all lowercase delimeters and whitespace in the sites
                df = df.rename(columns={
                "geneSymbol": "Name",
                "variableSites": "Site",
                "sequence": "Peptide", # We take this instead of sequenceVML, to match the other datasets' format
                "accession_numbers": "Database_ID" # We take all accession numbers they have, instead of the singular accession_number column
                })

                # Some rows have at least one localized phosphorylation site, but also have other phosphorylations that aren't localized. We'll drop those rows, if their localized sites are duplicated in another row, to avoid creating duplicates, because we only preserve information about the localized sites in a given row. However, if the localized sites aren't duplicated in another row, we'll keep the row.
                unlocalized_to_drop = df.index[~df['Best_numActualVMSites_sty'].eq(df['Best_numLocalizedVMsites_sty']) & df.duplicated(["Name", "Site", "Peptide", "Database_ID"], keep=False)] # Column 3 of the split "id" column is number of phosphorylations detected, and column 4 is number of phosphorylations localized, so if the two values aren't equal, the row has at least one unlocalized site
                df = df.drop(index=unlocalized_to_drop)

                # Give it a multiindex
                df = df.set_index(["Name", "Site", "Peptide", "Database_ID"])

                cols_to_drop = ['id','id.description', 'numColumnsVMsiteObserved', 'bestScore', 'bestDeltaForwardReverseScore',
                'Best_scoreVML', 'Best_numActualVMSites_sty', 'Best_numLocalizedVMsites_sty', 'sequenceVML',
                'accessionNumber_VMsites_numVMsitesPresent_numVMsitesLocalizedBest_earliestVMsiteAA_latestVMsiteAA', 'protein_mw', 'species',
                'speciesMulti', 'orfCategory', 'accession_number', 'protein_group_num', 'entry_name', 'GeneSymbol']
                df = df.drop(columns=cols_to_drop)
                df = df.apply(pd.to_numeric)
                df = df.sort_index()
                df = df.transpose()
                df = df.sort_index()
                df.index.name="Patient_ID"
                self._data["phosphoproteomics"] = df

            elif file_name == "lscc-v1.0-proteome-ratio-norm-NArm.gct.gz": 
                df = pd.read_csv(file_path, skiprows=2, sep='\t', dtype=object)
                gene_filter = df['geneSymbol'] != 'na' #Filter out rows of metadata
                df = df[gene_filter]

                df = df.rename(columns={"GeneSymbol": "Name", 'accession_numbers': "Database_ID"})
                df = df.set_index(["Name", "Database_ID"])
                cols_to_drop = ['id', 'id.description', 'geneSymbol', 'numColumnsProteinObserved',
                'numSpectraProteinObserved', 'protein_mw', 'percentCoverage', 'numPepsUnique',
                'scoreUnique', 'species', 'orfCategory', 'accession_number',
                'subgroupNum', 'entry_name']
                df = df.drop(columns=cols_to_drop)
                df = df.apply(pd.to_numeric)
                df = df.sort_index()
                df = df.transpose()
                df = df.sort_index()
                df.index.name="Patient_ID"
                df.columns.name=None
                self._data["proteomics"] = df


            elif file_name == "lscc-v1.0-cptac3-lscc-rna-seq-fusion-v2.2-y2.all-20190807.txt.gz": 
                 df = pd.read_csv(file_path, sep="\t", dtype=object)
                 df = df.rename(columns={"Sample.ID": "Patient_ID"})
                 df = df.set_index("Patient_ID")

                 self._data['gene_fusion'] = df

            elif file_name == "lscc-v1.0-sample-annotation.csv.gz": 
                df = pd.read_csv(file_path, sep=",", dtype=object)
                filter = df['QC.status'] == "QC.pass" #There are some samples that are internal references. IRs are used for scaling purposes, and don't belong to a single patient, so we want to drop them.
                df = df[filter]
                df = df.drop(columns="Participant") #Get rid of the "Participant" column becuase the same information is stored in Sample.ID  which is formatted the way we want.
                df = df.set_index("Sample.ID")
                df = df.drop(columns="Sample.IDs")
                df.index.name="Patient_ID"
                df = df.rename(columns={"Type":"Sample_Tumor_Normal"})
                df["Sample_Tumor_Normal"] = df["Sample_Tumor_Normal"].replace("NAT","Normal")

                #Split the metadata into multiple dataframes
                #Make experiemntal_set up dataframe
                experimental_design_cols = ['Experiment', 'Channel', 'QC.status'] #These are the columns for the experimental_design dataframe
                experimental_design_df = df[experimental_design_cols]
                df = df.drop(columns=experimental_design_cols)

                #Make a derived_molecular dataframe
                derived_molecular_cols = ['TP53.mutation', 'CDKN2A.mutation', 'PTEN.mutation', 'PIK3CA.mutation',
                 'KEAP1.mutation', 'HLA.A.mutation', 'NFE2L2.mutation', 'NOTCH1.mutation', 'RB1.mutation',
                 'HRAS.mutation', 'FBXW7.mutation', 'SMARCA4.mutation', 'NF1.mutation', 'SMAD4.mutation',
                 'EGFR.mutation', 'APC.mutation', 'BRAF.mutation', 'TNFAIP3.mutation', 'CREBBP.mutation',
                 'TP53.mutation.status', 'CDKN2A.mutation.status', 'PTEN.mutation.status', 'PIK3CA.mutation.status',
                 'KEAP1.mutation.status', 'HLA.A.mutation.status', 'NFE2L2.mutation.status', 'NOTCH1.mutation.status',
                 'RB1.mutation.status', 'HRAS.mutation.status', 'FBXW7.mutation.status', 'SMARCA4.mutation.status',
                 'NF1.mutation.status', 'SMAD4.mutation.status', 'EGFR.mutation.status', 'APC.mutation.status',
                 'BRAF.mutation.status', 'TNFAIP3.mutation.status', 'CREBBP.mutation.status']
                derived_molecular_df = df[derived_molecular_cols]
                df = df.drop(columns = derived_molecular_cols)
                self._data["clinical"]= df
                self._data['experimental_design'] = experimental_design_df
                self._data['derived_molecular'] = derived_molecular_df

            elif file_name == "lscc-v1.0-cptac3-lscc-wxs-somatic-variant-sw-v1.5-lscc.y2-20191211.maf.gz":
                df = pd.read_csv(file_path, sep="\t", dtype=object)
                df = df[["Sample.ID", "Hugo_Symbol", "Variant_Classification", "HGVSp_Short"]] # We don't need any of the other columns
                df = df.rename(columns={"Sample.ID": "Patient_ID", 'Hugo_Symbol': "Gene", "Variant_Classification": "Mutation", "HGVSp_Short": "Location"})
                df = df.set_index("Patient_ID")
                df = df.sort_values(by=["Patient_ID","Gene"])
                self._data['somatic_mutation'] = df

            elif file_name == "lscc-v1.0-mirna-mature-tpm-log2.gct.gz": 
                df = pd.read_csv(file_path, skiprows=2, sep='\t', dtype=object)
                gene_filter = df['Name'] != 'na' #Filter out rows of metadata
                df = df[gene_filter]
                df = df.rename(columns={"ID": "Database_ID"})
                df = df.set_index(["Name","Database_ID"])
                cols_to_drop = ["Derives_from","Quantified.in.Percent.Samples","id","Alias"]
                df = df.drop(columns = cols_to_drop)
                df= df.apply(pd.to_numeric)
                df = df.sort_index()
                df = df.transpose()
                df = df.sort_index()
                df.index.name="Patient_ID"
                df.columns.name=None
                self._data["miRNA"] = df

        print(' ' * len(loading_msg), end='\r') # Erase the loading message
        formatting_msg = "Formatting dataframes..."
        print(formatting_msg, end='\r')

        # Get a union of all dataframes' indices, with duplicates removed
        master_index = unionize_indices(self._data, exclude="followup")

        # Use the master index to reindex the clinical dataframe, so the clinical dataframe has a record of every sample in the dataset. Rows that didn't exist before (such as the rows for normal samples) are filled with NaN.
        clinical = self._data["clinical"]
        clinical = clinical.reindex(master_index)

        # Impute any NaNs in Sample_Tumor_Normal
        clinical["Sample_Tumor_Normal"] = clinical["Sample_Tumor_Normal"].where(cond=~(pd.isnull(clinical["Sample_Tumor_Normal"]) & clinical.index.str.endswith(".N")), other="Normal")
        clinical["Sample_Tumor_Normal"] = clinical["Sample_Tumor_Normal"].where(cond=~(pd.isnull(clinical["Sample_Tumor_Normal"]) & ~clinical.index.str.endswith(".N")), other="Tumor")

        # Replace the clinical dataframe in the data dictionary with our new and improved version!
        self._data['clinical'] = clinical

        # Replace periods with hyphens in all Patient_IDs
        for name in self._data.keys(): # Loop over just the keys to avoid any issues that would come if we looped over the values while editing them
            df = self._data[name]

            # Make the index a column so we can edit it
            df.index.name = "Patient_ID"
            df = df.reset_index()

            # Replace all '.' with '-'
            df["Patient_ID"] = df["Patient_ID"].str.replace(r"\.", "-")
            df["Patient_ID"] = df["Patient_ID"].str.replace(r"-N$", ".N") # If there's a "-N" at the end, it's part of the normal identifier, which we want to actually be ".N"

            # Set the index back to Patient_ID
            df = df.set_index("Patient_ID")

            self._data[name] = df

        # Call function from dataframe_tools.py to sort all tables first by sample status, and then by the index
        self._data = sort_all_rows(self._data)

        # Call function from dataframe_tools.py to standardize the names of the index and column axes
        self._data = standardize_axes_names(self._data)

        print(" " * len(formatting_msg), end='\r') # Erase the formatting message