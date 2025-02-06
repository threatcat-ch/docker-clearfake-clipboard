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

    else:
        route.fulfill(
            status=200,
            content_type='application/json',
            body=json.dumps({"jsonrpc":"2.0","id":97,"result":"0x000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000026e6f000000000000000000000000000000000000000000000000000000000000"})
        )


def get_clipboard_from_playwright(path):

    with sync_playwright() as p:
        
        debug = False
        browser = p.chromium.launch(headless= not debug, devtools=debug)
        context = browser.new_context(
            permissions=['clipboard-read', 'clipboard-write']
        )
        
        context.set_offline(True)
        page = context.new_page()

        page.route("**/*", handle_request)

        # open a local file 
        page.goto(f"file://{path}")
        page.get_by_role("button").click()
        time.sleep(2)
        
        clipboard_text = page.evaluate("navigator.clipboard.readText()")
        page.route("**/*", None) # remove handler, so we don't get errors
        time.sleep(1)
        p.stop()

        return clipboard_text
    

def create_parser():
    parser = argparse.ArgumentParser(description='get the clipboard text from clearfake js file')
    parser.add_argument('js_file', type=str, help='file with the js code from the contract')
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

    clippy = get_clipboard_from_playwright(filename)
    if "#" in clippy:
        clippy = clippy.split("#")[0]
    print(clippy)

    os.remove(filename)
    os.rmdir(temp_dir)


if __name__ == '__main__':
    main()