def suma (x,y):
    sum= x+y
    return sum
def difference (x,y):
    dif=x-y
    return dif
def multiplication (x,y):
    mul=x*y
    return mul
def devision (x,y):
    dev=x/y
    return dev
def devision_int (x,y):
    dev_int=x//y
    return dev_int
def remainder_devision (x,y):
    dev_rem=x%y
    return dev_rem
print("Suma to jest: ",suma (2,4))
print("Róźnica to jest: ",difference (2,4))
print("Mnożenie to jest: ",multiplication (2,4))
print("Dzielenie to jest: ",devision (2,4))
print("Dzielenie całeliczbowe to jest",devision_int (2,4))
print("Pozostalość od dzieleniadzielenie to jest",remainder_devision (4,3))