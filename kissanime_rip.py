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

USAGE = \
"""
Usage: kissanime-rip.py [--eps=n1-n2 | --eps-until=n | --eps-since=n] [--output=path] [--download] "http://kissanime.com/Anime/Anime-Name/"
    By default, download all new episodes.
    This means, if the newest one you have is Kawaii Uguu School Love Comedy Episode 9001.mp4, it will download from 9002 onward.
    If there are no episodes, it will download every single one of them.

    Optional arguments for controlling downloaded episodes (choose one):
    eps:
        start-end (1-3 will download 1, 2, 3; 4-4 will download only 4)
    eps-until:
        episodes until n (if n == 3, download 1, 2, 3)
    eps-since:
        episodes since n (if n == 20, download 20, 21, 22, ...)

    Other options:
    download:
        Actually download the episodes instead of just creating playlists of the streaming URLs.
        Using the streaming playlists can save you a lot of time and disk lifetime,
        but it obviously doesn't work offline and can be a pain to seek on slow connections.
    output:
        Output folder for the playlist files. By default is the Anime-Name part of the URL."""


class KissanimeRipper(object):
    """Extract streaming URLs from KissAnime and save them to .m3u8 playlists
    or download them"""
    def __init__(self, args, wait=(5, 10), url_base='http://kissanime.com'):
        self.args = self._parse_args(args)
        if not self.args.get('url'):
            raise Exception(USAGE)
        self.scraper = cfscrape.create_scraper()
        # Protection against possible scraping countermeasures.
        # Better safe than sorry.
        # You can't watch a 25-min ep in 10 seconds anyway.
        self.WAIT_RANGE = wait
        # other config
        self.URL_BASE = url_base

    def get_episodes(self):
        """Get the selected episodes. Either save the stream URLs as playlists
        or download the files."""
        self._initialize()
        try:
            os.makedirs(self.folder)
        except Exception as e: print(e)

        if self.args.get('download'):
            process_ep = self._download_episode
        else:
            process_ep = self._write_episode_playlist

        start, end = self._get_episode_range()
        for url, title in self.episode_urls_and_titles[start:end]:
            url = self._get_stream_url(url)
            process_ep(url, title)

    def _initialize(self):
        """Get ready for extraction."""
        self.episode_urls_and_titles = self._episode_urls_and_titles()
        self.folder = self._folder()

    def _get_episode_range(self):
        start = 0
        end = len(self.episode_urls_and_titles)
        if self.args.get('eps='):
            start, end = map(int, self.args['eps='].split('-'))
            start -= 1
        elif self.args.get('eps-until='):
            end = int(self.args['eps-until='])
        elif self.args.get('eps-since='):
            start = int(self.args['eps-since=']) - 1
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
        """Write the given URL and title to a .m3u8 playlist file."""
        filename = self._sanitize_filename(title) + '.m3u8'
        print('Writing stream URL to {}'.format(filename))
        filename = '{}/{}'.format(self.folder, filename).lstrip('/')
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("""#EXTM3U\n#EXTINF:-1,{}\n{}""".format(title, url))

    def _download_episode(self, url, title):
        """Save the video stream to the disk.
        The filename will be sanitized(title).mp4."""
        filename = self._sanitize_filename(title) + '.mp4'
        print('Downloading {}...'.format(title))
        filename = '{}/{}'.format(self.folder, filename).lstrip('/')
        urlretrieve(url, filename=filename)

    def _sanitize_filename(self, fn):
        """Make sure that the filenames don't contain illegal characters."""
        fn = re.sub(r'[/\\\.\"\']', '', fn)
        return re.sub(r'[^a-zA-Z0-9\-\.\(\) ]', '_', fn)

    def _folder(self):
        """Set the output folder for playlists or downloads.

        First checks if an explicit output folder is given.
        If not, parse something from the URL."""
        if self.args.get('output='):
            return self._sanitize_filename(self.args['output='])
        else:
            folder = self.args['url']
            folder = folder[len(self.URL_BASE + '/Anime/'):]
            return self._sanitize_filename(folder)

    def _parse_args(self, input_arguments):
        """Parse the command line arguments and return them as a dictionary."""
        recognized_arguments = ['--eps=', '--eps-until=', '--eps-since=',
            '--output=', '--download']
        arg_container = dict()
        for inp_arg in input_arguments:
            for recog_arg in recognized_arguments:
                if inp_arg.startswith(recog_arg):
                    arg_container[recog_arg[2:]] = \
                        inp_arg[len(recog_arg):] or True
                    break
            else:
                arg_container['url'] = inp_arg

        return arg_container

    def _soup(self, url):
        """Turn a URL into a BeautifulSoup4 object.
        Uses cfscrape to bypass CloudFlare protection."""
        page = self.scraper.get(url).content
        return BS(page, 'html5lib')

    def _episode_urls_and_titles(self):
        """Get episode page URLs and titles from the episode listing."""
        page = self._soup(self.args['url'])
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
        obfuscated = page.find(id='selectQuality').option['value']
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
