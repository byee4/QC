#!/usr/bin/env python

"""
General parsers for QC output of pipeline file,
generally pass a handle to the file you want to parse,
returns a dict containing all useful information
Currently this isn't standard
"""

# transitionning to python2/python3 support
# uncomment from this compatibility import list, as py3/py2 support progresses
from __future__ import print_function
from __future__ import division
# from __future__  import absolute_import
# from __future__  import unicode_literals
# from future import standard_library
# from future.builtins import builtins
# from future.builtins import utils
# from future.utils import raise_with_traceback
# from future.utils import iteritems

import glob
import os
import argparse

import pandas as pd
import pybedtools
import pysam

# from parse_cutadapt import parse_cutadapt_file
# from qcsummary_rnaseq import rnaseq_metrics_df, parse_star_file
from qc import parse_cutadapt as pc
from qc import qcsummary_rnaseq as rq
from qc import column_names

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from subprocess import call

from matplotlib import rc

rc('text', usetex=False)
matplotlib.rcParams['svg.fonttype'] = 'none'
rc('font', **{'family': 'DejaVu Sans'})




def write_clipseq_metrics_excel(df, output_excel, percent_usable, number_usable, peak_threshold):
    """
    Writes an excel file
    """

    
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    output_excel_annotated = os.path.splitext(output_excel)[0] + ".annotated.xlsx"
    for df, fn in zip([df, df[column_names.slim_qc_metrics]], [output_excel, output_excel_annotated]):
        if df.shape[1] == 54:
            initial_reads_num = 'C'
            adapter_round2_reads = 'R'
            repetitive_reads = 'AA'
            repetitive_perc = 'Z'
            star_input_reads = 'AB'
            star_uniquely_mapped = 'AX'
            star_too_many_loci = 'AP'
            star_too_short_perc = 'AG'
            usable_reads_col = 'AY'
            unique_mapped_perc = 'AW'
            usable_mapped_ratio = 'BA'
            usable_input_ratio = 'BB'
            clipper_peaks = 'AZ'
            peak_num = 'BC'
        elif df.shape[1] == 72:
            initial_reads_num = 'C'
            adapter_round2_reads = 'AC'
            repetitive_reads = 'AQ'
            repetitive_perc = 'AP'
            star_input_reads = 'AR'
            star_uniquely_mapped = 'BN'
            star_too_many_loci = 'BF'
            star_too_short_perc = 'AJ'
            usable_reads_col = 'BO'
            unique_mapped_perc = 'BM'
            usable_mapped_ratio = 'BS'
            usable_input_ratio = 'BT'
            clipper_peaks = 'BR'
            peak_num = 'BU'
        elif df.shape[1] == 15:
            initial_reads_num = 'B'
            adapter_round2_reads = 'C'
            repetitive_reads = 'D'
            repetitive_perc = 'E'
            star_input_reads = 'F'
            star_uniquely_mapped = 'G'
            unique_mapped_perc = 'H'
            star_too_many_loci = 'I'
            star_too_short_perc = 'J'
            usable_reads_col = 'L'
            usable_mapped_ratio = 'M'
            usable_input_ratio = 'N'
            clipper_peaks = 'O'
            peak_num = 'P'
        else:
            print("unknown number of columns (should be either 54 or 15 or ): . col names: {}".format(df.shape[1], df.columns))
            
        writer = pd.ExcelWriter(fn, engine='xlsxwriter')

        # Convert the dataframe to an XlsxWriter Excel object.
        df.to_excel(writer, sheet_name='Sheet1')

        # Get the xlsxwriter workbook and worksheet objects.
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        
        # Apply number format
        number_format = workbook.add_format()
        number_format.set_num_format("#,##0")
        # Apply a conditional formats

        # Add a format. Light red fill with dark red text.
        red_num = workbook.add_format(
            {'bg_color': '#FFC7CE',
             'font_color': '#9C0006'}
        )
        red_num.set_num_format('#,##0')
        # Add a format. Yellow fill with dark green text.
        yellow_num = workbook.add_format(
            {'bg_color': '#FFEFC2',
             'font_color': '#000000'}
        )
        yellow_num.set_num_format('#,##0')
        # Add a format. Green fill with dark green text.
        green_num = workbook.add_format(
            {'bg_color': '#C6EFCE',
             'font_color': '#006100'}
        )
        green_num.set_num_format('#,##0')
        
        # Add a format. Light red fill with dark red text.
        red_perc = workbook.add_format(
            {'bg_color': '#FFC7CE',
             'font_color': '#9C0006'}
        )
        red_perc.set_num_format('0.00%')
        # Add a format. Yellow fill with dark green text.
        yellow_perc = workbook.add_format(
            {'bg_color': '#FFEFC2',
             'font_color': '#000000'}
        )
        yellow_perc.set_num_format('0.00%')
        # Add a format. Green fill with dark green text.
        green_perc = workbook.add_format(
            {'bg_color': '#C6EFCE',
             'font_color': '#006100'}
        )
        green_perc.set_num_format('0.00%')
        
        offset = 1 # header
        start_row = 1 + offset
        end_row = df.shape[0] + offset
        
        # Conditional format rule for repetitive perc.
        for condition, color in zip(['>=','<'], [yellow_perc, green_perc]):
            worksheet.conditional_format(
                '{}{}:{}{}'.format(repetitive_perc, start_row, repetitive_perc, end_row), 
                {
                    'type':'cell',
                    'criteria': condition,
                    'value':.50,
                    'format':color
                }
            )
        # Condition format rule for uniquely mapped %
        for color, min_val, max_val in zip([red_perc, yellow_perc, green_perc], [-.01, .60, .75], [.60, .75, 1.01]):
            worksheet.conditional_format(
                '{}{}:{}{}'.format(unique_mapped_perc, start_row, unique_mapped_perc, end_row), 
                {
                    'type':'cell',
                    'criteria': 'between',
                    'minimum': min_val,
                    'maximum': max_val,
                    'format':color
                }
            )
        # Conditional format rule for too short %
        for color, min_val, max_val in zip([green_perc, yellow_perc, red_perc], [-.01, .1, .3], [.1, .3, 1.01]):
            worksheet.conditional_format(
                '{}{}:{}{}'.format(star_too_short_perc, start_row, star_too_short_perc, end_row), 
                {
                    'type':'cell',
                    'criteria': 'between',
                    'minimum': min_val,
                    'maximum': max_val,
                    'format':color
                }
            )
        # Conditional format rule for usable read number
        for condition, color in zip(['<','>='], [yellow_num, green_num]):
            worksheet.conditional_format(
                '{}{}:{}{}'.format(usable_reads_col, start_row, usable_reads_col, end_row), 
                {
                    'type':'cell',
                    'criteria': condition,
                    'value':number_usable,
                    'format':color
                }
            )
        # Conditional format rule for usable/mapped ratio
        for color, min_val, max_val in zip([red_perc, yellow_perc, green_perc], [-.01, .60, .75], [.60, .75, 1.01]):
            worksheet.conditional_format(
                '{}{}:{}{}'.format(usable_mapped_ratio, start_row, usable_mapped_ratio, end_row), 
                {
                    'type':'cell',
                    'criteria': 'between',
                    'minimum': min_val,
                    'maximum': max_val,
                    'format':color
                }
            )
        # Conditional format rule for usable/input ratio
        for color, min_val, max_val in zip([red_perc, yellow_perc, green_perc], [-.01, .60, .75], [.60, .75, 1.01]):
            worksheet.conditional_format(
                '{}{}:{}{}'.format(usable_input_ratio, start_row, usable_input_ratio, end_row), 
                {
                    'type':'cell',
                    'criteria': 'between',
                    'minimum': min_val,
                    'maximum': max_val,
                    'format':color
                }
            )
        # Conditional format rule for peak number
        for condition, color in zip(['<','>='], [red_num, green_num]):
            worksheet.conditional_format(
                '{}{}:{}{}'.format(peak_num, start_row, peak_num, end_row),  
                {
                    'type':'cell',
                    'criteria': condition,
                    'value':peak_threshold,
                    'format':color
                }
            )
        

        # Number format for numbers.
        for column in [initial_reads_num, adapter_round2_reads, repetitive_reads, star_input_reads, star_uniquely_mapped, star_too_many_loci, clipper_peaks]:
            worksheet.set_column("{}:{}".format(column, column), cell_format=number_format)
            
        for i, width in enumerate(get_col_widths(df)):
            worksheet.set_column(i, i, width)
            
        # Close the Pandas Excel writer and output the Excel file.
        
        
        writer.save()
        
def get_col_widths(dataframe):
    # First we find the maximum length of the index column   
    idx_max = max([len(str(s)) for s in dataframe.index.values] + [len(str(dataframe.index.name))])
    # Then, we concatenate this to the max of the lengths of column name and its values for each column, left to right
    return [idx_max] + [max([len(str(s)) for s in dataframe[col].values] + [len(col)]) for col in dataframe.columns]
        
def write_clipseq_metrics_csv(df, output_csv):
    """
    Writes CSV file with clipseq metrics.
    Writes "annotated" (abridged with the most useful QC stats) file.
    """
    df.to_csv(output_csv)
    df[column_names.slim_qc_metrics].to_csv(os.path.splitext(output_csv)[0] + ".annotated.csv")
    
    
def clipseq_metrics(analysis_dir, output_csv, percent_usable, number_usable, peak_threshold, paired_end, l10p, l2fc):
    
    # TODO: remove iclip param when new nomenclature is finalized.
    df = clipseq_metrics_df(
        analysis_dir=analysis_dir,
        percent_usable=percent_usable,
        number_usable=number_usable,
        iclip=False,
        paired_end=paired_end,
        l10p_cutoff=l10p,
        l2fc_cutoff=l2fc
    )
    df = df[column_names.PE_ORDER] if paired_end else df[column_names.SE_ORDER]
    
    write_clipseq_metrics_csv(df, output_csv)
    
    output_excel = os.path.splitext(output_csv)[0] + ".xlsx"
    write_clipseq_metrics_excel(df, output_excel, percent_usable, number_usable, peak_threshold)
    

def clipseq_metrics_df(
        analysis_dir, percent_usable,
        number_usable,
        iclip=False, num_seps=None,
        sep=".",
        cutadapt_round2_suffix="*TrTr.metrics",
        rm_dup_suffix=None,  # TODO: reimplement the metrics for single-end if available
        peak_suffix="*.peakClusters.bed",
        input_normed_suffix="*.normed.compressed.bed",
        paired_end=False,
        l10p_cutoff=3,
        l2fc_cutoff=3
    ):
    #######################################
    """
    Reports all clip-seq metrics in a given analysis directory
    outputs must follow gabes naming clipseq pipeline / naming conventions"
    Args:
        analysis_dir:
        iclip:
        num_seps:
        sep:
        percent_usable:
        number_usable:
    Returns:
    """
    # TODO: fix prefix name separator
    if num_seps is None:
        num_seps = 3 if iclip else 3

    if paired_end:
        rm_dup_suffix = "*.genome-mappedSo.rmDup.metrics"
    else:
        rm_dup_suffix = "*.genome-mappedSoSo.rmDupSo.bam"
        # rm_dup_suffix = "*_per_umi.tsv"
    cutadapt_round2_names, rm_duped_names, peaks_names, input_normed_names = get_all_names(
        analysis_dir=analysis_dir,
        cutadapt_round2_suffix=cutadapt_round2_suffix,
        rm_dup_suffix=rm_dup_suffix,
        peak_suffix=peak_suffix,
        input_normed_suffix=input_normed_suffix,
        sep=sep,
        num_seps=num_seps
    )
    ###########################################################################
    # make dataframes for each column
    ###########################################################################
    if len(cutadapt_round2_names) > 0:
        cutadapt_round2_df = pd.DataFrame(
            {
                name: pc.parse_cutadapt_file(cutadapt_file, paired_end)
                for name, cutadapt_file in cutadapt_round2_names.items()
            }
        ).transpose()

        cutadapt_round2_df.columns = [
            "{} Round 2".format(col) for col in cutadapt_round2_df.columns
        ]

    if len(rm_duped_names) > 0:
        if paired_end:
            rm_duped_df = pd.DataFrame(
                {name: parse_rm_duped_metrics_file_pe(rm_duped_file)
                 for name, rm_duped_file in rm_duped_names.items()}
            ).transpose()
        else:
            rm_duped_df = pd.DataFrame(
                {name: parse_rm_duped_metrics_file_se(rm_duped_file)
                 for name, rm_duped_file in rm_duped_names.items()}
            ).transpose()
    else:
        rm_duped_df = pd.DataFrame(index=['Usable reads', 'removed_count', 'total_count']).T

    if len(peaks_names) > 0:
        peaks_df = pd.DataFrame(
            {name: {"Clipper peaks num": len(pybedtools.BedTool(peaks_file))}
             for name, peaks_file in peaks_names.items()}
        ).transpose()
        
    if len(input_normed_names) > 0:
        input_normed_df = {}
        for prefix, filename in input_normed_names.items():
            input_normed_df[prefix] = get_sig_peaks(filename, l10p=l10p_cutoff, l2fc=l2fc_cutoff)
        input_normed_df = pd.DataFrame(
            input_normed_df, 
            index=['Input normed peaks num (log10p >= {}, l2fc >= {})'.format(
                l10p_cutoff, l2fc_cutoff
            )]
        ).T
    else:
        input_normed_df = pd.DataFrame(
            index=['Input normed peaks num (log10p >= {}, l2fc >= {})'.format(
                l10p_cutoff, l2fc_cutoff
            )]
        ).T
    ###########################################################################

    ###########################################################################
    # get the base dataframe rnaseq metrics dataframe
    ##############################
    combined_df = rq.rnaseq_metrics_df(analysis_dir, num_seps, sep, paired_end)
    ###########################################################################

    ###########################################################################
    # merge dataframes
    ##################
    combined_df = pd.merge(combined_df, cutadapt_round2_df,
                           left_index=True, right_index=True, how="outer")
    combined_df = pd.merge(combined_df, rm_duped_df,
                           left_index=True, right_index=True, how="outer")
    combined_df = pd.merge(combined_df, peaks_df,
                           left_index=True, right_index=True, how="outer")
    combined_df = pd.merge(combined_df, input_normed_df,
                           left_index=True, right_index=True, how="outer")
    
    ###########################################################################
    # Rename columns to be useful
    combined_df = combined_df.rename(
        columns={"Reads Written Round 2": "Reads after cutadapt 2"
                 })

    ###########################################################################

    # compute useful stats
    ######################
    combined_df['STAR genome uniquely mapped'] = combined_df['STAR genome uniquely mapped'].astype(float)
    combined_df['Initial reads num'] = combined_df['Initial reads num'].astype(float)
    try:
        combined_df["Percent usable / mapped"] = (
                    combined_df['Usable reads'] / combined_df['STAR genome uniquely mapped'])
        combined_df["Percent Usable / Input"] = (combined_df['Usable reads'] / combined_df['Initial reads num'])
        combined_df["Percent Repetitive"] = 1 - (
                    combined_df['STAR genome input reads'] / combined_df['Reads after cutadapt 2'].astype(float))
        combined_df["Repetitive Reads"] = combined_df['Reads after cutadapt 2'] - combined_df['STAR genome input reads']
        # combined_df['Passed basic QC'] = (combined_df['Usable reads'] > number_usable) & (
        #             combined_df['Percent usable / mapped'] > percent_usable)

    except ZeroDivisionError:
        print("passing on ZeroDivisionError")
        pass

    return combined_df


def get_all_names(
        analysis_dir,
        cutadapt_round2_suffix,
        rm_dup_suffix,
        peak_suffix,
        input_normed_suffix,
        sep,
        num_seps
    ):
    ###########################################################################
    # get file paths
    ################

    # cutadapt_round2_files = glob.glob(os.path.join(analysis_dir, "*.adapterTrim.round2.metrics"))
    cutadapt_round2_files = glob.glob(os.path.join(analysis_dir, cutadapt_round2_suffix))
    # print("cutadapt_round2_files: {}".format(cutadapt_round2_files))
    # rm_duped_files = glob.glob(os.path.join(analysis_dir, "*rmRep.rmDup.metrics"))
    rm_duped_files = glob.glob(os.path.join(analysis_dir, rm_dup_suffix))
    # print("rmdup files: {}".format(rm_duped_files))
    # peaks_files = glob.glob(os.path.join(analysis_dir, "*.peaks.bed"))
    peaks_files = glob.glob(os.path.join(analysis_dir, peak_suffix))
    # print("peaks files: {}".format(peaks_files))
    input_normed_peaks = glob.glob(os.path.join(analysis_dir, input_normed_suffix))
    ###########################################################################

    ###########################################################################
    # get file names
    ################
    cutadapt_round2_names = get_names(cutadapt_round2_files, num_seps, sep)
    # rmRep_mapping_names = get_names(rmRep_mapping_files, num_seps, sep)
    rm_duped_names = get_names(rm_duped_files, num_seps, sep)
    # spot_names = get_names(spot_files, num_seps, sep)
    peaks_names = get_names(peaks_files, num_seps, sep)
    input_normed_names = get_names(input_normed_peaks, num_seps, sep)
    ###########################################################################
    return cutadapt_round2_names, rm_duped_names, peaks_names, input_normed_names


def get_names(files, num_seps, sep):
    """
    Given a list of files,
     return that files base name and the path to that file

    :param files: list
        list of files
    :param num_seps: int
        number of separators to call real names
    :param sep: str
        separator to split names on
    :return basenames: dict
        dict basename to file
    """

    dict_basename_to_file = {
        sep.join(os.path.basename(file).split(sep)[0: num_seps]): file
        for file in files
    }
    # print("get names dict: {}".format(dict_basename_to_file))
    return dict_basename_to_file


def parse_peak_metrics(fn):
    """
    Unused function that has parsed/will parse CLIPPER metrics.

    :param fn: basestring
    :return spot_dict: dict
    """
    with open(fn) as file_handle:
        file_handle.next()
        return {'spot': float(next(file_handle))}


def parse_rm_duped_metrics_file_pe(rmDup_file):
    """
    Parses the rmdup file (tabbed file containing
     barcodes found ('randomer'),
     number of reads found ('total_count'),
     number of reads removed ('removed_count')

    :param rmDup_file: basestring
        filename of the rmDup file
    :return count_dict: dict
        dictionary containing sums of total, removed,
        and usable (total - removed)
    """
    # print("returning number of reads mapped in rmduped file")
    # return parse_rm_duped_metrics_file_se(rmDup_file)
    ########################################
    ### TODO: FIX THIS ###
    
    try:
        df = pd.read_csv(rmDup_file, sep="\t")
        return {
            "total_count": sum(df.total_count),
            "removed_count": sum(df.removed_count),
            "Usable reads": sum(df.total_count) - sum(df.removed_count)
        }
    except Exception as e:
        print(e)
        return {
            "total_count": None,
            "removed_count": None,
            "Usable reads": None
        }
    
    
def parse_rm_duped_metrics_file_se(rmDup_file):
    """
    Parses the BAM file to return the number of reads mapped.
    (in the future when we umi tools produce stats pages this will change)

    :param rmDup_file: basestring
        BAM file name
    :return:
    """
    check_for_index(rmDup_file)
    samfile = pysam.AlignmentFile(rmDup_file)
    return {
        "Usable reads": samfile.mapped
    }


def build_second_mapped_from_master(df):
    second_mapped = df[[
        '% of reads unmapped: too short',
        '% of reads mapped to too many loci',
        '% of reads unmapped: too many mismatches',
        'STAR genome uniquely mapped %',
        'Percent usable / mapped'
    ]].fillna('0')
    for col in second_mapped.columns:
        try:
            second_mapped[col] = second_mapped[col].apply(
                lambda x: float(x.strip('%')) / 100
            )
        except AttributeError:
            second_mapped[col] = second_mapped[col].astype(float)
    return second_mapped


def build_peak_df_from_master(df):
    peaks = df[[
        'Clipper peaks num',
    ]]

    return peaks


def build_raw_number_from_master(df):
    num = df[[
        'Usable reads',
        'STAR genome input reads',
        'STAR genome uniquely mapped',
        'Repetitive Reads'
    ]]
    return num


def plot_second_mapping_qc(df, percent_usable, ax):
    second_mapped = build_second_mapped_from_master(df)
    second_mapped.plot(kind='bar', ax=ax)
    ax.set_ylim(0, 1)
    ax.axhline(percent_usable, linestyle=':', alpha=0.75, label='minimum recommended percent usable threshold')
    ax.set_title("Percent Mapped/Unmapped/Usable (Usable: (dup removed read num) / (unique mapped reads))")
    ax.legend()


def plot_peak_qc(df, peak_threshold, ax):
    peaks = build_peak_df_from_master(df)
    peaks.plot(kind='bar', ax=ax)
    ax.axhline(peak_threshold, linestyle=':', alpha=0.75, label='minimum recommended peak threshold')
    ax.set_title("Peak Numbers (Only for merged files)")
    ax.legend()


def plot_raw_num_qc(df, number_usable, ax):
    ax.set_title("Number of Reads Mapped/Unmapped/Usable (Usable: (dup removed read num) / (unique mapped reads))")
    num = build_raw_number_from_master(df)
    num.plot(kind='bar', ax=ax)
    ax.axhline(number_usable, linestyle=':', alpha=0.75, label='minimum recommended number usable threshold')
    ax.legend()


def plot_qc(df, out_file, percent_usable, number_usable, peak_threshold):
    num_samples = len(df.index)

    f, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(5 * num_samples, 15), sharex=True)
    plot_second_mapping_qc(df, percent_usable, ax=ax1)
    plot_raw_num_qc(df, number_usable, ax=ax2)
    plot_peak_qc(df, peak_threshold, ax=ax3)
    plt.savefig(out_file)

def check_for_index(bamfile):

    """

    Checks to make sure a BAM file has an index, if the index does not exist it is created

    Usage undefined if file does not exist (check is made earlier in program)
    bamfile - a path to a bam file

    """

    if not os.path.exists(bamfile):
        raise NameError("file %s does not exist" % (bamfile))

    if os.path.exists(bamfile + ".bai"):
        return

    if not bamfile.endswith(".bam"):
        raise NameError("file %s not of correct type" % (bamfile))
    else:
        process = call(["samtools", "index", str(bamfile)])

        if process == -11:
            raise NameError("file %s not of correct type" % (bamfile))

def get_sig_peaks(input_normed_peaks_file, l10p, l2fc):
    """
    Reads in an input normalized file (-log10p in column 4, log2fold in column 5)
    and filters based on l10p and l2fc thresholds.
    Returns the number of peaks that survive these filters.
    """
    input_normed_headers = [
        'chrom','start','end','l10p','l2fc','strand'
    ]
    df = pd.read_csv(input_normed_peaks_file, names=input_normed_headers, sep='\t')
    df = df[(df['l10p'] >= l10p) & (df['l2fc'] >= l2fc)]
    return df.shape[0]


def main():
    parser = argparse.ArgumentParser(description="Make a summary csv files of all eclip metrics")
    parser.add_argument("--analysis_dir", help="analysis directory", required=False, default="./")
    parser.add_argument("--output_csv", help="output csv filename", required=False, default="./eclipqcsummary.csv")
    parser.add_argument("--number_usable", help="number of usable peaks", required=False, type=float, default=1000000)
    parser.add_argument("--percent_usable", help="percent of usable peaks", required=False, type=float, default=0.7)
    parser.add_argument("--peak_threshold", help="peak threshold", required=False, type=float, default=3000)
    parser.add_argument("--paired_end", help="if the analysis folder contains paired end data. Default is single-end.", required=False, default=False, action='store_true')
    parser.add_argument("--l10p", help="-log10(p) threshold for coloring excel sheet. Default: 3", required=False, type=float, default=3.)
    parser.add_argument("--l2fc", help="log2(foldchange) threshold for coloring excel sheet. Default: 3", required=False, type=float, default=3.)
    args = parser.parse_args()
    # print("args:", args)
    # need to modify the column names to include cutoff values.
    column_names.PE_ORDER += ['Input normed peaks num (log10p >= {}, l2fc >= {})'.format(args.l10p, args.l2fc)]
    column_names.SE_ORDER += ['Input normed peaks num (log10p >= {}, l2fc >= {})'.format(args.l10p, args.l2fc)]
    column_names.slim_qc_metrics += ['Input normed peaks num (log10p >= {}, l2fc >= {})'.format(args.l10p, args.l2fc)]
    
    clipseq_metrics(
        args.analysis_dir,
        args.output_csv,
        args.percent_usable,
        args.number_usable,
        args.peak_threshold,
        args.paired_end,
        args.l10p,
        args.l2fc
    )

if __name__ == '__main__':
    main()