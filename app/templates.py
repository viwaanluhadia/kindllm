HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KindLLM</title>
    <style>
        body {
            font-family: Georgia, serif;
            background-color: #ffffff;
            color: #000000;
            margin: 0;
            padding: 20px;
            font-size: 18px;
            line-height: 1.6;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            font-size: 28px;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .subtitle {
            text-align: center;
            font-size: 12px;
            color: #555555;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 20px;
        }
        .clear-container {
            text-align: center;
            margin-bottom: 20px;
        }
        .clear-btn {
            background: none;
            border: 1px solid #000000;
            color: #000000;
            padding: 5px 15px;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        hr {
            border: 0;
            border-top: 1px solid #000000;
            margin-bottom: 30px;
        }
        .header-inline {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }
        .section-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #333333;
            font-weight: bold;
        }
        .copy-btn {
            background: none;
            border: 1px dashed #000000;
            color: #000000;
            padding: 2px 8px;
            font-size: 10px;
            text-transform: uppercase;
            cursor: pointer;
            font-family: Georgia, serif;
        }
        .query-text {
            font-style: italic;
            margin-bottom: 30px;
            padding-left: 10px;
            border-left: 2px solid #000000;
        }
        .response-body {
            margin-bottom: 40px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 16px;
        }
        th, td {
            border: 1px solid #000000 !important;
            padding: 10px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        ul, ol {
            padding-left: 25px;
            margin: 15px 0;
        }
        li {
            margin-bottom: 5px;
        }
        pre {
            background-color: #f9f9f9;
            border: 1px dashed #000000;
            padding: 15px;
            overflow-x: auto;
            margin: 20px 0;
        }
        code {
            font-family: 'Courier New', Courier, monospace;
            font-size: 15px;
            font-weight: bold;
            color: #000000;
        }
        .input-area {
            margin-top: 50px;
        }
        textarea {
            width: 100%;
            height: 100px;
            padding: 15px;
            font-size: 16px;
            font-family: Georgia, serif;
            border: 2px solid #000000;
            box-sizing: border-box;
            resize: none;
            background-color: #ffffff;
            color: #000000;
        }
        button {
            width: 100%;
            background-color: #000000;
            color: #ffffff;
            border: none;
            padding: 15px;
            font-size: 16px;
            font-weight: bold;
            text-transform: uppercase;
            cursor: pointer;
            margin-top: 15px;
            letter-spacing: 1px;
        }
    </style>
    <script>
        function copyToClipboard() {
            const responseElement = document.getElementById('response-text');
            if (!responseElement) return;
            
            // Extracts plain text from the rendered HTML content container safely
            const textToCopy = responseElement.innerText;
            
            navigator.clipboard.writeText(textToCopy).then(() => {
                const btn = document.getElementById('copy-button');
                btn.innerText = 'Copied!';
                setTimeout(() => {
                    btn.innerText = 'Copy';
                }, 2000);
            }).catch(err => {
                console.error('Could not copy text: ', err);
            });
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>KindLLM</h1>
        <div class="subtitle">Minimal Reading Companion</div>
        <div class="clear-container">
            <a href="/clear" class="clear-btn">Clear Chat Memory</a>
        </div>
        <hr>

        <div class="section-label">Inquiry</div>
        <div class="query-text">{inquiry}</div>
        
        <div class="header-inline">
            <div class="section-label">Response</div>
            <button id="copy-button" class="copy-btn" onclick="copyToClipboard()">Copy</button>
        </div>
        <div id="response-text" class="response-body">{html_response}</div>

        <div class="input-area">
            <form method="POST" action="/">
                <textarea name="inquiry" placeholder="Ask anything, compare concepts, or request structured tables..." required></textarea>
                <button type="submit">Ask Assistant</button>
            </form>
        </div>
    </div>
</body>
</html>
"""
