import streamlit as st
import feedparser
from datetime import datetime
from dateutil import parser
import pytz
import html
import re
from urllib.parse import urljoin
from textblob import TextBlob

# External CSS (unchanged)
external_css = """
<style>
    .stApp {
        font-family: 'Roboto', sans-serif !important;
    }
    .main-header {
        font-size: 3.5rem !important;
        font-weight: 700 !important;
        text-align: center !important;
        margin-bottom: 2rem !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1) !important;
    }
    .news-grid {
        display: grid !important;
        gap: 1.5rem !important;
        padding: 1rem !important;
    }
    .news-card {
        border-radius: 15px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        padding: 1.5rem !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease !important;
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        margin-bottom: 15px;
    }
    .news-card:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15) !important;
    }
    .news-title {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        height: 3em;
    }
    .news-description {
        font-size: 0.9rem !important;
        margin-bottom: 1rem !important;
        flex-grow: 1 !important;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        height: 4.5em;
    }
    .news-meta {
        font-size: 0.8rem !important;
        margin-bottom: 0.5rem !important;
    }
    .read-more {
        padding: 0.4rem 0.8rem !important;
        border-radius: 20px !important;
        text-decoration: none !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        transition: background-color 0.3s !important;
        display: inline-block !important;
        text-align: center !important;
        width: 100% !important;
    }
    .news-image {
        width: 100% !important;
        height: 200px !important;
        object-fit: cover !important;
        border-radius: 10px !important;
        margin-bottom: 1rem !important;
    }
    .sentiment-positive {
        color: green !important;
    }
    .sentiment-negative {
        color: red !important;
    }
    .sentiment-neutral {
        color: gray !important;
    }
</style>
"""

# RSS feed URLs (unchanged)
RSS_FEEDS = [
    {"name": "NASA", "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss", "category": "Science"},
    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/news/rssindex", "category": "Finance"},
    {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "category": "Cryptocurrency"},
    {"name": "Reuters: Technology", "url": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best", "category": "Technology"},
    {"name": "HoopsHype", "url": "https://hoopshype.com/feed", "category": "Basketball"},
    {"name": "USA Today", "url": "https://giantswire.usatoday.com/feed", "category": "American Football"},
    {"name": "NYT World News", "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "category": "World"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "Technology"}
]

def parse_date(date_string):
    try:
        return parser.parse(date_string)
    except ValueError:
        return datetime.now(pytz.utc)

def extract_image_url(entry, feed_url):
    # Try to find image in media content
    if 'media_content' in entry and entry.media_content:
        media = entry.media_content[0]
        if 'url' in media:
            return media['url']
    
    # Try to find image in content
    content = entry.get('content', [{'value': ''}])[0].get('value', '')
    if not content and 'summary' in entry:
        content = entry.summary

    img_pattern = r'<img[^>]+src=["\'](https?://[^"\']+)["\']'
    match = re.search(img_pattern, content)
    if match:
        return urljoin(feed_url, match.group(1))
    
    return "https://via.placeholder.com/400x200?text=No+Image"

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return html.unescape(cleantext)

def analyze_sentiment(text):
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0:
        return "Positive", analysis.sentiment.polarity
    elif analysis.sentiment.polarity < 0:
        return "Negative", analysis.sentiment.polarity
    else:
        return "Neutral", analysis.sentiment.polarity

def fetch_news(feed):
    try:
        news = feedparser.parse(feed["url"])
        return [
            {
                "title": html.escape(entry.title),
                "description": clean_html(entry.get('summary', ''))[:150] + "...",
                "link": entry.link,
                "published": parse_date(entry.get('published', '')),
                "source": feed["name"],
                "category": feed["category"],
                "image_url": extract_image_url(entry, feed["url"]),
                "sentiment": analyze_sentiment(entry.title + " " + entry.get('summary', ''))
            }
            for entry in news.entries[:10]  # Limit to 10 entries per feed
        ]
    except Exception as e:
        st.error(f"Failed to fetch {feed['name']} news: {str(e)}")
        return []

def main():
    st.set_page_config(page_title="NewsPulse", layout="wide", initial_sidebar_state="collapsed")

    # Dark mode state
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False

    # Apply custom CSS
    st.markdown(external_css, unsafe_allow_html=True)

    # Dark mode toggle in sidebar
    with st.sidebar:
        st.title("Customize Your Feed")
        dark_mode = st.checkbox("Dark Mode", value=st.session_state.dark_mode)
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            st.experimental_rerun()

    # Apply dark mode
    if st.session_state.dark_mode:
        st.markdown("""
            <style>
            .stApp {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            .news-card {
                background-color: #2D2D2D;
            }
            .news-title {
                color: #FFFFFF;
            }
            .news-description, .news-meta {
                color: #CCCCCC;
            }
            </style>
        """, unsafe_allow_html=True)

    st.markdown("<h1 class='main-header'>NewsPulse</h1>", unsafe_allow_html=True)

    # Sidebar options
    layout = st.sidebar.radio("Layout", ("Grid", "Full Width"))
    items_per_row = st.sidebar.slider("Items per row", 1, 6, 3) if layout == "Grid" else 1
    search_term = st.sidebar.text_input("Search news")
    category_filter = st.sidebar.multiselect(
        "Select categories",
        options=["All"] + list(set(feed["category"] for feed in RSS_FEEDS)),
        default="All"
    )
    show_sentiment = st.sidebar.checkbox("Show Sentiment Analysis", value=True)

    # Fetch and process news
    all_news = []
    for feed in RSS_FEEDS:
        all_news.extend(fetch_news(feed))
    all_news.sort(key=lambda x: x['published'], reverse=True)

    # Apply filters
    filtered_news = [
        item for item in all_news
        if (search_term.lower() in item['title'].lower() or search_term.lower() in item['description'].lower()) and
        (item['category'] in category_filter or "All" in category_filter)
    ]

    # Display news
    col_width = 12 // items_per_row if layout == "Grid" else 12
    for i in range(0, len(filtered_news), items_per_row):
        cols = st.columns(items_per_row if layout == "Grid" else 1)
        for j, col in enumerate(cols):
            if i + j < len(filtered_news):
                item = filtered_news[i + j]
                with col:
                    sentiment_class = f"sentiment-{item['sentiment'][0].lower()}"
                    st.markdown(f"""
                    <div class="news-card">
                        <img src="{item['image_url']}" alt="News image" class="news-image">
                        <h2 class="news-title">{item['title']}</h2>
                        <p class="news-description">{item['description']}</p>
                        <p class="news-meta">
                            {item['source']} | {item['category']} | 
                            {item['published'].strftime('%b %d, %Y')}
                        </p>
                        {"<p class='" + sentiment_class + "'>Sentiment: " + item['sentiment'][0] + "</p>" if show_sentiment else ""}
                        <a href="{item['link']}" target="_blank" class="read-more">Read more</a>
                    </div>
                    """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div style='text-align: center; margin-top: 2rem;'>
        <p>© 2024 NewsPulse. All rights reserved.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
