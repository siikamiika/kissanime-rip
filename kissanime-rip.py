#!/usr/bin/env python3

import cfscrape
import html5lib
from bs4 import BeautifulSoup as BS
import sys
import time
import random
from base64 import b64decode
import os
import re
from urllib.request import urlretrieve
from urllib.parse import urlparse

USAGE = """
Usage:
kissanime-rip.py
    [--eps=n1-n2 | --eps-until=n | --eps-since=n]
    [--output=path]
    [--download]
    [--quality=quality]
    ["http://kissanime.com/Anime/Anime-Name" |
    "path/to/old/download"]

    Examples:
        By default, everything is saved as a .m3u playlist. Add --download
        to save the video files locally.
        kissanime-rip.py
            Downloads new episodes of the anime in the working directory.
        kissanime-rip.py "path/to/old/download"
            Downloads new episodes of the anime in the given path.
        kissanime-rip.py "path/to/old/download" --download
            Downloads new episodes of the anime in the given path
            as video files.
        kissanime-rip.py "http://kissanime.com/Anime/Anime-Name"
            Downloads all episodes of Anime-Name to the folder "Anime-Name".
            If the folder already exists, download all new episodes.
        kissanime-rip.py "http://kissanime.com/Anime/Anime-Name" --eps=1-3
            Downloads episodes 1, 2 and 3 of Anime-Name.

    Optional arguments for controlling downloaded episodes (choose one):
    eps:
        --eps=1-3: download 1, 2, 3
        --eps=4-4: download 4
    eps-until:
        --eps-until=3: download 1, 2, 3
    eps-since:
        --eps-since=20: download 20, 21, 22, ...

    ^ These also support replacing the n with a string included in the title.
    It's particularly useful when the anime has multiple episodes in one file,
    fucking up the indexing.
    Known features: with --eps="str1-str2", the strings can't contain dashes
    other than the one separating the episodes.
    As a workaround, to start from "Episode 100-101", use "Episode 100"
    instead.
    Examples of this:
        --eps-since="Episode 012"
        --eps="Episode 010-Episode 020"


    Other options:
    download:
        Actually download the episodes instead of just creating playlists of
        the streaming URLs. Using the streaming playlists can save you a lot
        of time and disk lifetime, but it obviously doesn't work offline and
        can be a pain to seek on slow connections.
    output:
        --output="Kawaii Uguu School Love Comedy"
        Output folder for the playlist files. By default is the show name in
        URL path.
    quality:
        --quality=720
        --quality=1080p
        Select which quality to download. By default select the first option,
        which should be the best quality.

    Should work on KissCartoon and in case the domain changes, but it's not
    tested."""


class KissanimeRipper(object):
    """Extract streaming URLs from KissAnime and save them to .m3u playlists
    or download them"""
    def __init__(self, args, wait=(5, 10)):
        self.args = self._parse_args(args)
        _url = self.args.get('url')
        self.scraper = cfscrape.create_scraper()
        # Protection against possible scraping countermeasures.
        # Better safe than sorry.
        # You can't watch a 25-min ep in 10 seconds anyway.
        self.WAIT_RANGE = wait
        # other config
        self.URL_BASE = '{url.scheme}://{url.netloc}'.format(url=_url)

    def get_episodes(self):
        """Get the selected episodes. Either save the stream URLs as playlists
        or download the files."""
        self._initialize()
        try:
            os.makedirs(self.folder)
        except Exception as e: print(e)
        self._write_urlfile()
        if self.args.get('download'):
            process_ep = self._download_episode
        else:
            process_ep = self._write_episode_playlist

        start, end = self._get_episode_range()
        for url, title in self.episode_urls_and_titles[start:end]:
            url = self._get_stream_url(url)
            process_ep(url, title)

    def _write_urlfile(self):
        urlfile = '{}/.kissanime'.format(self.folder)
        if not os.path.isfile(urlfile):
            with open(urlfile, 'w', encoding='utf-8') as f:
                f.write(self.args['url'].geturl())

    def _initialize(self):
        """Get ready for extraction."""
        self.episode_urls_and_titles = self._episode_urls_and_titles()
        self.folder = self._folder()

    def _get_episode_range(self):
        """Return a start and end index that match the given arguments."""
        start = 0
        end = len(self.episode_urls_and_titles)
        titles = map(lambda ep: ep[1], self.episode_urls_and_titles)
        if self.args.get('eps='):
            eps = self.args.get('eps=')
            if type(eps[0]) == str and type(eps[1]) == str:
                for i, title in enumerate(titles):
                    if eps[0] in title:
                        start = i
                    elif eps[1] in title:
                        end = i + 1
            elif type(eps[0]) == int and type(eps[1]) == int:
                start = eps[0] - 1
                end = eps[1]
        elif self.args.get('eps-until='):
            until = self.args['eps-until=']
            if type(until) == str:
                for i, title in enumerate(titles):
                    if until in title:
                        end = i + 1
            elif type(until) == int:
                end = until
        elif self.args.get('eps-since='):
            since = self.args['eps-since=']
            if type(since) == str:
                for i, title in enumerate(titles):
                    if since in title:
                        start = i
            elif type(since) == int:
                start = since - 1
        # all new episodes
        else:
            downloaded = sorted(os.listdir(self.folder),
                key=str.lower, reverse=True)
            sanitized_titles = [self._sanitize_filename(title)
                for _, title in self.episode_urls_and_titles]
            for fn in downloaded:
                fn = os.path.splitext(fn)[0]
                try:
                    start = sanitized_titles.index(fn) + 1
                    break
                except ValueError:
                    continue
        return start, end

    def _write_episode_playlist(self, url, title):
        """Write the given URL and title to a .m3u playlist file."""
        filename = self._sanitize_filename(title) + '.m3u'
        print('Writing stream URL to {}'.format(filename))
        filename = '{}/{}'.format(self.folder, filename)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("""#EXTM3U\n#EXTINF:-1,{}\n{}""".format(title, url))

    def _download_episode(self, url, title):
        """Save the video stream to the disk.
        The filename will be sanitized(title).mp4."""
        filename = self._sanitize_filename(title) + '.mp4'
        print('Downloading {}...'.format(title))
        filename = '{}/{}'.format(self.folder, filename)
        urlretrieve(url, filename=filename)

    def _sanitize_filename(self, fn):
        """Make sure that the filenames don't contain illegal characters."""
        fn = fn.replace('..', '')
        fn = re.sub(r'[/\\\"\']', '', fn)
        return re.sub(r'[^a-zA-Z0-9\-\.\(\) ]', '_', fn)

    def _folder(self):
        """Set the output folder for playlists or downloads.

        First checks if an explicit output folder is given.
        If not, parse something from the URL."""
        if self.args.get('output='):
            return self.args['output=']
        elif self.nourl:
            return self.args['old_dl']
        else:
            # /Anime/Anime-name <-- split from '/' and take the rightmost part
            folder = self.args['url'].path.split('/', 2)[-1]
            return self._sanitize_filename(folder)

    def _parse_args(self, input_arguments):
        """Parse the command line arguments and return them as a dictionary."""
        self.nourl = False
        arg_container = dict()
        for inp_arg in input_arguments:
            if inp_arg.startswith('--eps='):
                eps = inp_arg[len('--eps='):].split('-')
                try:
                    eps = tuple(map(int, eps))
                except ValueError:
                    eps = tuple(ep.strip('"') for ep in eps)
                arg_container['eps='] = eps
            elif inp_arg.startswith('--eps-until='):
                until = inp_arg[len('--eps-until='):]
                try:
                    until = int(until)
                except ValueError:
                    until = until.strip('"')
                arg_container['eps-until='] = until
            elif inp_arg.startswith('--eps-since='):
                since = inp_arg[len('--eps-since='):]
                try:
                    since = int(since)
                except ValueError:
                    since = since.strip('"')
                arg_container['eps-since='] = since
            elif inp_arg.startswith('--quality='):
                quality = inp_arg[len('--quality='):]
                arg_container['quality='] = quality
            elif inp_arg.startswith('--output='):
                arg_container['output='] = inp_arg[len('--output='):]
            elif inp_arg == '--download':
                arg_container['download'] = True
            elif inp_arg.startswith('http'):
                arg_container['url'] = urlparse(inp_arg)
            else:
                if (os.path.isdir(inp_arg)):
                    arg_container['old_dl'] = inp_arg
                else:
                    print('Unknown argument: {}; ignored.'.format(inp_arg))
        if not arg_container.get('url'):
            self.nourl = True
            try:
                if not arg_container.get('old_dl'):
                    arg_container['old_dl'] = '.'
                urlfile = '{}/.kissanime'.format(arg_container['old_dl'])
                with open(urlfile, 'r', encoding='utf-8') as f:
                    arg_container['url'] = urlparse(f.read().strip())
            except Exception as e:
                raise Exception(USAGE)
        return arg_container

    def _soup(self, url):
        """Turn a URL into a BeautifulSoup4 object.
        Uses cfscrape to bypass CloudFlare protection."""
        page = self.scraper.get(url).content
        return BS(page, 'html5lib')

    def _episode_urls_and_titles(self):
        """Get episode page URLs and titles from the episode listing."""
        page = self._soup(self.args['url'].geturl())
        urls = page.find('table', {'class': 'listing'}).find_all('a')
        ret = []
        for a in reversed(urls):
            if a['href'].startswith('http'):
                url = a['href']
            else:
                url = self.URL_BASE + a['href']
            ret.append((url, a.string.strip()))
        return ret

    def _get_stream_url(self, url):
        """Scrape and decode the streaming url from the video viewer page."""
        wait_time = random.randint(*self.WAIT_RANGE)
        print('Waiting {}s before opening {}...'.format(wait_time, url))
        time.sleep(wait_time)
        page = self._soup(url)
        quality_selector = page.find(id='selectQuality')
        quality = self.args.get('quality=')
        try:
            option = quality_selector.find(text=re.compile(quality)).parent
        except (TypeError, AttributeError) as e:
            option = quality_selector.option
            if type(e) == AttributeError:
                print('quality "{}" not found'.format(quality))
        print('Selected quality: {}'.format(option.text))
        obfuscated = option['value']
        deobfuscated = self.h4x(obfuscated)
        print('Stream URL: {}'.format(deobfuscated))
        return deobfuscated

    def h4x(self, asp_lol):
        """KissAnime's obfuscated function for deobfuscating stream URLs
        turned out to be just base64 decode... what a shame."""
        return b64decode(asp_lol).decode()

def main():
    """Instantiate KissanimeRipper using command line arguments and run its
    get_episodes method."""
    ripper = KissanimeRipper(sys.argv[1:])
    ripper.get_episodes()

if __name__ == '__main__':
    main()
