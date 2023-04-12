from automation_scraper import automation_scraper
import link_extractor
import time
import schedule

"""
    'automation'-method execute automatically the actual methods at a specific time
"""


def automation():
    #link_extractor.main()
    #print("Link Scraper finished running, updating the links file")
    #link_extractor.update_links()
    
    automation_scraper()



schedule.every().day.at("10:00").do(automation)
while True:
    schedule.run_pending()
    time.sleep(10)
