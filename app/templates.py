HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>KindLLM</title>
    <style>
        * {
            box-sizing: border-box;
            -webkit-font-smoothing: antialiased;
        }
        body { 
            font-family: "Amazon Ember", "Helvetica Neue", Helvetica, Arial, sans-serif; 
            background-color: #FFFFFF; 
            color: #111111; 
            padding: 24px 16px; 
            margin: 0; 
            line-height: 1.6; 
            font-size: 17px; 
        }
        .wrapper { 
            max-width: 580px; 
            margin: 0 auto; 
            display: flex;
            flex-direction: column;
            min-height: 90vh;
        }
        header { 
            text-align: center; 
            padding-bottom: 16px;
            margin-bottom: 24px;
            border-bottom: 1px solid #111111; 
        }
        .logo {
            font-family: Georgia, serif;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.5px;
            margin: 0;
            color: #000000;
        }
        .tagline {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin: 4px 0 0 0;
            color: #666666;
        }
        .content-area { 
            flex: 1;
            margin-bottom: 30px; 
        }
        .bubble-label {
            font-size: 12px;
            text-transform: uppercase;
            font-weight: bold;
            letter-spacing: 1px;
            color: #555555;
            margin-bottom: 6px;
        }
        .user-query { 
            font-family: Georgia, serif;
            font-style: italic;
            font-size: 18px;
            color: #333333;
            padding-left: 12px;
            border-left: 3px solid #000000;
            margin-bottom: 24px;
        }
        .ai-response { 
            font-family: Georgia, serif;
            font-size: 19px; 
            color: #000000;
            white-space: pre-wrap; 
            margin-bottom: 30px;
        }
        .system-status {
            font-size: 15px;
            color: #666666;
            text-align: center;
            font-style: italic;
            margin-top: 40px;
        }
        form {
            margin-top: auto;
        }
        .input-wrapper {
            position: relative;
            margin-bottom: 12px;
        }
        textarea { 
            width: 100%; 
            height: 100px; 
            font-size: 16px; 
            border: 1.5px solid #222222; 
            border-radius: 6px;
            padding: 12px; 
            resize: none; 
            font-family: inherit; 
            background: #FFFFFF;
            color: #000000;
        }
        textarea:focus {
            outline: none;
            border-color: #000000;
            border-width: 2px;
        }
        button { 
            width: 100%; 
            padding: 16px; 
            background-color: #111111; 
            color: #FFFFFF; 
            font-size: 16px; 
            font-weight: bold; 
            border: none; 
            border-radius: 6px;
            cursor: pointer; 
            letter-spacing: 1px;
            text-transform: uppercase;
            -webkit-appearance: none; 
            transition: background 0.1s ease;
        }
        button:active {
            background-color: #444444;
        }
    </style>
</head>
<body>
    <div class="wrapper">
        <header>
            <div class="logo">KindLLM</div>
            <div class="tagline">Minimal Reading Companion</div>
        </header>
        
        <div class="content-area">
            {% if prompt %}
                <div class="bubble-label">Inquiry</div>
                <div class="user-query">{{ prompt }}</div>
            {% endif %}
            
            {% if response %}
                {% if prompt %}
                    <div class="bubble-label" style="margin-top: 20px;">Response</div>
                    <div class="ai-response">{{ response }}</div>
                {% else %}
                    <div class="system-status">{{ response }}</div>
                {% endif %}
            {% endif %}
        </div>
        
        <form method="POST" action="/">
            <div class="input-wrapper">
                <textarea name="prompt" placeholder="Ask anything, simplify concepts, or request book summaries..." required></textarea>
            </div>
            <button type="submit">Ask Assistant</button>
        </form>
    </div>
</body>
</html>
"""
