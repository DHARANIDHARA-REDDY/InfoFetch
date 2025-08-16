import os
import logging
from flask import Flask, request, jsonify, render_template
from scraper import ShopifyStoreScraper

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key_change_in_production")

# Initialize scraper
scraper = ShopifyStoreScraper()

@app.route('/')
def index():
    """Render the main page with API testing interface"""
    return render_template('index.html')

@app.route('/fetch_insights', methods=['POST'])
def fetch_insights():
    """
    Main API endpoint to fetch Shopify store insights
    Accepts: website_url parameter
    Returns: JSON with structured store data
    """
    try:
        # Get website URL from request
        data = request.get_json()
        if not data or 'website_url' not in data:
            return jsonify({
                'error': 'Missing website_url parameter',
                'message': 'Please provide a valid Shopify store URL'
            }), 400
        
        website_url = data['website_url'].strip()
        
        if not website_url:
            return jsonify({
                'error': 'Empty website_url parameter',
                'message': 'Please provide a valid Shopify store URL'
            }), 400
        
        logger.info(f"Fetching insights for: {website_url}")
        
        # Scrape store insights
        insights = scraper.scrape_store(website_url)
        
        if insights is None:
            return jsonify({
                'error': 'Website not found or inaccessible',
                'message': 'The provided URL could not be accessed or is not a valid Shopify store'
            }), 401
        
        logger.info(f"Successfully scraped insights for: {website_url}")
        return jsonify(insights), 200
        
    except Exception as e:
        logger.error(f"Internal error while scraping {website_url}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while processing your request'
        }), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'Shopify Store Scraper API'}), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested API endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
