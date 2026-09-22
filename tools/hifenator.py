import os
import re
from collections import defaultdict

class NapredniHrvatskiHifenator:
    # Izvorni pravopisni prefiksi hrvatskog jezika
    PREFIKSI = sorted([
        "nad", "pod", "pred", "pret", "raz", "ras", "uz", "us", "bez", "bes",
        "iz", "is", "od", "ot", "ob", "op", "pre", "pri", "pro", "su", "do", 
        "ko", "izvan", "naj", "nadis", "nadod", "sub", "kontra", "dis"
    ], key=len, reverse=True)
    
    def __init__(self, popis_prefiksoida):
        # Sortiramo od najdužih prema kraćima radi ispravnog poklapanja
        self.prefiksoidi = sorted(list(popis_prefiksoida), key=len, reverse=True)
        self.morfemi = self.prefiksoidi + self.PREFIKSI
        
        self.SAMOGLASNICI = set("aeiouAEIOU")
        self.DIGRAFI = ("lj", "nj", "dž", "Lj", "Nj", "Dž", "LJ", "NJ", "DŽ")

    def _je_slogotvorno_r(self, rijec: str, idx: int) -> bool:
        if rijec[idx].lower() != 'r':
            return False
        lijevo_je_suglasnik = (idx == 0) or (rijec[idx-1] not in self.SAMOGLASNICI and rijec[idx-1].lower() != 'r')
        desno_je_suglasnik = (idx == len(rijec) - 1) or (rijec[idx+1] not in self.SAMOGLASNICI and rijec[idx+1].lower() != 'r')
        if idx + 1 < len(rijec) and rijec[idx+1].lower() == 'j':
            return False
        return lijevo_je_suglasnik and desno_je_suglasnik

    def _get_jezgre_sloga(self, rijec: str) -> list:
        jezgre = []
        for i, char in enumerate(rijec):
            if char in self.SAMOGLASNICI or self._je_slogotvorno_r(rijec, i):
                jezgre.append(i)
        return jezgre

    def hifeniraj_rijec(self, rijec: str) -> str:
        if "-" in rijec:
            return "-".join([self.hifeniraj_rijec(dio) for dio in rijec.split("-")])
            
        for p in self.morfemi:
            if rijec.lower().startswith(p) and len(rijec) > len(p) + 1:
                ostatak = rijec[len(p):]
                if any(c in self.SAMOGLASNICI or c.lower() == 'r' for c in ostatak):
                    return rijec[:len(p)] + "-" + self.hifeniraj_rijec(ostatak)

        jezgre = self._get_jezgre_sloga(rijec)
        if len(jezgre) <= 1:
            return rijec

        granice = []
        for idx in range(len(jezgre) - 1):
            j1 = jezgre[idx]
            j2 = jezgre[idx+1]
            suglasnici_izmedu = rijec[j1+1:j2]
            broj_suglasnika = len(suglasnici_izmedu)
            
            if len(rijec[j2:]) == 0:
                continue

            if broj_suglasnika == 0 or broj_suglasnika == 1:
                granice.append(j1 + 1)
            else:
                if suglasnici_izmedu.startswith(self.DIGRAFI):
                    granice.append(j1 + 3 if suglasnici_izmedu.startswith(("dž", "Dž", "DŽ")) else j1 + 2)
                else:
                    granice.append(j1 + 2)

        rezultat = []
        prethodni = 0
        for g in sorted(list(set(granice))):
            if g > prethodni:
                rezultat.append(rijec[prethodni:g])
                prethodni = g
        rezultat.append(rijec[prethodni:])
        
        return "-".join([r for r in resultado if r] if 'resultado' in locals() else [r for r in rezultat if r])

    def generiraj_morfolosku_blokadu(self, prefiksoid: str) -> str:
        if len(prefiksoid) < 3:
            return f".{prefiksoid}1"
            
        baza = prefiksoid[:-1]
        zadnje_slovo = prefiksoid[-1]
        
        if len(baza) > 1 and baza[-1] in self.SAMOGLASNICI and zadnje_slovo in self.SAMOGLASNICI:
            return f".{baza[:-1]}2{baza[-1]}2{zadnje_slovo}1"
            
        return f".{baza}2{zadnje_slovo}1"

    def procesiraj_hunspell_u_pravila(self, ulazna_hunspell: str, izlazna_dic: str):
        if not os.path.exists(ulazna_hunspell):
            print(f"[GREŠKA] Ne mogu pronaći Hunspell datoteku '{ulazna_hunspell}'!")
            return

        print(f"[INFO] Korak 1: Čitam Hunspell datoteku i hifeniram riječi...")
        uzorci_brojac = defaultdict(lambda: defaultdict(int))
        brojac_rijeci = 0

        with open(ulazna_hunspell, "r", encoding="utf-8") as f:
            # Preskačemo prvi redak s brojem riječi
            f.readline()
            
            for linija in f:
                linija = linija.strip()
                if not linija:
                    continue
                
                # POPRAVLJENO: Uzimamo samo prvi element liste (indeks 0) koji predstavlja riječ
                dijelovi = linija.split("/")
                cista_rijec = dijelovi[0].strip().lower()
                
                # Preskačemo ako su prazni redovi ili samo specijalni znakovi
                if not cista_rijec or (not cista_rijec.isalpha() and "-" not in cista_rijec):
                    continue

                hifenirana = self.hifeniraj_rijec(cista_rijec)
                if "-" not in hifenirana:
                    continue

                brojac_rijeci += 1
                if brojac_rijeci % 100000 == 0:
                    print(f"[PROGRES] Hifenirano {brojac_rijeci} riječi...")

                oznacena = "." + hifenirana + "."
                for i in range(len(oznacena)):
                    if oznacena[i] == "-":
                        for duljina in range(3, 6):
                            for lijevo in range(max(0, i - duljina + 1), i + 1):
                                desno = lijevo + duljina + 1
                                if desno > len(oznacena):
                                    continue
                                podniz = oznacena[lijevo:desno]
                                if "-" in podniz:
                                    cisti_kontekst = podniz.replace("-", "")
                                    pozicija_crtice = podniz.find("-")
                                    uzorci_brojac[cisti_kontekst][pozicija_crtice] += 1

        print("[INFO] Korak 2: Generiram i filtriram uzorke te uvozim morfološke blokade...")
        konacni_uzorci = set()

        for pref in self.prefiksoidi:
            blokada = self.generiraj_morfolosku_blokadu(pref)
            konacni_uzorci.add(blokada)

        for pref in ["nad", "pod", "pred", "pret", "raz", "ras", "uz", "us", "bez", "bes", "iz", "is", "od", "ot"]:
            konacni_uzorci.add(f".{pref[:-1]}2{pref[-1]}1")

        for kontekst, pozicije in uzorci_brojac.items():
            if len(kontekst) < 3:
                continue
                
            najbolja_pozicija = max(pozicije, key=pozicije.get)
            ukupno = sum(pozicije.values())
            frekvencija = pozicije[najbolja_pozicija]

            if frekvencija > 40 and (frekvencija / ukupno) >= 0.95:
                tekst_pravila = kontekst[:najbolja_pozicija] + "1" + kontekst[najbolja_pozicija:]
                
                for poz, broj in pozicije.items():
                    if broj == 0 and poz != najlepsa_pozicija and poz < najbolja_pozicija:
                        tekst_pravila = tekst_pravila[:poz] + "2" + tekst_pravila[poz:]

                konacni_uzorci.add(tekst_pravila)

        sortirani_uzorci = sorted(list(konacni_uzorci), key=lambda x: (len(re.sub(r'[0-9]', '', x)), x))

        print(f"[INFO] Korak 3: Zapisujem hifenacijsku datoteku '{izlazna_dic}'...")
        with open(izlazna_dic, "w", encoding="utf-8") as f_out:
            f_out.write("UTF-8\n")
            f_out.write("LEFTHYPHENMIN 2\n")
            f_out.write("RIGHTHYPHENMIN 2\n")
            f_out.write("NEXTLEVEL\n")
            
            for uzorak in sortirani_uzorci:
                f_out.write(uzorak + "\n")

        print(f"[USPJEH] Datoteka '{izlazna_dic}' je uspješno generirana!")
        print(f"Ukupno kreirano pravila: {len(sortirani_uzorci)}")

if __name__ == "__main__":
    popis_prefiksoida = set([
        "aero", "akro", "alto", "andro", "aritmo", "austro", "avio", "biblio", "bruto", "daktilo", "dija", "ego", 
        "elektro", "epi", "fero", "fono", "galvano", "gono", "helio", "hidro", "hiro", "infra", "izo", "kiber", 
        "kreno", "kripto", "kseno", "latino", "magneto", "megalo", "metro", "mili", "mono", "muzeo", "neo", 
        "nukleo", "osteo", "para", "pireto", "poli", "proto", "roto", "servo", "soc", "steno", "surdo", "tele", 
        "trofo", "vazo", "akva", "alu", "anglo", "arterio", "auto", "balneo", "bio", "centi", "deci", "disko", 
        "egzo", "empirio", "etno", "filo", "foto", "gastro", "grafo", "hemo", "hemato", "homo", "ino", "kabrio", 
        "kilo", "krim", "kromo", "ksero", "leuko", "makro", "melo", "mezo", "mini", "morfo", "nano", "neto", 
        "oligo", "paleo", "pato", "piro", "porno", "pseudo", "repro", "ruso", "sidero", "socio", "stereo", "tahi", 
        "teo", "turbo", "video", "afro", "alergo", "ampelo", "antropo", "astro", "baro", "blasto", "cito", "deka", 
        "domato", "ekstra", "endo", "euro", "fito", "geo", "grando", "hero", "hiper", "indo", "inter", "kardio", 
        "kino", "krimi", "krono", "kvazi", "lito", "maksi", "meta", "midi", "mio", "moto", "narko", "neuro", 
        "ornito", "palin", "pedo", "pluskvam", "profi", "psiho", "retro", "semio", "sinkro", "solo", "supra", 
        "tara", "termo", "ultra", "zoo", "agro", "alo", "anarho", "argiro", "audio", "auzo", "bi", "bronho", 
        "dakno", "demo", "doro", "eko", "entomo", "fizio", "franko", "germano", "hekto", "hetero", "hipo", "info", 
        "italo", "kata", "klepto", "krio", "kozmo", "labio", "logo", "mega", "meteo", "mikro", "mnemo", "multi", 
        "nekro", "nitro", "orto", "pan", "petro", "pneumo", "promo", "radio", "rino", "sero", "ski", "spektro", 
        "super", "tehno", "topo", "uni", "žiro"
    ])

    ulazni_hunspell = "hr_HR.dic"
    izlazna_pravila = "hyph_hr_HR.dic"
    
    hifenator = NapredniHrvatskiHifenator(popis_prefiksoida)
    hifenator.procesiraj_hunspell_u_pravila(ulazni_hunspell, izlazna_pravila)

