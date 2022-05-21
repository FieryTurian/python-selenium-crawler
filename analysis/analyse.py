"""Analyser

Analyse the data obtained by the crawler:
[WORK IN PROGRESS]
"""
import csv
import glob
import json
import os
from ast import literal_eval

import pandas as pd
import matplotlib.pyplot as plt


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
    files = glob.glob(f"../crawl_data/*.json")
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
    with open("data.csv", 'w', newline="") as f:
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
    dataframe = pd.read_csv("data.csv", usecols=headers)

    # Turn strings into their corresponding python literals
    dataframe['third_party_domains'] = dataframe.third_party_domains.apply(literal_eval)
    dataframe['requests_list'] = dataframe.requests_list.apply(literal_eval)

    return dataframe


def generate_box_plot(dataframe, header, crawl_mode):
    """Read the CSV file into a pandas dataframe in order to analyse the data

    Parameters
    ----------
    dataframe: pandas.core.series.Series
        A Pandas dataframe with all the data in the CSV file
    header: string
        A string with the value for one of the headers of the data in the dataframe
    crawl_mode: string
        A string with the value for the crawl_mode header of the data in the dataframe
    """
    dataframe.boxplot(header, by=crawl_mode)
    plt.savefig(f"box_plot_{header}.png")
    plt.show()


def main():
    headers = ["website_domain", "crawl_mode", "third_party_domains", "nr_requests", "requests_list"]
    write_data_to_csv(headers)
    dataframe = csv_to_pandas_dataframe(headers)
    generate_box_plot(dataframe, "nr_requests", "crawl_mode")


if __name__ == '__main__':
    main()