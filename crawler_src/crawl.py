"""Crawler

A placeholder for a very nice description of our crawler :)
"""
import argparse


def parse_arguments():
    """Parses the command line ArgumentParser

    Returns
    -------
    dict
        a dictionary with the values for all command line arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mobile", action="store_true", required=False,
                        help="Mobile crawl mode.")
    parser.add_argument("-u", "--url", action="store", type=str, required=False,
                        help="A single URL or domain to crawl.")
    parser.add_argument("-i", "--input", action="store", type=str, required=False,
                        help="A path to a CSV file containing domains to crawl and their Tranco ranks.")
    parser.add_argument("-v", "--view", action="store", type=str, required=True,
                        choices=["headless", "headful"],
                        help="Choose between headless and headful modes of the crawler.")
    args = parser.parse_args()

    if ((not args.url and not args.input) or (args.url and args.input)):
        parser.error("Invalid input: please provide either the -u or -i argument.")

    return vars(args)

if __name__ == '__main__':
    args = parse_arguments()
    print("Hello world!")
