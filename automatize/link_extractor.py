from scrapy.crawler import CrawlerRunner, CrawlerProcess

import requests
import pickle
from urllib.parse import urlparse
from urllib.parse import unquote
from scrapy import Spider, Request
from scrapy.linkextractors import LinkExtractor
from tqdm import tqdm
from bs4 import BeautifulSoup

headers = {
    'user-agent': "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"}


class automation_blog_feed_spot(Spider):

    def __init__(self):
        self.urls = ["https://blog.feedspot.com/news_websites_directory/"]
        self.found_links = []
        self.links_file = "links1.pkl"

    def start_requests(self):
        for doc_id in tqdm(self.urls):
            yield Request(url=doc_id,
                          callback=self.parse_find_link,
                          cb_kwargs={"doc_id": doc_id})

    def parse(self, response):
        print(response.url)
        r = requests.get(response.url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        for i in soup.find_all("h3", {"class": "feed_heading"}):
            a = i.find(href=True)
            # print(a["href"])
            link = unquote(a["href"].split("site:")[1])
            self.found_links.append(link)

    def close(self, spider, reason):
        with open(self.links_file, "wb") as jfile:
            pickle.dump(self.found_links, jfile)

    def retry(self, failure):
        """
        """
        # first I extract some data from the original request.

        print('Pattern', failure.request.url)
        print(failure)

    def parse_find_link(self, response, doc_id):
        """
        """
        extractor = LinkExtractor(allow_domains=urlparse(response.url).netloc)
        links = extractor.extract_links(response)
        found = False
        print(links)
        for link in tqdm(links):
            if "src" in link.url:
                pass
            elif "news websites" in link.text.lower():
                yield Request(url=link.url, callback=self.parse)


def main():
    process = CrawlerProcess()
    process.crawl(automation_blog_feed_spot)
    process.start()


def update_links():
    # reading the old links file
    with open("links.pkl", "rb") as jfile:
        loaded_links = pickle.load(jfile)
    # reading the scraped links file
    with open("links1.pkl", "rb") as jfile:
        loaded_links1 = pickle.load(jfile)
    # updating the list of links
    updated_list = list(set(loaded_links).union(set(loaded_links1)))
    # writing the output
    with open("links.pkl", "wb") as jfile:
        pickle.dump(updated_list, jfile)


if __name__ == "__main__":
    main()
    update_links()
