import requests
import json
import re
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import trafilatura

logger = logging.getLogger(__name__)

class ShopifyStoreScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.timeout = 10
    
    def scrape_store(self, website_url: str) -> Optional[Dict[str, Any]]:
        """
        Main method to scrape a Shopify store and return structured insights
        """
        try:
            # Normalize URL
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url
            
            # Test if website is accessible
            response = self.session.get(website_url, timeout=self.timeout)
            if response.status_code != 200:
                logger.error(f"Website not accessible: {website_url} (Status: {response.status_code})")
                return None
            
            # Check if it's a Shopify store
            soup = BeautifulSoup(response.content, 'html.parser')
            if not self._is_shopify_store(soup, response.text):
                logger.warning(f"Website may not be a Shopify store: {website_url}")
            
            # Extract store name
            store_name = self._extract_store_name(soup, website_url)
            
            # Initialize insights structure
            insights = {
                "store_name": store_name,
                "website_url": website_url,
                "products": [],
                "hero_products": [],
                "privacy_policy": "",
                "return_policy": "",
                "faqs": [],
                "social_handles": {},
                "contact_details": {},
                "brand_context": "",
                "important_links": []
            }
            
            # Scrape different components
            insights["products"] = self._scrape_products(website_url)
            insights["hero_products"] = self._scrape_hero_products(soup, website_url)
            insights["privacy_policy"] = self._scrape_privacy_policy(website_url)
            insights["return_policy"] = self._scrape_return_policy(website_url)
            insights["faqs"] = self._scrape_faqs(website_url)
            insights["social_handles"] = self._extract_social_handles(soup)
            insights["contact_details"] = self._extract_contact_details(soup, website_url)
            insights["brand_context"] = self._scrape_brand_context(website_url)
            insights["important_links"] = self._extract_important_links(soup, website_url)
            
            return insights
            
        except requests.RequestException as e:
            logger.error(f"Network error while scraping {website_url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while scraping {website_url}: {str(e)}")
            raise
    
    def _is_shopify_store(self, soup: BeautifulSoup, html_content: str) -> bool:
        """Check if the website is a Shopify store"""
        shopify_indicators = [
            'Shopify.theme',
            'shopify-section',
            'cdn.shopify.com',
            'myshopify.com'
        ]
        
        for indicator in shopify_indicators:
            if indicator in html_content:
                return True
        
        # Check for Shopify-specific meta tags
        shopify_meta = soup.find('meta', attrs={'name': 'shopify-checkout-api-token'})
        if shopify_meta:
            return True
            
        return False
    
    def _extract_store_name(self, soup: BeautifulSoup, website_url: str) -> str:
        """Extract store name from various sources"""
        # Try title tag
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
            # Remove common suffixes
            title = re.sub(r'\s*[-–|]\s*(Shop|Store|Online|eCommerce).*$', '', title, flags=re.IGNORECASE)
            if title:
                return title
        
        # Try site name meta tag
        site_name = soup.find('meta', property='og:site_name')
        if site_name and site_name.get('content'):
            return site_name['content'].strip()
        
        # Try header logo alt text
        logo = soup.find('img', alt=True)
        if logo and logo.get('alt'):
            alt_text = logo['alt'].strip()
            if alt_text and not alt_text.lower() in ['logo', 'image']:
                return alt_text
        
        # Fallback to domain name
        domain = urlparse(website_url).netloc
        return domain.replace('www.', '').replace('.com', '').replace('.myshopify.com', '').title()
    
    def _scrape_products(self, website_url: str) -> List[Dict[str, Any]]:
        """Scrape product catalog from /products.json"""
        try:
            products_url = urljoin(website_url, '/products.json')
            response = self.session.get(products_url, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                products = []
                
                for product in data.get('products', []):
                    product_info = {
                        'id': product.get('id'),
                        'title': product.get('title'),
                        'handle': product.get('handle'),
                        'vendor': product.get('vendor'),
                        'product_type': product.get('product_type'),
                        'tags': product.get('tags', '').split(',') if product.get('tags') else [],
                        'price_range': self._extract_price_range(product.get('variants', [])),
                        'available': any(variant.get('available', False) for variant in product.get('variants', [])),
                        'images': [img.get('src') for img in product.get('images', [])],
                        'url': urljoin(website_url, f"/products/{product.get('handle')}")
                    }
                    products.append(product_info)
                
                logger.info(f"Found {len(products)} products")
                return products
            
        except Exception as e:
            logger.error(f"Error scraping products: {str(e)}")
        
        return []
    
    def _extract_price_range(self, variants: List[Dict]) -> Dict[str, float]:
        """Extract price range from product variants"""
        if not variants:
            return {}
        
        prices = [float(variant.get('price', 0)) for variant in variants if variant.get('price')]
        if prices:
            return {
                'min_price': min(prices),
                'max_price': max(prices)
            }
        return {}
    
    def _scrape_hero_products(self, soup: BeautifulSoup, website_url: str) -> List[Dict[str, Any]]:
        """Scrape featured/hero products from homepage"""
        hero_products = []
        
        try:
            # Look for product links on homepage
            product_links = soup.find_all('a', href=re.compile(r'/products/'))
            
            seen_products = set()
            for link in product_links[:6]:  # Limit to first 6 featured products
                href = link.get('href')
                if href and href not in seen_products:
                    seen_products.add(href)
                    
                    # Extract product info from link
                    product_info = {
                        'title': '',
                        'url': urljoin(website_url, href),
                        'image': '',
                        'price': ''
                    }
                    
                    # Try to get title from link text or nearby elements
                    title_text = link.get_text().strip()
                    if title_text:
                        product_info['title'] = title_text
                    
                    # Look for product images
                    img = link.find('img')
                    if img and img.get('src'):
                        product_info['image'] = img['src']
                    
                    # Look for price in nearby elements
                    price_elem = link.find(class_=re.compile(r'price', re.I))
                    if price_elem:
                        product_info['price'] = price_elem.get_text().strip()
                    
                    if product_info['title'] or product_info['image']:
                        hero_products.append(product_info)
            
            logger.info(f"Found {len(hero_products)} hero products")
            
        except Exception as e:
            logger.error(f"Error scraping hero products: {str(e)}")
        
        return hero_products
    
    def _scrape_privacy_policy(self, website_url: str) -> str:
        """Scrape privacy policy content"""
        return self._scrape_policy_page(website_url, ['privacy', 'privacy-policy', 'policies/privacy-policy'])
    
    def _scrape_return_policy(self, website_url: str) -> str:
        """Scrape return/refund policy content"""
        return self._scrape_policy_page(website_url, ['return', 'refund', 'returns', 'refunds', 'shipping-returns', 'policies/refund-policy'])
    
    def _scrape_policy_page(self, website_url: str, possible_paths: List[str]) -> str:
        """Generic method to scrape policy pages"""
        for path in possible_paths:
            try:
                url = urljoin(website_url, f'/{path}')
                response = self.session.get(url, timeout=self.timeout)
                
                if response.status_code == 200:
                    # Use trafilatura to extract clean text
                    text_content = trafilatura.extract(response.content)
                    if text_content and len(text_content.strip()) > 100:
                        logger.info(f"Found policy content at: {url}")
                        return text_content.strip()
                        
            except Exception as e:
                logger.debug(f"Could not access {url}: {str(e)}")
                continue
        
        return ""
    
    def _scrape_faqs(self, website_url: str) -> List[Dict[str, str]]:
        """Scrape FAQ content"""
        faq_paths = ['faq', 'faqs', 'help', 'support', 'pages/faq']
        
        for path in faq_paths:
            try:
                url = urljoin(website_url, f'/{path}')
                response = self.session.get(url, timeout=self.timeout)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    faqs = []
                    
                    # Look for FAQ patterns
                    faq_sections = soup.find_all(['div', 'section'], class_=re.compile(r'faq|question|accordion', re.I))
                    
                    for section in faq_sections:
                        questions = section.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'dt'])
                        for q in questions:
                            question_text = q.get_text().strip()
                            if question_text and '?' in question_text:
                                # Look for answer in next sibling or parent
                                answer_elem = q.find_next_sibling(['p', 'div', 'dd'])
                                answer_text = answer_elem.get_text().strip() if answer_elem else ""
                                
                                if answer_text:
                                    faqs.append({
                                        'question': question_text,
                                        'answer': answer_text
                                    })
                    
                    if faqs:
                        logger.info(f"Found {len(faqs)} FAQs at: {url}")
                        return faqs
                        
            except Exception as e:
                logger.debug(f"Could not access FAQ at {url}: {str(e)}")
                continue
        
        return []
    
    def _extract_social_handles(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract social media handles and links"""
        social_handles = {}
        
        social_patterns = {
            'instagram': [r'instagram\.com/([^/\s"\']+)', r'@([a-zA-Z0-9_.]+)'],
            'facebook': [r'facebook\.com/([^/\s"\']+)'],
            'twitter': [r'twitter\.com/([^/\s"\']+)', r'x\.com/([^/\s"\']+)'],
            'tiktok': [r'tiktok\.com/@([^/\s"\']+)'],
            'youtube': [r'youtube\.com/([^/\s"\']+)'],
            'linkedin': [r'linkedin\.com/([^/\s"\']+)']
        }
        
        # Get all links
        links = soup.find_all('a', href=True)
        page_text = soup.get_text()
        
        for platform, patterns in social_patterns.items():
            for pattern in patterns:
                # Search in links
                for link in links:
                    href = link.get('href', '')
                    match = re.search(pattern, href, re.IGNORECASE)
                    if match:
                        social_handles[platform] = {
                            'handle': match.group(1),
                            'url': href
                        }
                        break
                
                # Search in page text for handles
                if platform not in social_handles:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        social_handles[platform] = {
                            'handle': match.group(1),
                            'url': f"https://{platform}.com/{match.group(1)}"
                        }
        
        return social_handles
    
    def _extract_contact_details(self, soup: BeautifulSoup, website_url: str) -> Dict[str, Any]:
        """Extract contact information"""
        contact_details = {}
        
        # Email patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        # Phone patterns (various formats)
        phone_pattern = r'(\+?1?[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        
        page_text = soup.get_text()
        
        # Extract emails
        emails = re.findall(email_pattern, page_text)
        if emails:
            # Filter out common non-contact emails
            contact_emails = [email for email in emails if not any(exclude in email.lower() 
                             for exclude in ['noreply', 'no-reply', 'admin', 'webmaster'])]
            if contact_emails:
                contact_details['emails'] = list(set(contact_emails))
        
        # Extract phone numbers
        phones = re.findall(phone_pattern, page_text)
        if phones:
            contact_details['phones'] = list(set(phones))
        
        # Look for address information
        address_keywords = ['address', 'location', 'office', 'store location']
        for keyword in address_keywords:
            address_elem = soup.find(text=re.compile(keyword, re.I))
            if address_elem:
                parent = address_elem.parent
                if parent:
                    address_text = parent.get_text().strip()
                    if len(address_text) > 20:  # Likely contains address info
                        contact_details['address'] = address_text
                        break
        
        # Try to scrape contact page
        contact_page_info = self._scrape_contact_page(website_url)
        if contact_page_info:
            contact_details.update(contact_page_info)
        
        return contact_details
    
    def _scrape_contact_page(self, website_url: str) -> Dict[str, Any]:
        """Scrape contact page for additional contact information"""
        contact_paths = ['contact', 'contact-us', 'pages/contact', 'pages/contact-us']
        
        for path in contact_paths:
            try:
                url = urljoin(website_url, f'/{path}')
                response = self.session.get(url, timeout=self.timeout)
                
                if response.status_code == 200:
                    text_content = trafilatura.extract(response.content)
                    if text_content:
                        contact_info = {}
                        
                        # Extract emails from contact page
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        emails = re.findall(email_pattern, text_content)
                        if emails:
                            contact_info['contact_page_emails'] = list(set(emails))
                        
                        # Extract phone numbers
                        phone_pattern = r'(\+?1?[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
                        phones = re.findall(phone_pattern, text_content)
                        if phones:
                            contact_info['contact_page_phones'] = list(set(phones))
                        
                        return contact_info
                        
            except Exception as e:
                logger.debug(f"Could not access contact page at {url}: {str(e)}")
                continue
        
        return {}
    
    def _scrape_brand_context(self, website_url: str) -> str:
        """Scrape brand context from About page"""
        about_paths = ['about', 'about-us', 'pages/about', 'pages/about-us', 'our-story', 'pages/our-story']
        
        for path in about_paths:
            try:
                url = urljoin(website_url, f'/{path}')
                response = self.session.get(url, timeout=self.timeout)
                
                if response.status_code == 200:
                    text_content = trafilatura.extract(response.content)
                    if text_content and len(text_content.strip()) > 100:
                        logger.info(f"Found brand context at: {url}")
                        return text_content.strip()
                        
            except Exception as e:
                logger.debug(f"Could not access about page at {url}: {str(e)}")
                continue
        
        return ""
    
    def _extract_important_links(self, soup: BeautifulSoup, website_url: str) -> List[Dict[str, str]]:
        """Extract important links like order tracking, blogs, etc."""
        important_links = []
        
        # Define important link patterns
        important_patterns = {
            'order_tracking': ['track', 'tracking', 'order-status', 'track-order'],
            'blog': ['blog', 'news', 'articles'],
            'support': ['support', 'help', 'customer-service'],
            'shipping': ['shipping', 'delivery'],
            'size_guide': ['size-guide', 'sizing', 'size-chart'],
            'gift_cards': ['gift-card', 'gift-cards'],
            'wholesale': ['wholesale', 'trade', 'bulk']
        }
        
        # Find all navigation links
        nav_links = []
        
        # Look in navigation menus
        nav_elements = soup.find_all(['nav', 'header', 'footer'])
        for nav in nav_elements:
            links = nav.find_all('a', href=True)
            nav_links.extend(links)
        
        # Also check general page links
        all_links = soup.find_all('a', href=True)
        nav_links.extend(all_links)
        
        for category, keywords in important_patterns.items():
            for link in nav_links:
                href = link.get('href', '').lower()
                text = link.get_text().strip().lower()
                
                # Check if any keyword matches the link
                for keyword in keywords:
                    if keyword in href or keyword in text:
                        full_url = urljoin(website_url, link.get('href'))
                        important_links.append({
                            'category': category,
                            'title': link.get_text().strip(),
                            'url': full_url
                        })
                        break
                
                if any(keyword in href or keyword in text for keyword in keywords):
                    break
        
        # Remove duplicates
        seen_urls = set()
        unique_links = []
        for link in important_links:
            if link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_links.append(link)
        
        return unique_links
