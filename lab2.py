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
print("suma jest: ",suma (2,4))
print("róźnica jest: ",difference (2,4))
print("mnożenie jest: ",multiplication (2,4))
print("dzielenie jest: ",devision (2,4))
print("dzielenie całeliczbowe",devision_int (2,4))
print("pozostalość od dzieleniadzielenie",remainder_devision (4,3))