from bs4 import BeautifulSoup
import pandas as pd
import unicodedata
import itertools
import requests
import time
import re


def get_soup(url):
    """create a tree structure (BeautifulSoup) out of a get request's html """
    r = requests.get(url)
    return BeautifulSoup(r.content, "html5lib")

def scrape_talk_urls(conference_url):
    """retreive a list of urls for each talk in a bi-annual conference 
    
    Per session of conference there are generally 5-8 talks given and 
    around 5 sessions per conference
    """
    soup = get_soup(conference_url)

    div = soup.find("div", {"class": "section-wrapper lumen-layout lumen-layout--landing-3"})
    sessions = div.findChildren("div", recursive=False)

    return ["https://www.lds.org" + a["href"]
            for session in sessions
            for a in session.find_all("a", href=True)
            if re.search("^/general-conference/\d{4}/(04|10)/.*[?]lang=eng", a["href"])]

def scrape_talk_data(url):
    """scrapes a single talk for data such as: 
    
    title: name of the talk 
    conference: "April or October - <year>" 
    calling: speaker's calling in Church 
    speaker: name of the speaker 
    content: the text of the entire talk presented 

    It is possible for some of the urls to fail for multiple reasons. The specific 
    logic provided allows a majority of the data to come through without problems. 
    """
    try:
        soup = get_soup(url)

        title = soup.find("div", {"class": "title-block"}).find("h1", {"class": "title"}).text
        conference = soup.find("a", {"class": "sticky-banner__link"}).text
        calling = soup.find("p", {"class": "article-author__title"}).text

        # older talks don't have the same exact structure
        speaker_div = soup.find("a", {"class": "article-author__name"})
        if speaker_div == None:
            speaker = soup.find("div", {"class": "article-author"}).text
        else:
            speaker = speaker_div.text

        content = soup.find("div", {"class": "article-content"}).text

        return {
            "title": title,
            "speaker": speaker,
            "calling": calling,
            "conference": conference,
            "url": url,
            "talk": content,
        }
    except Exception as e:
        print(f"\n\n\nURL: {url} FAILED")
        print(f"Exception: {e}\n\n\n")
        return dict()


# create all permutations of urls from 1971-2018
#   landing pages for a bi-annual session of conference always follow the same structure:
#   https://www.lds.org/general-conference/<year>/<month>?lang=eng
urls = [f"https://www.lds.org/general-conference/{year}/{month}?lang=eng"
        for year in range(1971, 2019)
        for month in ["04", "10"]]

start = time.time()

# create a list of all the urls for every talk 
all_urls = [scrape_talk_urls(url) for url in urls]
all_urls = list(itertools.chain(*all_urls)) # flatten into single list from a list of lists
print(len(all_urls))  # validate total number of urls

conference_talks = []
for i, url in enumerate(all_urls):
    print(f"Talk number {i+1}")
    conference_talks.append(scrape_talk_data(url))

conference_df = pd.DataFrame(conference_talks)

# simple cleaning
for col in conference_df.columns:
    conference_df[col] = conference_df[col].apply(lambda x: unicodedata.normalize("NFKD", x) if pd.notnull(x) else x)
    conference_df[col] = conference_df[col].apply(lambda x: x.replace("\n", "") if pd.notnull(x) else x)
    conference_df[col] = conference_df[col].apply(lambda x: x.replace("\t", "") if pd.notnull(x) else x)

print(conference_df)
# finish
conference_df.to_csv("conference_talks.csv", index=False)

end = time.time()
print(end - start)
