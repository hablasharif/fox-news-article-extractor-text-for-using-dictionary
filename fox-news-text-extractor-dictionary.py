import streamlit as st
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import logging
import re
import hashlib
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache(show_spinner=False)
def fetch_url_content(url, max_retries=1, timeout=20):
    for retry in range(max_retries):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            html = response.text
            return html
        except requests.RequestException as e:
            logger.warning(f"Error fetching {url}, Retry {retry + 1}/{max_retries}: {e}")
        except requests.Timeout:
            logger.warning(f"Timeout fetching {url}, Retry {retry + 1}/{max_retries}")

    return None

@st.cache(show_spinner=False)
def extract_paragraphs(url):
    html = fetch_url_content(url)
    if html is None:
        logger.error(f"HTML content is None for {url}")
        return None

    soup = BeautifulSoup(html, 'html.parser')
    p_tags = soup.find_all('p')
    content = [p.get_text() for p in p_tags]

    return content

@st.cache(show_spinner=False)
def remove_symbols_and_punctuation(text):
    # Add a space for each removed symbol or punctuation mark
    text = re.sub(r'(?<=[a-zA-Z])-(?=[a-zA-Z])', ' ', text)
    text = re.sub(r'[^\w\s-]', ' ', text)
    return text

@st.cache(show_spinner=False)
def filter_english_words(text):
    # Filter out non-English words
    english_words = re.findall(r'\b[a-zA-Z]+\b', text)
    return ' '.join(english_words)

@st.cache(show_spinner=False)
def process_url(url):
    try:
        content = extract_paragraphs(url)
        if content is None:
            return ""

        # Combine paragraphs into a single string
        content_text = ' '.join(content)

        # Remove symbols and punctuation
        cleaned_text = remove_symbols_and_punctuation(content_text)

        # Filter English words
        english_words_only = filter_english_words(cleaned_text)

        return english_words_only
    except Exception as e:
        logger.error(f"Error processing {url}: {e}")
        return ""

def main():
    st.title("Web Scraping with Streamlit")

    # File uploader for user to upload the .txt file
    uploaded_file = st.file_uploader("Choose a .txt file", type="txt")

    if uploaded_file is not None:
        # Read URLs from the uploaded file
        with uploaded_file:
            urls = [line.strip() for line in uploaded_file if line.strip()]

        # Print the total count of URLs
        total_urls = len(urls)
        st.write(f"Total URLs: {total_urls}")

        # Get the user's option for URL range extraction
        option = st.text_input("Enter the option ('a' to 'z'): ")

        # Validate user input
        if option.lower() not in [chr(i) for i in range(ord('a'), ord('z') + 1)]:
            st.error("Invalid option. Please enter a letter from 'a' to 'z'.")
            return

        # Determine the start and end indices based on the selected option
        start_index = (ord(option.lower()) - ord('a')) * 30000
        end_index = start_index + 30000

        selected_urls = urls[start_index:end_index]

        # Print the first and last URLs for the selected range
        st.write(f"\nSelected Range ({option.upper()}):")
        st.write(f"First URL: {selected_urls[0]}")
        st.write(f"Last URL: {selected_urls[-1]}")

        total_words = []

        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(tqdm(executor.map(process_url, selected_urls), total=len(selected_urls)))

        total_words = [word for result in results for word in result.split()]

        output_file_name = f"foxnewstext_{option}.txt"
        with open(output_file_name, "w", encoding="utf-8") as total_words_file:
            total_words_file.write(" ".join(total_words))
            st.success(f"Saved processed words to {output_file_name}")

if __name__ == "__main__":
    main()
