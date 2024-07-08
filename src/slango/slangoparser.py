# standard
import re
import pathlib

from dataclasses import dataclass, field
from itertools import combinations, chain

# parsing
from lxml import etree


SHOULD_RENDER_RICHTEXT = False


def paragraph_text_to_representation(paragraph_text):
    """Transform textual format into coded representation"""
    if paragraph_text.startswith("§ "):
        paragraph_text = paragraph_text[2:]
    try:
        if any(x in paragraph_text for x in "abcdefghijklmnopqrstuvwxyz"):
            return f"{int(paragraph_text[:-1]):03d}{paragraph_text[-1]}"
        return f"{int(paragraph_text):03d}"
    except ValueError:
        return paragraph_text


def test_paragraph_text_to_paragraph_representation():
    p = ["§ 17c", "90"]
    n = [paragraph_text_to_representation(x) for x in p]
    assert n == ["017c", "090"]


def get_refs_from_text(text, allpars):
    """Search the text for occurrences of § and get the referenced paragraphs"""

    # find the single refs
    single_refs = re.findall("(?<!§)§(?!§) [0-9a-z]*", text)
    single_refs = set([paragraph_text_to_representation(ref) for ref in single_refs])

    # find the double refs
    doubled_refs = []
    matches = re.search("(§§ ([0-9a-z]*) (und|oder|bis|,) ([0-9a-z]*))", text)

    if matches:
        first = paragraph_text_to_representation(matches.group(2))
        second = paragraph_text_to_representation(matches.group(4))

        if matches.group(3) == "bis":
            # we have a range
            doubled_refs = [k for k in sorted(allpars) if first <= k <= second]
        else:
            doubled_refs = [first, second]

    all_refs = single_refs.union(doubled_refs)
    return all_refs


def test_refs_from_text():
    t = "hallo § 17c and § 50. Paras §§ 16 bis 20c are here"
    refs = get_refs_from_text(t, "015 016 017 017c 018 019 020 021 040 050".split())
    assert refs == {"017c", "050", "016", "017", "018", "019", "020"}


def render_formatting_to_markdown(rich_text):
    """Render rich text containing simple tags to markdown like formatting"""

    if rich_text is None:
        return ""

    tag_to_surrounder = {
        "B": "**",
        "I": "*",
        "U": "__",
        "F": "$",
    }

    output = []
    for str_or_element in sequentialize_mixed_data(rich_text):
        if isinstance(str_or_element, str):
            output.append(str_or_element)
        else:
            # line break
            if str_or_element.tag == "BR":
                output.append("\n")
                continue
            # non-breaking space
            if str_or_element.tag == "NB":
                output.append(" ")
                continue

            if SHOULD_RENDER_RICHTEXT:
                surrounder = tag_to_surrounder.get(str_or_element.tag)

                if surrounder:
                    output.append(surrounder)

                output.append(render_formatting_to_markdown(str_or_element))

                if surrounder:
                    output.append(surrounder)
            else:
                output.append(render_formatting_to_markdown(str_or_element))

    return "".join(output)


@dataclass
class Revision:
    """
    I represent a Revision of a Law.

    """

    ident: str
    title: str
    subtitle: str

    def __repr__(self):
        return f"Rev({self.ident}, '{self.title}', '{self.subtitle}')"


def extract_revision(revision):
    """
    Gather identifier, title and subtitle of a revision into a Revision object

    A revision is a change in a law.

    """

    idents = revision.findall("Ident")
    if len(idents) not in [0, 1]:
        raise ValueError(f"more than one indent")

    titles = revision.findall("Title")
    if len(titles) not in [0, 1]:
        raise ValueError(f"more than one title")

    subtitles = revision.findall("Subtitle")
    if len(titles) not in [0, 1]:
        raise ValueError(f"more than one subtitle")

    ident = ""
    title = ""
    subtitle = ""

    if idents:
        ident = render_formatting_to_markdown(idents[0])
    if titles:
        title = render_formatting_to_markdown(titles[0])
    if subtitles:
        subtitle = render_formatting_to_markdown(subtitles[0])

    return Revision(ident, title, subtitle)


def extract(parent, tag_name):
    """
    Extract a tag from the parent with the given tag name and
    return its text contents if any.

    """
    content = parent.find(tag_name)
    if content is not None:
        if content.text is not None:
            return content.text.strip()
        else:
            """"""
    else:
        return None


def extract_all(obj, key):
    """
    Extract all elements of a tag from the parent
    and return their text contents if any.

    """
    elements = obj.findall(key)
    if elements:
        return [content.text.strip() for content in elements]
    else:
        return []


@dataclass(eq=True, frozen=True, repr=True, order=True)
class Origin:
    """
    I represent a reference to the original publication  where
    the corresponding law text was taken from.

    """

    periodical: str
    citation: str


def extract_fundstelle(metadaten):
    """
    Reify and coalesce citation sources from the meta data

    """
    fundstellen = []
    for fundstelle in metadaten.findall("fundstelle"):
        periodical = extract(fundstelle, "periodikum")
        citation = extract(fundstelle, "zitstelle")

        attachment = {}
        attachment_element = fundstelle.find("anlageabgabe")
        if attachment_element:
            attachment["attach_date"] = extract(attachment_element, "anlagedat")
            attachment["doc_place"] = extract(attachment_element, "dokst")
            attachment["emission_date"] = extract(attachment_element, "abgabedat")

        fundstellen.append(Origin(periodical=periodical, citation=citation))
    return fundstellen


def extract_standangabe(metadaten):
    """
    Extract status of document from metadata

    """
    standangaben = []
    for standangabe in metadaten.findall("standangabe"):
        standangaben.append(
            {
                "status_type": standangabe[0].text,
                "status_comment": standangabe[1].text,
            }
        )
    return standangaben


def sequentialize_mixed_data(element):
    """
    Get text and tags in the correct sequence from the
    element and return them in a list.

    """
    mix = []
    if element.text:
        mix.append(element.text)
    for child in element:
        mix.append(child)
        if child.tail:
            mix.append(child.tail)

    return mix


def extract_footnotes(container):
    """
    Get all the footnotes' contents from
    below the actual law -- so that we can embed them
    later on in the actual law text.

    """
    if container is None:
        return {}
    footnote_elements = container.findall("Footnote")
    footnotes = {fn.get("ID"): extract_structure(fn, {}) for fn in footnote_elements}
    return footnotes


@dataclass
class AddressedAtom:
    """
    I am a part of a paragraph, being individually addressable
    by my hierarchical address structure.

    """

    address: list[str]
    content: str
    references: set[str] = field(default_factory=set)

    def encode_address(
        self,
    ):
        if len(self.address) == 0:
            return ""

        output = ""
        for level in self.address:
            if isinstance(level, Revision):
                output += f"{level.ident}"
                continue
            if level and level.strip():
                output += level

        return output

    def clone(self):
        return AddressedAtom(self.address, self.content, self.references)

    def most_specific_address(self):
        return self.address[-1] if len(self.address) > 0 else ""

    def depth(self):
        return len(self.address)

    def get_ground_level(self):
        return self.address[0] if len(self.address) > 0 else "(0)"

    def encode_content(self):
        indent = "    " * self.depth()
        prefix = self.most_specific_address()
        content = self.content
        return f"{indent}{prefix} {content}"

    def __repr__(self):
        max_len_content = 66
        content_repr = (
            self.content
            if len(self.content) < max_len_content
            else self.content[: max_len_content - 1] + "[...]"
        )
        return f"【{' -> '.join(str(e) for e in self.address)} | {content_repr} | {self.references}】"


@dataclass
class Absatz:
    number: str
    contents: str
    references: set[str]


@dataclass
class Paragraph:
    """
    I represent a paragraph in a law text.

    """

    paragraph_number: str
    title: str
    contents: list = field(default=list)

    def __repr__(self):
        title_repr = " " + self.title if self.title else ""
        return f"§ {self.paragraph_number}{title_repr}"


@dataclass
class Law:
    """
    I represent a Law as encoded by a single file exported
    from GII platform.

    """

    juridical_short_names: list[str] = field(default_factory=list)
    official_short_name: list[str] = field(default_factory=list)
    heading: str = ""
    short_heading: str = ""
    origins: list[Origin] = field(default_factory=list)
    paragraphs: list[Paragraph] = field(default_factory=list)

    def __repr__(self):
        fav_short_name = (
            self.juridical_short_names[0]
            if len(self.juridical_short_names) > 0
            else "---"
        )
        return (
            f"Law({fav_short_name}"
            f' "{self.short_heading or self.heading}"'
            f" with {len(self.paragraphs)} paragraph(s))"
        )


def process_law_xml(xml_file: pathlib.PosixPath) -> Law:
    """
    Transform a xml representation of a law into an Law object.

    """
    law_tree = etree.parse(xml_file)
    dokumente = law_tree.getroot()
    norms = list(dokumente)  # Einzelnormen

    # work around the fact, that the DTD is underdefined
    # and does not model the law as an entity, so we have
    # to make sure that all annotations belonging to a law
    # that are actually attached to a norm are uplifted to
    # the law class.
    # We need to make sure, that this assumption is not
    # violated by having more than one law in a file etc.
    headings = set()
    short_headings = set()
    juridical_short_names = set()
    official_short_names = set()
    origins = set()

    law_corpus = []
    for norm in norms:
        metadaten = norm.find("metadaten")
        fragment = {}
        juridical_short_names_from_fragment = fragment["juridical_short_names"] = (
            extract_all(metadaten, "jurabk")
        )
        juridical_short_names.add(tuple(sorted(juridical_short_names_from_fragment)))

        official_short_name = fragment["official_short_name"] = extract(
            metadaten, "amtabk"
        )
        if official_short_name:
            official_short_names.add(official_short_name)

        fragment["heading"] = extract(metadaten, "langue")
        fragment["short_heading"] = extract(metadaten, "kurzue")

        if fragment["heading"]:
            headings.add(fragment["heading"])
        if fragment["short_heading"]:
            short_headings.add(fragment["short_heading"])

        fragment["preparation_date"] = extract(metadaten, "ausfertigung-datum")

        fragment["title"] = extract(metadaten, "titel")

        designation = extract(metadaten, "enbez")
        fragment["paragraph_number"] = (
            paragraph_text_to_representation(designation) if designation else None
        )
        fragment["place_of_origin"] = extract_fundstelle(metadaten)
        if fragment["place_of_origin"]:
            origins.add(tuple(sorted(fragment["place_of_origin"])))
        fragment["status_indicators"] = extract_standangabe(metadaten)

        fragment["outline_code"] = None
        fragment["outline_designation"] = None
        fragment["outline_title"] = None

        outline = metadaten.find("gliederungseinheit")
        if outline is not None:
            fragment["outline_code"] = extract(outline, "gliederungskennzahl")
            fragment["outline_designation"] = extract(outline, "gliederungsbez")
            fragment["outline_title"] = extract(outline, "gliederungstitel")

        fragment["law_content"] = []

        textdaten = norm.find("textdaten")
        if textdaten is not None:
            text = textdaten.find("text")
            if text is not None:
                # we have to incorporate the footnotes back into the text
                footnotes_container = text.find("Footnotes")
                footnotes = extract_footnotes(footnotes_container)

                content = text.find("Content")
                if content is not None:
                    fragment["law_content"] = extract_structure(content, footnotes)

        for law_atom in fragment["law_content"]:
            law_atom.references = get_refs_from_text(law_atom.content, [])

        law_corpus.append(fragment)

    # ensure only one group of origins exists
    if not (len(origins) == 1 or len(origins) == 0):
        raise ValueError(f"The law contains more than one origin {origins}")

    # ensure only one heading and subheading per law
    if not (len(headings) == 1 or len(headings) == 0):
        raise ValueError("The law contains more than one heading")
    if not (len(short_headings) == 1 or len(short_headings) == 0):
        raise ValueError("The law contains more than one short heading")

    law_heading = unpack_single_element(headings)
    law_short_heading = unpack_single_element(short_headings)

    for fragment in law_corpus:
        fragment["heading"] = law_heading
        fragment["short_heading"] = law_short_heading

    def only_allow_synonyms(sets):
        pairs = combinations(sets, 2)
        for left, right in pairs:
            if not set(left).intersection(set(right)):
                raise "Problem"

    # ensure only one tuple of juridical_short_name in law
    only_allow_synonyms(juridical_short_names)

    # build a list of all common synonyms from the collected
    # sets of synonyms
    condensed_short_names = list(sorted(set(chain(*juridical_short_names))))

    if not (len(official_short_names) == 1 or len(official_short_names) == 0):
        raise ValueError(
            f"The law contains more than one "
            f"official short name: {official_short_names}"
        )
    official_short_name = unpack_single_element(official_short_names)

    single_origin = unpack_single_element(list(origins))

    return Law(
        juridical_short_names=condensed_short_names,
        official_short_name=official_short_name,
        heading=law_heading,
        short_heading=law_short_heading,
        origins=single_origin,
        paragraphs=[
            Paragraph(
                title=norm_fragment["title"],
                paragraph_number=norm_fragment["paragraph_number"],
                contents=generate_absaetze(norm_fragment),
            )
            for norm_fragment in law_corpus
            if not (
                norm_fragment["title"] is None
                and norm_fragment["paragraph_number"] is None
            )
            and len(norm_fragment["law_content"]) != 0
        ],
    )


def generate_absaetze(norm_fragment):
    """
    Generate an Absatz object from sequence of AddressableAtoms

    """
    finalized_absaetze = []

    atoms = norm_fragment["law_content"]

    # make sure that we have at least absatz (0) always.
    first_atom_level = atoms[0].get_ground_level()
    if first_atom_level == "(0)":
        for atom in atoms:
            atom.address.insert(0, "(0)")

    last_absatz_nr = atoms[0].get_ground_level()
    accumulator = []

    def _create_absatz_from_accumulator_contents(
        absatz_nr,
        accumulator,
    ):
        """
        Use the accumulator to build a new Absatz object
        containing the actual text of the Absatz as well as
        all the references extracted from all AddressableAtoms.

        """
        atoms = _fuse_same_atoms(accumulator)
        return Absatz(
            absatz_nr,
            "\n".join(atom.encode_content() for atom in atoms),
            set(chain.from_iterable(atom.references for atom in atoms)),
        )

    def _fuse_same_atoms(atoms):
        current_atom = None

        fused_atoms = []
        for atom in atoms:
            if current_atom is None:
                current_atom = atom
                fused_atoms.append(current_atom)
                continue

            if current_atom.address == atom.address:
                current_atom.content = current_atom.content + " " + atom.content
                current_atom.references = current_atom.references.union(atom.references)
            else:
                current_atom = atom
                fused_atoms.append(current_atom)
        return fused_atoms

    current_absatz_nr = None

    for atom in atoms:
        current_absatz_nr = atom.get_ground_level()
        if current_absatz_nr == last_absatz_nr:
            accumulator.append(atom)
        else:
            finalized_absaetze.append(
                _create_absatz_from_accumulator_contents(last_absatz_nr, accumulator)
            )
            last_absatz_nr = current_absatz_nr
            accumulator = [atom]

    # we need to process all remaining contents of the accumulator
    # after we've gone through all the atoms
    if len(accumulator) != 0:
        finalized_absaetze.append(
            _create_absatz_from_accumulator_contents(current_absatz_nr, accumulator)
        )

    return finalized_absaetze


def unpack_single_element(container_set, replacement=None):
    """
    From a container that contains exactly one or none element,
    get the one element. If there's no element in the container,
    return the replacement instead (which is None by default).

    """
    if len(container_set) == 1:
        (element,) = list(container_set)
        return element
    return replacement


def extract_structure(content, footnotes, current_hierarchy=None):
    """
    Extract the textual elements from the content, but
    enhance the information with the outline knowledge available from
    the context of the current hierarchy.

    """
    current_hierarchy = [] if current_hierarchy is None else current_hierarchy

    mixed_bag = sequentialize_mixed_data(content)
    index = 0
    max_index = len(mixed_bag) - 1

    paragraphs = []

    while index <= max_index:
        item = mixed_bag[index]
        tag = getattr(item, "tag", None)
        if isinstance(item, str):
            if item and item.strip():
                content = item

                # remove the double numbering
                matches = re.match("^\\([ 0-9]*\\)", content)
                if matches:
                    absatz_designation = matches.group(0)
                    content = content[len(absatz_designation) :]

                paragraphs.append(AddressedAtom(current_hierarchy, content))

        elif tag in ["P"]:
            this_hierarchy = list(current_hierarchy)
            if item.text:
                matches = re.match("^\\([ 0-9]*\\)", item.text)
                if matches:
                    absatz_designation = matches.group(0)
                    this_hierarchy = this_hierarchy + [absatz_designation]

            sub_structure_content = extract_structure(
                item, footnotes, current_hierarchy=this_hierarchy
            )
            for subitem in sub_structure_content:
                paragraphs.append(subitem)

        # a bulleted, numbered or otherwise linear list
        elif tag == "DT":
            hierarchical_information = item.text

            # next item *must* be a DD
            index += 1
            next_item = mixed_bag[index]
            if getattr(next_item, "tag", None) != "DD":
                raise ValueError("Must be DD")
            sub_structure_content = extract_structure(
                next_item,
                footnotes,
                current_hierarchy=list(current_hierarchy) + [hierarchical_information],
            )
            for subitem in sub_structure_content:
                paragraphs.append(subitem)

        # footnote reference; we get the contents of the footnotes from
        # the actual footnotes we have already extracted
        elif tag in ["FnR"]:
            fn_reference = item.get("ID")
            fns = footnotes.get(fn_reference, None)

            if fns:
                for inline_fn in fns:
                    inline_fn = inline_fn.clone()
                    if len(paragraphs) > 0:
                        inline_fn.address = list(paragraphs[-1].address) + ["Fussnote"]
                    else:
                        inline_fn.address = ["Fussnote"]
                    if inline_fn is not None:
                        paragraphs.append(inline_fn)

        # for the moment, we just ignore formatting tags here
        elif tag in ["B", "I", "U", "F", "SP", "small", "SUP", "SUB", "NB"]:
            sub_structure_content = extract_structure(
                item, footnotes, current_hierarchy=list(current_hierarchy)
            )
            for subitem in sub_structure_content:
                paragraphs.append(subitem)

        # we ignore these tags as they are mostly just anemic wrappers
        elif tag in ["LA", "DL", "Content"]:
            sub_structure_content = extract_structure(
                item, footnotes, current_hierarchy=list(current_hierarchy)
            )
            for subitem in sub_structure_content:
                paragraphs.append(subitem)

        # this 'Revision' concept...
        elif tag == "Revision":
            revision = extract_revision(item)
            sub_structure_content = extract_structure(
                item, footnotes, current_hierarchy=list(current_hierarchy) + [revision]
            )
            for subitem in sub_structure_content:
                paragraphs.append(subitem)

        # and then the rest, e.g., probably tables
        else:
            sub_structure_content = extract_structure(
                item, footnotes, current_hierarchy=list(current_hierarchy)  # + [item]
            )
            for subitem in sub_structure_content:
                paragraphs.append(subitem)

        # next please!
        index += 1

    return paragraphs
