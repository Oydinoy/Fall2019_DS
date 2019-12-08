import socket
from sys import stdout
from threading import Thread
from time import sleep

class Sender(Thread):

    def __init__(self, filename: str, address: (str, int)):
        super().__init__(daemon=True)
        self.name: str = filename
        self.size: int = -1
        self.address = address

    def __send_file(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(self.address)

        filename_len = len(self.name).to_bytes(4, 'little')
        filename_send = self.name
        if self.name[:2] == '.\\':
            filename_send = self.name[2:]
            filename_len = (len(self.name) - 2).to_bytes(4, 'little')
        sock.send(filename_len)
        sock.send(filename_send.encode())

        from os.path import getsize
        self.size = getsize(self.name)

        self.bytes_sent = 0
        with open(self.name, 'rb') as file:
            data = file.read(1024)
            while data:
                sock.send(data)
                data = file.read(1024)
                self.bytes_sent += len(data)
        self.bytes_sent = self.size

        sock.shutdown(socket.SHUT_WR)
        sock.close()

    def run(self):
        self.__send_file()

    def get_progress(self) -> float:
        if self.size < 0:
            return 0
        return self.bytes_sent / self.size * 100

    def __bool__(self):
        return self.is_alive()


def print_progress_bar(title: str, progress: float):
    title_out = title
    if len(title) > 20:
        title_out = title[:17] + '...'
    if len(title) < 20:
        title_out = title + ' ' * (20 - len(title))
    progress_int = int(progress // 2)
    left_int = 50 - progress_int
    out = '%s  |%s%s|  %3.f%%\n' % (title_out, '*' * progress_int, '_' * left_int, progress)
    stdout.write(out)
    stdout.flush()


def main():
    given = [str(i) for i in input().split()]
    files = given[0:-2]
    given[-1] = int(given[-1])
    addr = tuple(given[-2:])
    to_send = []
    for i in files:
        sender = Sender(i, addr)
        sender.start()
        to_send.append(sender)


    while any(to_send):
        for i in to_send:
            print_progress_bar(i.name, i.get_progress())
        stdout.write('\033[%iA\r' % len(to_send))
        stdout.flush()
        sleep(0.5)
    for i in to_send:
        print_progress_bar(i.name, 100)

    for i in to_send:
        i.join()


if __name__ == '__main__':
    main()
