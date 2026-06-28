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
        .header-container {
            text-align: center;
            position: relative;
            margin-bottom: 30px;
        }
        h1 {
            font-size: 28px;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .subtitle {
            font-size: 12px;
            color: #555555;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 15px;
        }
        hr {
            border: 0;
            border-top: 1px solid #000000;
            margin-bottom: 30px;
        }
        .section-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #333333;
            font-weight: bold;
            margin-bottom: 5px;
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
        .clear-btn {
            display: inline-block;
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #000000;
            padding: 6px 12px;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            text-decoration: none;
            margin-top: 5px;
            font-family: sans-serif;
            font-weight: bold;
        }
        .clear-btn:hover {
            background-color: #000000;
            color: #ffffff;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-container">
            <h1>KindLLM</h1>
            <div class="subtitle">Minimal Reading Companion</div>
            <!-- Converted to a clean hyperlink to avoid browser form crashes -->
            <a href="/clear" class="clear-btn">Clear Chat Memory</a>
        </div>
        <hr>

        RENDERED_CONTENT_PLACEHOLDER

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
