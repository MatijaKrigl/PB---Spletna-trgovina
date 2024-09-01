import csv
import sqlite3
from sqlite3 import IntegrityError

PARAM_FMT = ":{}" # za SQLite
# PARAM_FMT = "%s({})" # za PostgreSQL/MySQL

class Tabela:
    """
    Razred, ki predstavlja tabelo v bazi.

    Polja razreda:
    - ime: ime tabele
    - podatki: ime datoteke s podatki ali None
    """
    ime = None
    podatki = None

    def __init__(self, conn):
        """
        Konstruktor razreda.
        """
        self.conn = conn

    def ustvari(self):
        """
        Metoda za ustvarjanje tabele.
        Podrazredi morajo povoziti to metodo.
        """
        raise NotImplementedError

    def izbrisi(self):
        """
        Metoda za brisanje tabele.
        """
        self.conn.execute(f"DROP TABLE IF EXISTS {self.ime};")

    def uvozi(self, encoding="UTF-8"):
        """
        Metoda za uvoz podatkov.

        Argumenti:
        - encoding: kodiranje znakov
        """
        if self.podatki is None:
            return
        with open(self.podatki, encoding=encoding) as datoteka:
            podatki = csv.reader(datoteka)
            stolpci = next(podatki)
            for vrstica in podatki:
                vrstica = {k: None if v == "" else v for k, v in zip(stolpci, vrstica)}
                self.dodaj_vrstico(**vrstica)

    def izprazni(self):
        """
        Metoda za praznjenje tabele.
        """
        self.conn.execute(f"DELETE FROM {self.ime};")

    def dodajanje(self, stolpci=None):
        """
        Metoda za gradnjo poizvedbe.

        Argumenti:
        - stolpci: seznam stolpcev
        """
        return f"""
            INSERT INTO {self.ime} ({", ".join(stolpci)})
            VALUES ({", ".join(PARAM_FMT.format(s) for s in stolpci)});
        """

    def dodaj_vrstico(self, **podatki):
        """
        Metoda za dodajanje vrstice.

        Argumenti:
        - poimenovani parametri: vrednosti v ustreznih stolpcih
        """
        podatki = {kljuc: vrednost for kljuc, vrednost in podatki.items()
                   if vrednost is not None}
        poizvedba = self.dodajanje(podatki.keys())
        cur = self.conn.execute(poizvedba, podatki)
        return cur.lastrowid
    
    def posodobi_csv(self, podatki):
        if self.podatki is not None:
            with open(self.podatki, 'a', newline='', encoding='UTF-8') as datoteka:
                writer = csv.DictWriter(datoteka, fieldnames=podatki.keys())
                writer.writerow(podatki)

class Stranka(Tabela):
    """
    Tabela za stranke.
    """
    ime = "stranka"
    podatki = "podatki/stranka.csv"

    def ustvari(self):
        """
        Ustvari tabelo stranka.
        """
        self.conn.execute("""
            CREATE TABLE stranka (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name   TEXT NOT NULL,
                last_name   TEXT NOT NULL,
                age         INTEGER NOT NULL,
                email       TEXT NOT NULL,
                gender      TEXT NOT NULL,
                region  TEXT NOT NULL
            );
        """)

class Oblacila(Tabela):
    """
    Tabela za oblacila.
    """
    ime = "oblacilo"
    podatki = "podatki/oblacila.csv"

    def ustvari(self):
        """
        Ustvari tabelo oblačilo.
        """
        self.conn.execute("""
            CREATE TABLE oblacilo (
                clothing_type     TEXT NOT NULL,
                size              TEXT NOT NULL,
                color             TEXT NOT NULL,
                brand             TEXT NOT NULL,
                material          TEXT NOT NULL,
                price             INTEGER NOT NULL,
                season            TEXT NOT NULL,
                ID        TEXT PRIMARY KEY,
                gender            TEXT NOT NULL
            );
        """)

class Zaloga(Tabela):
    """
    Tabela za dobavo in zalogo.
    """
    ime = "zaloga"
    podatki = "podatki/zaloga.csv"

    def ustvari(self):
        """
        Ustvari tabelo zaloga oz. dobava.
        """
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS zaloga (
                id_dobave TEXT PRIMARY KEY,
                id_izdelka TEXT REFERENCES oblacilo(ID),
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                date_of_launch DATE
            );
        """)

class Kosarica(Tabela):
    ime = "kosarica"
    podatki = "podatki/kosarica.csv"

    def ustvari(self):
        self.conn.execute("""
            CREATE TABLE kosarica (
                cart_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id     TEXT REFERENCES oblacilo(ID),
                discount       REAL
            );
        """)

    def dodaj_izdelek_v_kosarico(self, cart_id, product_id, discount):
        try:
            cur = self.conn.cursor()
            cur.execute(
                """
                INSERT INTO kosarica (cart_id, product_id, discount)
                VALUES (?, ?, ?)
            """, [cart_id, product_id, discount])
            self.conn.commit()
        except sqlite3.Error as e:
            print("Napaka pri dodajanju izdelka v košarico:", e)

    def odstrani_izdelek_iz_kosarice(self, cart_id, product_id):
        try:
            cur = self.conn.cursor()
            cur.execute(
                """
                DELETE FROM kosarica WHERE cart_id = ? AND product_id = ?
            """, [cart_id, product_id])
            self.conn.commit()
        except sqlite3.Error as e:
            print("Napaka pri odstranjevanju izdelka iz košarice:", e)

    def potrdi_nakup(self, cart_id):
        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM kosarica WHERE cart_id = ?", [cart_id])
            self.conn.commit()
        except sqlite3.Error as e:
            print("Napaka pri potrjevanju nakupa:", e)



class Narocilo(Tabela):
    """
    Tabela za eno naročilo. Združuje Id uporabnika z Id-jem košarice. Status in status2 opisujeta
    kakšno je stanje nakupa (ali se je naročilo šlo skozi). V primeru da sta oba "True", potem
    je stranka uspešno zaključila nakup. 
    """
    ime = "narocilo"
    podatki = "podatki/narocilo.csv"

    def ustvari(self):
        """
        Ustvari tabelo narocilo.
        """
        self.conn.execute("""
            CREATE TABLE narocilo (
                id_kosarice      TEXT REFERENCES kosarica(id_kosarice),
                ID               TEXT REFERENCES stranka(id),
                status           BOOLEAN,
                status_2         BOOLEAN
            )
        """)

def ustvari_tabele(tabele):
    """
    Ustvari podane tabele.
    """
    for t in tabele:
        t.ustvari()

def izbrisi_tabele(tabele):
    """
    Izbriši podane tabele.
    """
    for t in tabele:
        t.izbrisi()

def uvozi_podatke(tabele):
    """
    Uvozi podatke v podane tabele.
    """
    for t in tabele:
        print("uvozi v tabelo", t.ime)
        t.uvozi()

def izprazni_tabele(tabele):
    """
    Izprazni podane tabele.
    """
    for t in tabele:
        t.izprazni()


def ustvari_bazo(conn):
    """
    Izvede ustvarjanje baze.
    """
    tabele = pripravi_tabele(conn)
    izbrisi_tabele(tabele)
    ustvari_tabele(tabele)
    uvozi_podatke(tabele)


def pripravi_tabele(conn):
    """
    Pripravi objekte za tabele.
    """
    stranka = Stranka(conn)
    oblacilo = Oblacila(conn)
    zaloga = Zaloga(conn)
    kosarica = Kosarica(conn)
    narocilo = Narocilo(conn)
    return [stranka, oblacilo, zaloga, kosarica, narocilo]


def ustvari_bazo_ce_ne_obstaja(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS oblacilo (
        ID INTEGER PRIMARY KEY,
        clothing_type TEXT,
        size TEXT,
        color TEXT,
        brand TEXT,
        material TEXT,
        price REAL,
        season TEXT,
        gender TEXT
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS zaloga (
        id_dobave INTEGER PRIMARY KEY,
        id_izdelka INTEGER,
        price REAL,
        quantity INTEGER,
        date_of_launch TEXT,
        FOREIGN KEY (id_izdelka) REFERENCES oblacilo(ID)
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stranka (
        id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        age INTEGER,
        email TEXT,
        gender TEXT,
        region TEXT,
        role TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS kosarica (
        cart_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        FOREIGN KEY (cart_id) REFERENCES stranka(id),
        FOREIGN KEY (product_id) REFERENCES oblacilo(ID)
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS narocilo (
        id INTEGER PRIMARY KEY,
        id_kosarice INTEGER,
        ID INTEGER,
        status BOOLEAN,
        status_2 BOOLEAN,
        FOREIGN KEY (id_kosarice) REFERENCES kosarica(cart_id),
        FOREIGN KEY (ID) REFERENCES stranka(id)
    )
    """)
    
    conn.commit()


#BAZA = 'oblacila.db'
#conn = sqlite3.connect(BAZA)
#ustvari_bazo_ce_ne_obstaja(conn)
#conn.execute("SELECT * FROM stranka")
#conn.execute("SELECT * FROM oblacilo")
#conn.execute("SELECT * FROM zaloga")
#conn.execute("SELECT * FROM kosarica")
#conn.execute("SELECT * FROM narocilo")


# conn.close()
# conn.execute('PRAGMA foreign_keys = ON') #delovanje tujih kljucev