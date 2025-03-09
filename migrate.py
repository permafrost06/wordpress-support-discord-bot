import json
from wp import get_threads
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--verbose', action='store_true', help='Print logging')
args = parser.parse_args()

tableberg_support_url = "https://wordpress.org/support/plugin/tableberg/"
ub_support_url = "https://wordpress.org/support/plugin/ultimate-blocks/"
wptb_support_url = "https://wordpress.org/support/plugin/wp-table-builder/"

def check_threads(product, SUPPORT_URL):
    if args.verbose:
        print(f"starting {product}")
    data_filename = f'{product}-data.json'

    with open(data_filename, 'r') as fp:
        old_threads = json.load(fp)

    if args.verbose:
        print("data file loaded")

    thread_links = get_threads(SUPPORT_URL)
    thread_links.reverse()

    threads = {}
    
    if args.verbose:
        print("links received")
    for thread_obj in thread_links:
        link = thread_obj["link"]
        last_updated = thread_obj["last_updated"]

        if link in old_threads.keys():
            thread_details = old_threads[link]
            thread_details["last_updated"] = last_updated
            threads[link] = thread_details

    if args.verbose:
        print("dumping new threads data")
    with open(data_filename, 'w') as fp:
        json.dump(threads, fp)

check_threads("tableberg", tableberg_support_url)
check_threads("ub", ub_support_url)
check_threads("wptb", wptb_support_url)

