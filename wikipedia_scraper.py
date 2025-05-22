import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin # For handling relative links
import csv

def scrape_wikipedia_page(url, user_agent):
    print(f"Scraping Wikipedia page: {url}")
    headers = {"User-Agent": user_agent}
    
    # --- Extracted Data Storage ---
    article_text_parts = []
    links = set() # To store unique Wikipedia links
    tables_data = [] # Will store lists of lists for each table

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() # Check for HTTP errors
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # --- TODO: Logic to extract main text ---
        # Wikipedia article content is usually within a div with id="mw-content-text"
        # and then within that, often in <p> tags for main text.
        # We need to avoid sidebars, nav boxes, etc.
        print("\n--- Extracting Main Article Text ---")
        content_div = soup.find("div", id="mw-content-text")
        if content_div:
            # Find the main parser output div (often class="mw-parser-output")
            parser_output_div = content_div.find("div", class_="mw-parser-output")
            if parser_output_div:
                # Extract text primarily from <p> tags directly under parser_output_div
                # This is a starting point; might need refinement.
                for p_tag in parser_output_div.find_all("p", recursive=False): # Only direct children paragraphs
                    article_text_parts.append(p_tag.get_text(separator=" ", strip=True))
                
                # Also get text from paragraphs within other common content elements like divs
                # that are direct children of parser_output_div (excluding tables, infoboxes etc.)
                for child_element in parser_output_div.find_all(recursive=False):
                    if child_element.name == 'div' and not child_element.find(['table', '.infobox', '.thumb', '.tright', '.tleft', '.rellink', '.noprint', '.mw-references-wrap']):
                        for p_tag_in_div in child_element.find_all("p"):
                             article_text_parts.append(p_tag_in_div.get_text(separator=" ", strip=True))
            else:
                print("  Could not find 'div.mw-parser-output' within 'div#mw-content-text'.")
        else:
            print("  Could not find 'div#mw-content-text'.")

        main_text = "\n\n".join(filter(None, article_text_parts)) # Join non-empty parts
        print(f"  Extracted text (first 500 chars): {main_text[:500]}...")
        if not main_text:
            print("  No main text extracted. Check selectors.")


        # --- TODO: Logic to extract Tables ---
        print("\n--- Extracting Tables ---")
        # Tables in Wikipedia are usually <table> tags with class "wikitable"
        # or sometimes "infobox" for the side box (which we might want to treat differently or exclude)
        
        # Let's target general "wikitable" first
        for table_count, table_tag in enumerate(soup.find_all("table", class_="wikitable")):
            print(f"  Processing wikitable {table_count + 1}...")
            current_table_data = []
            for row in table_tag.find_all("tr"):
                row_data = []
                # Get th (header) and td (data) cells
                for cell in row.find_all(["th", "td"]):
                    row_data.append(cell.get_text(separator=" ", strip=True))
                if row_data: # Only add if the row had some cells
                    current_table_data.append(row_data)
            if current_table_data:
                tables_data.append(current_table_data)
                print(f"    Extracted {len(current_table_data)} rows.")
        
        if not tables_data:
            print("  No wikitables found or extracted.")
        else:
            print(f"  Total wikitables extracted: {len(tables_data)}")


        # --- TODO: Logic to extract Wikipedia Links ---
        print("\n--- Extracting Wikipedia Links ---")
        # Links to other Wikipedia articles are <a> tags whose href starts with "/wiki/"
        # and does not contain a colon ":" (to exclude Special pages, File pages, etc.)
        # and often within the main content area (e.g., inside 'div#mw-content-text')
        
        # If content_div was found earlier, search within it for better context.
        search_area_for_links = content_div if content_div else soup # Fallback to whole soup

        base_wikipedia_url = "https://en.wikipedia.org" # For constructing full URLs

        for link_tag in search_area_for_links.find_all("a", href=True):
            href = link_tag["href"]
            if href.startswith("/wiki/") and ":" not in href and not href.startswith("/wiki/Help:") and not href.startswith("/wiki/File:") and not href.startswith("/wiki/Category:") and not href.startswith("/wiki/Portal:") and not href.startswith("/wiki/Template:") and not href.startswith("/wiki/Wikipedia:") and not href.startswith("/wiki/Special:"):
                full_url = urljoin(base_wikipedia_url, href)
                links.add(full_url)
        
        print(f"  Found {len(links)} unique Wikipedia article links.")
        # Print a few examples
        # for i, link_url in enumerate(list(links)[:5]):
        #     print(f"    {i+1}. {link_url}")


    except requests.RequestException as e:
        print(f"  ❗️ Error fetching page: {e}")
        return None, None, None # Return None for all if fetching fails
    except Exception as e:
        print(f"  ❗️ An unexpected error occurred: {e}")
        # Depending on the error, some data might have been partially extracted
        # For simplicity, return what we have or None
        return main_text if 'main_text' in locals() else None, \
               tables_data if tables_data else None, \
               list(links) if links else None

    return main_text, tables_data, sorted(list(links))


if __name__ == "__main__":
    target_url = "https://en.wikipedia.org/wiki/Pope_Leo_XIV"
    # It's good practice to set a User-Agent for web scraping
    # See: https://meta.wikimedia.org/wiki/User-Agent_policy
    my_user_agent = "MyCoolBot/1.0 (https://example.com/mycoolbotinfo; myemail@example.com)" # CHANGE THIS!

    print(f"Starting Wikipedia scrape for: {target_url}\n")
    
    article_text, all_tables, wiki_links = scrape_wikipedia_page(target_url, my_user_agent)

    if article_text:
        print("\n\n=== Main Article Text (Snippet) ===")
        print(article_text[:1000] + "..." if article_text else "No text extracted.")
    
    if all_tables:
        print("\n\n=== Extracted Tables ===")
        for i, table in enumerate(all_tables):
            print(f"\n--- Table {i+1} ---")
            for row_num, row in enumerate(table[:3]): # Print first 3 rows of each table
                print(f"  Row {row_num + 1}: {row}")
            if len(table) > 3:
                print(f"  ... and {len(table) - 3} more rows.")
    else:
        print("\n\nNo tables extracted.")
        
    if wiki_links:
        print(f"\n\n=== Found {len(wiki_links)} Wikipedia Links ===")
        for i, link in enumerate(wiki_links[:10]): # Print first 10 links
            print(f"  {i+1}. {link}")
        if len(wiki_links) > 10:
            print(f"  ... and {len(wiki_links) - 10} more links.")
    else:
        print("\n\nNo Wikipedia links extracted.")

    # --- Save tables to CSV files ---
    if all_tables:
        for i, table in enumerate(all_tables):
            filename = f"wikipedia_table_{i+1}.csv"
            with open(filename, "w", newline='', encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                for row in table:
                    writer.writerow(row)
            print(f"Saved table {i+1} to {filename}")

    # --- Save links to a CSV file ---
    if wiki_links:
        links_filename = "wikipedia_links.csv"
        with open(links_filename, "w", newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Wikipedia Article Link"])
            for link in wiki_links:
                writer.writerow([link])
        print(f"Saved {len(wiki_links)} links to {links_filename}")
