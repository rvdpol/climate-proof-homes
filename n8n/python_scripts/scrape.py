"""Main funda scraper module"""

import argparse
import os
from collections import OrderedDict
from typing import List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

class FundaScraper(object):
    """
    A class used to scrape real estate data from the Funda website.
    """

    def __init__(
        self,
        area: str,
        want_to: str,
        page_start: int = 1,
        n_pages: int = 1,
        find_past: bool = False,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        publication_date: Optional[int] = None,
        property_type: Optional[str] = None,
        min_floor_area: Optional[str] = None,
        max_floor_area: Optional[str] = None,
        min_plot_area: Optional[str] = None,
        max_plot_area: Optional[str] = None,
        sort: Optional[str] = None,
    ):
        
        # Init attributes
        self.area = area.lower().replace(" ", "-")
        self.property_type = property_type
        self.want_to = want_to
        self.find_past = find_past
        self.page_start = max(page_start, 1)
        self.n_pages = max(n_pages, 1)
        self.page_end = self.page_start + self.n_pages - 1
        self.min_price = min_price
        self.max_price = max_price
        self.publication_date = publication_date
        self.min_floor_area = min_floor_area
        self.max_floor_area = max_floor_area
        self.min_plot_area = min_plot_area
        self.max_plot_area = max_plot_area
        self.sort = sort

        # Instantiate along the way
        self.links: List[str] = []
        self.raw_df = pd.DataFrame()
        self.clean_df = pd.DataFrame()
        self.base_url = 'https://www.funda.nl/en'
        self.selectors = {}

    def __repr__(self):
        return (
            f"FundaScraper(area={self.area}, "
            f"want_to={self.want_to}, "
            f"n_pages={self.n_pages}, "
            f"page_start={self.page_start}, "
            f"find_past={self.find_past}, "
            f"min_price={self.min_price}, "
            f"max_price={self.max_price}, "
            f"publication_date={self.publication_date}, "
            f"min_floor_area={self.min_floor_area}, "
            f"max_floor_area={self.max_floor_area}, "
            f"min_plot_area={self.min_plot_area}, "
            f"max_plot_area={self.max_plot_area}, "
            f"find_past={self.find_past})"
            f"min_price={self.min_price})"
            f"max_price={self.max_price})"
            f"publication_date={self.publication_date})"
            f"sort={self.sort})"
        )

    @property
    def to_buy(self) -> bool:
        """Determines if the search is for buying or renting properties."""
        if self.want_to.lower() in ["buy", "koop", "b", "k"]:
            return True
        elif self.want_to.lower() in ["rent", "huur", "r", "h"]:
            return False
        else:
            raise ValueError("'want_to' must be either 'buy' or 'rent'.")

    @property
    def check_publication_date(self) -> int:
        """Validates the 'publication_date' attribute."""
        if self.find_past:
            raise ValueError("'publication_date' can only be specified when find_past=False.")

        if self.publication_date in [None, 1, 3, 5, 10, 30]:
            return self.publication_date
        else:
            raise ValueError("'publication_date' must be either None, 1, 3, 5, 10 or 30.")

    @property
    def check_sort(self) -> str:
        """Validates the 'sort' attribute."""
        if self.sort in [
            None,
            "relevancy",
            "date_down",
            "date_up",
            "price_up",
            "price_down",
            "floor_area_down",
            "plot_area_down",
            "city_up" "postal_code_up",
        ]:
            return self.sort
        else:
            raise ValueError(
                "'sort' must be either None, 'relevancy', 'date_down', 'date_up', 'price_up', 'price_down', "
                "'floor_area_down', 'plot_area_down', 'city_up' or 'postal_code_up'. "
            )

    @staticmethod
    def _check_dir() -> None:
        """Ensures the existence of the directory for storing data."""
        if not os.path.exists("data"):
            os.makedirs("data")

    def get_info_from_one_parent(self, df, url: str):
        """Scrapes all available property links from a single Funda search page."""
        response = requests.get(url, headers={
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36"
        })
        soup = BeautifulSoup(response.text, "lxml")

        for i in range(1, 21):
            try:
                link =   soup.select(f'.css-1ml0i7b +div > .pt-4 > div:nth-child({i}) > div > div > div a')
                zipCity = self.get_value_from_css(soup, f'.css-1ml0i7b +div > .pt-4 > div:nth-child({i}) > div > div >div .text-neutral-80').strip()

                image = soup.select(f'.css-1ml0i7b +div > .pt-4 > div:nth-child({i}) > div > div > a > div > div > div> img')
                image_parts = image[0]['srcset'].split()
                data = {
                    'url': link[0]['href'],
                    'address': self.get_value_from_css(soup, f'.css-1ml0i7b +div > .pt-4 > div:nth-child({i}) > div > div > div h2').strip(),
                    'zip_code': zipCity[:7],
                    'city': zipCity[8:],
                    'floor_area' : self.get_value_from_css(soup, f'.css-1ml0i7b +div > .pt-4 > div:nth-child({i}) > div > div > div ul>li:nth-child(1)').strip(),
                    'plot_area': self.get_value_from_css(soup, f'.css-1ml0i7b +div > .pt-4 > div:nth-child({i}) > div > div> div ul>li:nth-child(2)').strip(),
                    'energy_label': self.get_value_from_css(soup, f'.css-1ml0i7b +div > .pt-4 > div:nth-child({i}) > div > div > div ul>li:nth-last-child(1)').strip(),
                    'price': self.get_value_from_css(soup, f'.css-1ml0i7b +div > .pt-4 > div:nth-child({i}) > div > div > div > div > p').strip(),
                    'image': image_parts[2][5:]
                }

                df = df._append(data, ignore_index=True)
            except Exception as e: 
                #print(e)
                #for now, just return the results we have. Should later check what the exception is so we dont miss results.
                continue
        return df
        
    def reset(
        self,
        area: Optional[str] = None,
        property_type: Optional[str] = None,
        want_to: Optional[str] = None,
        page_start: Optional[int] = None,
        n_pages: Optional[int] = None,
        find_past: Optional[bool] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        publication_date: Optional[int] = None,
        min_floor_area: Optional[str] = None,
        max_floor_area: Optional[str] = None,
        min_plot_area: Optional[str] = None,
        max_plot_area: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> None:
        """Resets or initializes the search parameters."""
        if area is not None:
            self.area = area
        if property_type is not None:
            self.property_type = property_type
        if want_to is not None:
            self.want_to = want_to
        if page_start is not None:
            self.page_start = max(page_start, 1)
        if n_pages is not None:
            self.n_pages = max(n_pages, 1)
        if find_past is not None:
            self.find_past = find_past
        if min_price is not None:
            self.min_price = min_price
        if max_price is not None:
            self.max_price = max_price
        if publication_date is not None:
            self.publication_date = publication_date
        if min_floor_area is not None:
            self.min_floor_area = min_floor_area
        if max_floor_area is not None:
            self.max_floor_area = max_floor_area
        if min_plot_area is not None:
            self.min_plot_area = min_plot_area
        if max_plot_area is not None:
            self.max_plot_area = max_plot_area
        if sort is not None:
            self.sort = sort

    @staticmethod
    def get_value_from_css(soup: BeautifulSoup, selector: str) -> str:
        """Extracts data from HTML using a CSS selector."""
        result = soup.select(selector)
        if len(result) > 0:
            result = result[0].text
        else:
            result = "na"
        return result
    
    @staticmethod
    def remove_duplicates(lst: List[str]) -> List[str]:
        """Removes duplicate links from a list."""
        return list(OrderedDict.fromkeys(lst))

    def fetch_all_links(self, page_start: int = None, n_pages: int = None) -> None:
        """Collects all available property links across multiple pages."""

        page_start = self.page_start if page_start is None else page_start
        n_pages = self.n_pages if n_pages is None else n_pages

        print("*** Phase 1: Fetch all the available links from all pages *** ")
        urls = []
        main_url = self._build_main_query_url()

        df = pd.DataFrame(columns = ['url','address','zip_code','city', 'floor_area','plot_area','energy_label'])
        for i in tqdm(range(page_start, page_start + n_pages)):
            try:
                df = self.get_info_from_one_parent(df,
                    f"{main_url}&search_result={i}"
                )
            except IndexError:
                self.page_end = i
                print(f"*** The last available page is {self.page_end} ***")
                break
        urls = self.remove_duplicates(urls)
        fixed_urls = [self.fix_link(url) for url in urls]

        print(
            f"*** Got all the urls. {len(fixed_urls)} houses found from {self.page_start} to {self.page_end} ***"
        )
        self.links = fixed_urls
        self.raw_df = df

    def _build_main_query_url(self) -> str:
        """Constructs the main query URL for the search."""
        query = "koop" if self.to_buy else "huur"

        main_url = (
            f"{self.base_url}/zoeken/{query}?selected_area=%5B%22{self.area}%22%5D"
        )

        if self.property_type:
            property_types = self.property_type.split(",")
            formatted_property_types = [
                "%22" + prop_type + "%22" for prop_type in property_types
            ]
            main_url += f"&object_type=%5B{','.join(formatted_property_types)}%5D"

        if self.find_past:
            main_url = f'{main_url}&availability=%5B"unavailable"%5D'

        if self.min_price is not None or self.max_price is not None:
            min_price = "" if self.min_price is None else self.min_price
            max_price = "" if self.max_price is None else self.max_price
            main_url = f"{main_url}&price=%22{min_price}-{max_price}%22"

        if self.publication_date is not None:
            main_url = f"{main_url}&publication_date={self.check_publication_date}"

        if self.min_floor_area or self.max_floor_area:
            min_floor_area = "" if self.min_floor_area is None else self.min_floor_area
            max_floor_area = "" if self.max_floor_area is None else self.max_floor_area
            main_url = f"{main_url}&floor_area=%22{min_floor_area}-{max_floor_area}%22"

        if self.min_plot_area or self.max_plot_area:
            min_plot_area = "" if self.min_plot_area is None else self.min_plot_area
            max_plot_area = "" if self.max_plot_area is None else self.max_plot_area
            main_url = f"{main_url}&plot_area=%22{min_plot_area}-{max_plot_area}%22"

        if self.sort is not None:
            main_url = f"{main_url}&sort=%22{self.check_sort}%22"

        print(f"*** Main URL: {main_url} ***")
        return main_url

    def run(
        self, raw_data: bool = False, save: bool = False, filepath: str = None
    ) -> pd.DataFrame:
        """
        Runs the full scraping process, optionally saving the results to a CSV file.

        :param raw_data: if true, the data won't be pre-processed
        :param save: if true, the data will be saved as a csv file
        :param filepath: the name for the file
        :return: the (pre-processed) dataframe from scraping
        """
        self.fetch_all_links()
        #self.scrape_pages()

        df = self.raw_df

        print("*** Done! ***")
        return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--area",
        type=str,
        help="Specify which area you are looking for",
        default="amsterdam",
    )
    parser.add_argument(
        "--want_to",
        type=str,
        help="Specify you want to 'rent' or 'buy'",
        default="rent",
        choices=["rent", "buy"],
    )
    parser.add_argument(
        "--find_past",
        action="store_true",
        help="Indicate whether you want to use historical data",
    )
    parser.add_argument(
        "--page_start", type=int, help="Specify which page to start scraping", default=1
    )
    parser.add_argument(
        "--n_pages", type=int, help="Specify how many pages to scrape", default=1
    )
    parser.add_argument(
        "--min_price", type=int, help="Specify the min price", default=None
    )
    parser.add_argument(
        "--max_price", type=int, help="Specify the max price", default=None
    )
    parser.add_argument(
        "--publication_date",
        type=int,
        help="Specify the days since publication",
        default=None,
    )
    parser.add_argument(
        "--sort",
        type=str,
        help="Specify sorting",
        default=None,
        choices=[
            None,
            "relevancy",
            "date_down",
            "date_up",
            "price_up",
            "price_down",
            "floor_area_down",
            "plot_area_down",
            "city_up" "postal_code_up",
        ],
    )
    parser.add_argument(
        "--raw_data",
        action="store_true",
        help="Indicate whether you want the raw scraping result",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Indicate whether you want to save the data",
    )

    args = parser.parse_args()
    scraper = FundaScraper(
        area=args.area,
        want_to=args.want_to,
        find_past=args.find_past,
        page_start=args.page_start,
        n_pages=args.n_pages,
        min_price=args.min_price,
        max_price=args.max_price,
        publication_date=args.publication_date,
        sort=args.sort,
    )
    df = scraper.run(raw_data=args.raw_data, save=args.save)
    print(df.head())
