from flask import Flask, render_template, request, flash, session, Markup, redirect, url_for
import cgi
import psycopg2

connect = psycopg2.connect(
    host = "ec2-18-210-64-223.compute-1.amazonaws.com",
    dbname = "d871o598hou16e",
    user = "ntvbkqtnpwzevj",
    password = "882d0df267e2ce38ec994997b52e1a0bff78d949d3c3ad15b1b1e138b1fc4e6a",
    port = "process.env.PORT || 5000")

class Film:
    def __init__(self, titel, karakteristika=None, årstal=None):
        self.titel = titel
        self.karakteristika = [karakteristika]
        self.årstal = årstal


# <editor-fold desc="DB connectect...">
cur = connect.cursor()

#
# script = ''' CREATE TABLE filmpostgres (
# titel varchar(40) NOT NULL,
# karakteristika varchar(1000),
# årstal int
# ) '''
# cur.execute(script)

# script2 = "INSERT INTO filmpostgres (titel, karakteristika) VALUES('Aladdin','3 wishes')"
# cur.execute(script2)
# # #
# cur.execute("select * from filpostgres")
# rows = cur.fetchall()
# print(f"{rows[2]}")






# cur.execute("""CREATE TABLE filmpostgres (titel text,karakteristika text,årstal integer)""")
# </editor-fold>

def insertFilm(film):
    try:
        if film.titel in getFilmByNameFetch(film.titel): # returner True hvis den kan finde en film i databases /SKAL TILFØJE ÅRSTAL HER ENGANG.
            print("halløj så findes den allerede i db")
    except TypeError:
        if isinstance(film.karakteristika, list):
            #for at sammensmeltes i een celle. Hvis der kun er én ting i listen, så sætter den intet kolon.
            if film.årstal != "":
                print("årstal er med, så jeg smider det ind")
                film.karakteristika = ";".join(film.karakteristika)
                with connect:
                    cur.execute("INSERT INTO filmpostgres VALUES(%s,%s,%s)", (film.titel, film.karakteristika, film.årstal,))
            else:
                print("årstal er IKKE med, så jeg smider bare titel og karkt ind")
                film.karakteristika = ";".join(film.karakteristika)
                with connect:
                    cur.execute("INSERT INTO filmpostgres VALUES(%s,%s)",
                                (film.titel, film.karakteristika,))

        else: #hvis det ikke er en liste, så tror jeg det gir problemer.
            print("indsat films karakteristika er ikke en liste.")
            print(film.karakteristika)

def getFilmByNameFetch(titel):
    cur.execute("SELECT * FROM filmpostgres WHERE titel=%s", (titel,)) #AND årstal=%s når der kommer flere film med samme navn
    return cur.fetchone() #Har skrevet fetchone i stedet for fetchall så den ikke skal søge hele databasen igennem, da filmen nok er unik

def fetchMovieNames():
    cur.execute("SELECT titel FROM filmpostgres")
    t = cur.fetchall()
    flat_list = [] # det her og nedenfor laver en liste med tupler om til en alm liste.
    for sublist in t:
        for item in sublist:
            flat_list.append(item)
    flat_list = sorted(flat_list)
    return flat_list

def altIDatabasenFetch():
    for row in cur.execute("select * from film"):
        print(row)

def bestemtFilmKaraktFetch(titel): #denne formular og den nedenunder gør det samme. Denne gør det bare ikke godt nok.
    cur.execute("SELECT karakteristika FROM filmpostgres WHERE titel=%s",(titel,))
    return list(cur.fetchone())

def traitsOfMovieFetch(titel): #her skal jeg også have årstal på, når der kommer flere film ind
    cur.execute("SELECT karakteristika FROM filmpostgres WHERE titel=%s",(titel,)) #AND årstal=%s når der kommer flere film med samme navn
    if titel:
        t = cur.fetchall()
        flat_list = []  # det her og nedenfor laver en liste med tupler om til en alm liste.
        for sublist in t:
            for item in sublist:
                flat_list.append(item)
        for n in flat_list:  # skulle lige have en klamme væk. Samme som [0]
            flat_list = n
        flat_list = flat_list.split(";")
        return flat_list
    else:
        return "no title in request.form"

def updateKrakteristika(titel,karakteristika): #den virker nok ikke for den ved jo ikke hvilken karakteristika der skal opdateres, hvis der er flere.
    with connect:
        cur.execute('UPDATE filmpostgres SET karakteristika = %s WHERE titel = %s',(karakteristika,titel,))
    print("karakt updateret")

def titelFromTraitFetch(karakteristika): #her skal jeg også have årstal på, når der kommer flere film ind
    cur.execute("SELECT titel FROM filmpostgres WHERE karakteristika ILIKE %(karakteristika)s", { 'karakteristika': '%{}%'.format(karakteristika)}) #AND årstal=%s når der kommer flere film med samme navn. LIKE '%'||?||'%' betyder ikke exact match.
    # "sci-fi;eventyr" er f.eks ikke exact match på "sci-fi". Så nu returner den alt der indeholder sci-fi. "sci-fi hvor hovedpersonen dør" er jo en ting som ik skal med, derfor skal jeg lave ekstra nedenfor for at sortere det væk.
    t = cur.fetchall()
    flat_list = [] # det her og nedenfor laver en liste med tupler om til en alm liste.
    for sublist in t:
        for item in sublist:
            flat_list.append(item)
    # Hertil ville man returne flatlist, men jeg skal lige sortere dem fra, som har mere end blot det, man leder efter i karkatieristika.
    sorted_list = []
    for y in flat_list:
        #---------------------#
        k = bestemtFilmKaraktFetch(y)[
            0]  # den her returnerer alle traitsne af en bestemt film, men vi skal lige have dem udpakket med split(";") hvis der er flere traits -.-
        if ";" in k:
            w = k.split(";")
            for line in w:
                if karakteristika.casefold() == line.casefold():
                    sorted_list.append(y)
        # ---------------------#
        # nedenfor siger bare, at hvis karakteristikaen findes NØJAGTIG i filmen, så skal være med.
        if karakteristika.casefold() == k.casefold():
            sorted_list.append(y)
    return sorted_list

def removeFilm(titel):
    with connect:
        cur.execute("DELETE FROM filmpostgres WHERE titel = %s",(titel,))
    print("movie removed")

def bindTraits(titel,traitToBeAppended):
    listeMedSemikolnner = bestemtFilmKaraktFetch(titel) #fetcher lige listen, men kun et [0] index: [;karakteristika;]
    listeMedKarakteristika = listeMedSemikolnner[0].split(";") #skal lige have det udpakket fra liste med ;semikolon
    # format til en liste med kommaer, der kan adskilles og arbejdes med. [0] er for at få listen udpakket, split er for at lave en ny liste
    toggle = True # den her skal bare sikre at vi kun tilføjer til databasen, hvis traitet ikke findes i forvejen.
    # Det er meget med vilje at det er gjort sådan her == items fordi det skal være muligt at tilføje ALT, medmindre det er HELT samme sætning
    for items in listeMedKarakteristika:
        if traitToBeAppended == items:
            print(f"karkteristika findes allerede på '{titel}': {listeMedKarakteristika}")
            toggle = False
    if toggle == True:
        # ovenstående er bare for at tjekke det ikke findes i forvejen. Nedenfor er det funktionen gør:
        print(f"Det findes ikke. Vi tilføjer.")
        if listeMedSemikolnner != [""]:  # hvis ikke listen er tom (hvis den er tom, skal der ikke semikolon med ind
            print("\nlisten er ikke tom, kan godt smide ind")
            listeMedSemikolnner.append(traitToBeAppended)
            samletliste = ";".join(listeMedSemikolnner) #denne laver det om til en string som kan komme ind i databasen
        else:
            print("listen tom, skal vel bare smide y ind")
            samletliste = traitToBeAppended
        updateKrakteristika(titel,samletliste)

def traitRemove(titel,traitToBeRemoved): #Skal huske, at den nok fjerner alle forekomster af strengen, så hvis der er en kort streng, så fjerner den det alle steder....
    streng1 = bestemtFilmKaraktFetch(titel)[0] #tager listen med alle karakterene og laver om til streng.
    traitToBeRemovedMedSemikolon = ";"+traitToBeRemoved

    if traitToBeRemovedMedSemikolon+";" in streng1: #her tjekker den lige om der er semikolon på begge sider.
        # Ellers må den nemlig kun fjerne, hvis det er det eneste trait i listen. Nej hvis der er to traits, eller det er den sidste i strengen, skal den også fjerne
        nyStreng = streng1.replace(traitToBeRemovedMedSemikolon, "")
        print(f"fjernertrait med semokolon: {nyStreng}")
    elif streng1.endswith(traitToBeRemovedMedSemikolon): #hvis det er den sidste streng i sætningen, skal den ikke tjekke om et semikolon findes til sidst.
        nyStreng = streng1.replace(traitToBeRemovedMedSemikolon, "")
        print(f"Det var den sidste trait i strengen. Nu er den fjernet: {nyStreng}")
    elif streng1.startswith(traitToBeRemoved+";"):  # hvis det er den første streng i sætningen, skal den ikke tjekke om et semikolon findes først.
        nyStreng = streng1.replace(traitToBeRemoved+";", "")
        print(f"Det var den første trait i strengen. Nu er den fjernet: {nyStreng}")
    else:
        if traitToBeRemoved == streng1: #Det her er fordi der findes ikke et semikolon, hvis bare der findes én trait. Så tjekker den lige om det er alt der er i strengen
            nyStreng = streng1.replace(traitToBeRemoved,"")
            print(f"fjerner trait uden semikolon: {nyStreng}")
        else:
            print("Traitet er forkert")

    # updateKrakteristika(titel,nyStreng) #hvis der er tildelt en ny streng, så kan vi indsætte den nye streng med traits i databasen i stedet for den gamle.
    # print("Trait deleted")

# print(titelFromTraitFetch("3 wishes"))
# removeFilm("Aladdin")

# bindTraits("Law Abiding Citizen","hej")
#
# cur.execute("SELECT titel FROM filmpostgres WHERE karakteristika LIKE '%Flyvende tæppe%'")
# print(cur.fetchall())
# #
#
# karakteristika = "flyvende tæppe"
#
# cur.execute("SELECT titel FROM filmpostgres WHERE karakteristika ILIKE %(karakteristika)s", { 'karakteristika': '%{}%'.format(karakteristika)})
# print(cur.fetchall())
# cur.execute("SELECT titel FROM filmpostgres WHERE karakteristika LIKE %s",(karakteristika,))

# print(traitsOfMovieFetch("Law Abiding Citizen"))

print(titelFromTraitFetch("hej"))

# print(getFilmByNameFetch('G.I.Joe'))

# removeFilm("G.I.Joe")
# print(getFilmByNameFetch("G.I.Joe"))
# insertFilm("G.I.Joe")
# fetchMovieNames() # virker heller ikke sgu da
# bestemtFilmKaraktFetch("G.I.Joe")


# inden publish:
# skal have lavet en footer, der giver kontaktoplysninger.
# call to action farver.
# eller
# Den skal kun vise de film, der har en anden film combined


# (optional, evt efter release) Tænk igennem hvordan Asger ville tilføje meget heri. Hvordan skal man kunne tilføje 1000 ting hurtigt?
# (optional evt efter release) den skal være flot med CSS
# (optional) bør nok lave noget med, at hvis man tilføjer en film, som allerede findes, så skal den sige, at den findes allerede. Du kan tilføje traitet til den ved at trykke her... (og så skal den jo loade værdierne...

# DONE:
# Den skal kunne combine (det laver jeg nok i aften)
#Jeg skal kunne bede asger indtaste hver gang han har 2 film der ligner hinanden på et underligt punkt... DET SKAL VÆRE LET FOR HAM AT INDTASTE BEGGE med mulighed for det i combine movie link tilbage med Trait=session.
# skal kunne søge i dropdowns
## Og hvis han overser den ene i dropdown og tilføjer, så skal den advare, eller bare appende (sådan tror jeg det var i forvejen)
# Den skal kunne appende nye traits...
# jeg kunne gøre så man kunne add/remove traits... Jeg kunne også gøre så der er mulighed for at reporte/flagge med det samme
# Under Thank you skal det være muligt at tilføje flere traits til session["movie"]







# module: web
app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])

def home():
    print("HEJ FOR FAEN DEN NYE")
    # if 'trait3' in session: # fjerner lige sessionen, fordi jeg bruger den midlertidigt til at smide ind i forms, så de ikke skal indtaste igen. Rent bord
    #     print("trait3 var i session og er nu fjernet")
    #     session.pop('trait3')
    #
    # if 'valgtTrait' in session:
    #     print("valgtTrait var i session og er nu fjernet")
    #     session.pop('valgtTrait')


    return render_template("index.html", fetchMovieNames=fetchMovieNames())







# 2 (select): vælg hvad du kan lide ved den specifikke film
@app.route("/select", methods=["GET", "POST"])
def select():
    if "movie" in request.form:
        global traits #simpelthen nødvendigt. Det er vist dårlig practise at bruge, men det virker for nu, og forstår ikke(det er jo ik sådan at jeg bruger trait et andet sted).
        session["film"] = request.form.get("movie")

    if "trait" in request.form:
        session["valgtTrait"] = request.form.get("trait")
        #kunne sikkert også have gavn af en session der gemte det vaglte trait
        flash(f"Følgende film i databasen, der passer med '{session['valgtTrait']}':","info")

        nyliste = titelFromTraitFetch(session['valgtTrait'])
        for x in nyliste:   #når x >1 så virker det ikke. Hvorfor?
            if x != "str(movie)":  # "den film der lige er valgt, som den har glemt fordi vi har opdateret til en ny side":
                flash(f"{x}", "info")
                print(f"{x}")
                # print(titelFromTraitFetch(trait)
                # print(f"session er {session['valgtTrait']} og x er filen: {x}")

        #ja, nedenstående er spaghettikode, for jeg kan ikke helt forklare hvad der foregår. Men
        urlfor = url_for('addMovies',type=session['valgtTrait'])
        flash(Markup("""<br><br><br>Mangler en film i listen? <a href={} class="alert-link">Tilføj den her</a> (skal også være muligt at tilføje en eksisterende film til traitet)""".format(urlfor)))

        if None in request.form:
            print("x")

    traits = traitsOfMovieFetch(session["film"])  # returnerer alle traits, som bruges i dropdown listen og vises uanset hvad der er i request.form.

    return render_template("select.html", traits=traits)


# tilføj film til databasen
@app.route("/addMovie", methods=["GET", "POST"])
def addMovies():
    # formdata = request.args.get('type')
    #
    # print(f"animal er {formdata}")



    return render_template("addMovie.html",)

# bind Movie
@app.route("/bindMovie", methods=["GET", "POST"])
def bindMovies():#dette navn er misvisende, for funktionen tilføjer egentlig bare movies... Det er først i Thankyou at den binder movies

    if "search" in request.form:
        session['film'] = request.form.get("search") #tager session inde fra addmovie // jeg kan godt se, hvad der er galt. Det hjælper helt klart at fjerne det her. For den laver sessionen om



    search = request.form.get("search")
    årgang = request.form.get("årgang")
    trait3 = request.form.get("trait3")

    session["movie"] = search
    session["trait3"] = trait3


    if "addTrait" in request.form: # det her er fra /addTrait, at hvis man kommer derinde fra, så skal den lige tilføje traitet(det gøres altid på næste side af en grund)
        session["trait3"] = request.form.get("trait3")
        print(session['film'], session['trait3'])
        bindTraits(session['film'],session['trait3'])

    if "searchform" in request.form:
        if len(search) < 2:
            print("input er for kort. Det er jo meget fint, men den skal også blive på siden, så skal jeg ha gang i IF-statements i jinja.")
        else:
            tempMovie = Film(search, trait3, årgang) #har sat trait3 ind i klammer, tror det er med vilje, for ellers er det ikke en liste
            insertFilm(tempMovie)



    text = f"Kender du en anden film i listen, der passer denne beskrivelse: '{session['trait3']}'?"

    return render_template("bindMovie.html", text=text, fetchMovieNames=fetchMovieNames()) #fetchmovienames bruges til noget i html'en

#thankyou
@app.route("/thankyou", methods=["GET", "POST"])
def thankyou(): #skal have kombineret de 2 film fra BindMovie siden
    thankyoutext = Markup(f"<a href='/addTrait'>Tilføj endnu et trait til '{session['film']}'</a>")


    if "combine" in request.form:
        movie3 = request.form.get("movie3")
        bindTraits(movie3,session['trait3'])






    return render_template("thankyou.html", thankyoutext=thankyoutext,)



# report
@app.route("/report", methods=["GET", "POST"]) # MANGLER SGU LIGE AT LAVE FUNKTION TIL REPORT, IKKE BARE VISUALS
def report():
    global traits
    traits = traitsOfMovieFetch(session["film"])  # returnerer alle traits, som bruges i dropdown listen og vises uanset hvad der er i request.form.

    if "titleReport" in request.form:
        flash("Thank you for reporting this movie! We've removed it now","info")
        flash("To comment on your reporting, please contact me at rasmuskvejborg+report(at)gmail.com","info")
        removeFilm(session["film"])

    if "traitReport" in request.form:

        # hvorfor reagerer den ikke på nedenstående?
        reportedTrait = request.form.get("traitReportSelect")
        traitRemove(session["film"],reportedTrait)

        flash(Markup("""Thank you for reporting this trait. We've removed it now. To add a new trait to this movie <a href='/addTrait'>click here</a>............................................"""))
        flash("To comment on your reporting, please contact me at rasmuskvejborg+report(at)gmail.com", "info")

    return render_template("report.html", traits = traits)

# add trait to list
@app.route("/addTrait", methods=["GET", "POST"])
def addTrait():

    return render_template("addTrait.html")




if __name__ == "__main__":
    app.secret_key="lol"
    app.run(debug=True, use_reloader=False, port=8000) #use_reloader=False gør at ellers loader den 2 gange i debug mode (og så har vi balladen med at filmene er tilføjet een gang)


connect.commit() #til indsæt der skal bruges commit
cur.close()
connect.close()

