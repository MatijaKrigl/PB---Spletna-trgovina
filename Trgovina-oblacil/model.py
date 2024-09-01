import sqlite3
import csv

conn = sqlite3.connect("oblacila.db")

# Definiramo osnovni razred za delo s tabelami v bazi
class Tabela:
    ime = None
    podatki = None

    # Konstruktor sprejme povezavo do baze
    def __init__(self, conn):
        self.conn = conn
    # Metoda za ustvarjanje tabelE
    def ustvari(self):
        raise NotImplementedError

    # Metoda za brisanje tabele
    def izbrisi(self):
        self.conn.execute(f"DROP TABLE IF EXISTS {self.ime};")

    # Metoda za uvoz podatkov iz CSV datoteke
    def uvozi(self, encoding="UTF-8"):
        if self.podatki is None:
            return
        with open(self.podatki, encoding=encoding) as datoteka:
            podatki = csv.reader(datoteka)
            stolpci = next(podatki)
            for vrstica in podatki:
                vrstica = {k: None if v == "" else v for k, v in zip(stolpci, vrstica)}
                self.dodaj_vrstico(**vrstica)

    # Metoda za brisanje vseh podatkov iz tabele
    def izprazni(self):
        self.conn.execute(f"DELETE FROM {self.ime};")

    # Metoda za pripravo SQL poizvedbe za vstavljanje podatkov v tabelo
    def dodajanje(self, stolpci=None):
        return f"""
            INSERT INTO {self.ime} ({", ".join(stolpci)})
            VALUES ({", ".join(f":{s}" for s in stolpci)});
        """

    # Metoda za dodajanje vrstice v tabelo
    def dodaj_vrstico(self, **podatki):
        podatki = {kljuc: vrednost for kljuc, vrednost in podatki.items()
                   if vrednost is not None}
        poizvedba = self.dodajanje(podatki.keys())
        cur = self.conn.execute(poizvedba, podatki)
        return cur.lastrowid

    # Metoda za posodabljanje CSV datoteke z novimi podatki
    def posodobi_csv(self, podatki):
        if self.podatki is not None:
            with open(self.podatki, 'a', newline='', encoding='UTF-8') as datoteka:
                writer = csv.DictWriter(datoteka, fieldnames=podatki.keys())
                writer.writerow(podatki)

# Razred za delo s tabelo oblacilo
class Oblacilo(Tabela):
    ime = "oblacilo"
    podatki = "podatki/oblacila.csv"
    
    # Konstruktor razreda za instanco oblačila
    def __init__(self, tip, velikost, barva, znamka, material, cena, sezona, id, spol):
        self.tip = tip
        self.velikost = velikost
        self.barva = barva
        self.znamka = znamka
        self.material = material
        self.cena = cena
        self.sezona = sezona
        self.id = id
        self.spol = spol

    # Metoda za ustvarjanje tabele 'oblacilo'
    def ustvari(self):
        self.conn.execute("""
            CREATE TABLE oblacilo (
                clothing_type TEXT NOT NULL,
                size TEXT NOT NULL,
                color TEXT NOT NULL,
                brand TEXT NOT NULL,
                material TEXT NOT NULL,
                price INTEGER NOT NULL,
                season TEXT NOT NULL,
                ID TEXT PRIMARY KEY,
                gender TEXT NOT NULL
            );
        """)

    # Statična metoda za iskanje oblačila po id-ju
    @staticmethod
    def poisci_izdelek(id_izdelka):
        cur = conn.cursor()
        cur.execute("SELECT * FROM oblacilo WHERE ID = ?", [id_izdelka])
        rezultat = cur.fetchone()
        if rezultat:
            return Oblacilo(*rezultat)
        else:
            return None

    # Statična metoda za iskanje oblačil po tipu in po želji tudi po velikosti
    @staticmethod
    def poisci_obleke_tipa(tip, velikost=None):
        cur = conn.cursor()
        if velikost:
            cur.execute('SELECT * FROM oblacilo WHERE lower(clothing_type) = ? AND size = ?', (tip.lower(), velikost))
        else:
            cur.execute('SELECT * FROM oblacilo WHERE lower(clothing_type) = ?', (tip.lower(),))
        
        results = cur.fetchall()
        return [Oblacilo(*result) for result in results]

    # Statična metoda za iskanje najdražjih oblačil v določeni sezoni
    @staticmethod
    def najdrazja_v_sezoni(sezona):
        cur = conn.cursor()
        sql = """
            SELECT *
            FROM oblacilo
            WHERE season = ? AND price > 100
            ORDER BY price DESC
            LIMIT 10
        """
        cur.execute(sql, [sezona])
        rezultati = cur.fetchall()
        return rezultati

    # Statična metoda za iskanje najbolj prodajanih oblačil
    @staticmethod
    def najbolj_prodajana(conn):
        sql = """
            SELECT o.clothing_type, o.size, o.color, o.brand, o.material, o.price, o.season, o.ID, COUNT(n.id_kosarice) as prodano
            FROM oblacilo o
            JOIN kosarica k ON o.ID = k.product_id
            JOIN narocilo n ON k.cart_id = n.id_kosarice
            GROUP BY o.ID
            ORDER BY prodano DESC
            LIMIT 10;
        """
        cur = conn.execute(sql)
        return cur.fetchall()
    
    # Statična metoda za iskanje oblačil po spolu
    @staticmethod
    def poisci_po_spolu(conn, spol):
        cur = conn.cursor()
        sql = "SELECT * FROM oblacilo WHERE gender = ?"
        cur.execute(sql, [spol])
        results = cur.fetchall()
        return [Oblacilo(*vrstica) for vrstica in results]

# Razred za delo s tabelo 'zaloga'
class Zaloge(Tabela):
    ime = "zaloga"
    podatki = "podatki/zaloga.csv"

    # Metoda za ustvarjanje tabele 'zaloga'
    def ustvari(self):
        self.conn.execute("""
            CREATE TABLE zaloga (
                id_dobave TEXT PRIMARY KEY,
                id_izdelka TEXT REFERENCES oblacilo(ID),
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                date_of_launch DATE
            );
        """)

    # Statična metoda za pridobitev najnovejših zalog
    @staticmethod
    def najnovejsi():
        cur = conn.cursor()
        sql = """
            SELECT zaloga.id_dobave, zaloga.id_izdelka, zaloga.price, zaloga.quantity, zaloga.date_of_launch,
                   oblacilo.clothing_type, oblacilo.size, oblacilo.color, oblacilo.brand, oblacilo.material, oblacilo.season, oblacilo.gender
            FROM zaloga
            JOIN oblacilo ON zaloga.id_izdelka = oblacilo.ID
            ORDER BY CAST(zaloga.date_of_launch AS DATE) DESC
            LIMIT 10
        """
        cur.execute(sql)
        rezultati = cur.fetchall()

        keys = ["id_dobave", "id_izdelka", "cena", "kolicina", "datum", "tip", "velikost", "barva", "znamka", "material", "sezona", "gender"]
        return [dict(zip(keys, row)) for row in rezultati]

    # Statična metoda za pridobitev zalog glede na ID izdelka
    @staticmethod
    def zaloge_po_izdelku(id_izdelka):
        cur = conn.cursor()
        sql = """
            SELECT *
            FROM zaloga
            WHERE id_izdelka = ?
        """
        cur.execute(sql, [id_izdelka])
        rezultati = cur.fetchall()
        return rezultati

# za dodajanje novega nakupa v tabelo zaloga
def dodaj_nakup(id_izdelka, cena, kolicina, datum):
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO zaloga (id_izdelka, price, quantity, date_of_launch)
            VALUES (?, ?, ?, ?)
        """, [id_izdelka, cena, kolicina, datum])
        conn.commit()
        Zaloge(conn).posodobi_csv({
            'id_izdelka': id_izdelka,
            'price': cena,
            'quantity': kolicina,
            'date_of_launch': datum
        })
        print("Nakup dodan.")
    except sqlite3.Error as e:
        print("Napaka pri dodajanju nakupa:", e)

# za dodajanje izdelka v košarico
def dodaj_kosarico(product_id, discount):
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO kosarica (product_id, discount)
            VALUES (?, ?)
        """, [product_id, discount])
        conn.commit()
        baza.Kosarica(conn).posodobi_csv({
            'product_id': product_id,
            'discount': discount
        })
        print("Košarica dodana.")
    except sqlite3.Error as e:
        print("Napaka pri dodajanju košarice:", e)

# Razred za delo s tabelo 'stranka'
class Stranka(Tabela):
    ime = "stranka"
    podatki = "podatki/stranka.csv"

    # Metoda za ustvarjanje tabele 'stranka'
    def ustvari(self):
        self.conn.execute("""
            CREATE TABLE stranka (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                age INTEGER NOT NULL,
                email TEXT NOT NULL,
                gender TEXT NOT NULL,
                region TEXT NOT NULL
            );
        """)

    # Statična metoda za iskanje strank po regiji
    @staticmethod
    def poisci_po_regiji(region):
        cur = conn.cursor()
        cur.execute("SELECT * FROM stranka WHERE region = ?", [region])
        rezultati = cur.fetchall()
        return rezultati

    # Statična metoda za pridobitev najstarejših strank
    @staticmethod
    def najstarejse_stranke():
        cur = conn.cursor()
        cur.execute("SELECT * FROM stranka ORDER BY age DESC LIMIT 10")
        rezultati = cur.fetchall()
        return rezultati

# Funkcija za dodajanje nove stranke v tabelo in CSV datoteko
def dodaj_stranko(password, first_name, last_name, age, email, gender, region):
    try:
        cur = conn.cursor()
        # Vstavimo podatke v tabelo stranka, vključno z geslom (ID uporabnika)
        cur.execute(
            """
            INSERT INTO stranka (id, first_name, last_name, age, email, gender, region)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [password, first_name, last_name, age, email, gender, region])
        conn.commit()
        
        # Posodobimo CSV datoteko s temi podatki
        Stranka(conn).posodobi_csv({
            'id': password,
            'first_name': first_name,
            'last_name': last_name,
            'age': age,
            'email': email,
            'gender': gender,
            'region': region
        })
        print("Stranka dodana.")
    except sqlite3.Error as e:
        print("Napaka pri dodajanju stranke:", e)

# Razred za delo s tabelo 'kosarica'
class Kosarica(Tabela):
    ime = "kosarica"
    podatki = "podatki/kosarica.csv"

    # Metoda za ustvarjanje tabele 'kosarica'
    def ustvari(self):
        self.conn.execute("""
            CREATE TABLE kosarica (
                cart_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id     TEXT REFERENCES oblacilo(ID),
                discount       REAL
            );
        """)

    # Metoda za dodajanje izdelka v košarico
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

    # Metoda za odstranjevanje izdelka iz košarice
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

    # Metoda za potrditev nakupa in praznjenje košarice
    def potrdi_nakup(self, cart_id):
        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM kosarica WHERE cart_id = ?", [cart_id])
            self.conn.commit()
        except sqlite3.Error as e:
            print("Napaka pri potrjevanju nakupa:", e)

# Razred za delo s tabelo 'narocilo'
class Narocilo(Tabela):
    ime = "narocilo"
    podatki = "podatki/narocilo.csv"

    # Metoda za ustvarjanje tabele 'narocilo'
    def ustvari(self):
        self.conn.execute("""
            CREATE TABLE narocilo (
                id_kosarice TEXT REFERENCES kosarica(cart_id),
                ID TEXT REFERENCES stranka(id),
                status BOOLEAN,
                status_2 BOOLEAN
            )
        """)

# Funkcija za dodajanje novega naročila
def dodaj_narocilo(id_kosarice, stranka_id, status, status_2):
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO narocilo (id_kosarice, ID, status, status_2)
            VALUES (?, ?, ?, ?)
        """, [id_kosarice, stranka_id, status, status_2])
        conn.commit()
        Narocilo(conn).posodobi_csv({
            'id_kosarice': id_kosarice,
            'ID': stranka_id,
            'status': status,
            'status_2': status_2
        })
        print("Naročilo dodano.")
    except sqlite3.Error as e:
        print("Napaka pri dodajanju naročila:", e)

# Funkcija za ustvarjanje baze, če ta še ne obstaja
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
        discount REAL,
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

# Ustvarjanje baze, če ta ne obstaja
ustvari_bazo_ce_ne_obstaja(conn)

