#requests is a library for making HTTP requests in Python
#urllib.robotparser is a module for parsing robots.txt files
#urllib.parse is a module for parsing URLs
#import urljoin to join URLs
import requests
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin


#define a class for the robots auditor
#initialize the class with a user-agent
#init is a special method that is called when the class is instantiated
#self is a reference to the instance of the class
#user_agent is the user-agent of the bot
#parser is the parser for the robots.txt file



class RobotsAuditor:
    def __init__(self, user_agent="AvniProjectBot/1.0"): # Replace with your bot's actual user-agent
        self.user_agent = user_agent
        self.parser = RobotFileParser()

    #fetch_robots_txt is a method that fetches the robots.txt file for a given domain
    #domain_url is the URL of the domain
    #returns True if fetched and parsing was initiated, False if a critical error occurred
    def fetch_robots_txt(self, domain_url):
        """
        Fetches the robots.txt file for a given domain.
        Returns True if fetched and parsing was initiated, False if a critical error occurred.
        """
        # Ensure domain_url has a scheme (http or https)
        if not domain_url.startswith(('http://', 'https://')):
            if not "://" in domain_url: # simple check if any scheme is present
                 print(f"Scheme missing from {domain_url}, prepending http://")
                 domain_url = 'http://' + domain_url
            elif not domain_url.startswith(('http://', 'https://')):
                print(f"Unsupported URL scheme in {domain_url}. Please use http or https.")
                self.parser.disallow_all = True # Safety default
                return False # Indicate critical issue

        robots_url = urljoin(domain_url, "robots.txt") # Construct full URL for robots.txt
        print(f"Fetching robots.txt from: {robots_url}")
        try:
            response = requests.get(robots_url, timeout=10) # Make the HTTP GET request
            response.raise_for_status() # Raise an exception for HTTP errors (4xx client error, 5xx server error)
            
            # If successful, parse the content
            self.parser.parse(response.text.splitlines())
            return True # Successfully fetched and parsed
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error fetching {robots_url}: {e}")
            if e.response.status_code == 404: # Not Found
                print(f"robots.txt not found at {robots_url}. Assuming access is allowed to all paths.")
                self.parser.allow_all = True # Standard practice for 404
            else: # Other HTTP errors like 401 (Unauthorized), 403 (Forbidden)
                print(f"Access to robots.txt at {robots_url} is restricted (status {e.response.status_code}). Assuming disallow all for safety.")
                self.parser.disallow_all = True # Safe default
            return False # Indicate fetching/parsing was not 'successful' in the typical sense but a decision was made
        except requests.exceptions.Timeout:
            print(f"Timeout error fetching {robots_url}")
            self.parser.disallow_all = True # Safe default
            return False
        except requests.exceptions.RequestException as e: # Other network issues
            print(f"Error fetching {robots_url}: {e}")
            self.parser.disallow_all = True # Safe default
            return False
        except Exception as e: # Catch other potential parsing errors
            print(f"Error parsing robots.txt from {robots_url}: {e}")
            self.parser.disallow_all = True
            return False

    def can_fetch(self, url_to_check):
        """
        Checks if the given URL can be fetched according to the parsed robots.txt.
        Assumes fetch_robots_txt was called for the target domain first.
        """
        if self.parser is None: 
            print("Error: Robots.txt parser not initialized.")
            return False 
        
        return self.parser.can_fetch(self.user_agent, url_to_check)

# --- Main execution for testing ---
if __name__ == "__main__":
    # --- Unit Test Example 1: Wikipedia ---
    print("\n--- Testing wikipedia.org ---")
    # Use YOUR chosen User-Agent string here
    wiki_auditor = RobotsAuditor(user_agent="AvniProjectBot/1.0")
    domain1 = "http://www.wikipedia.org"  # Your first sample site
    
    if wiki_auditor.fetch_robots_txt(domain1):
        # Test some URLs on Wikipedia
        url1_wiki = "http://www.wikipedia.org/wiki/Main_Page"
        print(f"Can '{wiki_auditor.user_agent}' fetch {url1_wiki}? {wiki_auditor.can_fetch(url1_wiki)}")

        url2_wiki = "https://en.wikipedia.org/wiki/Red-capped_parrot" # A page that gives a random article
        print(f"Can '{wiki_auditor.user_agent}' fetch {url2_wiki}? {wiki_auditor.can_fetch(url2_wiki)}")
        
        # You can add a path you think might be disallowed to see what happens
        # For example, many sites disallow /w/index.php?title=Special:Search&search= (or similar search paths)
        # Check Wikipedia's actual robots.txt (https://en.wikipedia.org/robots.txt) for ideas
        url3_wiki_maybe_disallowed = "http://www.wikipedia.org/w/index.php?title=Special:Export" # Example, check robots.txt
        print(f"Can '{wiki_auditor.user_agent}' fetch {url3_wiki_maybe_disallowed}? {wiki_auditor.can_fetch(url3_wiki_maybe_disallowed)}")
    else:
        print(f"Could not reliably fetch or parse robots.txt for {domain1} for the auditor to make a decision.")

    # --- Unit Test Example 2: Municode Chicago ---
    print("\n--- Testing Municode Chicago ---")
    # Use YOUR chosen User-Agent string here
    municode_auditor = RobotsAuditor(user_agent="AvniProjectBot/1.0") 
    domain2 = "https://codelibrary.amlegal.com" # CORRECTED: Base domain for robots.txt

    if municode_auditor.fetch_robots_txt(domain2): 
        # Test some URLs on Municode Chicago.
        url1_chicago = "https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il/0-0-0-2595356" # Your main page for Chicago
        print(f"Can '{municode_auditor.user_agent}' fetch {url1_chicago}? {municode_auditor.can_fetch(url1_chicago)}")
        
        # Example of a specific sub-path for Chicago (you'll need to find real ones)
        # This is a guess, find a real path from the Chicago site:
        url2_chicago = "https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il/0-0-0-12345" # Replace 12345 with actual part
        print(f"Can '{municode_auditor.user_agent}' fetch {url2_chicago}? {municode_auditor.can_fetch(url2_chicago)}")

        # Check robots.txt for amlegal: https://codelibrary.amlegal.com/robots.txt
        # Look for disallowed paths like /search/ or /api/ or specific document types
        # This is a hypothetical disallowed path for amlegal.com:
        url3_chicago_maybe_disallowed = "https://codelibrary.amlegal.com/search" # Check if /search is disallowed
        print(f"Can '{municode_auditor.user_agent}' fetch {url3_chicago_maybe_disallowed}? {municode_auditor.can_fetch(url3_chicago_maybe_disallowed)}")
    else:
        print(f"Could not reliably fetch or parse robots.txt for {domain2} for the auditor to make a decision.")

    # --- Key Metric Checks --- (These print statements are fine as they are)
    print("\n--- Key Metric Checks ---")
    print("Robots coverage — ≥ 2 domains parsed: The tests above attempt to parse two domains.")
    print("To meet the metric, ensure `fetch_robots_txt` indicates success or a clear fallback (like 404 resulting in 'allow all').")
    print("False-positive rate 0 %: This requires knowing the *actual* rules in the live robots.txt for your test domains")
    print("and your chosen user-agent. If robots.txt DISALLOWS a path for your bot, can_fetch must be False.")
    print("If robots.txt ALLOWS a path (or has no specific rule against it), can_fetch must be True.")
    print("Manually verify against the live robots.txt files for the user-agents used in tests.")    
