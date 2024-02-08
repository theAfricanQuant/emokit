import itertools
import os
import sys
from datetime import datetime, timedelta

import zmq
from Crypto.Cipher import AES

filename = 'emotiv_encrypted_data_UD20160103001874_2017-04-05.17-21-32.384061.txt'
# filename = 'emotiv_encrypted_data_UD20160103001874_2017-04-05.17-42-23.292665.txt'
serial_number = 'UD20160103001874'
iv = os.urandom(AES.block_size)

# Probably need to expand this and probably use a serial brute force like approach, but meh
# Lets just see if it works.
charset = list(serial_number[-4:])
charset.extend(['\x00', '\x10', 'H', 'T', 'B', 'P'])
possible_combinations = len(charset) * 16 * 16


# Credit http://stackoverflow.com/questions/11747254/python-brute-force-algorithm
def next_value():
    return (''.join(candidate)
            for candidate in itertools.chain.from_iterable(itertools.product(charset, repeat=i)
                                                           for i in range(16, 16 + 1)))


def counter_check(file_data, cipher, swap_data=False):
    counter_misses = 0
    last_counter = 0
    for counter_checks, line in enumerate(file_data):
        data = line.split(',')[1:]
        data = [int(value, 2) for value in data]
        data = ''.join(map(chr, data))
        if not swap_data:
            decrypted = cipher.decrypt(data[:16]) + cipher.decrypt(data[16:])
        else:
            decrypted = cipher.decrypt(data[16:]) + cipher.decrypt(data[:16])
        counter = ord(decrypted[0])
        # Uncomment this
        # print(counter)
        if (
            counter <= 127
            and counter != last_counter + 1
            or counter > 127
            and (counter != 0 or last_counter <= 127)
        ):
            counter_misses += 1
        if counter_misses > 2 and counter_checks > 16:
            return False
        if counter_checks > 16 and counter_misses < 2:
            return True
        last_counter = counter


with open(f'{filename}', 'r') as encrypted_data:
    file_data = encrypted_data.readlines()


def check_key(next_check):
    new_cipher = AES.new(''.join(next_check), AES.MODE_ECB, iv)
    if counter_check(file_data, new_cipher):
        print(f"Correct Key Found! {next_check}")
        sys.exit()


context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('tcp://127.0.0.1:1777')
then = datetime.now()
i = 0
last_i = 0
key_to_validate = ""
while True:
    i += 1
    now = datetime.now()
    if now - then > timedelta(minutes=1):
        print(f"{(i - last_i) / 60} keys per second, last key {key_to_validate}")
        last_i = i
        then = datetime.now()
    socket.send('next')
    key_to_validate = socket.recv()
    if check_key(key_to_validate):
        socket.send(f'validate {key_to_validate}')
        print(socket.recv())
