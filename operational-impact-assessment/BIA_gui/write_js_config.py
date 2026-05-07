import os

jsText = (
    f"var config = {{ biaBackendAddress: '{os.environ.get('BIA_BACKEND_ADDRESS')}', }}"
)
with open("config.js", "w") as js_file:
    js_file.write(jsText)
