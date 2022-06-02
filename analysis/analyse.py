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
from datetime import datetime


def read_blocklist():
    """Read all domains and their corresponding entities from the blocklist into a set

    Returns
    -------
    dict
        A dictionary with domains of trackers as key and the corresponding entity name as the value
    """
    with open("data/disconnect_blocklist.json", 'rb') as f:
        blocklist = json.load(f)

    # Add every domain in the blocklist to a set
    tracker_domains = dict()

    for cat in blocklist['categories'].keys():
        for item in blocklist['categories'][cat]:
            for entityname, urls in item.items():
                for url, domains in urls.items():
                    if url == "performance":
                        continue
                    for domain in domains:
                        tracker_domains[domain] = entityname
    return tracker_domains


def extract_tracker_domains_entities(third_party_domains, blocklist, blocklist_domains):
    """Extract tracker domains and their corresponding entity name from a list of third-party domain_list
        using a blocklist

    Parameters
    ----------
    third_party_domains: set
        A set with all distinct third-party domains for a request
    blocklist: dict
        A dictionary with the domains and their corresponding entity names from the blocklist
    blocklist_domains: dict_keys
        A list of domains that are present in the blocklist

    Returns
    -------
    tracker_domains: set
        A set of all (distinct) tracker domains for a request
    tracker_entities: set
        A set of all (distinct) tracker entities for a request
    """
    tracker_domains = set(blocklist_domains).intersection(third_party_domains)
    tracker_entities = {blocklist[domain] for domain in tracker_domains}
    return tracker_domains, tracker_entities


def calculate_page_load_time(start_time, end_time):
    """Calculate the page load time by subtracting the the start_time from end_time

    Parameters
    ----------
    start_time: string
        A string denoting the start time of the pageload
    end_time: string
        A string denoting the end time of the pageload

    Returns
    -------
    page_load_time: float
        The page load time in seconds
    """
    page_load_start = datetime.strptime(start_time, '%d/%m/%Y %H:%M:%S.%f')
    page_load_end = datetime.strptime(end_time, '%d/%m/%Y %H:%M:%S.%f')
    page_load_time = (page_load_end - page_load_start).total_seconds()

    return page_load_time


def write_data_to_csv(headers):
    """Writes the data from the JSON files for all the crawled websites to a CSV file

    Parameters
    ----------
    headers: list
        A list with the values for the headers of the data in the JSON files
    """
    blocklist = read_blocklist()
    blocklist_domains = blocklist.keys()

    # Get all JSON files within the crawl_data folder
    files = glob.glob("../crawl_data/*.json")
    data = []
    for file in files:
        with open(file, 'r') as f:
            try:
                json_file = json.load(f)
                tracker_domains, tracker_entities = extract_tracker_domains_entities(
                                                        json_file['third_party_domains'], blocklist, blocklist_domains)
                page_load_time = calculate_page_load_time(json_file['pageload_start_ts'], json_file['pageload_end_ts'])
                data.append([
                    json_file['website_domain'],
                    json_file['tranco_rank'],
                    json_file['crawl_mode'],
                    json_file['pageload_start_ts'],
                    json_file['pageload_end_ts'],
                    page_load_time,
                    json_file['post_pageload_url'],
                    json_file['consent_status'],
                    json_file['cookies'],
                    json_file['third_party_domains'],
                    len(json_file['third_party_domains']),
                    json_file['requests_list'],
                    len(json_file['requests_list']),
                    list(tracker_domains),
                    len(tracker_domains),
                    list(tracker_entities),
                    len(tracker_entities)
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
    dataframe['tracker_domains'] = dataframe.tracker_domains.apply(literal_eval)
    dataframe['tracker_entities'] = dataframe.tracker_entities.apply(literal_eval)

    return dataframe


def preprocess_data():
    """This function turns the data into a csv file and in turn this csv file to a Pandas dataframe

    Returns
    -------
    dataframe: pandas.core.series.Series
        A Pandas dataframe with all the data in the CSV file
    """
    headers = ["website_domain", "tranco_rank", "crawl_mode", "pageload_start_ts", "pageload_end_ts", "page_load_time",
               "post_pageload_url", "consent_status", "cookies", "third_party_domains", "nr_third_party_domains",
               "requests_list", "nr_requests", "tracker_domains", "nr_tracker_domains", "tracker_entities",
               "nr_tracker_entities"]
    write_data_to_csv(headers)
    dataframe = csv_to_pandas_dataframe(headers)

    return dataframe


def generate_table_question_1():
    """
    TODO: TEMPLATE FOR TABLE QUESTION 1 -> ADD ACTUAL CONTENT IN TABLE
    """
    # Remove the file if it is already existing
    if os.path.isfile("data/table_question_1.tex"):
        os.remove("data/table_question_1.tex")

    # Open the file and write to it
    file = open("data/table_question_1.tex", "a")
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
        flier.set(color=BOX_EDGECOLOR[i], marker='o')


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


def generate_box_plots_question_2(dataframe):
    """Generate five box plots to compare the data from the two crawls

    Parameters
    ----------
    dataframe: pandas.core.series.Series
        A Pandas dataframe with all the data in the CSV file
    """
    generate_box_plot(dataframe, "page_load_time", "crawl_mode", "page load time")
    generate_box_plot(dataframe, "nr_requests", "crawl_mode", "number of requests")
    generate_box_plot(dataframe, "nr_third_party_domains", "crawl_mode", "number of disctinct third-party domains")
    generate_box_plot(dataframe, "nr_tracker_domains", "crawl_mode", "number of disctinct tracker domains")
    generate_box_plot(dataframe, "nr_tracker_entities", "crawl_mode", "number of disctinct tracker entities")


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
    if os.path.isfile("data/table_question_3.tex"):
        os.remove("data/table_question_3.tex")

    # Open the file and write to it
    file = open("data/table_question_3.tex", "a")
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


def prevalence(dataframe, mode, target):
    """Find the prevalence of the targeted group in the crawl

    Parameters
    ----------
    dataframe: pandas.core.series.Series
        A Pandas dataframe with all the data in the CSV file
    mode: string
        A string that holds the crawl-mode to use: either desktop or mobile
    target: string
        The group that the prevalance needs to be find for, e.g., third-party domains

    Returns
    -------
    collections.Counter
        A counter object, holding a dictionary of all items of the targeted group (as keys)
        and their prevalence (as values) in the crawl
    """
    # Collect all items belonging to the target group for the (desktop or mobile) crawl
    third_parties = dataframe.loc[dataframe["crawl_mode"] == mode, target]
    # Turn the pandas series into a list and flatten it
    third_parties_list = sum(third_parties.tolist(), [])
    # Use Python Counter to return the count of every element in the list
    counter_third_parties = Counter(third_parties_list)

    return counter_third_parties


def generate_table_question(questionnr, target, top_ten_desktop, top_ten_mobile, label=""):
    """Generate a LaTeX table for questions 4, 5 and 6

    TODO: change loop to range(10) -> currently len because otherwise errors occurs :)

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
    if os.path.isfile(f"data/table_question_{questionnr}.tex"):
        os.remove(f"data/table_question_{questionnr}.tex")

    # Open the file and write to it
    file = open(f"data/table_question_{questionnr}.tex", 'a')
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
    file.write("\label{tab:%sTop10} \n" % (re.sub(r'(Third-Party|Domain| )', '', target.title())))
    file.write("\end{table}")

    # Close the file
    file.close()


def generate_table_question_4(dataframe):
    """Generate a LaTeX table holding the ten most prevalent third-party domains for each crawl

    Parameters
    ----------
    dataframe: pandas.core.series.Series
        A Pandas dataframe with all the data in the CSV file
    """
    top_ten_desktop = prevalence(dataframe, "Desktop", "third_party_domains").most_common(10)
    top_ten_mobile = prevalence(dataframe, "Mobile", "third_party_domains").most_common(10)

    generate_table_question(4, "third-party domain", top_ten_desktop, top_ten_mobile)


def generate_table_question_5(dataframe):
    """Generate a LaTeX table holding the ten most prevalent third-party tracker domains for each crawl

    Parameters
    ----------
    dataframe: pandas.core.series.Series
        A Pandas dataframe with all the data in the CSV file
    """
    top_ten_tracker_desktop = prevalence(dataframe, "Desktop", "tracker_domains").most_common(10)
    top_ten_tracker_mobile = prevalence(dataframe, "Mobile", "tracker_domains").most_common(10)

    generate_table_question(5, "tracker domain", top_ten_tracker_desktop, top_ten_tracker_mobile)


def generate_table_question_6(dataframe):
    """Generate a LaTeX table holding the ten most prevalent tracker entities (companies) for each crawl

    Parameters
    ----------
    dataframe: pandas.core.series.Series
        A Pandas dataframe with all the data in the CSV file
    """
    top_ten_entities_desktop = prevalence(dataframe, "Desktop", "tracker_entities").most_common(10)
    top_ten_entities_mobile = prevalence(dataframe, "Mobile", "tracker_entities").most_common(10)
    generate_table_question(6, "tracker entity", top_ten_entities_desktop, top_ten_entities_mobile)


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
    """Generate the scatter plots showing the number of distinct third parties vs the website's Tranco rank

    Parameters
    ----------
    dataframe: pandas.core.series.Series
        A Pandas dataframe with all the data in the CSV file
    """
    third_parties_list = dataframe["third_party_domains"]
    crawl_mode = dataframe["crawl_mode"]
    tranco_ranks_list = list(dataframe["tranco_rank"])

    generate_scatter_plot("Desktop", third_parties_list, crawl_mode, tranco_ranks_list, "third_parties", "Number of distinct third parties")
    generate_scatter_plot("Mobile", third_parties_list, crawl_mode, tranco_ranks_list, "third_parties", "Number of distinct third parties")


def generate_scatter_plots_question_8(dataframe):
    """Generate the scatter plots showing the number of distinct trackers vs the website's Tranco rank

    Parameters
    ----------
    dataframe: pandas.core.series.Series
        A Pandas dataframe with all the data in the CSV file
    """
    third_parties_list = dataframe["third_party_domains"]
    tracker_list = copy.deepcopy(third_parties_list)
    crawl_mode = dataframe["crawl_mode"]
    tranco_ranks_list = list(dataframe["tranco_rank"])
    tracker_domains = read_blocklist()

    # Transform the third party domains list to a tracker list by only saving the tracker domains in tracker_list
    for i in range(len(tracker_list)):
        tracker_list[i] = set(tracker_list[i])
        tracker_list[i].intersection_update(tracker_domains)
        tracker_list[i] = list(tracker_list[i])

    generate_scatter_plot("Desktop", tracker_list, crawl_mode, tranco_ranks_list, "trackers", "Number of distinct trackers")
    generate_scatter_plot("Mobile", tracker_list, crawl_mode, tranco_ranks_list, "trackers", "Number of distinct trackers")


def main():
    # We first preprocess the data and turn it into a Pandas dataframe
    dataframe = preprocess_data()

    # Generate answers for all the questions in the assignment
    generate_table_question_1()
    generate_box_plots_question_2(dataframe)
    generate_table_question_3(dataframe, [("nr_requests", "Page load time(s)")])
    generate_table_question_4(dataframe)
    # generate_table_question_5(dataframe)
    # generate_table_question_6(dataframe)
    generate_scatter_plots_question_7(dataframe)
    generate_scatter_plots_question_8(dataframe)


if __name__ == '__main__':
    # Set theme that seaborn should use
    sns.set_theme(color_codes=True)

    # Change the current working directory to the directory of the running file:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Start main function
    main()
