import pytest, os, sys, importlib
from decimal import Decimal, getcontext

getcontext().prec = 4

basepath = os.path.dirname(os.path.abspath(__file__))
basedir = os.path.dirname(basepath)
sys.path.insert(0, basedir)
engine = importlib.import_module('payment_engine')

@pytest.fixture
def clear_transx_and_accts():
    engine.accounts = {}
    engine.transactions = {}
    assert 44 not in engine.transactions
    assert 99 not in engine.accounts
    
pytestmark = pytest.mark.usefixtures("clear_transx_and_accts")

def test_account():
    acct = engine.Account(client_id=99)
    assert str(acct) == '99, 0, 0, 0, False'    
    
def test_account_client_id():
    acct = engine.Account(client_id=99)
    assert acct.client_id == 99

def test_account_total():
    acct = engine.Account(client_id=99)
    acct.total = Decimal('33.33')
    assert acct.total == Decimal('33.33')

def test_account_available():
    acct = engine.Account(client_id=99)
    acct.available = Decimal('11.11')
    assert acct.available == Decimal('11.11')    

def test_account_held():
    acct = engine.Account(client_id=99)
    acct.held = Decimal('22.22')
    assert acct.held == Decimal('22.22')
    
def test_account_locked():
    acct = engine.Account(client_id=99)
    acct.locked = True
    assert acct.locked
    
def test_transaction():
    transx = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value, 
                                client_id=99, tx_id=3, amount=Decimal('33.33'))  
    assert str(transx) == f"<TransactionType='deposit', ID='3', " \
                          f"Client='99', Amount='33.33'>"  

def test_transaction_client_id_not_exist():
    transx = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value, 
                                client_id=99, tx_id=3, amount=Decimal('33.33'))
    assert 99 in engine.accounts
    assert str(engine.accounts[99]) == '99, 33.33, 0, 33.33, False'

def test_transaction_client_id_already_exist():
    transx = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value, 
                                client_id=99, tx_id=3, amount=Decimal('33.33'))
    assert 99 in engine.accounts
    assert str(engine.accounts[99]) == '99, 33.33, 0, 33.33, False'
    transx = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value, 
                                client_id=99, tx_id=4, amount=Decimal('33.33'))    
    assert str(engine.accounts[99]) == '99, 66.66, 0, 66.66, False'
    
def test_transaction_deposit():
    engine.accounts[99] = engine.Account(client_id=99)
    engine.accounts[99].total = Decimal('11.22')
    engine.accounts[99].available = Decimal('11.22')
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('22.44')

def test_transaction_deposit_to_frozen_acct():
    engine.accounts[99] = engine.Account(client_id=99)
    engine.accounts[99].total = Decimal('11.22')
    engine.accounts[99].available = Decimal('11.22')
    engine.accounts[99].locked = True
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('11.22')    

def test_transaction_withdrawal():
    engine.accounts[99] = engine.Account(client_id=99)
    engine.accounts[99].total = Decimal('11.22')
    engine.accounts[99].available = Decimal('11.22')
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.WITHDRAWAL.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('0')
    
def test_transaction_withdrawal_overdraw():
    engine.accounts[99] = engine.Account(client_id=99)
    engine.accounts[99].total = Decimal('11.22')
    engine.accounts[99].available = Decimal('11.22')
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.WITHDRAWAL.value,
                                                 client_id=99, tx_id=44, amount=Decimal('100.00'))
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('11.22')   

def test_transaction_withdrawal_from_frozen_acct():
    engine.accounts[99] = engine.Account(client_id=99)
    engine.accounts[99].total = Decimal('11.22')
    engine.accounts[99].available = Decimal('11.22')
    engine.accounts[99].locked = True
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.WITHDRAWAL.value,
                                                 client_id=99, tx_id=44, amount=Decimal('100.00'))
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('11.22')    

def test_transaction_dispute_withdrawal():
    engine.accounts[99] = engine.Account(client_id=99)
    engine.accounts[99].total = Decimal('11.22')
    engine.accounts[99].available = Decimal('11.22')
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.WITHDRAWAL.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))
    transx = engine.Transaction(_type=engine.TransactionType.DISPUTE.value, 
                                client_id=99, tx_id=44)                                                 
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('0')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('0')
    
def test_transaction_dispute_deposit():
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))
    transx = engine.Transaction(_type=engine.TransactionType.DISPUTE.value, 
                                client_id=99, tx_id=44)                                                 
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('11.22')

def test_transaction_dispute_deposit_frozen_acct():
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))
    engine.accounts[99].locked = True                                                  
    transx = engine.Transaction(_type=engine.TransactionType.DISPUTE.value, 
                                client_id=99, tx_id=44)                                                 
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('11.22')
    assert engine.accounts[99].held == Decimal('0')    
    
def test_transaction_dispute_deposit_unknown_tx_id():
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))
    transx = engine.Transaction(_type=engine.TransactionType.DISPUTE.value, 
                                client_id=99, tx_id=5)                                                 
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('11.22')
    assert engine.accounts[99].held == Decimal('0')
    
def test_transaction_dispute_deposit_other_client():
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))
    engine.transactions[45] = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value,
                                                 client_id=100, tx_id=45, amount=Decimal('12.34'))                                                 
    transx = engine.Transaction(_type=engine.TransactionType.DISPUTE.value, 
                                client_id=99, tx_id=45)                                                 
    assert 44 in engine.transactions
    assert 45 in engine.transactions
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('11.22')
    assert engine.accounts[99].held == Decimal('0')   

def test_transaction_resolve_dispute():
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))
    transx = engine.Transaction(_type=engine.TransactionType.DISPUTE.value, 
                                client_id=99, tx_id=44)                                                 
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('11.22')
    transx = engine.Transaction(_type=engine.TransactionType.RESOLVE.value, 
                                client_id=99, tx_id=44)
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('11.22')
    assert engine.accounts[99].held == Decimal('0')
    
def test_transaction_resolve_dispute_frozen_acct():
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))                                                    
    transx = engine.Transaction(_type=engine.TransactionType.DISPUTE.value, 
                                client_id=99, tx_id=44)                                                 
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('11.22')
    engine.accounts[99].locked = True
    transx = engine.Transaction(_type=engine.TransactionType.RESOLVE.value, 
                                client_id=99, tx_id=44)
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('11.22')    

def test_transaction_resolve_dispute_unknown_tx_id():
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))
    transx = engine.Transaction(_type=engine.TransactionType.DISPUTE.value, 
                                client_id=99, tx_id=44)                                                 
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('11.22')
    transx = engine.Transaction(_type=engine.TransactionType.RESOLVE.value, 
                                client_id=99, tx_id=45)
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('11.22')    
    
def test_transaction_resolve_dispute_other_client():
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))
    transx = engine.Transaction(_type=engine.TransactionType.DISPUTE.value, 
                                client_id=99, tx_id=44)                                                 
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('11.22')
    transx = engine.Transaction(_type=engine.TransactionType.RESOLVE.value, 
                                client_id=100, tx_id=44)
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('11.22')

def test_transaction_resolve_dispute_already_resolved():
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))
    transx = engine.Transaction(_type=engine.TransactionType.DISPUTE.value, 
                                client_id=99, tx_id=44)                                                 
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('11.22')
    transx = engine.Transaction(_type=engine.TransactionType.RESOLVE.value, 
                                client_id=99, tx_id=44)
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('11.22')
    assert engine.accounts[99].held == Decimal('0')
    transx = engine.Transaction(_type=engine.TransactionType.RESOLVE.value, 
                                client_id=99, tx_id=44)
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('11.22')
    assert engine.accounts[99].held == Decimal('0')
    
def test_transaction_chargeback():
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))
    transx = engine.Transaction(_type=engine.TransactionType.DISPUTE.value, 
                                client_id=99, tx_id=44)                                                 
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('11.22')
    transx = engine.Transaction(_type=engine.TransactionType.CHARGEBACK.value, 
                                client_id=99, tx_id=44)
    assert engine.accounts[99].total == Decimal('0')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('0')

def test_transaction_chargeback_frozen_acct():
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))
    transx = engine.Transaction(_type=engine.TransactionType.DISPUTE.value, 
                                client_id=99, tx_id=44)                                                 
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('11.22')
    engine.accounts[99].locked = True
    transx = engine.Transaction(_type=engine.TransactionType.CHARGEBACK.value, 
                                client_id=99, tx_id=44)
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('11.22')    

def test_transaction_chargeback_unknown_tx_id():
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))
    transx = engine.Transaction(_type=engine.TransactionType.DISPUTE.value, 
                                client_id=99, tx_id=44)                                                 
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('11.22')
    transx = engine.Transaction(_type=engine.TransactionType.CHARGEBACK.value, 
                                client_id=99, tx_id=45)
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('11.22')  

def test_transaction_chargeback_other_client():
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))
    transx = engine.Transaction(_type=engine.TransactionType.DISPUTE.value, 
                                client_id=99, tx_id=44)                                                 
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('11.22')
    transx = engine.Transaction(_type=engine.TransactionType.CHARGEBACK.value, 
                                client_id=100, tx_id=44)
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('11.22')   

def test_transaction_resolve_dispute_already_chargedback():
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))
    transx = engine.Transaction(_type=engine.TransactionType.DISPUTE.value, 
                                client_id=99, tx_id=44)                                                 
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('11.22')
    transx = engine.Transaction(_type=engine.TransactionType.CHARGEBACK.value, 
                                client_id=99, tx_id=44)
    assert engine.accounts[99].total == Decimal('0')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('0')
    transx = engine.Transaction(_type=engine.TransactionType.RESOLVE.value, 
                                client_id=99, tx_id=44)
    assert engine.accounts[99].total == Decimal('0')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('0')

def test_transaction_chargeback_already_resolved():
    engine.transactions[44] = engine.Transaction(_type=engine.TransactionType.DEPOSIT.value,
                                                 client_id=99, tx_id=44, amount=Decimal('11.22'))
    transx = engine.Transaction(_type=engine.TransactionType.DISPUTE.value, 
                                client_id=99, tx_id=44)                                                 
    assert 44 in engine.transactions
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('0')
    assert engine.accounts[99].held == Decimal('11.22')
    transx = engine.Transaction(_type=engine.TransactionType.RESOLVE.value, 
                                client_id=99, tx_id=44)
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('11.22')
    assert engine.accounts[99].held == Decimal('0')
    transx = engine.Transaction(_type=engine.TransactionType.CHARGEBACK.value, 
                                client_id=99, tx_id=44)
    assert engine.accounts[99].total == Decimal('11.22')    
    assert engine.accounts[99].available == Decimal('11.22')
    assert engine.accounts[99].held == Decimal('0')    