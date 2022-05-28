"""Analyser

Analyse the data obtained by the crawler:
[WORK IN PROGRESS]
"""
from ast import literal_eval
from collections import Counter
from colors import *
import csv
import copy
import glob
import json
import os
import re

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def write_data_to_csv(headers):
    """Writes the data from the JSON files for all the crawled websites to a CSV file

    Parameters
    ----------
    headers: list
        A list with the values for the headers of the data in the JSON files
    """
    # Get all JSON files within the crawl_data folder
    files = glob.glob("../crawl_data/*.json")
    data = []
    for file in files:
        with open(file, 'r') as f:
            try:
                json_file = json.load(f)
                data.append([
                    json_file['website_domain'],
                    json_file['crawl_mode'],
                    json_file['third_party_domains'],
                    json_file['nr_requests'],
                    json_file['requests_list']
                ])
            except KeyError:
                print(f"Skipping {file} because of bad formatting.")

    # Add headers
    data.insert(0, headers)
    with open("data/data.csv", 'w', newline="") as f:
        writer = csv.writer(f)
        writer.writerows(data)


def csv_to_pandas_dataframe(headers):
    """Read the CSV file into a pandas dataframe in order to analyse the data

    Parameters
    ----------
    headers: list
        A list with the values for the headers of the data in the JSON files

    Returns
    -------
    pandas.core.series.Series
        A Pandas dataframe with all the data in the CSV file
    """
    dataframe = pd.read_csv("data/data.csv", usecols=headers)

    # Turn strings into their corresponding python literals
    dataframe['third_party_domains'] = dataframe.third_party_domains.apply(literal_eval)
    dataframe['requests_list'] = dataframe.requests_list.apply(literal_eval)

    return dataframe


def generate_table_question_1():
    """
    TODO: TEMPLATE FOR TABLE QUESTION 1 -> ADD ACTUAL CONTENT IN TABLE
    """
    # Remove the file if it is already existing
    if os.path.isfile("data/table_question_1.txt"):
        os.remove("data/table_question_1.txt")

    # Open the file and write to it
    file = open("data/table_question_1.txt", "a")
    file.write("\\begin{table}[ht] \n")
    file.write("\caption{Number of failures encountered during each crawl.} \n")
    file.write("\centering \n")
    file.write("\\begin{tabular}{|l|r|r|} \n")
    file.write("\hline \n")
    file.write(
        "\\textbf{Error type} & \multicolumn{1}{l|}{\\textbf{Crawl-desktop}} & \multicolumn{1}{l|}{\\textbf{Crawl-mobile}} \\\\ \hline \n")

    # for header in headers
    #    do something to make the entries for each error type

    file.write("\end{tabular} \n")
    file.write("\label{table:NumberOfFailures} \n")
    file.write("\end{table}")

    # Close the file
    file.close()


def customize_grid(ax, border, yaxis, xaxis, bg_color='white', grid_color='gray', width=1.2, yminor=True, xminor=True):
    """Customize the looks of the grid

    Parameters
    ----------
    ax: matplotlib.axes._subplots.AxesSubplot
        The matplotlib axes instance the plot is drawn on
    border: bool
        A Boolean value that defines whether or not the border needs to be drawn
    yaxis, xaxis: bool
        Boolean values that define whether respectively the horizontal and vertical
         (mayor) grid lines need to be drawn
    bg_color: str, default='white'
        The background color of the grid
    grid_color: str, default='gray'
        The color of the grid lines
    width: float, default=1.2
        The width of the grid lines
    yminor, xminor: bool, default=True
       Boolean values that define whether respectively the horizontal and vertical
        minor grid lines need to be drawn
    """
    ax.set_facecolor(bg_color)  # Set background color
    [ax.spines[spine].set_visible(border) for spine in ax.spines]  # Remove border around the grid
    if yaxis:
        ax.yaxis.grid(yaxis, which='major', color=grid_color, linewidth=width)
    if yminor:
        ax.yaxis.grid(yminor, which='minor', color=grid_color, linewidth=width / 4)
    if xaxis:
        ax.xaxis.grid(xaxis, which='major', color=grid_color, linewidth=width)
    if xminor:
        ax.xaxis.grid(xminor, which='minor', color=grid_color, linewidth=width / 4)
    if yminor or xminor:  # Show minor grid lines, but not minor ticks
        ax.minorticks_on()
        ax.tick_params(which='minor', bottom=False, left=False)
    ax.set(axisbelow=True)  # Do not draw the grid over the plotted items


def customize_box_plot_color(ax):
    """Customize the colors of all boxplot parts

    Parameters
    ----------
    ax: matplotlib.axes._subplots.AxesSubplot
        The matplotlib axes instance the plot is drawn on
    """
    for i, box in enumerate(ax['boxes']):
        box.set(facecolor=BOX_FACECOLOR[i], edgecolor=BOX_EDGECOLOR[i])
    for whisker in ax['whiskers']:
        whisker.set(color=BOX_LINE, linestyle=':')
    for cap in ax['caps']:
        cap.set_color(BOX_LINE)
    for median in ax['medians']:
        median.set(color=BOX_MEDIAN)
    for flier in ax['fliers']:
        flier.set(color=BOX_EDGECOLOR[i], marker='*')


def generate_box_plot(dataframe, header, crawl_mode, metric):
    """Generate a box plot for dataframe[header] grouped by crawl_mode

    Parameters
    ----------
    dataframe: pandas.core.series.Series
        A Pandas dataframe with all the data in the CSV file
    header: string
        A string with the value for one of the headers of the data in the dataframe
    crawl_mode: string
        A string with the value for the crawl_mode header of the data in the dataframe
    metric: string
        A string with the metric that is plotted
    """
    bp_dict = dataframe.boxplot(header, grid=False, by=crawl_mode, return_type='both', patch_artist=True)
    customize_grid(bp_dict[0][0], False, True, False, BOX_BACKGROUND, BOX_GRID, xminor=False)
    customize_box_plot_color(bp_dict[0][1])
    plt.title(f"The distribution of the {metric} per website\nfor both desktop and mobile crawl mode.")
    plt.suptitle("")  # Remove the automatic "grouped by" title
    plt.xlabel("Crawl mode")
    plt.ylabel(metric.capitalize())
    plt.savefig(f"data/box_plot_{header}.png", bbox_inches='tight')
    # plt.show()
    plt.close()


def generate_entry_table_question_3(dataframe, header):
    """Generate a header specific entry for the table about the comparison of desktop and mobile crawl data

    Parameters
    ----------
    dataframe: pandas.core.series.Series
        A Pandas dataframe with all the data in the CSV file
    header: tuple
        A tuple holding the header name and belonging text that should appear in the entry

    Returns
    -------
    string
        A string that holds the precise entry text that will be added in the table
    """
    # Sort the CSV data by crawl_mode and then by the value of the provided header
    df = dataframe.sort_values(['crawl_mode', header[0]]).groupby('crawl_mode')

    # Get the minimum, maximum and median values for each provided header
    min_desktop = df[header[0]].min()[0]
    max_desktop = df[header[0]].max()[0]
    median_desktop = df[header[0]].median()[0]
    min_mobile = df[header[0]].min()[1]
    max_mobile = df[header[0]].max()[1]
    median_mobile = df[header[0]].median()[1]

    entry = "%s & \multicolumn{1}{r|}{%s} & \multicolumn{1}{r|}{%s} & \multicolumn{1}{r|}{%s} & \multicolumn{1}{r|}{%s} & \multicolumn{1}{r|}{%s} & \multicolumn{1}{r|}{%s} \\\\ \hline \n" % (
    header[1], min_desktop, max_desktop, median_desktop, min_mobile, max_mobile, median_mobile)

    return entry


def generate_table_question_3(dataframe, headers):
    """Generate a LaTeX table about the comparison of desktop and mobile crawl data in a file

    Parameters
    ----------
    dataframe: pandas.core.series.Series
        A Pandas dataframe with all the data in the CSV file
    headers: list
        A list of tuples holding the headers and text that should appear in the table
    """
    # Remove the file if it is already existing
    if os.path.isfile("data/table_question_3.txt"):
        os.remove("data/table_question_3.txt")

    # Open the file and write to it
    file = open("data/table_question_3.txt", "a")
    file.write("\\begin{table}[ht] \n")
    file.write("\caption{Comparison of the desktop and mobile crawl data.} \n")
    file.write("\centering \n")
    file.write("\\begin{tabular}{|l|rrl|lll|} \n")
    file.write("\\hline \n")
    file.write(
        "\\textbf{} & \multicolumn{3}{c|}{\\textbf{Crawl-desktop}} & \multicolumn{3}{c|}{\\textbf{Crawl-mobile}} \\\\ \hline \n")
    file.write(
        "\\textbf{Metric} & \multicolumn{1}{r|}{\\textbf{Min}} & \multicolumn{1}{r|}{\\textbf{Max}} & \\textbf{Median} & \multicolumn{1}{l|}{\\textbf{Min}} & \multicolumn{1}{l|}{\\textbf{Max}} & \\textbf{Median} \\\\ \hline \n")

    for header in headers:
        entry = generate_entry_table_question_3(dataframe, header)
        file.write(entry)

    file.write("\end{tabular} \n")
    file.write("\label{table:Comparison} \n")
    file.write("\end{table}")

    # Close the file
    file.close()


def prevalence_third_party(dataframe, mode):
    """Find the prevalence of third-party domains in the crawl

    Parameters
    ----------
    dataframe: pandas.core.series.Series
        A Pandas dataframe with all the data in the CSV file
    mode: string
        A string that holds the crawl-mode to use: either desktop or mobile

    Returns
    -------
    collections.Counter
        A counter object, holding a dictionary of all third-party domains (as keys)
        and their prevalence (as values) in the crawl
    """
    # Collect the third-parties belonging to the (desktop or mobile) crawl
    third_parties = dataframe.loc[dataframe["crawl_mode"] == mode, "third_party_domains"]
    # Turn the pandas series into a list and flatten it
    third_parties_list = sum(third_parties.tolist(), [])
    # Use Python Counter to return the count of every element in the list
    counter_third_parties = Counter(third_parties_list)

    return counter_third_parties


def read_blocklist():
    """Read all domains from the blocklist into a set"""
    with open("data/disconnect_blocklist.json", 'rb') as f:
        blocklist = json.load(f)

    # Add every domain in the blocklist to a set
    tracker_domains = set()

    for cat in blocklist['categories'].keys():
        for item in blocklist['categories'][cat]:
            for _, urls in item.items():
                for url, domains in urls.items():
                    if url == "performance":
                        continue
                    for domain in domains:
                        tracker_domains.add(domain)
    return tracker_domains


def prevalence_third_party_trackers(prevalence_third_party):
    """Find the top ten most prevalent third-party tracker domains in the crawl

    Parameters
    ----------
    prevalence_third_party: collections.Counter
        A counter object, holding a dictionary of all third-party domains (as keys)
        and their prevalence (as values) in the crawl

    Returns
    -------
    list
        A list, holding a tuples of the top ten third-party tracker domains and their prevalence
    """
    # Create a set of all third party domains encountered in the crawl
    third_parties = set(prevalence_third_party)
    # Read the tracker domains from the blocklist into a set
    tracker_domains = read_blocklist()
    # Remove the tracker domains from the set of third party domains
    third_parties.difference_update(tracker_domains)
    # Assign a count of zero to all non-tracker domains by updating a dictionary
    #  with the counts of all third party domains
    count_non_trackers = dict.fromkeys(third_parties, 0)
    dict_third_party_count = dict(prevalence_third_party)
    dict_third_party_count.update(count_non_trackers)
    # Keep only the third-party tracker domains by removing all entries with a count <= 0
    third_party_trackers = +Counter(dict_third_party_count)

    return third_party_trackers.most_common(10)


def generate_table_question(questionnr, target, top_ten_desktop, top_ten_mobile, label=""):
    """Generate a LaTeX table for questions 4, 5 and 6

    TODO: change loop to range(10) -> currently len because otherwise errors occur :)

    Parameters
    ----------
    questionnr: int
        The number of the question for which the table needs to be generated
    target: str
        The target that we are building the prevalence table for, e.g., third-party domains
    top_ten_desktop: list
        The top ten prevalent instances of the target for the desktop crawl mode
    top_ten_mobile: list
        The top ten prevalent instances of the target for the mobile crawl mode
    """
    # Remove the file if it is already existing
    if os.path.isfile(f"data/table_question_{questionnr}.txt"):
        os.remove(f"data/table_question_{questionnr}.txt")

    # Open the file and write to it
    file = open(f"data/table_question_{questionnr}.txt", 'a')
    file.write("\\begin{table}[ht] \n")
    file.write("\caption{The ten most prevalent %ss for each crawl.} \n" % (re.sub(r'y$', r'ie', target)))
    file.write("\centering \n")
    file.write("\\begin{tabular}{|l|ll|ll|} \n")
    file.write("\hline")
    file.write(
        "\\textbf{} & \multicolumn{2}{c|}{\\textbf{Crawl-desktop}} & " +
        "\multicolumn{2}{c|}{\\textbf{Crawl-mobile}} \\\\ \hline \n")
    file.write(
        "& \multicolumn{1}{r|}{\\textbf{%s}} & \\textbf{\# websites} & " % (target.capitalize()) +
        "\multicolumn{1}{l|}{\\textbf{%s}} & \\textbf{\# websites} \\\\ \hline \n" % (target.capitalize()))

    # Write the data of the top ten for both mobile and desktop to the table
    for i in range(len(top_ten_desktop)):
        entry = ("\\textbf{%d} & \multicolumn{1}{l|}{%s} & " % (i + 1, top_ten_desktop[i][0]) +
                "\multicolumn{1}{r|}{%d} & \multicolumn{1}{l|}{%s} & " % (top_ten_desktop[i][1], top_ten_mobile[i][0]) +
                "\multicolumn{1}{r|}{%d} \\\\ \hline \n" % (top_ten_mobile[i][1]))
        file.write(entry)

    file.write("\end{tabular} \n")
    file.write("\label{tab:%sTop10} \n" % (re.sub(r'(Third-Party| Domain)', '', target.title())))
    file.write("\end{table}")

    # Close the file
    file.close()


def generate_scatter_plot(mode, third_parties_list, crawl_mode, tranco_ranks_list, png_text, plot_text):
    """Generate scatter plots of the provided data along with a linear regression line

    Parameters
    ----------
    mode: string
        A string that holds the crawl-mode to use: either desktop or mobile
    third_parties_list: pandas.core.series.Series
        A Pandas dataframe that holds the third party data from the CSV file
    crawl_mode: pandas.core.series.Series
        A Pandas dataframe with the data crawl mode data from the CSV file
    tranco_ranks_list: list
        A list of the Pandas dataframe that holds the website's Tranco ranks
    text: string
        A string that holds information on how to name the output .png file
    """
    # Define lists to hold the values belonging to the x- and y-axis
    y_axis = []
    x_axis = []

    for i in range(len(tranco_ranks_list)):
        if crawl_mode[i] == mode:
            x_axis.append(tranco_ranks_list[i])
    for index, third_parties in enumerate(third_parties_list):
        if crawl_mode[index] == mode:
            y_axis.append(len(third_parties))

    df = pd.DataFrame(list(zip(x_axis, y_axis)),
                      columns=["Website's Tranco rank", plot_text])
    sns.lmplot(x="Website's Tranco rank", y=plot_text, data=df)

    plt.title(f"The {plot_text.lower()} vs the website's Tranco rank ({mode}-crawl)")
    plt.savefig(f"data/scatter_plot_{png_text}_{mode}.png", bbox_inches='tight')
    # plt.show()  # use plt.show(block=True) if the window closes too soon
    plt.close()


def generate_scatter_plots_question_7(dataframe):
    """
    TODO: CHANGE DATAFRAME["NR_REQUESTS"] TO DATAFRAME["TRANCO_RANK"] (OR SIMILAR)
    """
    third_parties_list = dataframe["third_party_domains"]
    crawl_mode = dataframe["crawl_mode"]
    tranco_ranks_list = list(dataframe["nr_requests"])

    generate_scatter_plot("desktop", third_parties_list, crawl_mode, tranco_ranks_list, "third_parties", "Number of distinct third parties")
    generate_scatter_plot("mobile", third_parties_list, crawl_mode, tranco_ranks_list, "third_parties", "Number of distinct third parties")


def generate_scatter_plots_question_8(dataframe):
    """
    TODO: CHANGE DATAFRAME["NR_REQUESTS"] TO DATAFRAME["TRANCO_RANK"] (OR SIMILAR)
    """
    third_parties_list = dataframe["third_party_domains"]
    tracker_list = copy.deepcopy(third_parties_list)
    crawl_mode = dataframe["crawl_mode"]
    tranco_ranks_list = list(dataframe["nr_requests"])
    tracker_domains = read_blocklist()

    # Transform the third party domains list to a tracker list by only saving the tracker domains in tracker_list
    for i in range(len(tracker_list)):
        tracker_list[i] = set(tracker_list[i])
        tracker_list[i].intersection_update(tracker_domains)
        tracker_list[i] = list(tracker_list[i])

    generate_scatter_plot("desktop", tracker_list, crawl_mode, tranco_ranks_list, "trackers", "Number of distinct trackers")
    generate_scatter_plot("mobile", tracker_list, crawl_mode, tranco_ranks_list, "trackers", "Number of distinct trackers")


def main():
    headers = ["website_domain", "crawl_mode", "third_party_domains", "nr_requests", "requests_list"]
    write_data_to_csv(headers)
    dataframe = csv_to_pandas_dataframe(headers)

    # Generate answers for all the questions in the assignment
    generate_table_question_1()
    generate_box_plot(dataframe, "nr_requests", "crawl_mode", "number of requests")
    generate_table_question_3(dataframe, [("nr_requests", "Page load time(s)")])
    prevalence_desktop = prevalence_third_party(dataframe, "desktop")
    prevalence_mobile = prevalence_third_party(dataframe, "mobile")
    top_ten_desktop = prevalence_desktop.most_common(10)
    top_ten_mobile = prevalence_mobile.most_common(10)
    generate_table_question(4, "third-party domain", top_ten_desktop, top_ten_mobile)
    top_ten_tracker_desktop = prevalence_third_party_trackers(prevalence_desktop)
    top_ten_tracker_mobile = prevalence_third_party_trackers(prevalence_mobile)
    generate_table_question(5, "tracker domain", top_ten_tracker_desktop, top_ten_tracker_mobile)
    generate_scatter_plots_question_7(dataframe)
    generate_scatter_plots_question_8(dataframe)


if __name__ == '__main__':
    # Set theme that seaborn should use
    sns.set_theme(color_codes=True)

    # Change the current working directory to the directory of the running file:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Start main function
    main()
