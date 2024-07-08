question_template = """\
Ich habe die folgende rechtliche Frage und möchte die relevanten Gesetze finden, die ich zur Klärung der rechtlichen Situation heranziehen könnte: "Ich lebe in Niedersachsen. {actual_question}" Gib mir eine Liste der Namen der Gesetze sowie jeweils deren Abkürzung als Strings in JSON. Hierbei ist beim Schlüssel "name" der Name des Gesetzes und unter dem Schlüssel "abbrevation" die Abkürzung des Gesetzes abgelegt. Gib mir bitte nur diese Liste. Ich benötige keine weiteren Erklärungen."""


data = [
    {
        "question": "Die Bäume meines Nachbarn ragen in mein Grundstück. Auf einigen der Bäume wachsen Äpfel. Darf ich die Äpfel pflücken, die an den Ästen wachen, die in mein Grundstück ragen?",
        "answers": [
            {"name": "Bürgerliches Gesetzbuch", "abbreviation": "BGB"},
            {
                "name": "Niedersächsisches Nachbarrechtsgesetz",
                "abbreviation": "NNachbG",
            },
        ],
    },
    {
        "question": "Mein Vermiter möchte meine Wohnung anschauen, aber ich habe keine Lust auf Besuch. Muss ich ihn reinlassen? ",
        "answers": [
            {"name": "Bürgerliches Gesetzbuch", "abbreviation": "BGB"},
            {"name": "Mietrechtsänderungsgesetz", "abbreviation": "MietRÄndG"},
            {"name": "Niedersächsisches Mietrecht", "abbreviation": "NMietR"},
        ],
    },
    {
        "question": "Muss ich die Reparaturkosten für meine Mietwohnung übernehmen, wenn ich den Schaden nicht verursacht habe und der Vermieter die Wohnung nicht ordnungsgemäß instand gehalten hat?",
        "answers": [
            {"name": "Bürgerliches Gesetzbuch", "abbreviation": "BGB"},
            {"name": "Mietrechtsreformgesetz", "abbreviation": "MietRRefG"},
            {
                "name": "Niedersächsisches Wohnraumförderungsgesetz",
                "abbreviation": "NWoFG",
            },
        ],
    },
    {
        "question": "Mein Nachbar spielt jede Nacht laut Musik und stört meine Ruhe. Kann ich ihn wegen Lärmbelästigung verklagen?",
        "answers": [
            {"name": "Bürgerliches Gesetzbuch", "abbreviation": "BGB"},
            {
                "name": "Niedersächsisches Ländliches Raumordnungsgesetz",
                "abbreviation": "NLROG",
            },
            {
                "name": "Niedersächsisches Immissionsschutzgesetz",
                "abbreviation": "NImschG",
            },
            {"name": "Bundes-Immissionsschutzgesetz", "abbreviation": "BImSchG"},
        ],
    },
    {
        "question": "Ich war in einen Autounfall verwickelt und die Versicherung des anderen Beteiligten bietet mir eine Entschädigung an. Muss ich ihr Angebot annehmen oder kann ich um ein höheres Entgelt verhandeln?",
        "answers": [
            {"name": "Bürgerliches Gesetzbuch", "abbreviation": "BGB"},
            {"name": "Straßenverkehrsgesetz", "abbreviation": "StVG"},
            {"name": "Pflichtversicherungsgesetz", "abbreviation": "PflVG"},
        ],
    },
    {
        "question": "Ich bin Freiberufler und mein Kunde weigert sich, mich für die geleistete Arbeit zu bezahlen. Kann ich ihn vor Gericht bringen, um mein Geld zu bekommen?",
        "answers": [
            {"name": "Bürgerliches Gesetzbuch", "abbreviation": "BGB"},
            {"name": "Zivilprozessordnung", "abbreviation": "ZPO"},
            {
                "name": "Gesetz über die Vergütung von Vorschüssen für Berufsträger",
                "abbreviation": "VorschussG",
            },
            {"name": "Gesetz gegen den unlauteren Wettbewerb", "abbreviation": "UWG"},
        ],
    },
    {
        "question": "Mein Arbeitgeber zwingt mich, Überstunden ohne Extrazahlung zu leisten. Ist das legal?",
        "answers": [
            {"name": "Bundesurlaubsgesetz", "abbreviation": "BUrlG"},
            {"name": "Arbeitszeitgesetz", "abbreviation": "ArbZG"},
            {"name": "Bürgerliches Gesetzbuch", "abbreviation": "BGB"},
            {"name": "Tarifvertragsgesetz", "abbreviation": "TVG"},
            {"name": "Mindestlohngesetz", "abbreviation": "MiLoG"},
        ],
    },
    {
        "question": "Darf ich ein Gespräch mit meinem Chef heimlich aufzeichnen, wenn ich mich belästigt fühle?",
        "answers": [
            {"name": "Bürgerliches Gesetzbuch", "abbreviation": "BGB"},
            {"name": "Telekommunikationsgesetz", "abbreviation": "TKG"},
            {"name": "Strafgesetzbuch", "abbreviation": "StGB"},
            {"name": "Niedersächsisches Datenschutzgesetz", "abbreviation": "NDSG"},
            {"name": "Bundesdatenschutzgesetz", "abbreviation": "BDSG"},
        ],
    },
    {
        "question": "Ich habe ein Produkt online gekauft, das sich als defekt herausgestellt hat. Kann ich es zurückgeben und eine volle Rückerstattung erhalten?",
        "answers": [
            {"name": "Bürgerliches Gesetzbuch", "abbreviation": "BGB"},
            {"name": "Verbraucherrechtsgesetz", "abbreviation": "VVG"},
            {"name": "Fernabsatzgesetz", "abbreviation": "FAG"},
        ],
    },
    {
        "question": "Mein Vermieter erhöht meine Miete um 20% ohne ordnungsgemäße Ankündigung. Ist das erlaubt?",
        "answers": [
            {"name": "Bürgerliches Gesetzbuch", "abbreviation": "BGB"},
            {"name": "Mietrechtsnovellierungsgesetz", "abbreviation": "MietNovG"},
            {
                "name": "Niedersächsisches Gesetz über das Mietrecht",
                "abbreviation": "NMietRdG",
            },
        ],
    },
    {
        "question": "Ich wurde in einem öffentlichen Raum verletzt, weil der Eigentümer des Grundstücks seine Sorgfaltspflicht verletzt hat. Kann ich ihn auf Schadenersatz verklagen?",
        "answers": [
            {"name": "Bürgerliches Gesetzbuch", "abbreviation": "BGB"},
            {"name": "Haftpflichtgesetz", "abbreviation": "HaftPflG"},
        ],
    },
    {
        "question": "Kann ich entlassen werden, wenn ich wegen einer Behinderung nicht arbeiten kann, selbst wenn ich viele Jahre bei dem Unternehmen beschäftigt war?",
        "answers": [
            {"name": "Sozialgesetzbuch Neuntes Buch", "abbreviation": "SGB IX"},
            {"name": "Bundesgleichstellungsgesetz", "abbreviation": "BGG"},
            {"name": "Allgemeines Gleichbehandlungsgesetz", "abbreviation": "AGG"},
            {"name": "Kündigungsschutzgesetz", "abbreviation": "KSchG"},
            {"name": "Bürgerliches Gesetzbuch", "abbreviation": "BGB"},
        ],
    },
    # Strafrecht:
    {
        "question": "Wenn ich versehentlich ein fremdes Fahrrad mitnehme und es mir nicht gehört, kann ich deswegen wegen Diebstahls angeklagt werden?",
        "answers": [
            {"name": "Strafgesetzbuch", "abbreviation": "StGB"},
            {"name": "Bürgerliches Gesetzbuch", "abbreviation": "BGB"},
        ],
    },
    {
        "question": "Ich habe in einer Bar eine Schlägerei provoziert und einer der Beteiligten wurde verletzt. Bin ich strafrechtlich für die Verletzung verantwortlich?",
        "answers": [
            {"name": "Strafgesetzbuch", "abbreviation": "StGB"},
            {"name": "Bürgerliches Gesetzbuch", "abbreviation": "BGB"},
        ],
    },
    {
        "question": "Mein Freund hat mir erzählt, dass er einen Drogenhandel plant. Wenn ich ihn nicht anzeige, kann ich deswegen strafrechtlich belangt werden?",
        "answers": [
            {"name": "Strafgesetzbuch", "abbreviation": "StGB"},
            {
                "name": "Gesetz über die Zusammenarbeit des Bundes und der Länder in Angelegenheiten des Verfassungsschutzes und über die Errichtung eines Bundesamtes für Verfassungsschutz",
                "abbreviation": "BVerfSchG",
            },
        ],
    },
    # Steuern
    {
        "question": "Ich habe im Ausland Einkünfte erzielt, muss ich diese in Deutschland versteuern, auch wenn ich sie bereits im Ausland versteuert habe?",
        "answers": [
            {"name": "Einkommensteuergesetz", "abbreviation": "EStG"},
            {"name": "Außensteuergesetz", "abbreviation": "AStG"},
            {"name": "Deutschland-Doppelbesteuerungsabkommen", "abbreviation": "DBA"},
            {"name": "Bundesgesetzblatt", "abbreviation": "BGBl"},
        ],
    },
    {
        "question": "Kann ich meine Ausgaben für eine Home-Office-Arbeitsplatz als Betriebsausgaben absetzen, wenn ich nur teilweise von zu Hause aus arbeite?",
        "answers": [
            {"name": "Einkommensteuergesetz", "abbreviation": "EStG"},
            {"name": "Abgabenordnung", "abbreviation": "AO"},
            {"name": "Bundesfinanzhof", "abbreviation": "BFH"},
        ],
    },
    {
        "question": "Ich habe eine Erbschaft erhalten und muss Steuern darauf zahlen. Kann ich die Steuern auf die Erbschaft von den Erträgen der Erbschaft selbst bezahlen oder muss ich sie aus meinem eigenen Vermögen zahlen?",
        "answers": [
            {"name": "Erbschaftsteuergesetz", "abbreviation": "ErbStG"},
            {"name": "Bürgerliches Gesetzbuch", "abbreviation": "BGB"},
            {"name": "Abgabenordnung", "abbreviation": "AO"},
            {"name": "Einkommensteuergesetz", "abbreviation": "EStG"},
        ],
    },
    # Verkehr
    {
        "question": "Ich bin als Fahranfänger innerhalb der Probezeit mit 31 km/h zu schnell gefahren. Verliere ich meinen Führerschein, wenn ich bereits einen Punkte in Flensburg habe?",
        "answers": [
            {"name": "Straßenverkehrsgesetz", "abbreviation": "StVG"},
            {"name": "Fahrerlaubnis-Verordnung", "abbreviation": "FeV"},
            {"name": "Bundeszentralregistergesetz", "abbreviation": "BZRG"},
        ],
    },
    {
        "question": "Ich habe ein falsches Parkticket erhalten, weil die Parkuhr defekt war. Kann ich mich erfolgreich gegen das Ticket wehren, wenn ich Beweise dafür habe?",
        "answers": [
            {"name": "Straßenverkehrsgesetz", "abbreviation": "StVG"},
            {"name": "Bundesfernstraßengesetz", "abbreviation": "FStrG"},
            {"name": "Niedersächsisches Straßengesetz", "abbreviation": "NStrG"},
            {"name": "Verwaltungsverfahrensgesetz", "abbreviation": "VwVfG"},
            {"name": "OwVG Niedersachsen", "abbreviation": "OwVG ND"},
        ],
    },
    {
        "question": "Ich bin als Beifahrer in einem Fahrzeug mitgewesen, das ohne Versicherung unterwegs war. Bin ich strafrechtlich verantwortlich, wenn ich wusste, dass das Fahrzeug nicht versichert war?",
        "answers": [
            {"name": "Strafgesetzbuch", "abbreviation": "StGB"},
            {
                "name": "Gesetz über die Pflichtversicherung für Kraftfahrzeuge",
                "abbreviation": "PflVG",
            },
            {"name": "Straßenverkehrsgesetz", "abbreviation": "StVG"},
            {
                "name": "Niedersächsisches Straßen- und Weggesetz",
                "abbreviation": "NStrWG",
            },
        ],
    },
]
