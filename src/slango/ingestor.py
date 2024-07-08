from pathlib import Path
from pprint import pprint, pformat

from .ingestor import process_law_xml
from .database import get_database


def ingest_laws():
    mainpath = "/path/to/downloaded/files/"

    # different interesting laws:
    # interesting = "BJNR230200001.xml"
    # interesting = "BJNR0700A0024.xml"
    # interesting = "BJNR005910953.xml" # flurbereinigungsgesetz
    interesting = "BJNR195010004.xml"  # Aufenthaltsgesetz
    # interesting = "BJNR341300016.xml"  # footnotes
    # interesting = "test.xml"
    # interesting = "*.xml"

    xml_files = [p for p in Path(mainpath).glob(interesting)]
    print(f"xml_files: {xml_files}")

    print(f"PROCESSING FILES IN {mainpath}..")
    laws = []
    for xml_file in xml_files:  # [0:1000]:
        law = process_law_xml(xml_file)
        laws.append(law)
    neodb = get_database()
    for law in laws:
        # create the law node
        query = """
            // Create a Law node
            CREATE (law:Law {
            juridical_short_names: $juridical_short_names,
            official_short_name: $official_short_name,
            heading: $heading,
            short_heading: $short_heading
            })

            // Iterate over each paragraph and create a Paragraph node connected to the Law node
            WITH law, $paragraphs AS paragraphs
            UNWIND paragraphs AS paragraph_data
            CREATE (paragraph:Paragraph {
            paragraph_number: paragraph_data.paragraph_number,
            title: paragraph_data.title
            })
            CREATE (law)-[:HAS_PARAGRAPH]->(paragraph)

            // Iterate over each addressed_atom within the current paragraph and create AddressedAtom nodes connected to the Paragraph node
            WITH law, paragraph, paragraph_data.contents AS addressed_atoms
            UNWIND addressed_atoms AS atom_data
            CREATE (atom:AddressedAtom {
            address: atom_data.address,
            content: atom_data.content,
            references: atom_data.references
            })
            CREATE (paragraph)-[:HAS_ADDRESSED_ATOM]->(atom)
            """
        params = {
            "juridical_short_names": law.juridical_short_names,
            "official_short_name": law.official_short_name,
            "heading": law.heading,
            "short_heading": law.short_heading,
            "paragraphs": [
                {
                    "paragraph_number": paragraph.paragraph_number,
                    "title": paragraph.title,
                    "contents": [
                        {
                            "sentence_number": absatz.number,
                            "content": absatz.contents,
                            "references": list(absatz.references),
                        }
                        for absatz in paragraph.contents
                    ],
                }
                for paragraph in law.paragraphs
            ],
        }
        pprint(params)
        neodb.run_with_params(query, params=params)
