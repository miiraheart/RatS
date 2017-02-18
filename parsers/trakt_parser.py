from bs4 import BeautifulSoup

from data.movie import Movie
from parsers.base_parser import Parser
from sites.trakt import Trakt


class TraktRatingsParser(Parser):
    def __init__(self):
        super(TraktRatingsParser, self).__init__(Trakt())

    def parse(self):
        self.browser.get(self.site.MY_RATINGS_URL)
        overview_page = BeautifulSoup(self.browser.page_source, 'html.parser')
        self._parse_html(overview_page)
        return self.movies

    def _parse_html(self, overview):
        pages_count = overview.find(id='rating-items').find_all('li', class_='page')[-1].find('a').get_text()
        movies_count = overview.find('section', class_='subnav-wrapper').find('a', attrs={'data-title': 'Movies'}). \
            find('span').get_text().strip().replace(',', '')

        print('===== Parsing %s pages with %s movies in total =====' % (pages_count, movies_count))
        # for i in range(1, 2):  # testing purpose
        for i in range(1, int(pages_count) + 1):
            self.browser.get(self.site.MY_RATINGS_URL + '?page=%i' % i)
            self._parse_movie_listing_page()

    def _parse_movie_listing_page(self):
        movie_listing_page = BeautifulSoup(self.browser.page_source, 'html.parser')
        movies_tiles = movie_listing_page.find(class_='row posters').find_all('div', attrs={'data-type': 'movie'})
        for movie_tile in movies_tiles:
            movie = self._parse_movie(movie_tile)
            self.movies.append(movie)

    def _parse_movie(self, movie_tile):
        movie = Movie()
        movie.trakt.id = movie_tile['data-movie-id']
        movie.trakt.url = 'https://trakt.tv%s' % movie_tile['data-url']
        movie.title = movie_tile.find('h3').get_text()
        movie.trakt.my_rating = movie_tile.find_all('h4')[1].get_text().strip()

        self.browser.get(movie.trakt.url)

        movie_page = BeautifulSoup(self.browser.page_source, 'html.parser')

        movie.trakt.overall_rating = movie_page.find(id='summary-ratings-wrapper').find('ul', class_='ratings') \
            .find('li', attrs={'itemprop': 'aggregateRating'}).find('div', class_='rating').get_text()

        external_links = movie_page.find(id='info-wrapper').find('ul', class_='external').find_all('a')
        for link in external_links:
            if 'imdb.com' in link['href']:
                movie.imdb.url = link['href']
                movie.imdb.id = movie.imdb.url.split('/')[-1]
            if 'themoviedb.org' in link['href']:
                movie.tmdb.url = link['href']
                movie.tmdb.id = movie.tmdb.url.split('/')[-1]

        print("      Parsed movie: %s" % movie.title)

        return movie
