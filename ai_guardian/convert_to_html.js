const fs = require('fs');
const path = require('path');
const { marked } = require('marked');

// Read the markdown file
const markdownPath = path.join(__dirname, 'DEPLOYMENT_RESULTS.md');
const markdownContent = fs.readFileSync(markdownPath, 'utf8');

// Convert to HTML
const htmlContent = marked(markdownContent);

// Create a complete HTML document with styling
const fullHtml = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>MESA Rights Vault - Deployment Results</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      line-height: 1.6;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
    }
    h1, h2, h3 {
      color: #333;
    }
    code {
      background-color: #f4f4f4;
      padding: 2px 5px;
      border-radius: 3px;
    }
    pre {
      background-color: #f4f4f4;
      padding: 10px;
      border-radius: 5px;
      overflow-x: auto;
    }
    a {
      color: #0066cc;
    }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    th, td {
      border: 1px solid #ddd;
      padding: 8px;
      text-align: left;
    }
    th {
      background-color: #f2f2f2;
    }
  </style>
</head>
<body>
  ${htmlContent}
</body>
</html>
`;

// Write the HTML file
const htmlPath = path.join(__dirname, 'DEPLOYMENT_RESULTS.html');
fs.writeFileSync(htmlPath, fullHtml);

console.log(`HTML file created at: ${htmlPath}`); 