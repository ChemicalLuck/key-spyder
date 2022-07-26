from argparse import ArgumentError, ArgumentParser
from logging import INFO
from multiprocessing import Process, log_to_stderr
from os import makedirs, path

from key_spyder.crawler import Crawler
from key_spyder.defaults import DEFAULT_PATH
from key_spyder.sitemap import Sitemapper


def command():
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
        required=False,
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
    parser.add_argument(
        '-s', '--sitemap',
        action='store_true',
        dest='sitemap',
        required=False,
        default=False,
        help='Use Sitemap for faster crawling'
    )

    def run_from_cli(url, params, keywords, recursive, output, verbose,
                     clear_cache,
                     known_urls):
        Crawler(
            url=url,
            params=params,
            keywords=keywords,
            recursive=recursive,
            output_directory=output,
            verbose=verbose,
            clear_cache=clear_cache,
            known_urls=known_urls
        ).run()


    def parse_params(params_args):
        for param in params_args:
            if '=' in param:
                key, value = param.split('=')
                yield key, value
            else:
                raise ArgumentError(
                    f"Invalid parameter argument: {param}, parameters must be in the form 'key=value'")


    args = parser.parse_args()

    output_path = DEFAULT_PATH
    if args.output:
        if not path.exists(args.output):
            makedirs(args.output)
            output_path = args.output

    sitemaps = {}
    if args.sitemap:
        sitemaps = {url: Sitemapper(url) for url in args.urls}
        for sitemap in sitemaps.values():
            sitemap.to_csv(output_path)

    params = dict(parse_params(args.params)) if args.params else None

    processes = []
    for url in args.urls:
        known_urls = list(sitemaps[url].all_urls["loc"]) if sitemaps else []
        processes.append(Process(name=url,
                                 target=run_from_cli,
                                 args=(url, params, args.keywords,
                                       args.recursive, output_path,
                                       args.verbose, args.clear_cache,
                                       known_urls)))

    if len(processes):
        if args.verbose:
            log_to_stderr(INFO)
        [process.start() for process in processes]
        [process.join() for process in processes]
