# Pravila za rastavljanje riječi hrvatskoga jezika

# hyph-hr: Generator pravila za automatsku hifenaciju hrvatskog jezika

Ovaj projekt sadrži alate i pravila za automatsko rastavljanje riječi na kraju retka (hifenaciju) u hrvatskom jeziku, u potpunosti optimizirana za formate koje koriste popularni programi poput **LibreOffice**, **Firefox**, **Adobe InDesign** (putem Hunspell/libhyphen sustava) i **TeX**.

## O projektu i porijeklu podataka

Ovaj repozitorij nastao je kao spoj jezične baze, algoritamske analize i suvremene tehnologije:
1. **Izvorna baza podataka (Rječnik):** Kao osnova za učenje i ekstrakciju jezičnih zakonitosti poslužio je hrvatski Hunspell rječnik s repozitorija [github.com/krunose/hunspell-hr](https://github.com).
2. **Razvoj algoritma (AI):** Python skripta `hifenator.py` razvijena je u suradnji s **umjetnom inteligencijom (AI)**. Cilj je bio stvoriti hibridni model koji kombinira stroga morfološka pravila hrvatskog standardnog jezika s naprednom statističkom analizom (n-gram extraction) kako bi se zamijenio tradicionalni, komplicirani TeX-ov `patgen` proces.

---

## Kako su pravila nastala? (Proces)

Generiranje datoteke s pravilima (`hyph_hr_HR.dic`) odvija se kroz tri ključna koraka unutar skripte:

1. **Čišćenje Hunspell baze:** Skripta u letu čita izvornu datoteku `hr_HR.dic`, preskače metapodatke i automatski uklanja sve Hunspell numeričke i morfemske zastavice (npr. transformira `riječ/21` ili `riječ/353` u čisti tekst `riječ`).
2. **Hibridna hifenacija (Jezični modul):** 
   - **Morfemska granica (Prioritet):** Riječi se prvo provjeravaju kroz masovnu bazu hrvatskih prefiksa (`raz-`, `nad-`, `pod-`, `bez-`...) i opsežan popis od preko 150 prefiksoida (`auto-`, `pseudo-`, `tele-`, `cyber-`...). Time se sprječava računalni kaos poput pogrešnih lomova `pseu-doznanost` ili `ra-zuvjeriti`.
   - **Fonološki prijelom:** Nad čistim ostatkom riječi primjenjuju se standardna fonološka pravila (poput prijeloma unutar suglasničkih skupina VC-CV, obrade digrafa `lj`, `nj`, `dž` kao jedinstvenih glasova te prepoznavanja slogotvornog `r`).
3. **Statističko sažimanje (Generiranje TeX obrazaca):** Skripta analizira stvorene crtice kroz n-grame (okruženja od 3 do 6 slova). Ako se određeni prijelom u bazi od milijun oblika riječi ponavlja s točnošću većom od **95%**, skripta ga pretvara u TeX uzorak. Istovremeno se automatski ubrizgavaju **blokade (parni brojevi, npr. 2)** unutar prefiksoida kako opća pravila o zijatu (hiatu) ne bi razbila njihovu unutrašnjost.

---

## Kako pokrenuti skriptu?

Sve što treba je instaliran Python 3 i datoteka s rječnikom smještena i istoj mapi.

1. Osiguraj da ti se izvorna datoteka u mapi zove **`hr_HR.dic`** (ili prilagodi nazive na dnu skripte).
2. Pokreni skriptu kroz terminal / command prompt:

```bash
python hifenator.py
```

### Što se događa nakon pokretanja?
- Skripta će u terminalu ispisivati napredak svakih 100.000 obrađenih riječi (`[PROGRES] Hifenirano...`).
- Po završetku, u istoj mapi će se generirati finalna hifenacijska datoteka **`hyph_hr_HR.dic`**.

---

## Struktura izlazne datoteke (`hyph_hr_HR.dic`)

Izlazna datoteka sadrži standardno UTF-8 zaglavlje s ugrađenom **pravopisnom i estetskom zaštitom** koja sprječava ostavljanje jednog slova na kraju ili početku retka:

```text
UTF-8
LEFTHYPHENMIN 2    # Najmanje 2 slova moraju ostati na kraju retka (sprječava o-daslati -> oda-slati)
RIGHTHYPHENMIN 2   # Najmanje 2 slova moraju prijeći u novi redak (sprječava vrtlarstv-o -> vrtlar-stvo)
NEXTLEVEL
.a1d
.be2s1
.pseud2o1
...
```
*(Neparni brojevi označavaju dopuštene točke prijeloma, parni brojevi označavaju strogu zabranu prijeloma, a točka `.` označava hvatište na samom početku riječi).*

---

## Instalacija i korištenje pravila

### LibreOffice (Linux)
Kopiraj generiranu datoteku preko postojeće sistemske datoteke (zahtijeva administratorska prava):
```bash
sudo cp hyph_hr_HR.dic /usr/share/hyphen/hyph_hr_HR.dic
```
Ponovno pokreni LibreOffice i provjeri je li u postavkama jezika uključeno rastavljanje riječi za Hrvatski.

### Mozilla Firefox
1. Otvori Firefox i u adresnu traku upiši `about:support`.
2. Pod stavkom **Profile Folder** klikni na *Open Directory*.
3. Stvori mapu s nazivom `dictionaries` (ako već ne postoji) i u nju kopiraj `hyph_hr_HR.dic`.
4. Ponovno pokreni Firefox.

---

## Doprinosi i licence
Slobodno otvarajte *Issues* i *Pull Requestove* ako primijetite specifične riječi ili neologizme koje sustav ne prelama optimalno, kako bismo dodatno ugodili statističke filtre i popis prefiksoida!

- Izvorni rječnik: LGPL / MySpell [krunose/hunspell-hr](https://github.com)
- Skripta i generator pravila: MIT licenca

