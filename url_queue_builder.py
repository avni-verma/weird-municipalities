import requests
import json # Though not used by AmLegal parser, often useful
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit # For urljoin and get_base_url

# --- Helper to get the base URL (scheme + domain) ---
# Useful for AmLegal if URLs are relative
def get_base_url(url):
    split_url = urlsplit(url)
    return f"{split_url.scheme}://{split_url.netloc}"

# --- American Legal Publishing Parser ---
def get_urls_from_amlegal(city_overview_url, bot_user_agent, max_depth=2):
    print(f"Processing AmLegal: {city_overview_url} (max_depth={max_depth})")
    start_time = time.time()
    
    scrape_queue = [(city_overview_url, 0)] 
    queued_tasks = set([(city_overview_url, 0)]) # Keep track of (url, depth) in queue

    final_ordinance_base_urls = set()
    visited_page_bases = set() 

    headers = {"User-Agent": bot_user_agent}
    target_domain = urlsplit(city_overview_url).netloc
    overview_page_base_url = urlsplit(city_overview_url)._replace(fragment="").geturl()


    while scrape_queue:
        current_url_to_process, current_depth = scrape_queue.pop(0)
        queued_tasks.remove((current_url_to_process, current_depth)) # Remove from tracking set

        current_url_base = urlsplit(current_url_to_process)._replace(fragment="").geturl()

        if current_url_base in visited_page_bases:
            continue
        
        # print(f"  Depth {current_depth}: Processing {current_url_to_process}") 
        visited_page_bases.add(current_url_base)

        if current_url_base != overview_page_base_url: # Add to final if not the overview page
            final_ordinance_base_urls.add(current_url_base)

        if current_depth >= max_depth:
            continue

        try:
            response = requests.get(current_url_to_process, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            links_found_on_page = [] # Raw hrefs found
            is_overview_page = current_url_base == overview_page_base_url

            if is_overview_page:
                toc_container = soup.find("div", class_="codenav__toc")
                if toc_container:
                    toc_entries = toc_container.find_all("div", class_=lambda c: c is not None and "toc-entry" in c.split())
                    for entry in toc_entries:
                        wrap = entry.find("div", class_="toc-entry__wrap")
                        if wrap:
                            link_tag = wrap.find("a")
                            if link_tag and link_tag.get("href"):
                                links_found_on_page.append(link_tag.get("href"))
            else: 
                content_area = soup.find("div", id="codecontent")
                if content_area:
                    normal_level_divs = content_area.find_all("div", class_="Normal-Level")
                    if normal_level_divs: 
                        for item_div in normal_level_divs:
                            link_tag = item_div.find("a")
                            if link_tag and link_tag.get("href"):
                                links_found_on_page.append(link_tag.get("href"))
            
            for rel_href in links_found_on_page:
                full_url = urljoin(current_url_to_process, rel_href)
                if urlsplit(full_url).netloc == target_domain: # Stay on target domain
                    full_url_base_to_check = urlsplit(full_url)._replace(fragment="").geturl()
                    
                    task_to_add = (full_url, current_depth + 1)
                    if full_url_base_to_check not in visited_page_bases and task_to_add not in queued_tasks:
                        # print(f"    Queueing {task_to_add}") # Debug
                        scrape_queue.append(task_to_add)
                        queued_tasks.add(task_to_add)
        except Exception as e:
            print(f"  ❗️ Error processing {current_url_to_process} at depth {current_depth}: {e}")


    duration = time.time() - start_time
    url_queue = sorted(list(final_ordinance_base_urls))
    
    print(f"\n--- Results for {city_overview_url} (AmLegal) ---")
    print(f"Total unique URLs found: {len(url_queue)}")
    print(f"Time taken: {duration:.2f} s")

    # KPIs
    if len(url_queue) >= 400:
        print("METRIC: Queue fill rate (>= 400 URLs) - PASSED")
    else:
        print(f"METRIC: Queue fill rate (>= 400 URLs) - FAILED (Found {len(url_queue)})")

    if duration <= 15 and len(url_queue) > 0 : # Add check for some URLs found for time KPI
        print("METRIC: Queue build time (<= 15s) - PASSED")
    elif len(url_queue) > 0 : # If URLs found but time exceeded
        print(f"METRIC: Queue build time (<= 15s) - FAILED (Took {duration:.2f}s)")
    # Else: no URLs found, time KPI less relevant or also failed.

    return url_queue, duration

# --- Main block to test ---
if __name__ == "__main__":
    my_user_agent = "AvniProjectBot/1.0" # Your bot's user agent

    # Test American Legal Publishing
    # Target URL for Tippecanoe County, IN (Overview page which contains the ToC)
    amlegal_test_url = "https://codelibrary.amlegal.com/codes/tippecanoe/latest/overview"
    
    print(f"\nAttempting to fetch URLs for Tippecanoe County, OH (AmLegal) from {amlegal_test_url}...")
    amlegal_urls, amlegal_time = get_urls_from_amlegal(amlegal_test_url, my_user_agent, max_depth=3)

    if amlegal_urls:
        print(f"Successfully found {len(amlegal_urls)} unique URLs in {amlegal_time:.2f}s for Tippecanoe (AmLegal).")
        print("First 5 URLs:")
        for i, url in enumerate(amlegal_urls[:5]):
            print(f"  {i+1}. {url}")
        if len(amlegal_urls) > 5:
            print(f"  ... and {len(amlegal_urls) - 5} more.")
    else:
        print(f"No URLs found for Tippecanoe (AmLegal) from {amlegal_test_url}.")

    # You can add calls to other parsers here if you reactive them:
    # print("\nAttempting to fetch URLs for eCode360 site...")
    # ecode_urls, ecode_time = get_urls_from_ecode360("YOUR_ECODE360_TEST_URL", my_user_agent)
    # ...
