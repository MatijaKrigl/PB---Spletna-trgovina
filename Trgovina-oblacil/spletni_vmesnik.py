import bottle
import sqlite3
import csv
from model import Oblacilo, Zaloge, Stranka, Kosarica, Narocilo, dodaj_nakup, dodaj_stranko, dodaj_kosarico, dodaj_narocilo
from datetime import datetime

# Ustvarimo povezavo z bazo
# Povežemo se z bazo oblacila.db ki vsebuje vse potrebne tabele za aplikacijo
conn = sqlite3.connect("oblacila.db")

# Ustvarimo objekt razreda Kosarica
# Ta objekt bomo uporabili za upravljanje s košarico uporabnika
kosarica_objekt = Kosarica(conn)

# Ustvarimo preprosto sejo za upravljanje prijav uporabnikov
session = {}

#za pridobivanje trenutnega uporabnika
def get_current_user():
    global session
    # Vrnemo uporabnika iz seje
    return session.get('user')

@bottle.route('/static/<filepath:path>')
def serve_static(filepath):
    return bottle.static_file(filepath, root='./static')

# Prikažemo prijavno stran
@bottle.get('/login')
def login_get():
    # Prikažemo obrazec za prijavo brez napake
    return bottle.template("login.html", session=session, napaka=None)

# Obdelava prijave
@bottle.post('/login')
def login_post():
    # Pridobimo email in geslo (ID) iz obrazca
    email = bottle.request.forms.get('email')
    password = bottle.request.forms.get('password')  # Geslo je v našem primeru ID
    
    # Povežemo se z bazo, da preverimo podatke uporabnika
    with sqlite3.connect("oblacila.db") as conn:
        cur = conn.cursor()
        # Poizvedba za iskanje uporabnika z določenim emailom in ID-jem
        cur.execute("SELECT * FROM stranka WHERE email = ? AND id = ?", (email, password))
        user = cur.fetchone()
        
        if user:
            # Če uporabnik obstaja, shranimo njegove podatke v sejo
            session['user'] = {
                'id': user[0],
                'first_name': user[1],
                'last_name': user[2],
                'email': user[4],
                'role': user[5]  # Domnevamo, da je vloga shranjena v stolpcu spol, spremenite po potrebi
            }
            # Preusmerimo na domačo stran
            bottle.redirect('/')
        else:
            # Če prijava ne uspe, prikažemo obrazec za prijavo z napako
            return bottle.template("login.html", session=session, napaka="Invalid login")

# Odjava uporabnika
@bottle.get('/logout')
def logout():
    # Iz seje odstranimo uporabnika
    session.pop('user', None)
    # Preusmerimo na domačo stran
    bottle.redirect('/')

# Prikažemo domačo stran
@bottle.get('/')
def pozdravi():
    # Pridobimo trenutnega uporabnika in košarico
    user = get_current_user()
    kosarica = session.get('kosarica', [])
    # Prikažemo osnovno predlogo s pozdravom in košarico
    return bottle.template("base.html", title="Trgovina z Oblačili", kosarica=kosarica, session=session, user=user, content=bottle.template("glavna_content.html", user=user))

# Prikažemo stran za iskanje oblačil po tipu in velikosti
@bottle.get('/iskanje_oblacila')
def iskanje_oblacila():
    user = get_current_user()
    session_data = session if session else {}  # Poskrbimo, da je `session` definiran
    return bottle.template("base.html", title="Poišči oblačilo po tipu in velikosti", session=session_data, user=user, content=bottle.template("iskanje_oblacila_content.html"))

@bottle.post('/iskanje_oblacila')
def rezultati_iskanja_oblacila():
    tip = bottle.request.forms.get('tip')
    velikost = bottle.request.forms.get('velikost')
    # Poiščemo oblačila glede na tip in velikost
    oblacila = Oblacilo.poisci_obleke_tipa(tip, velikost)
    user = get_current_user()
    # Ustvarimo naslov za prikaz v predlogi
    title = f"Rezultati za tip: {tip}"
    # Pokličemo predlogo `rezultati_iskanja_oblacila.html` in posredujemo ustrezne podatke
    return bottle.template("base.html", title=title, session=session, user=user, content=bottle.template("rezultati_iskanja_oblacila.html", title=title, oblacila=oblacila, tip=tip))

# Filtriramo oblačila po velikosti
@bottle.post('/filtriraj_po_velikosti')
def filtriraj_po_velikosti():
    # poiscemo tip in velikost iz obrazca
    tip = bottle.request.forms.get('tip')
    velikost = bottle.request.forms.get('velikost')
    # poiscemo oblačila glede na tip in velikost
    oblacila = Oblacilo.poisci_obleke_tipa(tip, velikost)
    user = get_current_user()
    # rezultati iskanja
    return bottle.template("base.html", title="Rezultati iskanja", session=session, user=user, content=bottle.template("rezultati_iskanja_oblacila.html", oblacila=oblacila, tip=tip))

# Prikažemo oblačila glede na spol
@bottle.get('/iskanje_po_spolu')
def iskanje_po_spolu():
    spol = bottle.request.query.get('spol')
    # Pravilno pokličemo metodo z vsemi potrebnimi argumenti
    with sqlite3.connect("oblacila.db") as conn:
        oblacila = Oblacilo.poisci_po_spolu(conn, spol)
    user = get_current_user()
    title = f"Rezultati iskanja za spol: {spol}"
    # Prikaz predloge z rezultati iskanja po spolu
    return bottle.template("base.html", title=title, session=session, user=user, content=bottle.template("rezultati_iskanja_po_spolu.html", title=title, oblacila=oblacila))

# Prikažemo najboljša oblačila v sezoni
@bottle.get('/najboljsa_oblacila')
def najboljsa_oblacila():
    user = get_current_user()
    # Prikažemo obrazec za izbiro sezone
    return bottle.template("base.html", title="Najboljša oblačila v sezoni", session=session, user=user, content=bottle.template("najboljsa_oblacila_content.html"))

# Prikažemo rezultate najboljših oblačil v sezoni
@bottle.post('/najboljsa_oblacila')
def rezultati_najboljsih_oblacil():
    # Pridobimo sezono iz obrazca
    sezona = bottle.request.forms.get('sezona')
    # Poiščemo najdražja oblačila v izbrani sezoni
    oblacila = Oblacilo.najdrazja_v_sezoni(sezona)
    # Formatiramo cene oblačil, da bodo prikazane z dvema decimalnima mestoma
    formatted_oblacila = []
    for oblacilo in oblacila:
        formatted_oblacilo = list(oblacilo)
        formatted_oblacilo[5] = f"{formatted_oblacilo[5]:.2f}"
        formatted_oblacila.append(formatted_oblacilo)
    user = get_current_user()
    # Prikažemo rezultate za izbrano sezono
    return bottle.template("base.html", title="Rezultati sezonska oblačila", session=session, user=user, content=bottle.template("rezultati_najboljsih_oblacil.html", oblacila=formatted_oblacila))

# Prikažemo posamezni izdelek
@bottle.get('/izdelek/<id>')
def prikazi_izdelek(id):
    # Poiščemo izdelek glede na ID
    izdelek = Oblacilo.poisci_izdelek(id)
    user = get_current_user()
    if izdelek:
        # Definiramo naslov strani na podlagi lastnosti izdelka
        title = f"{izdelek.tip} - {izdelek.znamka}"  # Privzamemo, da imata 'tip' in 'znamka' ustrezni atributi v razredu Oblacilo
        # Prikažemo podrobnosti izdelka
        return bottle.template("izdelek.html", izdelek=izdelek, session=session, user=user, title=title)
    else:
        # Če izdelek ne obstaja, vrnemo sporočilo
        return "Izdelek ne obstaja."

# Prikažemo vse izdelke v uporabnikovi košarici
@bottle.get('/kosarica')
def prikazi_kosarico():
    user = get_current_user()
    if user:
        # Pridobimo košarico iz seje
        kosarica = session.get('kosarica', [])
        # Če je košarica polna, pridobimo podrobnosti o vseh izdelkih v košarici
        if kosarica:
            with sqlite3.connect("oblacila.db") as conn:
                items = []
                for item in kosarica:
                    cur = conn.cursor()
                    # Poizvedba za pridobitev podrobnosti o izdelku iz tabele 'oblacilo' glede na ID izdelka
                    cur.execute("""
                        SELECT clothing_type, size, color, brand, price
                        FROM oblacilo
                        WHERE ID = ?
                    """, [item['product_id']])
                    product = cur.fetchone()
                    if product:
                        # Dodamo podrobnosti izdelka v seznam 'items'
                        items.append({
                            'tip': product[0],
                            'velikost': product[1],
                            'barva': product[2],
                            'znamka': product[3],
                            'cena': product[4],
                            'popust': item['discount'],
                            'id': item['product_id']
                        })
        # Posodobimo število izdelkov v košarici
        session['cart_count'] = len(kosarica)
        # Prikažemo stran s košarico in vsemi izdelki
        return bottle.template("base.html", title="Košarica", kosarica=items, session=session, user=user, content=bottle.template("kosarica.html", kosarica=items))
    
    else:
        # Če uporabnik ni prijavljen, vrnemo sporočilo
        return "Najprej se morate prijaviti."

# Dodamo izdelek v košarico
@bottle.post('/dodaj_v_kosarico')
def dodaj_v_kosarico():
    # Pridobimo ID izdelka in popust iz obrazca
    product_id = bottle.request.forms.get('product_id')
    discount = bottle.request.forms.get('discount')
    # Preverimo, ali je polje za popust prazno, če je, ga nastavimo na 0.0
    if not discount:
        discount = 0.0
    else:
        discount = float(discount)
    user = get_current_user()
    if user:
        # Pridobimo obstoječo košarico iz seje ali ustvarimo novo, če ta ne obstaja
        cart = session.get('kosarica', [])
        
        # Dodamo nov izdelek v košarico
        cart.append({
            'product_id': product_id,
            'discount': discount,
        })
        # Posodobimo sejo z novo košarico
        session['kosarica'] = cart
        # Posodobimo število izdelkov v košarici
        session['cart_count'] = len(cart)
        bottle.redirect('/kosarica')
    else:
        return "Najprej se morate prijaviti."

# Odstranimo izdelek iz košarice
@bottle.post('/odstrani_iz_kosarice')
def odstrani_iz_kosarice():
    # Pridobimo ID izdelka iz obrazca
    product_id = bottle.request.forms.get('product_id')
    user = get_current_user()
    if user:
        cart_id = user['id']
        # Odstranimo izdelek iz košarice v bazi
        kosarica_objekt.odstrani_izdelek_iz_kosarice(cart_id, product_id)
        session['cart_count'] = max(session.get('cart_count', 0) - 1, 0)
        bottle.redirect('/kosarica')
    else:
        return "Najprej se morate prijaviti."

# Potrdimo nakup
@bottle.post('/potrdi_nakup')
def potrdi_nakup():
    print("Funkcija potrdi_nakup je bila poklicana.")
    user = get_current_user()
    if user:
        print(f"Uporabnik {user['id']} potrjuje nakup.")
        cart_id = user['id']
        # Preverimo izdelke v košarici
        with sqlite3.connect("oblacila.db") as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT kosarica.cart_id, kosarica.product_id, kosarica.discount, oblacilo.clothing_type, oblacilo.size, oblacilo.color, oblacilo.brand, oblacilo.price
                FROM kosarica
                JOIN oblacilo ON kosarica.product_id = oblacilo.ID
                WHERE kosarica.cart_id = ?
            """, [cart_id])
            kosarica = cur.fetchall()
            print(f"Izdelki v košarici: {kosarica}")

        # Pridobimo zadnji cart_id iz kosarica.csv in določimo nov ID
        try:
            with open('podatki/kosarica.csv', 'r', newline='', encoding='UTF-8') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Preskočimo glavo datoteke
                zadnji_cart_id = max([int(row[0]) for row in reader], default=0)
                print(f"Zadnji cart_id: {zadnji_cart_id}")
        except FileNotFoundError:
            zadnji_cart_id = 0
            print("Datoteka kosarica.csv ne obstaja, nastavljamo zadnji cart_id na 0.")

        nov_cart_id = zadnji_cart_id + 1

        # Zapišemo podatke o nakupu v kosarica.csv
        with open('podatki/kosarica.csv', 'a', newline='', encoding='UTF-8') as csvfile:
            writer = csv.writer(csvfile)
            for item in kosarica:
                nova_vrstica = [nov_cart_id, item[1], item[2]]
                writer.writerow(nova_vrstica)
                print(f"Dodan zapis v kosarica.csv: {nova_vrstica}")
                nov_cart_id += 1  # Povečamo ID za naslednji izdelek

        # Po potrditvi nakupa izbrišemo košarico iz seje in baze
        print("Izbrišemo košarico po potrditvi nakupa.")
        kosarica_objekt.potrdi_nakup(cart_id)
        session['cart_count'] = 0
        return "Nakup potrjen."
    else:
        print("Uporabnik ni prijavljen.")
        return "Najprej se morate prijaviti."

# Prikažemo najbolj prodajana oblačila
@bottle.get('/najbolj_prodajana')
def najbolj_prodajana():
    user = get_current_user()
    with sqlite3.connect("oblacila.db") as conn:
        # Pridobimo najbolj prodajana oblačila iz baze
        oblacila = Oblacilo.najbolj_prodajana(conn)
    # Prikažemo stran z rezultati najbolj prodajanih oblačil
    return bottle.template("base.html", title="Najbolj prodajana oblačila", session=session, user=user, content=bottle.template("rezultati_najbolj_prodajanih_content.html", oblacila=oblacila))

# Prikažemo najnovejše izdelke v zalogi
@bottle.get('/novo_v_zalogi')
def novo_v_zalogi():
    user = get_current_user()  # Pridobimo trenutnega uporabnika
    with sqlite3.connect("oblacila.db") as conn:
        # Pridobimo najnovejše izdelke v zalogi
        zaloge = Zaloge.najnovejsi()
    # Prikažemo stran z najnovejšimi izdelki v zalogi
    return bottle.template("base.html", title="Novo v zalogi", session=session, user=user, content=bottle.template("novo_v_zalogi_content.html", title="Novo v zalogi", zaloge=zaloge))

# Registracijska stran
@bottle.get('/register')
def register_get():
    # Prikažemo obrazec za registracijo z morebitno napako
    return bottle.template("register.html", session=session, napaka=None)

# Obdelava registracije novega uporabnika
@bottle.post('/register')
def register_post():
    # Pridobimo podatke iz obrazca za registracijo
    first_name = bottle.request.forms.get('first_name')
    last_name = bottle.request.forms.get('last_name')
    age = int(bottle.request.forms.get('age'))
    email = bottle.request.forms.get('email')
    password = bottle.request.forms.get('password') 
    gender = bottle.request.forms.get('gender')
    region = bottle.request.forms.get('region')

    try:
        # Dodamo novo stranko v CSV datoteko ali bazo
        dodaj_stranko(password, first_name, last_name, age, email, gender, region)
        return bottle.template("uspesno_content.html", sporocilo="Registracija uspešna. Sedaj se lahko prijavite.", session=session, user=None)
    except Exception as e:
        # Če pride do napake prikažemo obrazec z napako
        return bottle.template("register.html", napaka="Prišlo je do napake: " + str(e), session=session, user=None)

# Zaženemo spletni strežnik
bottle.run(debug=True, reloader=True)

