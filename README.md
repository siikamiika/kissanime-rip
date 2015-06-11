# kissanime-rip
A command line tool for saving KissAnime's videos for use with better video players.

## Examples
Simple example: `kissanime-rip.py --download http://kissanime.com/Anime/Anime-Name`

To save the videos as streaming playlists, leave out the `--download`.

For more advanced use, see Usage.
## Usage
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
            Output folder for the playlist files. By default is the show name in URL path.

        Should work on KissCartoon and in case the domain changes, but it's not tested.

## Dependencies
Make sure you have Node.js installed, because cfscrape doesn't want to run without it.

Other dependencies can be obtained with pip. The list should be something like this:

    pip install cfscrape beautifulsoup4 html5lib
