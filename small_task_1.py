def decimal_to_roman(data):
    base = "I"*data
    
    base = base.replace("I"*5, "V") 
    base = base.replace("V"*2, "X")
    base = base.replace("X"*5, "L")
    base = base.replace("L"*2, "C")
    base = base.replace("C"*5, "D")
    base = base.replace("D"*2, "M")
    
    base = base.replace("DCCCC", "CM")
    base = base.replace("CCCC", "CD")
    base = base.replace("LXXXX", "XC")
    base = base.replace("XXXX", "XL")
    base = base.replace("VIIII", "IX")
    base = base.replace("IIII", "IV")
    
    return base

def roman_to_decimal(roman):
    
    roman = roman.replace("CM", "DCCCC")  # 900
    roman = roman.replace("CD", "CCCC")   # 400
    roman = roman.replace("XC", "LXXXX")  # 90
    roman = roman.replace("XL", "XXXX")   # 40
    roman = roman.replace("IX", "VIIII")  # 9
    roman = roman.replace("IV", "IIII")   # 4


    roman = roman.replace("M", "DD")      # 1000
    roman = roman.replace("D", "CCCCC")   # 500
    roman = roman.replace("C", "LL")      # 100
    roman = roman.replace("L", "XXXXX")   # 50
    roman = roman.replace("X", "VV")      # 10
    roman = roman.replace("V", "IIIII")   # 5

    # count ilosc I
    return roman.count("I")


def main():
    # decimal_to_roman
    
    #decimal_number = 2023
    decimal_number = int(input("Wpisz arabską liczbę: "))
    roman_number = decimal_to_roman(decimal_number)
    print(f"Arabska liczba {decimal_number} w rzymskiej systemie: {roman_number}")

    # roman_to_decimal
    #roman_number = "MMXXIII"
    roman_number = input("Wpisz rzymską liczbę: ")
    decimal_number = roman_to_decimal(roman_number)
    print(f"Rzymska liczba {roman_number} w arabskiej systemie: {decimal_number}")


if __name__ == "__main__":
    main()