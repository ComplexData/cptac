import os
from .dataframe import DataFrameLoader
from .meta import MetaData
from .molecular import MolecularData
from .utilities import Utilities
from .queries import Queries

clinical = DataFrameLoader("CPTAC" + os.sep + "Data" + os.sep + "clinical.csv").createDataFrame()
clinical_meta = DataFrameLoader("CPTAC" + os.sep + "Data" + os.sep + "meta_clinical.csv").createDataFrame() #TODO isn't finished yet
proteomics = DataFrameLoader("CPTAC" + os.sep + "Data" + os.sep + "proteomics.txt").createDataFrame()
transcriptome = DataFrameLoader("CPTAC" + os.sep + "Data" + os.sep + "transcriptome.txt").createDataFrame()
cna = DataFrameLoader("CPTAC" + os.sep + "Data" + os.sep + "CNA.txt").createDataFrame()
phosphoproteomics = DataFrameLoader("CPTAC" + os.sep + "Data" + os.sep + "phosphoproteomics.txt").createDataFrame()

metaData = MetaData(clinical, clinical_meta)
molecularData = MolecularData(proteomics, transcriptome, cna, phosphoproteomics)

def get_meta_completeness():
    return clinical
def get_proteomics():
    return proteomics
def get_transcriptome():
    return transcriptome
def get_cna():
    return cna
def get_phosphoproteomics():
    return phosphoproteomics
def get_meta_cols():
    return clinical.columns
def get_cohort_meta(cols):
    return clinical[cols]
def get_proteomics_quant(colon_ids):
    return proteomics.loc(colon_ids)
def get_proteomics_cols():
    return proteomics.columns
def get_transcriptome_cols():
    return transcriptome.columns
def get_cohort_proteomics(cols):
    return proteomics[cols]
def get_cohort_transcriptome(cols):
    return transcriptome[cols]
def get_cohort_cna(cols):
    return cna[cols]
def get_cohort_phosphoproteomics(cols):
    return phosphoproteomics[cols]

def get_tumor_ids(spec, type, value):
    """spec is the type of tumor query, e.g. by SNP, mutated gene, outlier
    type is the tumor type, e.g. colon
    value corresponds with the type of tumor query, e.g. TP53 for mutated gene or EGFR for outlier"""
    dataframe = None #TODO what should the dataframe be?
    return Queries(dataframe).query(spec, type, value)
def get_gene_mapping():
    return Utilities().get_gene_mapping()
def convert(snp_or_sap):
    return Utilities().convert(snp_or_sap)
def compare_gene(df1, df2, gene):
    return Utilities().compare_gene(df1, df2, gene)


def start():

    joke = u'Wenn ist das Nunst\u00fcck git und Slotermeyer? Ja! ... Beiherhund das Oder die Flipperwaldt gersput.'

    print("Welcome to our CPTAC data. Below are a list of main functions for this package: \nfunction1()\nfunction2()\nfunction3()")
