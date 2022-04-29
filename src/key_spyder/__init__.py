from key_spyder.crawler import Crawler
from argparse import ArgumentParser
from multiprocessing import Process, log_to_stderr
from logging import INFO

parser = ArgumentParser(
    prog='key-spyder',
    description='Crawl websites for keywords')
parser.add_argument(
    '-u', '--urls',
    action='store',
    dest='urls',
    nargs='+',
    type=str,
    required=True,
    help='Entrypoint URLs to begin crawling',
    metavar='URLS'
)
parser.add_argument(
    '-p', '--params',
    action='store',
    dest='params',
    nargs='+',
    required=False,
    help='Parameters for requests while crawling',
    metavar='PARAMS'
)
parser.add_argument(
    '-k', '--keywords',
    action='store',
    dest='keywords',
    nargs='+',
    required=True,
    help='Keywords to search for in crawled pages',
    metavar='KEYWORDS'
)
parser.add_argument(
    '-r', '--recursive',
    action='store_true',
    dest='recursive',
    required=False,
    default=False,
    help='Recursively crawl linked pages'
)
parser.add_argument(
    '-o', '--output',
    action='store',
    dest='output',
    help='Output directory',
    default=None,
    metavar='OUTPUT'
)
parser.add_argument(
    '-v', '--verbose',
    action='store_true',
    dest='verbose',
    required=False,
    default=False,
    help='Verbose output'
)
parser.add_argument(
    '-c', '--clear-cache',
    action='store_true',
    dest='clear_cache',
    required=False,
    default=False,
    help='Clear cache before crawling'
)


def run_from_cli(url, params, keywords, recursive, output, verbose, clear_cache):
    Crawler(
        urls=url,
        params=params,
        keywords=keywords,
        recursive=recursive,
        output_directory=output,
        verbose=verbose,
        clear_cache=clear_cache
    ).run()


# Main function
def main():
    args = parser.parse_args()

    processes = []
    for url in args.urls:
        processes.append(Process(name=url,
                                 target=run_from_cli,
                                 args=([url], args.params, args.keywords, args.recursive, args.output, args.verbose, args.clear_cache)))

    if len(processes):
        if args.verbose:
            log_to_stderr(INFO)
        [process.start() for process in processes]
        [process.join() for process in processes]