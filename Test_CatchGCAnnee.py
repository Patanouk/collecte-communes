# -*- coding: utf-8 -*-
import csv
import io
import os
from sys import platform

import selenium.webdriver.support.ui as UI
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

# Commentaires

# Année de recherche des données
Annee = '2017'
AnneeMax = 2017
AnneeMin = 2017

# Choix des départements à scraper. Il y a 102 départements, 97 pour métropole +Corse, et 5 pour les DOM (Guadeloupe, Guyane, Martinique, Réunion, Mayootte)
DepMin = 1  # Min=1
DepMax = 103  # Max 103

# Référencement du répertoire de travail

# root_directory : le répertoire où doit être placé l'instance de Chromedriver qui va servir à la collecte des données
root_directory = os.path.dirname(__file__)
print("root directory dans Etape0", root_directory)

root_output_directory = '.'
# Output_directory : le sous-répertoire de root_directory où seront enregistrés les rsultats (fochier log, données btutes communes et groupements)
output_directory = os.path.join(root_output_directory,
                                'output/' + str(Annee) + '/ScraperResults-Argus-Vtest' + str(Annee))
print("output directory", output_directory)


# lignes 289-292 écriture du fichier commune
# lignes 218-221 écriture du fichier groupement

#  -------- Fonctions auxiliaires et d'analyse des données des pages extraites -------

def norm_3(var):
    """
    Normalisation d'un nombre entier en chaîne de 3 caractères
    :param var:
    :return:
    """
    if var <= 9:
        return '00' + str(var)
    elif var <= 99:
        return '0' + str(var)
    else:
        return str(min(var, 999))


def clean1(str):
    """
    fonction de nettoyage des chaines scrapées par élimination de &nbsp
    :param str:
    :return:
    """
    cleanstr = str[:str.find('&nbsp')]
    return cleanstr


def get_data_commune(page_source: webdriver) -> str:
    """
    Fonction de collecte des données dans la page de la commune
    :param page_source:
    :return:
    """
    dom = BeautifulSoup(page_source)
    nom_commune = dom.find('span', attrs={"id": "gfp"}).contents[0].strip(u'\xe0')

    if " (commune nouvelle" in nom_commune:
        nom_commune = str(nom_commune)[0:str(nom_commune).find(" (commune nouvelle")]

    nom_departement = dom.find('span', attrs={"id": "departement"}).contents[0] \
        .strip(u'\xe0') \
        .replace("-", "")

    population_commune = dom.find('td', attrs={"id": "population"}).contents[0] \
        .strip(u'\xe0') \
        .replace("Population légale", "") \
        .replace(" en vigueur au 1er janvier de l'exercice : ", "") \
        .replace(" habitants - Budget principal seul", "") \
        .replace(" ", "")

    res = nom_commune + "," + nom_departement + "," + population_commune
    return res


def find_groupement_communes(text, annee, annee_min, annee_max):
    if text.find("partir de") > -1:
        return True
    else:
        for Year in range(annee_min, int(annee) + 1):
            if text.find(str(Year)) > -1:
                for Year2 in range(int(annee), annee_max + 1):
                    if text.find(str(Year2)) > -1:
                        return True
    # print("Search GC",Var,Text)
    return False


def open_main_page(url: str) -> webdriver:
    print("url=", url)
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--headless")
    print("path to chromedriver in open_main_page", path_to_chromedriver)
    browser = webdriver.Chrome(executable_path=path_to_chromedriver, chrome_options=chrome_options)
    browser.implicitly_wait(10)  # seconds
    browser.get(url)
    return browser


def getdep(page: webdriver):
    """
    Selection de la liste des départements
    :param page:
    :return:
    """
    return UI.Select(page.find_element_by_id('listeDepartements'))


def getalpha(page: webdriver):
    """
    Selection de la liste alphabétique des communes
    :param page:
    :return:
    """
    return page.find_elements_by_xpath(dbox + '/tbody/tr[1]/td[2]/p/a')


def identify_groupement_commune(page: webdriver) -> (str, str):
    """
    :param page:
    :return: Nom et reference du groupement de commune
    """
    # Identification du groupement de commune
    nomcc = page.find_element_by_xpath('// *[@id="gfp"]').text
    nomccs = str(nomcc).replace("/", "_")
    # print("identify _groupement_commune-nomccs", nomccs, "nomcc", nomcc)
    # Si la cc à déjà été vue
    if nomcc in listecc:
        # Renvoie la référence
        idx = listecc.index(nomcc)
        print("cc deja dans la liste'", nomccs, refcc[idx], refccnom[idx], listecc)
        return nomccs, refcc[idx], refccnom[idx]
    else:
        # Ajoute la cc dans la liste 'déjà vue' et envoie la référence
        idxcc = len(listecc)
        listecc.append(nomccs)
        # print("liste augmentee",listecc)
        refcc.append('*'.join((nodep, str(idxcc).zfill(3))))
        refccnom.append('*'.join((nomccs, nodep, str(idxcc).zfill(3))))
        print("liste augmentée", nomccs, refcc[-1], refccnom[-1], listecc)
        return nomccs, refcc[-1], refccnom[-1]


# SearchGC : fonction de recherche des coordonnées d'un groupement de communes depuis la page page_start des commune+ goupemments via le chemin pth
def search_groupement_commune(page_start, id_commune, nom_commune, long, tu, pth):
    if page_start.find_elements_by_xpath(pth):
        # ... le suivre
        page_start.find_element_by_xpath(pth).click()

        # Lecture de la page
        infos = page_start.find_element_by_xpath('//*[@id="donnees"]').text

        # Si la page contient 'non disponibles' ou n'affiche pas les données de l'année
        if (infos.find(Annee) == -1) or (infos.find(u'non disponibles') > -1):
            # Renseigner la variable de disponibilité
            idccnom = 'N/D'
            nmcc = 'N/D'
            idcc = 'N/D'
            dispocc = 'N/D'
        else:
            # Sinon, ouvrir la page 'Fiche détaillée'
            # Ouvre l'annee
            click_sur_fiche_departement_annee(page, "Groupement de Communes")
            # Ouvre la page fiche detaille
            print(page.page_source)
            page.find_element_by_xpath(fiche_departement).click()

            # Récupération des infos du groupement
            nmcc, idcc, idccnom = identify_groupement_commune(page_start)
            # Enregistrer son contenu dans un fichier nommé
            # 'NoDépartement-Index' dans le dossier 'Groupements'
            with io.open('Groupements/' + idcc + '.html', 'w') as f:
                f.write(page.page_source)
            with io.open('Groupements/' + idccnom + '.html', 'w') as f:
                f.write(page.page_source)
            dispocc = 'OK'
    else:
        print("SearchGC-pas de lien vers GC")
        dispocc = "NOK"
        idcc = "N/D"
        nmcc = 'N/D'
        idccnom = 'N/D'
    lien2 = [id_commune, idcc, nom_commune, nmcc, long - 1, tu]
    return lien2, nmcc, idcc, idccnom, dispocc


def boucle_commune(page: webdriver):
    global reprise, idxcomm, bclc, bclt

    # Calcul du nombre de table(s) dans la page
    nombre_tables = len(page.find_elements_by_xpath(dbox))

    # Boucle des tables
    for index_table in range(bclt, nombre_tables + 1):
        table = page.find_elements_by_xpath(dbox)[index_table - 1]
        nombre_communes = len(table.find_elements_by_class_name('libellepetit'))
        # Boucle des communes de la table
        for index_commune in range(bclc, nombre_communes):
            #  Récupération du lien de la commune
            pth = dbox + '[' + str(index_table) + ']/tbody/tr/td/a'
            lien_commune = page.find_elements_by_xpath(pth)[index_commune * 2 + 1]

            # print("page de la commune :", lien_commune.text)

            # Identification de la commune
            nom_commune = lien_commune.text
            nom_communes = str(nom_commune).replace("/", "_")
            id_commune = '*'.join((nodep, alpha, str(idxcomm).zfill(3)))
            id_commune_nom = '*'.join((nom_communes, nodep, alpha, str(idxcomm).zfill(3)))

            # Page de la commune
            lien_commune.click()

            # Budget principal
            page.find_element_by_xpath('//*[@id="bpcommune"]/a[2]').click()

            # recherche des liens par année
            # Vérification de la disponibilité des données
            infos = page.find_element_by_xpath('//*[@id="donnees"]').text

            # Si la page contient 'non disponibles' ou n'affiche pas les données de l'année
            if (infos.find(Annee) == -1) or (infos.find(u'non disponibles') > -1):
                # Renseigner la variable de disponibilité
                dispo_commune = 'N/D'
            else:
                # Sinon, se positionner à l'année souhaitée et ouvrir la page 'Fiche détaillée'
                # print("exploration par annee")
                click_sur_fiche_departement_annee(page, "Commmune")
                # Ouvre la page fiche detaille
                page.find_element_by_xpath(fiche_departement).click()

                # Enregistrer son contenu dans un fichier nommé
                # 'NoDépartement-PremiéreLettre-Index' dans le dossier 'Communes'
                with io.open('Communes/' + id_commune + '.html', 'w') as f:
                    f.write(page.page_source)
                with io.open('Communes/' + id_commune_nom + '.html', 'w') as f:
                    f.write(page.page_source)
                #################################################
                # Ici votre code de traitement par commune avec #
                # les données de page.page_source               #
                resultat_commune = get_data_commune(page.page_source)
                #################################################
                dispo_commune = 'OK'

            # Retour à "Choix d'un budget" ("d'une commune ?")
            print()
            page.find_element_by_xpath('//*[@class="chemincontainer"]/a[3]').click()
            pth_tot = dbox + '/tbody/tr/td/div'
            liste_c_et_gc = page.find_elements_by_xpath(pth_tot)

            try:
                length_list_commmune_and_groupements = len(liste_c_et_gc)
            except:
                length_list_commmune_and_groupements = 0
            Text_gc = []

            print(nom_commune, "longueur de liste_c_et_gc", length_list_commmune_and_groupements)
            for k in range(length_list_commmune_and_groupements):
                print("element", k, "de la liste c et gc", liste_c_et_gc[k].text, liste_c_et_gc[k])
                if k > 0:
                    Text_gc.append(liste_c_et_gc[k].text)

            print()
            if len(liste_c_et_gc) > 0:
                print(nom_commune, liste_c_et_gc[0].text, "nombre d'éléments GC :", length_list_commmune_and_groupements - 1, 'liste_gc',
                      Text_gc)  # liste_c_et_gc)
                print()
            Listegc = []
            if length_list_commmune_and_groupements == 0:
                tu0 = "na"
                pass
            else:
                count = 0
                for tu in range(1, length_list_commmune_and_groupements):
                    list_groupement_commune = liste_c_et_gc[tu].text.split("\n")
                    print("Elément", tu, " de Liste GC", list_groupement_commune)
                    for groupement_commune in list_groupement_commune:
                        print(nom_commune, "GC", groupement_commune, "Actif " + str(Annee) + " ? : ",
                              find_groupement_communes(groupement_commune, Annee, AnneeMin, AnneeMax))

                        if find_groupement_communes(groupement_commune, Annee, AnneeMin, AnneeMax):
                            Listegc.append([count, groupement_commune, liste_c_et_gc[tu]])
                            tu0 = tu  # sans doute ce tu0 a servi à repérer le bon groupement, mais maintenant il y en a plusieurs
                            print("Valide ", tu, [count, groupement_commune, liste_c_et_gc[tu]])
                            # ta = 1
                            print("in - tu0", tu0, "Listegc", Listegc)
                            count = count + 1
            print("tu0", tu0, "Listegc", Listegc)
            Listelien2 = []

            if tu0 == "na":
                pth = dbox + '/tbody/tr[3]/td/div/a[2]'
                Result, nmcc, idcc, idccnom, dispocc = search_groupement_commune(page, id_commune, nom_commune, length_list_commmune_and_groupements, tu0, pth)
                Listelien2.append(Result)
                # Création des informations de boucle (utiles en cas de reprise)
                cursor = '-'.join((str(d), str(a), str(index_table), str(index_commune), str(idxcomm)))
                # Création de la ligne à écrire dans le fichier log.csv
                logcomm = ';'.join(
                    (id_commune, nom_commune, dispo_commune, idcc, nmcc, dispocc, str(length_list_commmune_and_groupements - 1), str(tu0), cursor))

                # Ne pas écrire la ligne en cas de reprise (elle existe déjà)
                if reprise:
                    reprise = False
                else:
                    print("ligne de log", logcomm)
                    log.write(logcomm + '\n')
            else:
                for k in range(len(Listegc)):
                    # Retour à "Choix d'un budget" ("d'une commune ?")
                    tx = Listegc[k][0]
                    Lien = Listegc[k][2].find_elements_by_xpath("//a[@href]")

                    print("éléments à tester pour trouver la page de la communauté de communes", Lien)
                    if k > 0:
                        # repositionnement sur la page de choix d'un budget pour la commune visée
                        page.find_element_by_xpath('//*[@class="chemincontainer"]/a[3]').click()

                    pth = dbox + '/tbody/tr[3]/td/div/a[' + str(2 + tx) + ']'
                    Result, nmcc, idcc, idccnom, dispocc = search_groupement_commune(page, id_commune, nom_commune, length_list_commmune_and_groupements, tu0, pth)
                    Listelien2.append(Result)

                    # Création des informations de boucle (utiles en cas de reprise)
                    cursor = '-'.join((str(d), str(a), str(index_table), str(index_commune), str(idxcomm)))
                    # Création de la ligne à écrire dans le fichier log.csv
                    logcomm = ';'.join(
                        (id_commune, nom_commune, dispo_commune, idcc, nmcc, dispocc, str(length_list_commmune_and_groupements - 1), str(tu0), cursor))

                    # Ne pas écrire la ligne en cas de reprise (elle existe déjà)
                    if reprise:
                        reprise = False
                    else:
                        print("ligne de log", logcomm)
                        log.write(logcomm + '\n')

            try:
                print("ResCommune", resultat_commune)
            except:
                print("erreur Rescommunes")
            for v in range(len(Listelien2)):
                print("Listelien2", Listelien2[v])
                LinkC_GC.writerow(Listelien2[v])

            # Retour à "Choix d'une commune"
            pth = '//*[@class="chemincontainer"]/a[2]'
            if page.find_elements_by_xpath(pth):
                page.find_element_by_xpath(pth).click()

            # Incrémentation de l'index des communes
            idxcomm += 1
        # Remise à défaut des variables de boucle
        bclc = 0
    bclt = 2
    idxcomm = 0


def click_sur_fiche_departement_nomgc(page: webdriver, Nomgc, Niveau):
    elems = page.find_elements_by_xpath("//a[@href]")
    for elem in elems:
        print(Niveau, "elem:", elem.text, elem.get_attribute("href"))
        if Nomgc in elem.text:
            elem.click()
            click_sur_fiche_departement_annee(elem, Niveau)
            break
    page.find_element_by_xpath(fiche_departement).click()


def click_sur_fiche_departement_annee(page: webdriver, Niveau):
    elems = page.find_elements_by_xpath("//a[@href]")
    for elem in elems:
        print(Niveau, "elem:", elem.text, elem.get_attribute("href"))
        if Annee in elem.text:
            elem.click()
            break


def get_path_to_chrome_driver() -> str:
    if platform == "linux" or platform == "linux2":
        return os.path.join(root_directory, "chrome/driver/chromedriver_linux")
    elif platform == "darwin":
        Dir_chrome = os.path.join(root_directory, "chrome/driver/chromedriver_mac")
        print('Dir_Chrome', Dir_chrome)
        return Dir_chrome
    else:
        raise EnvironmentError("Only supporting Linux & Mac")


print("__name__", __name__)
if __name__ == '__main__':

    path_to_chromedriver = get_path_to_chrome_driver()
    # print("chromedriver directory", path_to_chromedriver)

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    os.chdir(output_directory)
    print("Actual work directory : {work_directory}".format(work_directory=os.getcwd()))

    # Création des dossier 'Communes' et 'Groupements' s'ils n'existent pas
    for dossier in ('Communes', 'Groupements'):
        if not os.path.isdir(dossier):
            os.makedirs(dossier)

    # -------- Initialisation des variables -------
    # Lien vers le site
    url = 'https://www.impots.gouv.fr/cll/zf1/cll/zf1/accueil/flux.ex?_flowId=accueilcclloc-flow'
    # Paths les plus utilisés dans la recherche de liens
    dbox = '//*[@id="donneesbox"]/table'
    fiche_departement = '//*[@id="pavegestionguichets"]/table[2]/tbody/tr/td[5]/a'
    # Variables de boucles utiles au premier lancement...
    # ... sinon elle sont alimentées par le fichier de log
    bcld, bcla, bclt, bclc, idxcomm = (1, 0, 2, 0, 0)
    alpha = ''
    listecc, refcc, refccnom = ([], [], [])
    reprise = False

    # Gestion du fichier log
    # S'il existe
    if os.path.isfile('log.csv'):
        # L'ouvrir en lecture
        log = io.open('log.csv', 'r')
        nbline = 0
        oldd = 1
        # Lire jusqu'a la derniére ligne afin de trouver où reprendre la boucle
        for line in log:
            # print("ligne de log",nbline,":",line)
            cols = line.split(';')
            # print("ligne de log",nbline,":",cols)
            # Ne pas lire la première ligne (en-tête)
            if nbline != 0:
                # Récupérer les variables de boucles à partir de la colonne 'Boucle'
                bcld, bcla, bclt, bclc, idxcomm = [int(i) for i in cols[8].replace('\n', "").split('-')]
                # Si changement de département...
                if bcld != oldd:
                    # ...vider la liste des cc
                    listecc, refcc, refccnom = ([], [], [])
                    oldd = bcld
                # Si la cc n'est pas dans la liste...
                if cols[4] not in listecc:
                    # ... l'ajouter
                    listecc.append(cols[4])
                    refcc.append(cols[3])
            nbline += 1
        log.close()
        reprise = True
    else:
        # S'il n'existe pas le créer et écrire l'en-tête
        log = io.open('log.csv', 'w')
        log.write(u'IdCommunes;Nom_C;Dispo;IDGroupement;Nom_GC;Dispo;Boucle;Nbre_GC;Indice_GC\n')
        log.close()

    # Réouvrir le fichier de log afin de l'alimenter avec les nouvelles entrées
    log = io.open('log.csv', 'a')
    try:
        Nreprise = nbline
    except:
        Nreprise = 0

    # Ouverture du fichier csv d'écriture des liens communes - groupement de communes
    # FichierDest1=open("Lien-C-GC"+str(Annee)+"-"+str(date.today())+".csv", "w")
    FichierDest1 = open("Lien-C-GC" + str(Annee) + "-DepMin_Max" + str(DepMin) + "-" + str(DepMax) + "-Reprise" + str(
        Nreprise) + ".csv", "w")
    LinkC_GC = csv.writer(FichierDest1)

    Titre = ["Id C", "Id GC", "Nom C", "Nom GC", "Nbre GC", "Indice GC " + str(Annee)]
    LinkC_GC.writerow(Titre)

    # Ouverture des fichiers csv d'écriture des enregistrements scrapés et des urls incorrects
    # FichierDest1=open("Scraper-Data finance communes-"+str(Annee)+"-"+str(date.today())+".csv", "wb")
    FichierDest1 = open("Scraper-Data finance communes-" + str(Annee) + "-DepMin_Max" + str(DepMin) + "-" + str(
        DepMax) + "-Reprise" + str(Nreprise) + ".csv", "wb")
    FileVigie = csv.writer(FichierDest1)

    # FichierDest2=open("ScraperCom"+str(Annee)+"-communes_incorrectes"+str(date.today())+".csv", "wb")
    FichierDest2 = open("ScraperCom-communes incorrectes" + str(Annee) + "-DepMin_Max" + str(DepMin) + "-" + str(
        DepMax) + "-Reprise" + str(Nreprise) + ".csv", "wb")
    Fileurldef = csv.writer(FichierDest2)

    # Lancer Chrome et ouvrir le site
    page = open_main_page(url)

    # Imprimer la liste des départements
    # for i in range(len(getdep(page).options)):
    #    print(getdep(page).options[i].text)
    # print("nbre depts",len(getdep(page).options) )

    # Boucle départements
    Dep0 = max(bcld, DepMin)
    Dep1 = min(len(getdep(page).options), DepMax)
    print("bcld", bcld, "DepMin", DepMin, "Dep0", Dep0, "len(getdep(page).options)", len(getdep(page).options),
          "DepMax", DepMax, "Dep1", Dep1)
    for d in range(Dep0, Dep1):
        # Selection et page du département
        print("Num Dep", d)
        print("getdep(page)", getdep(page), type(getdep(page)))
        try:
            getdep(page).select_by_index(d)
        except:
            print("erreur recherche commune", page, d)
        print("d=", d)
        print("page", page)
        # Click sur OK
        page.find_element_by_name('_eventId_validercommunesetgroupts').click()
        # Log du département
        nodep = page.find_element_by_xpath(dbox + '[1]/tbody/tr[1]/td[1]/p').text
        nodep = nodep.split(' ')[0]
        print("nodep", nodep, "bcla", bcla, "bclmax", len(getalpha(page)))
        # Remise à zéro de la liste des cc
        listecc = []
        refcc = []
        # Boucle alphabétique
        for a in range(bcla, len(getalpha(page))):
            try:
                lkalpha = getalpha(page)[a]
                alpha = lkalpha.text
                lkalpha.click()
            except:
                print("erreur", bcla, len(getalpha(page)))

            # Boucle des communes
            boucle_commune(page)
        bcla = 0
        # retour aux départements
        page.find_element_by_xpath('//*[@id="formulaire"]/div[2]/a[1]').click()

    log.close()
