# kissanime-rip
A command line tool for saving KissAnime's videos for use with better video players.

## Examples
Simple example: `kissanime-rip.py --download http://kissanime.com/Anime/Anime-Name`

To save the videos as streaming playlists, leave out the `--download`.

For more advanced use, see Usage.
## Usage
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
        tested.

## Dependencies
Make sure you have Node.js installed, because cfscrape doesn't want to run without it.

Other dependencies can be obtained with pip. The list should be something like this:

    pip install cfscrape beautifulsoup4 html5lib
