from http.server import BaseHTTPRequestHandler, HTTPServer
import multiprocessing as mp
import json
import time
import psutil


def faas(event):
    with open(event["file_name"], 'a') as file:
        message = event["message"]
        file.write(message + '\n')
        file.flush()


class Manager():
    def __init__(self, queue):
        self.total_invocation = 0
        self.file_name = 'temp.txt'
        self.queue = queue

    def get_stats(self, context):
        current_process = psutil.Process()
        children = current_process.children(recursive=True)

        statistics = {
            "active_instances": len(children) - 1,
            "total_invocation": self.total_invocation
        }

        context.send_response(200)
        context.send_header("Content-type", "application/json")
        context.end_headers()
        context.wfile.write(json.dumps(statistics).encode())

    def post_message(self, message):
        event = {
            "file_name": self.file_name,
            "message": message
        }

        self.total_invocation += 1

        current_process = psutil.Process()
        children = current_process.children(recursive=True)

        if len(children) - 1 < self.queue.qsize():
            process = mp.Process(target=self.process_handler, args=(event,))
            process.start()
        else:
            self.queue.put(event)

    def process_handler(self, event):
        faas(event)

        startTime = time.time()
        while(time.time() - startTime < 2):
            if not self.queue.empty():
                break

        mp.Lock()
        if not self.queue.empty():
            print(self.queue.qsize())
            self.process_handler(self.queue.get())
            mp.RLock()
        else:
            mp.RLock()
            current_process = psutil.Process()
            current_process.kill()


class MyApiServer(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/statistics":
            self.server.manager.get_stats(self)

    def do_POST(self):
        if self.path == "/messages":
            length = int(self.headers['content-length'])
            post_data = self.rfile.read(length)
            my_json = json.loads(post_data.decode('utf8').replace("'", '"'))
            message = my_json["message"]

            self.send_response(200)
            self.wfile.write(
                bytes("<html><body>%s</body></html>" % message, "utf-8"))

            self.server.manager.post_message(message)


class http_server:
    hostName = "localhost"
    serverPort = 8000

    def __init__(self, manager):
        server = HTTPServer((self.hostName, self.serverPort), MyApiServer)
        server.manager = manager

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass

        server.server_close()


if __name__ == "__main__":
    manager = Manager(mp.Manager().Queue())
    server = http_server(manager)
