"""Analyser

Analyse the data obtained by the crawler:
[WORK IN PROGRESS]
"""
from colors import *
import csv
import glob
import json
import os
from ast import literal_eval

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns;

sns.set_theme(color_codes=True)


def write_data_to_csv(headers):
    """Writes the data from the JSON files for all the crawled websites to a CSV file

    Parameters
    ----------
    headers: list
        A list with the values for the headers of the data in the JSON files
    """
    # Change the current working directory to the directory of the running file:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

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
    dataframe: pandas.core.series.Series
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
    plt.show()


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
    entry: string
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
    """Find the top ten most prevalent third-party domains in the crawl

    Parameters
    ----------
    dataframe: pandas.core.series.Series
        A Pandas dataframe with all the data in the CSV file
    mode: string
        A string that holds the crawl-mode to use: either desktop or mobile

    Returns
    -------
    prevalence_tuples[:10]: list
        A list of tuples holding the ten most prevalent third-party domains
    """
    third_party_domains = []
    third_parties_list = dataframe["third_party_domains"]
    crawl_mode = dataframe["crawl_mode"]

    # Collect the third-parties belonging to the (desktop or mobile) crawl
    for index, third_parties in enumerate(third_parties_list):
        if crawl_mode[index] == mode:
            third_party_domains += third_parties

    # Remove duplicates from the list
    third_party_domains = list(dict.fromkeys(third_party_domains))
    # Add a zero count to all third party domains
    prevalence_third_parties = dict.fromkeys(third_party_domains, 0)

    # If the third party has been found in the CSV file, increment the count
    for third_party in third_party_domains:
        for i in range(len(third_parties_list)):
            if third_party in third_parties_list[i] and crawl_mode[i] == mode:
                prevalence_third_parties[third_party] += 1

    # Sort the domains on their prevalence
    prevalence_tuples = sorted(prevalence_third_parties.items(), key=lambda item: item[1], reverse=True)

    return prevalence_tuples[:10]


def generate_table_question_4(dataframe):
    """Generate a LaTeX table about the ten most prevalent third-party domains in a file

    Parameters
    ----------
    dataframe: pandas.core.series.Series
        A Pandas dataframe with all the data in the CSV file
    """
    # Remove the file if it is already existing
    if os.path.isfile("data/table_question_4.txt"):
        os.remove("data/table_question_4.txt")

    # Open the file and write to it
    file = open("data/table_question_4.txt", "a")
    file.write("\\begin{table}[ht] \n")
    file.write("\caption{The ten most prevalent third-party domains for each crawl.} \n")
    file.write("\centering \n")
    file.write("\\begin{tabular}{|l|ll|ll|} \n")
    file.write("\hline")
    file.write(
        "\\textbf{} & \multicolumn{2}{c|}{\\textbf{Crawl-desktop}} & \multicolumn{2}{c|}{\\textbf{Crawl-mobile}} \\\\ \hline \n")
    file.write(
        "& \multicolumn{1}{r|}{\\textbf{Third-party domain}} & \\textbf{\# websites} & \multicolumn{1}{l|}{\\textbf{Third-party domain}} & \\textbf{\# websites} \\\\ \hline \n")

    # Get the top 10 for both desktop and mobile
    top_ten_desktop = prevalence_third_party(dataframe, "desktop")
    top_ten_mobile = prevalence_third_party(dataframe, "mobile")

    for i in range(10):
        entry = "\\textbf{%d} & \multicolumn{1}{l|}{%s} & \multicolumn{1}{r|}{%d} & \multicolumn{1}{l|}{%s} & \multicolumn{1}{r|}{%d} \\\\ \hline \n" % (
        i + 1, top_ten_desktop[i][0], top_ten_desktop[i][1], top_ten_mobile[i][0], top_ten_mobile[i][1])
        file.write(entry)

    file.write("\end{tabular} \n")
    file.write("\label{tab:Top10} \n")
    file.write("\end{table}")

    # Close the file
    file.close()


def generate_scatter_plot(dataframe, mode):
    """
    TODO: CHANGE DATAFRAME["NR_REQUESTS"] TO DATAFRAME["TRANCO_RANK"] (OR SIMILAR)
    """
    third_parties_list = dataframe["third_party_domains"]
    crawl_mode = dataframe["crawl_mode"]
    tranco_ranks_list = list(dataframe["nr_requests"])
    number_of_distinct_third_parties = []
    tranco_ranks = []

    for i in range(len(tranco_ranks_list)):
        if crawl_mode[i] == mode:
            tranco_ranks.append(tranco_ranks_list[i])
    for index, third_parties in enumerate(third_parties_list):
        if crawl_mode[index] == mode:
            number_of_distinct_third_parties.append(len(third_parties))

    df = pd.DataFrame(list(zip(tranco_ranks, number_of_distinct_third_parties)),
                      columns=["website's Tranco rank", "number of distinct third parties"])
    sns.lmplot(x="website's Tranco rank", y="number of distinct third parties", data=df)

    plt.title(f"The number of distinct third parties vs the website's Tranco rank ({mode}-crawl)")
    plt.savefig(f"data/scatter_plot_{mode}.png", bbox_inches='tight')
    plt.show()  # use plt.show(block=True) if the window closes too soon


def main():
    headers = ["website_domain", "crawl_mode", "third_party_domains", "nr_requests", "requests_list"]
    write_data_to_csv(headers)
    dataframe = csv_to_pandas_dataframe(headers)

    # Generate answers for all the questions in the assignment
    generate_table_question_1()
    generate_box_plot(dataframe, "nr_requests", "crawl_mode", "number of requests")
    generate_table_question_3(dataframe, [("nr_requests", "Page load time(s)")])
    generate_table_question_4(dataframe)
    generate_scatter_plot(dataframe, "desktop")


if __name__ == '__main__':
    main()
