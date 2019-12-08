import socket
from threading import Thread, Event
from os.path import exists


class Downloader(Thread):
    def __init__(self, connect: socket, address: (str, int), stop_event: Event):
        super().__init__(daemon=True)
        self.connect: socket = connect
        self.addr: (str, int) = address
        self.__stop_event: Event = stop_event

        print(address + "is connected")

    def __receive_file_name(self) -> str:
        length = self.connect.recv(4)
        length = int.from_bytes(length, 'little')
        name = self.connect.recv(length).decode()
        copy_n = 0
        if exists(name):
            copy_n += 1
        ex = ''
        try:
            dot_ix = name.rindex('.')
            name, ex = name[:dot_ix], name[dot_ix:]
        except ValueError:
            pass
        while exists(name + '_copy' + str(copy_n) + ex):
            copy_n += 1
        if copy_n > 0:
            name += '_copy' + str(copy_n) + ex
        else:
            name += ex
        return name

    def __receive_file(self):
        filename = self.__receive_file_name()
        print('Downloading' + filename)
        with open(filename, 'wb') as file:
            data = self.connect.recv(1024)
            while data and not self.__stop_event.is_set():
                file.write(data)
                data = self.connect.recv(1024)
        self.connect.shutdown(socket.SHUT_RD)
        self.connect.close()
        print(filename + 'has been successfully downloaded.')


    def run(self):
        self.__receive_file()


class Waiter(Thread):
    def __init__(self):
        super().__init__()
        self.sock: socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__stop_event = Event()

    def run(self):
        self.sock.bind(('', 20123))
        self.sock.listen(8)
        print('Maybe anyone wants to send anything? Lets wait')
        while not self.__stop_event.is_set():
            connect, address = self.sock.accept()
            Downloader(connect, address, self.__stop_event).start()
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()

    def stop(self):
        self.__stop_event.set()
        self.sock.close()
        print('Closed main socket.')




def main():
    waiter = Waiter()
    try:
        waiter.start()
        waiter.join()
    except KeyboardInterrupt:
        print('\nBye bye')
        waiter.stop()


if __name__ == '__main__':
    main()
