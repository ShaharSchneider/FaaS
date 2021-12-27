from http.server import BaseHTTPRequestHandler, HTTPServer
import multiprocessing as mp
import json
from queue import Empty
import time
import psutil

hostName = "localhost"
serverPort = 8000
file_name = 'temp.txt'


def write_to_temp_file(queue):
    with open(file_name, 'a') as file:
        while 1:
            time.sleep(5)
            if queue.empty():
                break
            message = queue.get()
            file.write(message + '\n')
            file.flush()


class MyServer(BaseHTTPRequestHandler):
    global total_invocation
    total_invocation = 0

    def __init__(self, request, client_address, server):
        self.queue = server.queue
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def do_GET(self):
        if self.path == "/statistics":
            global total_invocation
            current_process = psutil.Process()
            children = current_process.children(recursive=True)

            statistics = {
                "active_instances": len(children) - 1,
                "total_invocation": total_invocation
            }

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(statistics).encode())

    def do_POST(self):
        if self.path == "/messages":
            global total_invocation
            total_invocation += 1

            length = int(self.headers['content-length'])
            post_data = self.rfile.read(length)
            my_json = json.loads(post_data.decode('utf8').replace("'", '"'))
            message = my_json["message"]
            self.queue.put(message)

            if not self.queue.empty():
                p = mp.Process(target=write_to_temp_file, args=(queue,))
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
    manager = mp.Manager()
    queue = manager.Queue()
    webServer.queue = queue

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
