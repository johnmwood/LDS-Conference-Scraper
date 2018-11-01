from bs4 import BeautifulSoup
import pandas as pd 
import unicodedata
import itertools
import threading 
import requests 
import time
import re 



def get_soup(url): 
    r = requests.get(url)
    return BeautifulSoup(r.content, "html5lib")

# get all sessions within a conference 
def scrape_talk_urls(conference_url): 
    soup = get_soup(conference_url) 

    div = soup.find("div", {"class": "section-wrapper lumen-layout lumen-layout--landing-3"})
    sessions = div.findChildren("div", recursive=False)

    return ["https://www.lds.org" + a["href"]
            for session in sessions
            for a in session.find_all("a", href=True) 
            if re.search("^/general-conference/\d{4}/(04|10)/.*[?]lang=eng", a["href"])]

def scrape_talk_data(url): 
    try: 
        soup = get_soup(url)
        # time.sleep(0.2) 

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
        print(f"Exception: {e} occurred\n\n\n") 


# get all conferences  
urls = [f"https://www.lds.org/general-conference/{year}/{month}?lang=eng"
        for year in range(2018, 2019) 
        for month in ["04", "10"]]

start = time.time()

# t = threading.Thread(target=course.scrape_course_data, args=())
# t.start()

all_urls = [scrape_talk_urls(url) for url in urls]
all_urls = list(itertools.chain(*all_urls)) # compress into single list 
print(len(all_urls))

conference_talks = []
for i, url in enumerate(all_urls): 
    print(f"Talk number {i+1}")
    conference_talks.append(scrape_talk_data(url)) 

conference_df = pd.DataFrame(conference_talks) 

# cleaning 
for col in conference_df.columns: 
    conference_df[col] = conference_df[col].apply(lambda x: unicodedata.normalize("NFKD", x))
    conference_df[col] = conference_df[col].apply(lambda x: x.replace("\n", ""))
    conference_df[col] = conference_df[col].apply(lambda x: x.replace("\t", ""))

# finish 
conference_df.to_csv("conference_talks.csv", index=False)

end = time.time()
print(end - start)
