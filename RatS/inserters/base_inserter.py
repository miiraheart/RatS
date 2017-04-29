import datetime
import os
import sys
import time

from selenium.common.exceptions import ElementNotVisibleException, NoSuchElementException, \
    ElementNotInteractableException

from RatS.utils import file_impex
from RatS.utils.command_line import print_progress

TIMESTAMP = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')


class Inserter:
    def __init__(self, site):
        self.site = site
        self.failed_movies = []
        self.exports_folder = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'RatS', 'exports'))
        self.failed_movies_filename = '%s_%s_failed.json' % (TIMESTAMP, self.site.site_name)

    def insert(self, movies, source):
        counter = 0
        sys.stdout.write('\r===== %s: posting %i movies\r\n' % (self.site.site_name, len(movies)))
        sys.stdout.flush()

        for movie in movies:
            movie_detail_page_found = self._go_to_movie_detail_page(movie)
            if movie_detail_page_found:
                self._post_movie_rating(movie[source.lower()]['my_rating'])
            else:
                self.failed_movies.append(movie)
            counter += 1
            print_progress(counter, len(movies), prefix=self.site.site_name)

        self._print_summary(movies)
        self._handle_failed_movies(movies)
        self.site.kill_browser()

    def _go_to_movie_detail_page(self, movie):
        if self.site.site_name.lower() in movie and movie[self.site.site_name.lower()]['url'] != '':
            self.site.browser.get(movie[self.site.site_name.lower()]['url'])
            success = True
        else:
            success = self._find_movie(movie)
        return success

    def _find_movie(self, movie):
        self._search_for_movie(movie)
        time.sleep(1)
        try:
            search_results = self._get_search_results(self.site.browser.page_source)
        except (NoSuchElementException, KeyError):
            time.sleep(3)
            search_results = self._get_search_results(self.site.browser.page_source)
        for result in search_results:
            if self._is_requested_movie(movie, result):
                return True  # Found
        return False  # Not Found

    def _search_for_movie(self, movie):
        pass

    @staticmethod
    def _get_search_results(search_result_page):
        pass

    def _is_requested_movie(self, movie, result):
        pass

    def _post_movie_rating(self, my_rating):
        try:
            self._click_rating(my_rating)
        except (ElementNotVisibleException, NoSuchElementException, ElementNotInteractableException):
            time.sleep(3)
            self._click_rating(my_rating)

    def _click_rating(self, my_rating):
        pass

    def _print_summary(self, movies):
        success_number = len(movies) - len(self.failed_movies)
        sys.stdout.write('\r\n===== %s: sucessfully posted %i of %i movies\r\n' %
                         (self.site.site_name, success_number, len(movies)))
        sys.stdout.flush()

    def _handle_failed_movies(self, movies):
        for failed_movie in self.failed_movies:
            sys.stdout.write('FAILED TO FIND: %s (%i)\r\n' % (failed_movie['title'], failed_movie['year']))
        if len(self.failed_movies) > 0:
            file_impex.save_movies_to_json(movies, folder=self.exports_folder, filename=self.failed_movies_filename)
            sys.stdout.write('===== %s: export data for %i failed movies to %s/%s\r\n' %
                             (self.site.site_name, len(self.failed_movies),
                              self.exports_folder, self.failed_movies_filename))
        sys.stdout.flush()
