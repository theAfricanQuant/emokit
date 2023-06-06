import itertools
import multiprocessing
import os
import sys
import time
from datetime import datetime, timedelta

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


pool = multiprocessing.Pool(multiprocessing.cpu_count() - 1)

last_i = 1
then = datetime.now()
for i, key in enumerate(next_value(), start=1):
    pool.apply_async(check_key, args=(key,))
    now = datetime.now()
    if now - then > timedelta(minutes=1):
        print(f"{(i - last_i) / 60} keys per second, last key {key}")
        last_i = i
        then = now
    time.sleep(0.00001)

print("No good.")
