from bs4 import BeautifulSoup
import urllib2
import re
import webbrowser
from Tkinter import *
import tkMessageBox
import ttk


class Poveznica:
    def __init__(self, naslov, url, ocjena):
        self.naslov = naslov
        self.url = url
        self.ocjena = ocjena
#global lista_poveznica
global lista_url_za_pretragu
zastavica = False


stranice_za_pretragu = ["http://stackoverflow.com/search?tab=relevance&pagesize=50&q="]
rezervna_stranica = "http://stackoverflow.com/questions/tagged/trazena_rijec?page=1&sort=newest&pagesize=50"
mapa_znakova={'#':'%23','$':'%24','%':'%25','&':'%26','/':'%2F','=':'%3D','?':'%3F','+':'%2B',',':'%2C',';':'%3B',':':'%3A'}

#lista_poveznica = []
lista_url_za_pretragu = []

#povezivanje na postgresql bazu podataka
def povezivanje_na_bazu():
    global conn
    global cursor
    conn_string = "host='localhost' dbname='Crawler' user='postgres' password='supersonic'"
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    print "Connected!\n"

#funkcija koja sprema URL i naslov u bazu
def spremanje_u_bazu(broj,naziv,poveznica,ocjena):
    cursor.execute("INSERT INTO Pohranjene poveznice(ID, Naslov, poveznica, ocjena) VALUES (%s, %s, %s, %s)",(broj, naziv, poveznica, ocjena))
    conn.commit()
    cursor.close()
    conn.close()

#unos riječi koje korisnik hoće pretražiti se razdvajaju i predaju funkciji dodavanje_rijeci_u_pretragu
def razdvajanje_rijeci(rijeci_za_pretragu, unisti_prozor):
    global razdvojene_rijeci
    razdvojene_rijeci = re.findall('(\w+)', rijeci_za_pretragu)
    unisti_prozor.destroy()
    for i, j in mapa_znakova.iteritems():
        for n in range(0, len(razdvojene_rijeci)):
            if i in razdvojene_rijeci[n]:
                zamjena = lista_rijeci[n].replace(i, j)
                razdvojene_rijeci[n] = zamjena
    dodavanje_rijeci_u_pretragu(razdvojene_rijeci)

#razdvojene rijeci se dodaju u URL za pretrazivanje na www.stackoverflow.com.
#postoje dva nacina pretrage, jedna rijec se pretrazuje na drugaciji nacin nego vise pa zato postoji for petlja i zastavice
def dodavanje_rijeci_u_pretragu(razdvojene_rijeci):
    za_pretragu = stranice_za_pretragu[0]
    for i in range(0,len(razdvojene_rijeci)):
        if i == 0:
            print razdvojene_rijeci[i]
            za_pretragu += razdvojene_rijeci[i].lower()
        else:
            print razdvojene_rijeci[i]
            za_pretragu += "+" + razdvojene_rijeci[i].lower()
    pretrazivanje_po_unosu(za_pretragu)

def rezervna_pretraga(razdvojeno):
    zamjena = rezervna_stranica.replace("trazena_rijec", str(razdvojeno).strip('[\'\']'))
    pretrazivanje_po_unosu(zamjena)

#pretrazivanje sa urllib2 modulom, header sam morao dodati kako me stranica nebi blokirala svaki put
#zastavica u kodu se postavlja na 1 ako se u inicijalnom pretrazivanju nije pronasla niti jedna poveznica,
#te se tada pokrece drugaciji nacin pretrage(tagged)
def pretrazivanje_po_unosu(pretrazi):
    print pretrazi
    headers = {}
    headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
    pretraga = urllib2.Request(pretrazi, headers=headers)
    pretraga.add_header('Accept-Encoding', 'utf-8')
    website = urllib2.urlopen(pretraga)
    website.info()
    ucitani_html = BeautifulSoup(website)
    if zastavica:
        tagged_pretraga_poveznica(ucitani_html)
    else:
        podjeli_prema_a(ucitani_html)

#parsiranje html koda sa regularnim izrazima nakon cega dobijem naslove i url koji se ponude korisniku
#ova pretraga se aktivira u slucaju da je zastavica 1(tagged pretraga, jedna rijec)
def tagged_pretraga_poveznica(ucitano):
    global lista_poveznica
    lista_poveznica = []
    nadi_h3 = ucitano.find_all('h3')
    nadi_a = re.findall('<a(.*?)</a>', str(nadi_h3))
    uzmi_fqdn = re.findall ('(http.*com)', stranice_za_pretragu[0])
    ocjena = 5
    for n in nadi_a:
        path = re.findall('href="(.*)"', str(n))
        naslov = re.findall('href=".*?>(.*)',str(n))
        cijela_poveznica = str(uzmi_fqdn[0]) + str(path[0])
        novi_url = Poveznica(naslov, cijela_poveznica, ocjena)
        lista_poveznica.append(novi_url)
    zastavica = False
    prijenos_poveznica(lista_poveznica)

#parsiranje html koda sa beautifulsoup4 modulom
def podjeli_prema_a(ucitani_html):
    podjeli_a = ucitani_html.find_all('a')
    nadi_naslove_i_url(podjeli_a)

#parsiranje html koda sa reg exp nakon cega dobijem naslove i url koji se nude korisniku
#uva pretraga se aktivira u slucaju da je zastavica 0(pretraga vise rijeci)
def nadi_naslove_i_url(podjeli_a):
    global lista_poveznica
    global zastavica
    print podjeli_a
    lista_poveznica = []
    uzmi_fqdn = re.findall ('(http.*com)', stranice_za_pretragu[0])
    ocjena = 5
    for i in podjeli_a:
        b = re.findall('(.searchsession.)', str(i), re.IGNORECASE)
        if b:
            c = re.findall('title="(.*)"', str(i))
            d = re.findall('href="(.*)" ', str(i))
            cijela_poveznica = str(uzmi_fqdn[0]) + str(d[0])
            novi_url = Poveznica(c, cijela_poveznica, ocjena)
            lista_poveznica.append(novi_url)
    for i in lista_poveznica:
        print i
    if len(lista_poveznica) < 1:
        print "podignuta je zastavica"
        zastavica = True
        print "Sada je zastavica:,", zastavica

        rezervna_pretraga(razdvojene_rijeci)
    else:
        prijenos_poveznica(lista_poveznica)

#funkcija koja spremljene poveznice u listi poveznica sa ttk modulom prikazuje korisniku kao treeview
def prijenos_poveznica(lista_poveznica):
    global prozor
    global izlistaj
    if "prozor" in globals():
        prozor.destroy()
    prozor = Frame()
    prozor.configure(background = "gray93")
    prozor.pack(fill = "both", expand = True)
    imena_stupaca = ("id", "poveznica")
    izlistaj = ttk.Treeview(height = "30",columns = imena_stupaca,\
                            show = "headings", selectmode="extended")
    ysb = ttk.Scrollbar(orient='vertical', command=izlistaj.yview)
    xsb = ttk.Scrollbar(orient='horizontal', command=izlistaj.xview)
    izlistaj['yscroll'] = ysb.set
    izlistaj['xscroll'] = xsb.set
    izlistaj.column("id", width = 30, stretch = NO)
    izlistaj.heading("id", text = "ID")
    izlistaj.column("poveznica", width = 600)
    izlistaj.heading("poveznica", text = "Poveznice")
    ysb.grid(in_=prozor, row=0, column=1, sticky=NS)
    xsb.grid(in_=prozor, row=1, column=0, sticky=EW)
    prozor.rowconfigure(0, weight = 1)
    prozor.columnconfigure(0, weight = 1)
    izlistaj.grid(column = 0, row = 0, in_=prozor)
    
    for i in range(0, len(lista_poveznica)):
        var_poveznica = lista_poveznica[i]
        izlistaj.insert("", i, iid = i,\
                        values = (i+1, str(lista_poveznica[i].naslov).strip('[\'\']')))
    izlistaj.bind("<Double-1>", objekt_klik)
    
#u slucaju dvostrukog klika na naslov ova funkcija poziva funkciju html_sample
def objekt_klik(event):
    obj = izlistaj.selection()[0]
    #webbrowser.open_new(lista_poveznica[(int(obj)+ 1)].url)
    html_sample(lista_poveznica[(int(obj)+ 1)].url)

#otvaranje kliknute poveznice u novom Python prozoru kao tekst
def html_sample(odabrani_url):
    print odabrani_url
    lista_tekst_stranica = []
    headers = {}
    headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
    pretraga = urllib2.Request(odabrani_url, headers=headers)
    pretraga.add_header('Accept-Encoding', 'utf-8')
    print headers
    website = urllib2.urlopen(pretraga)
    ucitani_html = BeautifulSoup(website)
    nadi_post = ucitani_html.find_all({'p','code'})
    for i in nadi_post:
        c = re.findall('.span.', str(i))
        if c:
            break
        else:
            spajanje = str(i) + "\n"
            lista_tekst_stranica.append(str(spajanje))
    var = ''.join(lista_tekst_stranica)
    tekst_sa_stranice(var)

#tkinter prozor u kojem se otvara parsirani tekst sa stranice koju je korisnik kliknuo
def tekst_sa_stranice(procisceni_tekst):
    global glavni_okvir
    glavni_okvir = Tk()
    scrollbar = Scrollbar(glavni_okvir)
    scrollbar.pack(side = RIGHT, fill = Y)
    unos_teksta = Text(master = glavni_okvir, yscrollcommand = scrollbar.set)
    unos_teksta.pack(side=RIGHT)
    okvir = Frame()
    okvir.pack(side = LEFT)
    unos_teksta.insert(END,  procisceni_tekst)
    unos_teksta.see(END)
    scrollbar.config(command = unos_teksta.yview)
    gumb = Button(glavni_okvir, text = "Zatvori", command = lambda: glavni_okvir.destroy()).pack()
    gumb2 = Button(glavni_okvir, text = "Spremi za kasnije", command = lambda:spremi_za_kasnije()).pack()
    #glavni_okvir.protocol("WM_DELETE_WINDOW", spremi_za_kasnije)
    glavni_okvir.mainloop()

#prozor koji se otvara kod spremanja procitanog teksta sa poveznice, nudi odabir ocjene za procitani tekst
def spremi_za_kasnije():
    global spremanje
    spremanje = Tk()
    naslov = Label(spremanje, text = "Ocijenite koliko je pomogla spremljena poveznica")
    naslov.pack(side = TOP)
    for i in range(0, 10):
        but = Button(spremanje, text = str(i+1), command = lambda:unos_ocjene(i+1))
        but.pack(side = LEFT,fill= BOTH)
    spremanje.mainloop()

#ovaj dio ce zapisivati ocjenu koju je korisnik kliknuo u bazu
def unos_ocjene(ocjena):
    spremanje.destroy()
    glavni_okvir.destroy()
    print ocjena

#tkinter prozor koji se pojavljuje kad se odabere pretrazivanje, trazi unos korisnika sto zeli pretraziti
def pretraga():
    global crawler_prozor
    global unos_fqdn
    crawler_prozor = Tk()
    Label(crawler_prozor, text = "Unesite pretragu ").grid(row = 0, sticky = W)
    unos_fqdn = Entry(crawler_prozor)
    unos_fqdn.pack()
    unos_fqdn.focus_force()
    unos_fqdn.grid(row = 0, column = 1, sticky = E)
    gumb_pretraga = Button(crawler_prozor, text = "Pretrazi", command = crawler_bind_klik)
    gumb_pretraga.grid(row = 1, column = 0, columnspan = 2)
    crawler_prozor.bind('<Return>', crawler_bind_enter)

#nakon unosa rijeci u pretragu, kod pritiska tipke enter, ova funkcija se aktivira
def crawler_bind_enter(event):
    razdvajanje_rijeci(unos_fqdn.get(),crawler_prozor)

#isto kao i kod entera samo sa klikom misa na gumb pretrazi
def crawler_bind_klik(event):
    razdvajanje_rijeci(unos_fqdn.get(),crawler_prozor)

#funkcija za gasenje tkinter prozora
def gasenje_prozora(za_ugasiti):
    za_ugasiti.destroy()

    
glavni_prozor = Tk()
glavni_prozor.configure(background = "gray95")
glavni_prozor.geometry("630x700")

osnovni_meni = Menu(glavni_prozor)
file_menu = Menu(osnovni_meni, tearoff=0)

file_menu.add_command(label="Pokreni pretrazivanje", command=pretraga)
file_menu.add_command(label="Ugasi", command=glavni_prozor.quit)
osnovni_meni.add_cascade(label="Pretrazivanja", menu=file_menu)
glavni_prozor.config(menu = osnovni_meni)




glavni_prozor.mainloop()
