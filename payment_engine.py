from enum import Enum
from decimal import Decimal, getcontext
from csv import Sniffer, DictReader
from sys import argv, exit

getcontext().prec = 4

class TransactionType(Enum):
    DEPOSIT = 'deposit'
    WITHDRAWAL = 'withdrawal'
    DISPUTE = 'dispute'
    RESOLVE = 'resolve'
    CHARGEBACK = 'chargeback'
	
class Account():
    def __init__(self, client_id: int):
        self._client_id = client_id
        self._total = Decimal(0)
        self._available = Decimal(0)
        self._held = Decimal(0)
        self._locked = False

    def __str__(self):
        return f'{self._client_id}, {self._available}, {self._held}, ' \
               f'{self._total}, {self._locked}'	

    @property
    def client_id(self):
        return self._client_id
        
    @property
    def total(self):
        return self._total
        
    @total.setter
    def total(self, new_total):
        self._total = Decimal(new_total)
        
    @property
    def available(self):
        return self._available
        
    @available.setter
    def available(self, new_available):
        self._available = Decimal(new_available)
        
    @property
    def held(self):
        return self._held
        
    @held.setter
    def held(self, new_held):
        self._held = Decimal(new_held)
        
    @property
    def locked(self):
        return self._locked
      
    @locked.setter
    def locked(self, new_locked):
        self._locked = new_locked
        
        
class Transaction():
    def __init__(self, _type: TransactionType, client_id: int, tx_id: int, amount: Decimal=0):
        self._type = _type
        self._client_id = client_id
        self._tx_id = tx_id
        self._amount = amount
        # If new client, create account
        if client_id not in accounts:
            accounts[client_id] = Account(client_id)
        # Ignore frozen accounts
        if accounts[client_id].locked:
            return         
        if _type == TransactionType.DEPOSIT.value:
            accounts[client_id].total += amount
            accounts[client_id].available += amount
        elif _type == TransactionType.WITHDRAWAL.value:
            # Don't allow withdrawal of more than available (all or nothing)
            if Decimal(amount) <= Decimal(accounts[client_id].available):
                accounts[client_id].total -= amount
                accounts[client_id].available -= amount
        elif _type == TransactionType.DISPUTE.value:
            # Do nothing if we can't find the tx_id
            if tx_id in transactions:
                # Also do nothing if this client is disputing another client
                if client_id == transactions[tx_id].client_id:
                    # Only handle disputing deposits
                    if transactions[tx_id].tx_type == TransactionType.DEPOSIT.value:
                        accounts[client_id].available -= transactions[tx_id].amount
                        accounts[client_id].held += transactions[tx_id].amount
        elif _type == TransactionType.RESOLVE.value:
            # Do nothing if we can't find the tx_id
            if tx_id in transactions:
                # Also do nothing if this client is resolving another client
                if client_id == transactions[tx_id].client_id:
                    # This may have been resolved or chargedback already
                    if accounts[client_id].held > 0:
                        # Only handle resolving deposits
                        if transactions[tx_id].tx_type == TransactionType.DEPOSIT.value:
                            accounts[client_id].available += transactions[tx_id].amount
                            accounts[client_id].held -= transactions[tx_id].amount
        elif _type == TransactionType.CHARGEBACK.value:
            # Do nothing if we can't find the tx_id
            if tx_id in transactions:
                # Also do nothing if this client is charging back another client
                if client_id == transactions[tx_id].client_id:
                    # This may have been resolved or chargedback already
                    if accounts[client_id].held > 0:
                        # Only handle chargeback on deposits
                        if transactions[tx_id].tx_type == TransactionType.DEPOSIT.value:
                            accounts[client_id].total -= transactions[tx_id].amount
                            accounts[client_id].held -= transactions[tx_id].amount
                            accounts[client_id].locked = True
                    
    def __str__(self):
        return f"<TransactionType='{self._type}', ID='{self._tx_id}', " \
               f"Client='{self._client_id}', Amount='{self._amount}'>"
               
    @property
    def tx_type(self):
        return self._type

    @property
    def client_id(self):
        return self._client_id

    @property
    def tx_id(self):
        return self._tx_id

    @property
    def amount(self):
        return self._amount

accounts = {}
transactions = {}        

def main():
    if len(argv) < 2:
        exit("No input file specified")
    else:
        input_csv = argv[1]
        csvfile = open(input_csv, newline='')
        has_header = Sniffer().has_header(csvfile.read(1024))
        csvfile.close()
        fields = ['type', 'client', 'tx', 'amount']
        with open(input_csv, newline='') as csvfile:
            reader = DictReader(csvfile, fieldnames=None if has_header else fields)
            for row in reader:
                # If tx_id already recorded, ignore deposits and withdrawals
                if int(row['tx']) in transactions:
                    if row['type'] in [TransactionType.DEPOSIT.value, TransactionType.WITHDRAWAL.value]:
                        continue
                    else:
                        # Not adding disputes, resolves, or chargebacks to transactions
                        transx = Transaction(row['type'], int(row['client']), int(row['tx']), 0)
                # If tx_id NOT already recorded, can only be deposits and withdrawals
                else:
                    if row['type'] not in [TransactionType.DEPOSIT.value, TransactionType.WITHDRAWAL.value]:
                        continue
                    else:
                        # These need to be added to the transactions
                        transx = Transaction(row['type'], int(row['client']), int(row['tx']), Decimal(row['amount']))
                        transactions[int(row['tx'])] = transx
        print('client,available,held,total,locked')
        for acct in accounts:
            print(accounts[acct])
            
if __name__ == "__main__":
    main()            