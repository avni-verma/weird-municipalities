import requests # For making HTTP requests
import json
import time
# from urllib.parse import urlsplit # Only if get_base_url stays here and is used

# ==============================================================================
# This file contains parser functions that are experimental, under development,
# or were found to be non-functional for their intended purpose and are
# archived here for reference.
# Specifically, the MunicodeNEXT parser below did not yield a usable ToC.
# ==============================================================================

# --- Potentially Archived Helper ---
# If get_base_url is ONLY for the archived municode_next function, it can stay.
# Otherwise, it should be in url_queue_builder.py or a utils file.
# def get_base_url(url):
#     from urllib.parse import urlsplit
#     split_url = urlsplit(url)
#     return f"{split_url.scheme}://{split_url.netloc}"

# Helper function originally for get_urls_from_municode_next
def _extract_municonext_urls_recursive(node, base_url_prefix, url_list):
    if not isinstance(node, dict):
        return

    # Hypothetical new keys - UPDATE BASED ON NEW DEBUG OUTPUT
    node_path = node.get("NodePath") # Example: "NodePath" instead of "path"
    if node_path:
        if not node_path.startswith("/"):
            node_path = "/" + node_path
        full_url = base_url_prefix + node_path
        url_list.append(full_url)

    # Hypothetical new keys - UPDATE BASED ON NEW DEBUG OUTPUT
    children = node.get("ChildNodes") # Example: "ChildNodes" instead of "children"
    if isinstance(children, list):
        for child_node in children:
            _extract_municonext_urls_recursive(child_node, base_url_prefix, url_list)

# ------------------------------------------------------------------------------
# Archived MunicodeNEXT Parser
# The parser below is non-functional for its intended purpose.
# It is preserved here for reference or future investigation if a new API
# endpoint or method for MunicodeNEXT ToC is discovered.    
#The core issue with this parser is that the API endpoint did not lead us to where we wanted to be, the heirachial tree structure could not be found.
#This lead me to pivot and focus on American Legal Publishing Corporation (ALPC) and their API. since it is a static HTML outline

# ------------------------------------------------------------------------------
def get_urls_from_municode_next(city_name, state_abbr, bot_user_agent):
    print(f"Processing MunicodeNEXT site for: {city_name}, {state_abbr}")
    start_time = time.time()
    url_queue = []
    # It's good practice to specify a User-Agent and that we accept JSON
    headers = {
        "User-Agent": bot_user_agent,
        "Accept": "application/json"
    }
    client_id = None # Initialize to None

    # --- Step 1: Get clientId ---
    try:
        # 1. Construct the URL
        client_id_url = f"https://api.municode.com/Clients/name?clientName={city_name.lower()}&stateAbbr={state_abbr.lower()}"
        print(f"  Fetching clientId from: {client_id_url}")

        # 2. Make the request
        response = requests.get(client_id_url, headers=headers, timeout=10) # Added timeout
        response.raise_for_status() # This will raise an HTTPError if the HTTP request returned an unsuccessful status code

        # 3. Parse the JSON response
        # This API returns a list containing one dictionary
        data = response.json() # data is a dictionary

        # Corrected logic: Expect a dictionary, not a list
        if data and isinstance(data, dict): # Check if it's a dictionary
            print(f"  DEBUG: Keys in response data: {list(data.keys())}")
            client_id = data.get("ClientID")
            if client_id:
                print(f"  Successfully fetched ClientId: {client_id}")
            else:
                print("  ❗️ Error: 'ClientId' not found in the response from Clients API.")
                print(f"  DEBUG: Full response data: {data}")
                return [], time.time() - start_time
        else:
            print(f"  ❗️ Error: Unexpected response format from Clients API (expected a dictionary): {data}")
            return [], time.time() - start_time # Early exit

    except requests.RequestException as e:
        print(f"  ❗️ Error fetching ClientId: {e}")
        return [], time.time() - start_time # Early exit on network or HTTP error
    except json.JSONDecodeError:
        print(f"  ❗️ Error decoding JSON for ClientId. Raw response: {response.text[:200]}") # Show a bit of the raw response
        return [], time.time() - start_time
    except Exception as e:
        print(f"  ❗️ An unexpected error occurred during ClientId fetching: {e}")
        return [], time.time() - start_time

    # --- Step 2: Get productId ---
    product_id = None
    if client_id: # Only proceed if we have a client_id
        try:
            # 1. Construct the URL
            # For now, we assume "code of ordinances" is the desired product.
            # The space in "code of ordinances" should be URL-encoded to %20,
            # but requests library usually handles this automatically for parameters.
            # Let's be explicit with f-string or let requests handle it.
            product_id_url = f"https://api.municode.com/Products/name?clientId={client_id}&productName=code+of+ordinances"
            print(f"  Fetching productId from: {product_id_url}")

            # 2. Make the request
            response = requests.get(product_id_url, headers=headers, timeout=10)
            response.raise_for_status()

            # 3. Parse the JSON response
            data = response.json() # This API returns a direct dictionary

            # 4. Extract the productId
            if data and isinstance(data, dict):
                print(f"  DEBUG: Keys in ProductId response data: {list(data.keys())}") # For debugging
                product_id = data.get("ProductID") # Key is "ProductID"
                if product_id:
                    print(f"  Successfully fetched ProductId: {product_id}")
                else:
                    print("  ❗️ Error: 'ProductID' not found in the response from Products API.")
                    print(f"  DEBUG: Full ProductId response data: {data}")
                    # We might not want to exit the whole function yet,
                    # but for now, if we don't get a product_id, we can't continue this path.
            else:
                print(f"  ❗️ Error: Unexpected response format from Products API (expected a dictionary): {data}")

        except requests.RequestException as e:
            print(f"  ❗️ Error fetching ProductId: {e}")
        except json.JSONDecodeError:
            print(f"  ❗️ Error decoding JSON for ProductId. Raw response: {response.text[:200]}")
        except Exception as e:
            print(f"  ❗️ An unexpected error occurred during ProductId fetching: {e}")
    else:
        print("  Skipping ProductId fetching because ClientId was not found.")

    # --- Step 3: Get jobId ---
    job_id = None
    if product_id: # Only proceed if we have a product_id
        try:
            # 1. Construct the URL
            job_id_url = f"https://api.municode.com/Jobs/latest/{product_id}"
            print(f"  Fetching jobId from: {job_id_url}")

            # 2. Make the request
            response = requests.get(job_id_url, headers=headers, timeout=10)
            response.raise_for_status()

            # 3. Parse the JSON response
            data = response.json() # This API returns a direct dictionary

            # 4. Extract the jobId (which is under the key "Id")
            if data and isinstance(data, dict):
                print(f"  DEBUG: Keys in JobId response data: {list(data.keys())}") # For debugging
                job_id = data.get("Id") # Key is "Id"
                if job_id:
                    print(f"  Successfully fetched JobId: {job_id}")
                else:
                    print("  ❗️ Error: 'Id' (for JobId) not found in the response from Jobs API.")
                    print(f"  DEBUG: Full JobId response data: {data}")
            else:
                print(f"  ❗️ Error: Unexpected response format from Jobs API (expected a dictionary): {data}")

        except requests.RequestException as e:
            print(f"  ❗️ Error fetching JobId: {e}")
        except json.JSONDecodeError:
            print(f"  ❗️ Error decoding JSON for JobId. Raw response: {response.text[:200]}")
        except Exception as e:
            print(f"  ❗️ An unexpected error occurred during JobId fetching: {e}")
    elif client_id: # If we had client_id but not product_id
        print("  Skipping JobId fetching because ProductId was not found.")
    else: # If we didn't even have client_id
        print("  Skipping JobId fetching because ClientId was not found.")

    # --- Step 4: Get Table of Contents (ToC) ---
    toc_data = None # Initialize toc_data
    if job_id and product_id: # Only proceed if we have both job_id and product_id
        try:
            # 1. Construct the URL
            toc_url = f"https://api.municode.com/CodesContent?jobId={job_id}&productId={product_id}"
            print(f"  Fetching Table of Contents (ToC) from: {toc_url}")

            # 2. Make the request
            response = requests.get(toc_url, headers=headers, timeout=15) # Increased timeout slightly for potentially larger response
            response.raise_for_status()

            # 3. Parse the JSON response
            toc_data = response.json() # This should be the ToC data structure

            if toc_data:
                print(f"  Successfully fetched ToC data. (Top-level type: {type(toc_data)})")
                # For now, let's just print a snippet of it to verify
                # We'll do the actual parsing in Step 5.
                # If it's a list, print the first item's keys, or if a dict, its keys.
                if isinstance(toc_data, list) and len(toc_data) > 0 and isinstance(toc_data[0], dict):
                    print(f"  DEBUG: Keys in first item of ToC data: {list(toc_data[0].keys())}")
                elif isinstance(toc_data, dict):
                     print(f"  DEBUG: Keys in ToC data: {list(toc_data.keys())}")
                # print(f"  DEBUG: ToC data snippet: {str(toc_data)[:500]}") # Might be too long
            else:
                print("  ❗️ Error: ToC data is empty or None after fetching.")

        except requests.RequestException as e:
            print(f"  ❗️ Error fetching ToC data: {e}")
        except json.JSONDecodeError:
            print(f"  ❗️ Error decoding JSON for ToC data. Raw response: {response.text[:200]}")
        except Exception as e:
            print(f"  ❗️ An unexpected error occurred during ToC data fetching: {e}")

    elif product_id: # If we had product_id but not job_id
        print("  Skipping ToC fetching because JobId was not found.")
    # (other elif/else for skipping if client_id or product_id were missing)
    

    # --- Step 5: Parse ToC and build URLs ---
    if toc_data and isinstance(toc_data, dict):
        print("  DEBUG: Starting Step 5. Full toc_data keys:", list(toc_data.keys()))

        docs_content = toc_data.get("Docs")
        if isinstance(docs_content, list) and len(docs_content) > 0:
            print(f"    DEBUG: toc_data['Docs'] is a list with {len(docs_content)} item(s).")
            first_doc_item = docs_content[0]
            if isinstance(first_doc_item, dict):
                print(f"      DEBUG: Keys in first item of 'Docs': {list(first_doc_item.keys())}")
                # Let's print some values from this first_doc_item to understand it better
                print(f"        Title: {first_doc_item.get('Title', 'N/A')}")
                print(f"        Id: {first_doc_item.get('Id', 'N/A')}")
                print(f"        DocType: {first_doc_item.get('DocType', 'N/A')}")
                
                # What is the type of 'Content' if it's not None?
                content_value = first_doc_item.get("Content")
                if content_value is not None:
                    print(f"        'Content' key's value type: {type(content_value)}")
                    # If 'Content' is a list, let's see its first item's keys
                    if isinstance(content_value, list) and len(content_value) > 0 and isinstance(content_value[0], dict):
                        print(f"          DEBUG: Keys in first item of 'Content' list: {list(content_value[0].keys())}")
                    # If 'Content' is a dict, let's see its keys
                    elif isinstance(content_value, dict):
                         print(f"          DEBUG: Keys in 'Content' dict: {list(content_value.keys())}")
                else:
                    print("        'Content' key's value is None.")

                # Now, the crucial part: where is the list of nodes that have 'path' and 'children'?
                # We need to find it. For now, let's assume our recursive function won't find anything.
                # So url_queue will remain empty from this path.

            else:
                print("      DEBUG: First item in 'Docs' is not a dictionary.")
        elif docs_content is not None:
            print(f"    DEBUG: toc_data['Docs'] exists but is not a list. Type: {type(docs_content)}")
        else:
            print("    DEBUG: toc_data['Docs'] key not found or is None.")
            
            # If, after all this, we can't find where to start the recursion, url_queue will be empty.
            if not url_queue: # Check if it's still empty
                 print("  Could not identify the starting point for URL extraction in ToC structure.")

    else:
        print("  Skipping URL extraction because ToC data was not fetched or not a dict.")

    duration = time.time() - start_time
    url_queue = sorted(list(set(url_queue))) # Deduplicate and sort

    print(f"\n--- Results for {city_name}, {state_abbr} (MunicodeNEXT) ---")
    print(f"Total unique URLs found: {len(url_queue)}")
    print(f"Time taken: {duration:.2f} s")

    # KPI checks (similar to eCode360)
    if len(url_queue) >= 400: # Target for Phase 3 KPI
        print("METRIC: Queue fill rate (>= 400 URLs) - PASSED")
    else:
        print(f"METRIC: Queue fill rate (>= 400 URLs) - FAILED (Found {len(url_queue)})")

    if duration <= 15: # Target for Phase 3 KPI
        print("METRIC: Queue build time (<= 15s) - PASSED")
    else:
        print(f"METRIC: Queue build time (<= 15s) - FAILED (Took {duration:.2f}s)")

    return url_queue, duration

# --- main block to test ---
if __name__ == "__main__":
    my_user_agent = "AvniProjectBot/1.0"

    print("Attempting to fetch URLs for Miami, FL (MunicodeNEXT)...")
    municonext_urls, municonext_time = get_urls_from_municode_next(
        city_name="miami",
        state_abbr="fl",
        bot_user_agent=my_user_agent
    )
    # ... (rest of the test block)

