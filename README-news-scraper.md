# 📰 News Scraper for Politie Forum Nederland

This module handles automated news scraping and AI-powered rewriting for the Politie Forum Nederland website.

## Features

- **Automated News Scraping**: Selenium-based scraping from Dutch news sources
- **AI-Powered Rewriting**: Uses Groq API to rewrite articles in police/security context  
- **Firestore Integration**: Stores both original and rewritten articles
- **HTML Formatting**: Adds proper heading structure (H1, H2, H3) and paragraphs
- **Category Classification**: Automatically categorizes articles by security topic

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Setup Firebase**:
   - Place your `serviceAccountKey.json` in the project root
   - Configure Firestore rules: `firebase deploy --only firestore:rules`

## Usage

### Manual Run
```bash
python news-ripper-selenium.py
```

### Automated Schedule
```bash
# Add to crontab for daily runs
0 6 * * * /path/to/python /path/to/news-ripper-selenium.py
```

## Configuration

### Environment Variables

- `GROQ_API_KEY`: Your Groq API key for AI rewriting
- `FIREBASE_PROJECT_ID`: Firebase project identifier
- `NEWS_SOURCES_LIMIT`: Maximum articles to process (default: 50)
- `SCRAPE_INTERVAL_HOURS`: Hours between scraping runs (default: 24)

### News Sources

The scraper targets Dutch news sources with focus on:
- Crime and security news
- Police operations and reports  
- Public safety announcements
- Law enforcement updates

## Output

### Firestore Collections

1. **articles_full**: Original scraped articles
   - `title`: Original article title
   - `content`: Full original content  
   - `url`: Source URL
   - `timestamp`: Scraping timestamp
   - `source`: News source identifier

2. **articles_rewritten**: AI-enhanced articles
   - `title`: Rewritten title for police context
   - `content`: AI-rewritten content with HTML formatting
   - `category`: Auto-assigned category
   - `original_url`: Link to original source
   - `timestamp`: Processing timestamp
   - `summary`: Brief article summary

## AI Rewriting Process

1. **Content Analysis**: Analyzes article relevance to police/security topics
2. **Contextual Rewriting**: Rewrites from police/security professional perspective  
3. **HTML Formatting**: Adds proper heading hierarchy and paragraph structure
4. **Category Assignment**: Classifies into relevant security categories
5. **Quality Check**: Validates output before storage

## Categories

- **Crime Prevention**: Community safety and prevention strategies
- **Traffic Safety**: Road safety and traffic enforcement
- **Cybercrime**: Digital security and cyber threats  
- **Drug Enforcement**: Narcotics operations and prevention
- **Emergency Response**: Crisis management and emergency services
- **Youth Safety**: Programs and initiatives for young people
- **Community Policing**: Community engagement and partnerships
- **Border Security**: Immigration and border control
- **Environmental Crime**: Environmental law enforcement
- **Forensic Investigation**: Crime scene and forensic updates

## Error Handling

- **Rate Limiting**: Respects API limits with exponential backoff
- **Network Errors**: Robust retry mechanisms for network issues
- **Content Validation**: Filters inappropriate or irrelevant content
- **Duplicate Detection**: Prevents duplicate article processing

## Monitoring

- **Logging**: Comprehensive logging of all operations
- **Success Metrics**: Tracks processing success rates
- **Error Reporting**: Detailed error logging for debugging
- **Performance Monitoring**: Tracks processing times and efficiency

## Security

- **API Key Protection**: Environment variable storage for sensitive data
- **Content Sanitization**: XSS protection for user-generated content
- **Access Control**: Firestore security rules for data protection
- **Rate Limiting**: Prevents API abuse and overuse

## Troubleshooting

### Common Issues

1. **Selenium WebDriver**: Ensure Chrome/ChromeDriver compatibility
2. **API Limits**: Check Groq API quota and rate limits  
3. **Firestore Permissions**: Verify service account permissions
4. **Network Connectivity**: Check internet connection and firewall settings

### Debug Mode

```bash
DEBUG=true python news-ripper-selenium.py
```

## Contributing

See `CONTRIBUTING.md` for guidelines on contributing to this module.

## License

See `LICENSE` file for license information.
