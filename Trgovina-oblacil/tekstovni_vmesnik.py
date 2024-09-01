import sqlite3
from model import Oblacilo, Zaloge, Stranka, Kosarica, Narocilo, dodaj_nakup, dodaj_stranko, dodaj_kosarico, dodaj_narocilo
from datetime import datetime

conn = sqlite3.connect("oblacila.db")
print("Pozdravljeni v trgovini z oblačili!")

def prikazi_meni():
    print("\n1 - Poišči oblačilo po tipu")
    print("2 - Najboljša oblačila v sezoni")
    print("3 - Najbolj prodajana oblačila")
    print("4 - Novo v zalogi")
    print("5 - Dodaj nakup")
    print("6 - Dodaj stranko")
    print("7 - Prikaži stranke po regiji")
    print("8 - Prikaži najstarejše stranke")
    print("9 - Dodaj košarico")
    print("10 - Prikaži vse košarice")
    print("11 - Prikaži košarice po izdelku")
    print("12 - Dodaj naročilo")
    print("13 - Prikaži vsa naročila")
    print("14 - Prikaži naročila po stranki")
    print("15 - Poišči oblačila po spolu")
    print("16 - Izhod")

def izpisi_oblacilo(oblacilo):
    print(f"Tip: {oblacilo.tip}, Velikost: {oblacilo.velikost}, Barva: {oblacilo.barva}, "
          f"Znamka: {oblacilo.znamka}, Material: {oblacilo.material}, Cena: {oblacilo.cena:.2f}, "
          f"Sezona: {oblacilo.sezona}, Spol: {oblacilo.spol}, ID: {oblacilo.id}\n")

# def izpisi_zalogo(zaloga):
#     print(f"ID Dobave: {zaloga.id_dobave}, ID Izdelka: {zaloga.id_izdelka}, Cena: {zaloga.cena:.2f}, "
#           f"Količina: {zaloga.kolicina}, Datum: {zaloga.datum}, "
#           f"Tip: {zaloga.tip}, Velikost: {zaloga.velikost}, Barva: {zaloga.barva}, "
#           f"Znamka: {zaloga.znamka}, Material: {zaloga.material}, Sezona: {zaloga.sezona}, "
#           f"Spol: {zaloga.gender}\n")
def izpisi_zalogo(zaloga):
    print(f"ID Dobave: {zaloga['id_dobave']}, ID Izdelka: {zaloga['id_izdelka']}, Cena: {zaloga['cena']:.2f}, "
          f"Količina: {zaloga['kolicina']}, Datum: {zaloga['datum']}, "
          f"Tip: {zaloga['tip']}, Velikost: {zaloga['velikost']}, Barva: {zaloga['barva']}, "
          f"Znamka: {zaloga['znamka']}, Material: {zaloga['material']}, Sezona: {zaloga['sezona']}, "
          f"Spol: {zaloga['gender']}\n")


def izpisi_stranko(stranka):
    print(f"ID: {stranka[0]}, Ime: {stranka[1]}, Priimek: {stranka[2]}, Starost: {stranka[3]}, "
          f"Email: {stranka[4]}, Spol: {stranka[5]}, Regija: {stranka[6]}\n")

def izpisi_kosarico(kosarica):
    print(f"ID Košarice: {kosarica[0]}, ID Izdelka: {kosarica[1]}, Popust: {kosarica[2]:.2f}\n")

def izpisi_narocilo(narocilo):
    print(f"ID Košarice: {narocilo[0]}, ID Stranke: {narocilo[1]}, Status: {narocilo[2]}, "
          f"Status 2: {narocilo[3]}\n")

while True:
    prikazi_meni()
    izbira = input("Izberite možnost (1-16): ")

    if izbira == "1":
        tip_obleke = input("Vnesite vrsto/tip oblačila: ")
        for oblacilo in Oblacilo.poisci_obleke_tipa(tip_obleke):
            izpisi_oblacilo(oblacilo)

    elif izbira == "2":
        sezona = input("Vnesite sezono: ")
        for oblacilo in Oblacilo.najdrazja_v_sezoni(sezona):
            izpisi_oblacilo(oblacilo)

    elif izbira == "3":
        for oblacilo in Oblacilo.najbolj_prodajana(conn):
            izpisi_oblacilo(oblacilo)

    elif izbira == "4":
        for zaloga in Zaloge.najnovejsi():
            izpisi_zalogo(zaloga)

    elif izbira == "7":
        region = input("Vnesite regijo: ")
        for stranka in Stranka.poisci_po_regiji(region):
            izpisi_stranko(stranka)

    elif izbira == "8":
        for stranka in Stranka.najstarejse_stranke():
            izpisi_stranko(stranka)

    elif izbira == "9":
        product_id = input("Vnesite ID izdelka: ")
        discount = float(input("Vnesite popust: "))
        dodaj_kosarico(product_id, discount)

    elif izbira == "10":
        for kosarica in Kosarica.vse_kosarice():
            izpisi_kosarico(kosarica)

    elif izbira == "11":
        product_id = input("Vnesite ID izdelka: ")
        for kosarica in Kosarica.kosarice_po_izdelku(product_id):
            izpisi_kosarico(kosarica)

    elif izbira == "12":
        id_kosarice = input("Vnesite ID košarice: ")
        stranka_id = input("Vnesite ID stranke: ")
        status = input("Vnesite status naročila (True/False): ")
        status_2 = input("Vnesite drugi status naročila (True/False): ")
        dodaj_narocilo(id_kosarice, stranka_id, status, status_2)

    elif izbira == "13":
        for narocilo in Narocilo.vsa_narocila():
            izpisi_narocilo(narocilo)

    elif izbira == "14":
        stranka_id = input("Vnesite ID stranke: ")
        for narocilo in Narocilo.narocila_stranke(stranka_id):
            izpisi_narocilo(narocilo)

    elif izbira == "15":
        spol = input("Vnesite spol (Men/Women/Children): ")
        for oblacilo in Oblacilo.poisci_po_spolu(conn, spol):
            izpisi_oblacilo(oblacilo)

    elif izbira == "16":
        print("Hvala za obisk. Nasvidenje!")
        break

    else:
        print("Neveljavna izbira. Poskusite znova.")
