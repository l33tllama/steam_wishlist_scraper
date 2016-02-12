#! /usr/bin/python
from __future__ import division

import ConfigParser
import datetime
import json
import sys
from BeautifulSoup import BeautifulSoup
from math import pow

import requests


def get_max_splits(price):
    if price > 192:
        print "todo: calculate higher amount of fractions.. only allowing up to 7 for now, may give weird results"
        return 7
    elif 192 >= price > 96:
        print "High split - this may give weird results.."
        return 7
    elif 96 >= price > 48:
        return 6
    elif 48 >= price > 24:
        return 5
    elif 24 >= price > 12:
        return 4
    elif 12 >= price > 6:
        return 3
    elif 6 >= price > 3:
        return 2
    elif 3 >= price > 0:
        return 1
    else:
        print("Number < 0.. returning -1")
        return -1


class WishListScraper:
    saved_username = False
    empty_wishlist_items_db = {}
    wishlist_items_arr = []
    html = ''
    config = ConfigParser.RawConfigParser()
    loadedWishlist = False
    databaseEmpty = True

    def load_config_file(self):
        self.config.readfp(open('config.cfg'))

    def get_username(self):
        return self.config.get('All', 'username')

    def set_username(self, username):
        self.config.set('All', 'username', username)
        with open('config.cfg', 'w') as configFile:
            self.config.write(configFile)

    def enter_new_username(self):
        return not self.config.get('All', 'use_same_username')

    def read_json_games(self):
        """

        :rtype: None
        """
        try:
            games = open('games.json', 'r')
            self.wishlist_items_db = json.load(games)
        except IOError:
            print "Wishlisted games database not found.. creating it!"
            games = open('games.json', 'w+')
            json.dump({'wishlisted_items': []}, games)
            self.wishlist_items_db = {'wishlisted_items': []}
        except ValueError:
            print "Wishlisted games database error found.. re-creating it!"
            games = open('games.json', 'w+')
            json.dump({'wishlisted_items': []}, games)
            self.wishlist_items_db = {'wishlisted_items': []}
        finally:
            self.loadedWishlist = True

    def clear_games_db(self):
        games = open('games.json', 'w+')
        json.dump({'wishlisted_items': []}, games)
        self.wishlist_items_db = {'wishlisted_items': []}

    def save_games_db(self):
        games = open('games.json', 'w+')
        json.dump(self.wishlist_items_db, games)

    def count_wishlisted_games(self):
        if not self.loadedWishlist:
            self.read_json_games()

        games_arr = self.wishlist_items_db['wishlisted_items']
        games_count = len(games_arr)
        return games_count

    def load_static_html(self):
        with open('static_page.html', 'r') as myfile:
            self.html = myfile.read().replace('\n', '')

    def load_live_wishlist(self):
        response = requests.get("http://steamcommunity.com/id/l33t_llama/wishlist")
        self.html = response.content

    @staticmethod
    def load_json_games():
        print "todo"

    def parse_html(self):
        self.soup = BeautifulSoup(self.html)
        wishlist_items = self.soup.find('div', attrs={'id': 'wishlist_items'})
        i = 0
        for item in wishlist_items.findAll('div', attrs={'class': 'wishlistRow '}):
            i += 1
            game_name = 'NA'
            game_url = 'NA'
            game_price = 999
            on_sale = False
            for cell in item.findAll('h4'):
                game_name = cell.text
            for storelink in item.findAll('div', attrs={'class': 'wishlistRowItem'}):
                game_url = storelink.find('div', attrs={'class': 'storepage_btn_ctn'}).find('a')['href']
                game_price_el = storelink.find('div', attrs={'class': 'price'})
                # print game_price_el
                try:
                    game_price_str = game_price_el.text[1:]
                    if len(game_price_str) > 0:
                        game_price = float(game_price_str)
                except AttributeError:
                    try:
                        game_sale_price_el = storelink.find('div', attrs={'class': 'discount_final_price'})
                        game_sale_price_str = game_sale_price_el.text[1:]
                        on_sale = True
                        game_price = float(game_sale_price_str)
                    except AttributeError:
                        print game_name + " has no price :("

            self.wishlist_items_db['wishlisted_items'].append(
                {'name': game_name, 'url': game_url, 'userscore': 0, 'price': game_price, 'onsale': on_sale})

        print "Found " + str(i) + " items."

    def read_each_game_page(self):
        # newlist = sorted(wishlist_items_arr, key=lambda k: k['userscore'])
        avg_time = 0
        item_count = len(self.wishlist_items_db['wishlisted_items'])
        c = 0
        initial_time = datetime.datetime.now()
        for item in self.wishlist_items_db['wishlisted_items']:
            # print str(item['url'])
            c += 1
            start_time = datetime.datetime.now()
            # print "getting page for: " + item['name']
            sys.stdout.write("getting page for: " + item['name'] + "\n")
            # <span class="nonresponsive_hidden responsive_reviewdesc">
            if item['url'] is not None and item['url'] is not '':
                print item['url']
                item_response = BeautifulSoup(requests.get(str(item['url'])).content)
                try:
                    score_text = item_response.find('span',
                                                    attrs={'class': 'nonresponsive_hidden responsive_reviewdesc'}).text
                    if score_text[4] == "%":
                        score = int(score_text[2:4])
                    elif score_text[5] == "%":
                        score = int(score_text[2:5])
                    else:
                        score = 0
                    print ("Score: %f" % score)
                    item['userscore'] = score
                except AttributeError:
                    sys.stdout.write("this page doesn't have a userscore.. defaulting to 0\n")
                    item['userscore'] = 0
                    # print "this page doesn't have a userscore.. defaulting to 0"
                finally:
                    end_time = datetime.datetime.now()
                    delta_time = (end_time - start_time).microseconds / 1000000
                    avg_time = (avg_time + delta_time) / 2
                    # total_time = end_time - initial_time
                    # eta: num_remaining * avg_time
                    eta = (item_count - c) * avg_time
                    sys.stdout.write('Completed: %d/%d average time: %f ETA: %f\n' % (c, item_count, avg_time, eta))
                    sys.stdout.flush()

        print("Done!")

    # for testing, before we start scraping..
    def fill_db_with_dummy_vals(self):
        import names, random
        from math import floor
        for i in range(0, 20):
            item = {}
            name = names.get_full_name()
            userscore = floor(random.random() * 100)
            price = floor(random.random() * 100)
            item['name'] = name
            item['userscore'] = userscore
            item['price'] = price
            self.wishlist_items_db['wishlisted_items'].append(item)
            print "Adding " + name + " score: " + str(userscore) + " price: " + str(price)

        games = open('games.json', 'w+')
        json.dump(self.wishlist_items_db, games)

    def get_best_games(self, max_price, num_games, num_results, include_not_onsale):
        selected_games = []
        # todo: more splits..
        splits = [
            [1],
            [2 / 3, 1 / 3],
            [1 / 2, 1 / 3, 1 / 6],
            [1 / 2, 1 / 4, 1 / 6, 1 / 12],
            [1 / 2, 1 / 4, 1 / 8, 1 / 12, 1 / 24],
            [1 / 2, 1 / 4, 1 / 8, 1 / 16, 1 / 24, 1 / 48],
            [1 / 2, 1 / 4, 1 / 8, 1 / 16, 1 / 32, 1 / 48, 1 / 96],
            [1 / 2, 1 / 4, 1 / 8, 1 / 16, 1 / 32, 1 / 64, 1 / 96, 1 / 192]
        ]
        total_max_price = 0
        total_min_price = 0
        split = 2
        last_max_price = 0
        last_min_price = 0
        for g in range(1, num_games + 1):
            # magic divisor... not scaling well..
            #max_price_i = ((split * num_games + 1) * max_price) / pow(num_games, 2)
            max_price_i = splits[num_games - 1][g - 1] * max_price
            if g > 1:
                max_price_im1 = splits[num_games - 1][g - 2] * max_price
                price_delta = (max_price_im1 - last_max_price)
                if price_delta > 0:
                    max_price_i += price_delta
                    print("Last max price: %f adding %f to this price bracket." % (
                        last_max_price, (max_price_im1 - last_max_price)))
                if last_min_price > max_price_i:
                    print "My calculations may be incorrect.. sadface.."
                    max_price_i = last_min_price

            split /= 2
            total_max_price += max_price_i
            this_min_price = 0
            print "Under: " + str(max_price_i)
            max_price_ip1 = 0
            if g < num_games:
                #max_price_ip1 = ((split * num_games + 1) * max_price) / pow(num_games, 2)
                max_price_ip1 = 1.05 * splits[num_games - 1][g] * max_price
                last_min_price = max_price_ip1
                print "Above : " + str(max_price_ip1)

            all_under_current_price = []
            for item in self.wishlist_items_db['wishlisted_items']:
                if item['price'] < max_price_i:
                    skipAdd = False
                    if g < num_games:
                        if (item['price'] < max_price_ip1):
                            skipAdd = True
                    if not item['onsale'] and not include_not_onsale:
                        skipAdd = True

                    if not skipAdd:
                        all_under_current_price.append(item)
            if len(all_under_current_price) > 0:
                repeat_count = 0
                userscore_sorted = sorted(all_under_current_price, key=lambda k: k['userscore'], reverse=True)
                this_min_price = userscore_sorted[0]['price']
                last_max_price = userscore_sorted[0]['price']
                loop_finished = False
                i = 0
                while not loop_finished:
                    item = userscore_sorted[i]
                    this_min_price = min(item['price'], this_min_price)
                    last_max_price = max(item['price'], last_max_price)

                    print("%d: %s - %s" % (i + 1, item['name'], item['url']))
                    print("\tscore: %d%c" % (item['userscore'], '%'))
                    print("\tprice: $%0.2f" % item['price'])

                    for selected in selected_games:
                        if item['name'] == selected['name']:
                            print("Repeat game detected, increasing results count")
                            repeat_count += 1
                    selected_games.append(item)
                    i += 1
                    if i >= repeat_count + min(len(userscore_sorted), num_results):
                        loop_finished = True
                total_min_price += this_min_price

        print("Total min price %f max price: %f" % (total_min_price, total_max_price))

    def __init__(self):
        self.wishlist_items_db = {}
        # Read settings from config file, get username
        self.load_config_file()
        username = self.get_username()
        done = False
        # If no username set, get user to enter one
        if username == '' or self.enter_new_username():
            print 'Enter Steam username: '
            new_username = raw_input()
            print "Using " + new_username
            self.set_username(new_username)

        # read pre-existing wishlisted games data file, if it exists (otherwise it will create a new one)
        print "Loading: " + username + "'s wishlist.."
        self.read_json_games()

        # Count number of games. If 0, it will ask user to scrape their wishlist from the Steam website
        games_count = self.count_wishlisted_games()
        print str(games_count) + " games found in local db"
        if games_count < 1:  # No games in db
            print "No games in wishlist! Database must be empty, or please add some games to your wishlist"
            raw_input(
                "Press ENTER to scrape Steam website. (This may take some time if you have many wihlisted items): ")
            self.load_live_wishlist()
            self.parse_html()
            self.read_each_game_page()  # scrape!!
            self.save_games_db()
        else:
            yn = raw_input("Database already filled. Scrape Steam again? [y/N]: ")
            if yn == 'y' or yn == 'Y':
                self.clear_games_db()
                self.load_live_wishlist()
                self.parse_html()
                self.read_each_game_page()  # scrape!!
                self.save_games_db()
            run_once = False
            while not done:

                max_price = float(raw_input("Enter max price: \t"))
                max_splits = get_max_splits(max_price)
                num_games = int(raw_input("Enter num games [1-%d]: \t" % max_splits))
                num_results_in = raw_input("Enter max results [10]: \t")
                include_not_onsale_in = raw_input("Include games not on sale?[y/N]")
                include_not_onsale = False
                num_results = 10

                if include_not_onsale_in == 'y' or include_not_onsale_in == 'Y':
                    include_not_onsale = True

                if num_results_in != '':
                    num_results = int(num_results_in)

                self.get_best_games(max_price, min(max_splits, num_games), num_results, include_not_onsale)
                if not run_once:
                    yn = raw_input("Run again? [Y/n")
                    if yn == 'n' or yn == 'N':
                        done = True


scraper = WishListScraper()

# TODO: GUI with more dynamic options generator - instant update when changing values like price and number of games
# TODO: consider popularity (or number of reviews) somehow. Unpopular games maybe reduce score by a fraction times how unpopular they are?
# TODO: less greedy database updating - only update games that have changed price, or newly added items, or removed items
# FIXME: issue with large max price
# For now it works well enough :P
