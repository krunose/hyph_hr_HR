import os
import re
from collections import defaultdict

class HrvatskiGeneratorPravila:
    # 1. MORFOLOŠKA PRAVILA: Prefiksi i prefiksoidi
    PREFIKSI = sorted([
        "nad", "pod", "pred", "pret", "raz", "ras", "uz", "us", "bez", "bes",
        "iz", "is", "od", "ot", "ob", "op", "pre", "pri", "pro", "su", "do", 
        "ko", "izvan", "naj", "nadis", "nadod", "sub", "kontra", "dis"
    ], key=len, reverse=True)
    
    PREFIKSOIDI = sorted([
        "auto", "biomed", "geo", "eko", "foto", "hidro", "makro", "mikro", 
        "neuro", "psihod", "pseudo", "tele", "termo", "astro", "bio", "krono",
        "kvazi", "multi", "poli", "video", "mono", "giga", "mega", "kilo"
    ], key=len, reverse=True)
    
    SAMOGLASNICI = set("aeiouAEIOU")
    DIGRAFI = ("lj", "nj", "dž", "Lj", "Nj", "Dž", "LJ", "NJ", "DŽ")

    def __init__(self):
        self.morfemi = self.PREFIKSOIDI + self.PREFIKSI

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
            
        # Prefiksi imaju prednost (morfemska granica)
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
        
        return "-".join([r for r in rezultat if r])

    def procesiraj(self, ulazna_hunspell, izlazna_dic):
        if not os.path.exists(ulazna_hunspell):
            print(f"[GREŠKA] Ne mogu pronaći Hunspell datoteku '{ulazna_hunspell}'!")
            return

        print(f"[INFO] Čitam Hunspell datoteku i čistim zastavice...")
        uzorci_brojac = defaultdict(lambda: defaultdict(int))
        brojac_rijeci = 0

        with open(ulazna_hunspell, "r", encoding="utf-8") as f:
            # Preskačemo prvi redak koji sadrži samo broj riječi
            prva_linija = f.readline().strip()
            
            for linija in f:
                linija = linija.strip()
                if not linija:
                    continue
                
                # Čišćenje zastavica: režemo sve nakon znaka '/'
                cista_rijec = linija.split("/")[0].strip().lower()
                
                # Ignoriramo brojeve, kratice i specijalne znakove ako su zalutali
                if not cista_rijec.isalpha() and "-" not in cista_rijec:
                    continue

                # Pokrećemo hifenaciju na čistoj riječi
                hifenirana = self.hifeniraj_rijec(cista_rijec)
                if "-" not in hifenirana:
                    continue

                brojac_rijeci += 1
                if brojac_rijeci % 100000 == 0:
                    print(f"[PROGRES] Obrađeno {brojac_rijeci} riječi...")

                # Ekstrakcija okoline oko crtica (duljine 3 do 5 slova za stabilna pravila)
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

        print("[INFO] Generiram i filtriram optimalna pravila (razina 1 i 2)...")
        konacni_uzorci = set()

        # Eksplicitno dodajemo fiksne morfološke blokade za prefikse
        # To osigurava da se riječi poput 'raz-uvjeriti' ne slome unutar samog prefiksa (ra2z1)
        for p in ["nad", "pod", "pred", "pret", "raz", "ras", "uz", "us", "bez", "bes", "iz", "is", "od", "ot"]:
            konacni_uzorci.add(f".{p[:-1]}2{p[-1]}1")

        for kontekst, pozicije in uzorci_brojac.items():
            najbolja_pozicija = max(pozicije, key=pozicije.get)
            ukupno = sum(pozicije.values())
            frekvencija = pozicije[najbolja_pozicija]

            # Strogi statistički filteri:
            # 1. Pravilo mora biti točno u barem 95% svih pojavljivanja te kombinacije slova
            # 2. Pravilo se mora pojaviti minimalno 40 puta (reže rijetke iznimke i anomalije)
            if frekvencija > 40 and (frekvencija / ukupno) >= 0.95:
                # Generiramo pravilo s oznakom 1 (dozvoljen lom)
                tekst_pravila = kontekst[:najbolja_pozicija] + "1" + kontekst[najbolja_pozicija:]
                
                # Dodajemo blokade (parni broj 2) na mjesta gdje se crtica statistički nikada ne smije pojaviti
                for poz, broj in pozicije.items():
                    if broj == 0 and poz != najbolja_pozicija and poz < najbolja_pozicija:
                        tekst_pravila = tekst_pravila[:poz] + "2" + tekst_pravila[poz:]

                konacni_uzorci.add(tekst_pravila)

        # Sortiranje pravila po TeX/LibreOffice standardu
        sortirani_uzorci = sorted(list(konacni_uzorci), key=lambda x: (len(re.sub(r'[0-9]', '', x)), x))

        print(f"[INFO] Zapisujem finalnu datoteku '{izlazna_dic}'...")
        with open(izlazna_dic, "w", encoding="utf-8") as f_out:
            f_out.write("UTF-8\n")
            f_out.write("LEFTHYPHENMIN 2\n")
            f_out.write("RIGHTHYPHENMIN 2\n")
            f_out.write("NEXTLEVEL\n")
            
            for uzorak in sortirani_uzorci:
                f_out.write(uzorak + "\n")

        print(f"[USPJEH] Datoteka '{izlazna_dic}' je spremna za LibreOffice i Firefox!")
        print(f"Ukupno izvučeno čistih pravila: {len(sortirani_uzorci)}")

if __name__ == "__main__":
    # --- PRILAGODI NAZIV SVOJE DATOTEKE OVDJE ---
    # Ako ti se Hunspell datoteka zove npr. 'hr_HR.dic', promijeni prvi argument ispod
    ulazni_hunspell = "hr_HR.dic" 
    izlazna_pravila = "hyph_hr_HR.dic"
    
    generator = HrvatskiGeneratorPravila()
    generator.procesiraj(ulazni_hunspell, izlazna_pravila)

