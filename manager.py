# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
from multiprocessing import Process
import json
import time
import psutil

hostName = "localhost"
serverPort = 8000
file_name = 'temp.txt'


# todo: reuse


def write_to_temp_file(message):
    time.sleep(5)
    with open(file_name, 'a') as file:
        file.write(message + '\n')
        file.flush()


class MyServer(BaseHTTPRequestHandler):
    global total_invocation
    total_invocation = 0

    def do_GET(self):
        if self.path == "/statistics":
            global total_invocation
            current_process = psutil.Process()
            children = current_process.children(recursive=True)

            statistics = {
                "active_instances": len(children),
                "total_invocation": total_invocation
            }

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(statistics).encode())

            # self.wfile.write(bytes("<html>", "utf-8"))
            # self.wfile.write(bytes("<body>", "utf-8"))
            # self.wfile.write(
            #     bytes("<p>This is an example web server.</p>", "utf-8"))
            # self.wfile.write(bytes("</body></html>", "utf-8"))

    def do_POST(self):
        if self.path == "/messages":
            global total_invocation
            total_invocation += 1

            length = int(self.headers['content-length'])
            post_data = self.rfile.read(length)
            my_json = json.loads(post_data.decode('utf8').replace("'", '"'))
            message = my_json["message"]

            p = Process(target=write_to_temp_file, args=(message,))
            p.start()

            self.send_response(200)
            self.wfile.write(
                bytes("<html>", "utf-8"))
            self.wfile.write(bytes("<body>", "utf-8"))
            self.wfile.write(bytes(message, "utf-8"))
            self.wfile.write(bytes("</body></html>", "utf-8"))


if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
