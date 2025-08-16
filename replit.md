# Shopify Store Scraper API

## Overview

A Flask-based web scraping application that extracts comprehensive insights from Shopify stores without using official APIs. The application provides a REST API endpoint that accepts any Shopify store URL and returns structured JSON data containing product catalogs, policies, brand information, and contact details. It includes a web interface for testing the API and uses web scraping techniques to gather data from publicly available store pages.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework for lightweight API development
- **Web Scraping Engine**: Custom `ShopifyStoreScraper` class using requests, BeautifulSoup, and trafilatura for content extraction
- **Session Management**: Persistent HTTP sessions with browser-like headers to avoid bot detection
- **Error Handling**: Comprehensive logging and graceful error responses for failed scraping attempts

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 for responsive UI
- **Styling**: Bootstrap with dark theme customizations and Feather icons
- **JavaScript**: Vanilla JavaScript for form handling and AJAX API calls
- **Layout**: Single-page application with API testing interface

### API Design
- **Endpoint Structure**: RESTful `/fetch_insights` POST endpoint accepting JSON payloads
- **Input Validation**: URL normalization and validation with proper error responses
- **Response Format**: Structured JSON containing store name, products, policies, and brand information
- **HTTP Methods**: POST for data submission with JSON content type

### Data Extraction Strategy
- **Store Detection**: HTML parsing to verify Shopify platform presence
- **Content Sources**: Multiple extraction methods including JSON endpoints (`/products.json`) and HTML parsing
- **Data Categories**: 
  - Product catalog and hero products
  - Legal policies (privacy, returns)
  - Brand context and FAQs
  - Contact information and social media handles
  - Important navigation links

### Error Handling and Resilience
- **Timeout Management**: 10-second request timeouts to prevent hanging
- **Graceful Degradation**: Continues extraction even if some data sources fail
- **Logging**: Debug-level logging for troubleshooting scraping issues
- **Status Code Handling**: Proper HTTP status codes for different error scenarios

## External Dependencies

### Core Web Framework
- **Flask**: Main web application framework
- **Jinja2**: Template rendering (included with Flask)

### Web Scraping Libraries
- **requests**: HTTP client for making web requests with session management
- **BeautifulSoup4**: HTML parsing and DOM manipulation
- **trafilatura**: Advanced content extraction for clean text parsing

### Frontend Dependencies (CDN)
- **Bootstrap 5**: UI framework with dark theme support
- **Feather Icons**: Icon library for consistent visual elements

### Development Dependencies
- **Python logging**: Built-in logging for debugging and monitoring
- **urllib.parse**: URL manipulation and validation utilities

### Optional Integrations
- Session management ready for authentication systems
- Extensible architecture for additional data sources
- Environment variable support for configuration management