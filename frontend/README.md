# FastML Serve Frontend

A simple HTML/CSS/JavaScript frontend for the FastML Serve sentiment analysis API.

## Features

- **Single Text Analysis**: Analyze individual text snippets
- **Batch Analysis**: Process multiple texts at once (up to 32)
- **Real-time Service Status**: Monitor API health and uptime
- **Character Counter**: Visual feedback for text input limits
- **Responsive Design**: Works on desktop and mobile devices
- **Visual Results**: Color-coded sentiment results with confidence scores

## Usage

1. **Start the FastML Serve API** (see main README)

2. **Port-forward the service**:
   ```bash
   kubectl port-forward -n fastml-serve service/fastml-serve-service 8080:8000
   ```

3. **Open the frontend**:
   Simply open `index.html` in your web browser.

## API Configuration

The frontend is configured to connect to `http://localhost:8080` by default. 

To change the API endpoint, edit the `baseUrl` in `script.js`:

```javascript
constructor() {
    this.baseUrl = 'http://your-api-endpoint:port';
    // ...
}
```

## Browser Compatibility

- Modern browsers (Chrome 60+, Firefox 55+, Safari 12+)
- ES6+ features used (async/await, classes, template literals)
- CSS Grid and Flexbox for layout

## Files

- `index.html` - Main HTML structure
- `style.css` - Styling with gradient backgrounds and animations  
- `script.js` - JavaScript functionality and API integration