import json
import time
import tempfile
import argparse
import os

from playwright.sync_api import sync_playwright

def create_html(js_code):

    head = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Clearfake</title>
        <style>
            body {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                font-family: system-ui, sans-serif;
            }
            .message {
                padding: 20px;
                border-radius: 4px;
                background-color: #f0f0f0;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="message">
            Clearfake URL grabber
        </div>

        <script>
    
    """

    tail = """
        </script>
      </body>
    </html>
    """

    return f"{head} {js_code} {tail}"



def handle_request(route, request):

    if request.url.startswith("file:"):
        route.continue_()
    elif 'bsc' in request.url:
        route.fulfill(
            status=200,
            content_type='application/json',
            body=json.dumps({"jsonrpc":"2.0","id":97,"result":"0x000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000026e6f000000000000000000000000000000000000000000000000000000000000"})
        )
    else:
        route.fulfill(
            status=404,
            content_type="text/plain",
            body="not found!")
        


def get_clipboard_from_playwright(path, user_agent):

    with sync_playwright() as p:
        
        debug = False
        browser = p.chromium.launch(headless= not debug)
        
        context = browser.new_context(
            permissions=['clipboard-read', 'clipboard-write'],
            user_agent=user_agent,
            viewport={"width": 1920, "height": 1080},
        )
        
        # Lower the default timeout from 30 to 3 seconds
        context.set_default_timeout(3000)
        
        context.set_offline(True)
        page = context.new_page()

        page.route("**/*", handle_request)

        # open a local file 
        page.goto(f"file://{path}")

        clips = []
        # do the click, then reload so we can determine if there is always a different subdomain
        for _ in range(2): 
            page.get_by_role("button").first.click()
            time.sleep(1)
            clipboard_text = page.evaluate("navigator.clipboard.readText()")
            clips.append(clipboard_text)
            page.reload()

        
        page.route("**/*", None) # remove handler, so we don't get errors
        time.sleep(1)
        p.stop()

        return clips
    

def create_parser():
    parser = argparse.ArgumentParser(description='get the clipboard text from clearfake js file')
    parser.add_argument('js_file', type=str, help='file with the js code from the contract')
    parser.add_argument('--user-agent', type=str, default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0", help='user agent to use for the browser')
    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    js_code = ""
    with open(args.js_file, "r") as f: 
        js_code = f.read()


    temp_dir = tempfile.mkdtemp(prefix="pw_clearfake")

    filename = f"{temp_dir}/file.html"

    with open(filename, 'w') as f:
        f.write(create_html(js_code))

    clips = get_clipboard_from_playwright(filename, args.user_agent)
    for clippy in clips: 
        print(clippy)
    with open(f'{args.js_file}.out', 'w') as f:
        f.write("\n".join(clips))

    os.remove(filename)
    os.rmdir(temp_dir)


if __name__ == '__main__':
    main()
