# Other binary-format files.
from stuphlib.binary import Record, BuildRecordClass, ReadOneFromFile

# etc/bank
class NumberOfAccounts(Record, metaclass=BuildRecordClass):
    Fields = [('number', Record.SizeT)]

class BankAccountBalance(Record, metaclass=BuildRecordClass):
    Fields = [('balance', Record.SizeT)]

def ReadBankFile(fp):
    numAccounts = ReadOneFromFile(fp, NumberOfAccounts).number
    for x in range(numAccounts):
        yield ReadOneFromFile(fp, BankAccountBalance).balance

# etc/shopgold
class NumberOfShops(Record, metaclass=BuildRecordClass):
    Fields = [('number', Record.UInt)]

class ShopBankAccount(Record, metaclass=BuildRecordClass):
    Fields = [('gold', Record.UInt),
              ('bank', Record.UInt)]

def ReadShopGold(fp):
    # This is supposed to match the number of shops internally.
    numShops = ReadOneFromFile(fp, NumberOfShops).number

    # So it shall, sequentially (but with no validation).
    for x in range(numShops):
        yield ReadOneFromFile(fp, ShopBankAccount)

# Inspection Front End
if __name__ == '__main__':
    from sys import argv
    from os.path import basename
    if len(argv) == 2:
        filename = argv[1]
        base = basename(filename)

        if base == 'bank':
            nr = 0
            for balance in ReadBankFile(open(filename)):
                nr += 1
                print('#%-5d : $%10d' % (nr, balance))

        elif base == 'shopgold':
            nr = 0
            for shopBankAcct in ReadShopGold(open(filename)):
                nr += 1
                print('#%-5d : $%10d  [ $%10d ]' % (nr, shopBankAcct.gold,
                                                    shopBankAcct.bank))
