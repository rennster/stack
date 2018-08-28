# -*- coding: cp1252 -*-

#import urllib2
import re
import webbrowser
from Tkinter import *
import tkMessageBox
import ttk
import sys
import stackexchange
import requests
import psycopg2
from bs4 import BeautifulSoup
import requests.packages.urllib3

class Poveznica:
    def __init__(self, naslov, url):
        self.naslov = naslov
        self.url = url

requests.packages.urllib3.disable_warnings()
lista_poveznica=[]
lista_gumbi = []
#podaci_iz_baze = []

def pretraga(parametri_pretrage, unisti_prozor):
    so = stackexchange.Site(stackexchange.StackOverflow, app_key="q)CtGxFiOE5CiaikkBG25Q((", impose_throttling=True)
    so.be_inclusive()
    if __name__ == '__main__':
        if len(sys.argv) > 2:
            parametri_pretrage = ' '.join(sys.argv[1:])
        
        print('Searching for %s...' % parametri_pretrage,)
        sys.stdout.flush()
        qs = so.search(intitle=parametri_pretrage,pagesize = 100, sort='votes')[:100]
    
        for q in qs:
            poveznica = Poveznica(q.title, q.id)
            lista_poveznica.append(poveznica)

        prijenos_poveznica(lista_poveznica)
        unisti_prozor.destroy()
            #print('%8d %s' % (q.id, q.title))

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
    cursor.execute("""INSERT INTO pohranjeno(id, naslov, odgovori, ocjena) VALUES (%s, %s, %s, %s);""",(broj, str(naziv), str(poveznica), ocjena))
    conn.commit()
    cursor.close()
    conn.close()

def pretraga_baze(parametar, prozor):
    global podaci_iz_baze
    povezivanje_na_bazu()
    rijec = ('%' + parametar + '%')
    cursor.execute("""SELECT id,naslov,ocjena FROM pohranjeno WHERE UPPER(naslov) LIKE UPPER('%s') ORDER BY id ASC;""" %rijec)
    podaci_iz_baze = cursor.fetchall()
    izlistaj_iz_baze(podaci_iz_baze)
    conn.close()
    crawler_prozor.destroy()



def dohvat_odgovora(unq_oznaka):
    cursor.execute("""SELECT odgovori FROM pohranjeno WHERE id = %s;""" %unq_oznaka)
    dohvati_tekst = cursor.fetchone()
    print dohvati_tekst
    conn.close()
    glavni_okvir = Tk()
    scrollbar = Scrollbar(glavni_okvir)
    scrollbar.pack(side = RIGHT, fill = Y)
    unos_teksta = Text(master = glavni_okvir, yscrollcommand = scrollbar.set)
    unos_teksta.pack(side=RIGHT)
    unos_teksta.insert(END,  dohvati_tekst[0])
    unos_teksta.see(END)
    scrollbar.config(command = unos_teksta.yview)
    glavni_okvir.mainloop()

def naj_naslovi():
    global najbolji_naslovi
    povezivanje_na_bazu()
    cursor.execute("""SELECT id,naslov,ocjena FROM pohranjeno ORDER BY ocjena DESC;""")
    najbolji_naslovi = cursor.fetchall()
    izlistaj_iz_baze(najbolji_naslovi)
    conn.close()

def izlistaj_iz_baze(podaci_iz_baze):
    global prozor
    global izlistaj
    if "prozor" in globals():
        prozor.destroy()
    prozor = Frame()
    prozor.configure(background = "gray93")
    prozor.pack(fill = "both", expand = True)
    imena_stupaca = ("id", "poveznica", "ocjena")
    izlistaj = ttk.Treeview(height = "30",columns = imena_stupaca,\
                            show = "headings", selectmode="extended")
    ysb = ttk.Scrollbar(orient='vertical', command=izlistaj.yview)
    xsb = ttk.Scrollbar(orient='horizontal', command=izlistaj.xview)
    izlistaj['yscroll'] = ysb.set
    izlistaj['xscroll'] = xsb.set
    izlistaj.column("id", width = 100, stretch = NO)
    izlistaj.heading("id", text = "ID")
    izlistaj.column("poveznica", width = 450, stretch = YES)
    izlistaj.heading("poveznica", text = "Poveznice")
    izlistaj.column("ocjena", width = 50, stretch = NO)
    izlistaj.heading("ocjena", text = "Ocjena")
    ysb.grid(in_=prozor, row=0, column=1, sticky=NS)
    xsb.grid(in_=prozor, row=1, column=0, sticky=EW)
    prozor.rowconfigure(0, weight = 1)
    prozor.columnconfigure(0, weight = 1)
    izlistaj.grid(column = 0, row = 0, in_=prozor)
    
    for i in range(0, len(podaci_iz_baze)):
        izlistaj.insert("", i, iid = i,\
                        values = (podaci_iz_baze[i][0], podaci_iz_baze[i][1], podaci_iz_baze[i][2]))
    izlistaj.bind("<Double-1>", dohvat_txt_baza)
    if len(podaci_iz_baze) < 1:
        tkMessageBox(" ","U bazi nema zapisa koji odgovaraju pretragi")

def dohvat_txt_baza(event):
    broj = izlistaj.selection()[0]
    odabrani_objekt = podaci_iz_baze[int(broj)][0]
    print odabrani_objekt
    povezivanje_na_bazu()
    dohvat_odgovora(odabrani_objekt)

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
    izlistaj.column("id", width = 100, stretch = NO)
    izlistaj.heading("id", text = "ID")
    izlistaj.column("poveznica", width = 500)
    izlistaj.heading("poveznica", text = "Poveznice")
    ysb.grid(in_=prozor, row=0, column=1, sticky=NS)
    xsb.grid(in_=prozor, row=1, column=0, sticky=EW)
    prozor.rowconfigure(0, weight = 1)
    prozor.columnconfigure(0, weight = 1)
    izlistaj.grid(column = 0, row = 0, in_=prozor)
    
    for i in range(0, len(lista_poveznica)):
        var_poveznica = lista_poveznica[i]
        izlistaj.insert("", i, iid = i,\
                        values = (lista_poveznica[i].url, lista_poveznica[i].naslov))
    izlistaj.bind("<Double-1>", objekt_klik)
    
#u slucaju dvostrukog klika na naslov ova funkcija poziva funkciju html_sample
def objekt_klik(event):
    obj = izlistaj.selection()[0]
    print obj
    naslov_pitanja = lista_poveznica[int(obj) + 1].naslov
    print naslov_pitanja
    id_pitanja = lista_poveznica[(int(obj)+ 1)].url
    print id_pitanja
    #webbrowser.open_new(lista_poveznica[(int(obj)+ 1)].url)
    odabir_qs(lista_poveznica[(int(obj)+ 1)].url, naslov_pitanja, id_pitanja)    

#otvaranje kliknute poveznice u novom Python prozoru kao tekst
def odabir_qs(id_qs, naslov_pitanja, id_pitanja):
    odgovori = []
    qs_url=("https://api.stackexchange.com/2.2/questions/%s/answers?order=desc&sort=activity&site=stackoverflow&filter=!9YdnSM68i" %id_qs)
    sadrzaj_ans = requests.get(qs_url)
    soup = BeautifulSoup(sadrzaj_ans.content)
    for string in soup.stripped_strings:
        odgovori.append(repr(string).replace("\\\\n","\n").strip("u'"))
    #odgovori = sadrzaj_ans.text
    #tekst = re.findall('{.*?"body":(.*?)}',odgovori)
    #lista_odgovora = tekst.split("\n")
    tekst_sa_stranice(odgovori, naslov_pitanja, id_pitanja)

#tkinter prozor u kojem se otvara parsirani tekst sa stranice koju je korisnik kliknuo
def tekst_sa_stranice(procisceni_tekst, naslov_pitanja, id_pitanja):
    global glavni_okvir
    glavni_okvir = Tk()
    scrollbar = Scrollbar(glavni_okvir)
    scrollbar.pack(side = RIGHT, fill = Y)
    unos_teksta = Text(master = glavni_okvir, yscrollcommand = scrollbar.set)
    unos_teksta.pack(side=RIGHT)
    okvir = Frame()
    okvir.pack(side = LEFT)
    for i in procisceni_tekst:
        unos_teksta.insert(END,  i,"\n")
    unos_teksta.see(END)
    scrollbar.config(command = unos_teksta.yview)
    gumb = Button(glavni_okvir, text = "Zatvori", command = lambda: glavni_okvir.destroy()).pack()
    gumb2 = Button(glavni_okvir, text = "Spremi za kasnije", command = lambda:spremi_za_kasnije(procisceni_tekst, naslov_pitanja, id_pitanja)).pack()
    gumb3 = Button(glavni_okvir, text = "Otvori u pregledniku", command = lambda:otvori_u_pregledniku(id_pitanja)).pack()
    #glavni_okvir.protocol("WM_DELETE_WINDOW", spremi_za_kasnije)
    glavni_okvir.mainloop()
    
def otvori_u_pregledniku(oznaka):
    cijeli_url = "http://stackoverflow.com/questions/%s/" %oznaka
    webbrowser.open_new_tab(cijeli_url)

#prozor koji se otvara kod spremanja procitanog teksta sa poveznice, nudi odabir ocjene za procitani tekst
def spremi_za_kasnije(procisceni_tekst, naslov_pitanja, id_pitanja):
    global spremanje
    spremanje = Tk()
    naslov = Label(spremanje, text = "Ocijenite koliko je pomogla spremljena poveznica")
    naslov.pack(side = TOP)
    for i in range(10):
        but = Button(spremanje, text = i+1, command = lambda i=i: unos_ocjene(procisceni_tekst, naslov_pitanja, id_pitanja, i+1))
        but.pack(side = LEFT,fill= BOTH)
    spremanje.mainloop()

def odabir_gumba(broj):
    ocjena = lista_gumbi[broj]
    return ocjena
    

#ovaj dio ce zapisivati ocjenu koju je korisnik kliknuo u bazu
def unos_ocjene(procisceni_tekst, naslov_pitanja, id_pitanja, ocjena):   
    povezivanje_na_bazu()
    spremanje_u_bazu(int(id_pitanja), naslov_pitanja, procisceni_tekst, ocjena)
    spremanje.destroy()
    glavni_okvir.destroy()
    print ocjena

def trazi_u_bazi():
    global crawler_prozor
    global unos_fqdn
    crawler_prozor = Tk()
    Label(crawler_prozor, text = "Unesite rijeci za pretragu ").grid(row = 0, sticky = W)
    unos_fqdn = Entry(crawler_prozor)
    unos_fqdn.pack()
    unos_fqdn.focus_force()
    unos_fqdn.grid(row = 0, column = 1, sticky = E)
    gumb_pretraga = Button(crawler_prozor, text = "Pretrazi", command = klik)
    gumb_pretraga.grid(row = 1, column = 0, columnspan = 2)
    crawler_prozor.bind('<Return>', enter)
    

#tkinter prozor koji se pojavljuje kad se odabere pretrazivanje, trazi unos korisnika sto zeli pretraziti
def unos_parametara():
    global crawler_prozor
    global unos_fqdn
    crawler_prozor = Tk()
    Label(crawler_prozor, text = "Unesite rijeci za pretragu ").grid(row = 0, sticky = W)
    unos_fqdn = Entry(crawler_prozor)
    unos_fqdn.pack()
    unos_fqdn.focus_force()
    unos_fqdn.grid(row = 0, column = 1, sticky = E)
    gumb_pretraga = Button(crawler_prozor, text = "Pretrazi", command = crawler_bind_klik)
    gumb_pretraga.grid(row = 1, column = 0, columnspan = 2)
    crawler_prozor.bind('<Return>', crawler_bind_enter)

#nakon unosa rijeci u pretragu, kod pritiska tipke enter, ova funkcija se aktivira
def crawler_bind_enter(event):
    pretraga(unos_fqdn.get(),crawler_prozor)

#isto kao i kod entera samo sa klikom misa na gumb pretrazi
def crawler_bind_klik(event = None):
    pretraga(unos_fqdn.get(),crawler_prozor)

def enter(event):
    pretraga_baze(unos_fqdn.get(),crawler_prozor)


def klik(event = None):
    pretraga_baze(unos_fqdn.get(),crawler_prozor)

    
glavni_prozor = Tk()
glavni_prozor.configure(background = "gray95")
glavni_prozor.geometry("650x650")
osnovni_izbornik = Menu(glavni_prozor)

prvi_izbornik = Menu(osnovni_izbornik, tearoff=0)
prvi_izbornik.add_command(label="Pretrazi Stack Exchange", command=unos_parametara)

drugi_izbornik = Menu(osnovni_izbornik, tearoff = 0)
drugi_izbornik.add_command(label = "Pretrazi pohranjeno u bazi", command = trazi_u_bazi)
drugi_izbornik.add_command(label = "Najbolje ocijenjeni naslovi", command =naj_naslovi)

treci_izbornik = Menu(osnovni_izbornik, tearoff = 0)
treci_izbornik.add_command(label = "Ugasi aplikaciju", command = exit)

osnovni_izbornik.add_cascade(label="Pretrazivanje Stack Exchange", menu=prvi_izbornik)
osnovni_izbornik.add_cascade(label = "Pretrazivanje pohranjenih tema", menu = drugi_izbornik)
osnovni_izbornik.add_cascade(label = "Gasenje aplikacije", menu = treci_izbornik)
glavni_prozor.config(menu = osnovni_izbornik)

glavni_prozor.mainloop()
