# Shopify Store InfoFetch

A simple FastAPI-based service that extracts Brand Context information from a given Shopify store URL.

The API accepts a website_url as input and returns structured JSON containing brand details.

---

##Features

- Extracts **product catalogs**, **policies**, **brand info**, and **contact details**.
- Works without Shopify API access — uses **web scraping**.
- Provides **structured JSON output**.
- Web interface with **Bootstrap 5 dark theme** for API testing.
- Graceful error handling with **status codes** and logging.
- Extensible architecture for future integrations.

---

##System Architecture

###Backend
- **Framework**: Flask
- **Scraping Engine**: Custom `ShopifyStoreScraper` using:
  - `requests` (with session + browser headers)
  - `BeautifulSoup4` (HTML parsing)
  - `trafilatura` (clean text extraction)
- **Error Handling**: Logging, timeouts, and graceful degradation

###Frontend
- **UI Framework**: Bootstrap 5 (dark theme)
- **Templates**: Jinja2
- **Icons**: Feather Icons
- **JavaScript**: Vanilla JS with AJAX calls
- **Interface**: Single-page API tester

---

## 🔗 API Design

###Endpoint
`POST /fetch_insights`

###Input
```json
{
  "url": "https://examplestore.myshopify.com"
}
```

### Output (example)
```json
{
  "store_name": "Example Store",
  "products": [
    {
      "title": "T-Shirt",
      "price": "19.99",
      "url": "https://..."
    }
  ],
  "policies": {
    "privacy_policy": "...",
    "returns_policy": "..."
  },
  "brand_info": {
    "about": "...",
    "faqs": "..."
  },
  "contact": {
    "email": "support@example.com",
    "socials": ["instagram.com/example", "facebook.com/example"]
  },
  "navigation": [
    "Home", "Shop", "Contact"
  ]
}
```

---

##Data Extraction Strategy

- Detects Shopify presence from HTML
- Uses:
  - `/products.json` endpoints (if available)
  - HTML scraping for products & policies
  - `trafilatura` for clean text
- Collects:
  - ✅ Products (catalog + hero items)  
  - ✅ Policies (privacy, returns, shipping)  
  - ✅ Brand context & FAQs  
  - ✅ Contact info + social links  
  - ✅ Important navigation links  

---

## Error Handling & Resilience

- **Timeouts**: 10s per request  
- **Graceful degradation**: Partial data returned if some sections fail  
- **Logging**: Debug-level logs for troubleshooting  
- **HTTP status codes**: Clear error responses (400 for bad input, 500 for scrape failure, etc.)  

---

##Installation

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/shopify-infofetch.git
cd shopify-infofetch
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
flask run
```

By default, the app runs at:  
👉 `http://127.0.0.1:5000`

---

##Dependencies

- **Backend**
  - Flask
  - Jinja2 (bundled with Flask)
- **Scraping**
  - requests
  - BeautifulSoup4
  - trafilatura
- **Frontend**
  - Bootstrap 5 (CDN)
  - Feather Icons (CDN)

---
