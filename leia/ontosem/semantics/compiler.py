from leia.ontomem.lexicon import Lexicon, SemStruc
from leia.ontomem.ontology import Ontology
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.semantics.candidate import Candidate
from leia.ontosem.semantics.tmr import TMRInstance
from leia.ontosem.syntax.results import SenseMap, SynMap, Syntax, Word
from typing import Iterable, Union

import itertools


class SemanticCompiler(object):

    def __init__(self, config: OntoSemConfig, ontology: Ontology=None, lexicon: Lexicon=None):
        self.config = config
        self.memory = config.memory()

        self.ontology = ontology if ontology is not None else self.config.ontology()
        self.lexicon = lexicon if lexicon is not None else self.config.lexicon()
        self.properties = self.config.memory().properties

    def run(self, syntax: Syntax) -> Iterable[Candidate]:
        for candidate in self.expand_candidates(syntax.synmap):
            self.process_candidate(candidate)
            yield candidate

    def expand_candidates(self, synmap: SynMap) -> Iterable[Candidate]:
        return map(lambda senses: Candidate(self.memory, *senses), itertools.product(*synmap.words))

    def process_candidate(self, candidate: Candidate):
        # First, generate a TMR frame for each sense in the syn-mapping.
        list(self.generate_frames(candidate))

        # Next, bind all variables in the syn-mapping.
        self.bind_variables(candidate)

        # Now, populate each frame based on the contents of the syn-mapping.
        self.populate_frames(candidate)

        # Any relation to a null-sem frame can now be replaced by the frame that performed the null-sem.
        self.redirect_null_sem_relations(candidate)

        # Remove all null-sem frames.
        self.remove_null_sems(candidate)

        # Fix all inverses (reverse them so that none are present in the output).
        self.fix_inverses(candidate)

        # Build MP frames for each MP in each sense in the syn-mapping.
        self.build_mp_frames(candidate)

    def generate_frames(self, candidate: Candidate) -> Iterable[TMRInstance]:
        # Generates all frames needed for the TMR - the heads of the senses, and all refsems.
        # Each is bound in the candidate's index.

        for sense_map in candidate.senses:
            # Get the sense from the lexicon, and get its head concept
            sense = self.lexicon.sense(sense_map.sense)

            # Get the head concept, generate a frame, and resolve it (e.g., 0.HEAD).
            # Some senses don't have a HEAD.  (e.g., THE-ART1 which is empty, or FOR-PREP4, which only has vars and refsems).
            head = sense.semstruc.head()
            if head is not None:
                frame = candidate.basic_tmr.new_instance(head.concept)
                frame.resolutions.add(candidate.bind(sense_map.word.index, head, frame))
                yield frame

            # Get all of the subs, generate frames, and resolve them (e.g., 0.SUB.1)
            for sub in sense.semstruc.subs():
                frame = candidate.basic_tmr.new_instance(sub.concept)
                frame.resolutions.add(candidate.bind(sense_map.word.index, sub, frame))
                yield frame

            # Get all of the refsems, find their concepts, generate frames, and resolve them (e.g., 0.REFSEM.1)
            for refsem in sense.semstruc.refsems():
                head = refsem.semstruc.head()
                frame = candidate.basic_tmr.new_instance(head.concept)
                frame.resolutions.add(candidate.bind(sense_map.word.index, refsem, frame))
                yield frame

            # Get all properties for unbound variables, generate frames, and resolve them (e.g., 1.VAR.3.COLOR)
            # For the first such property, if there is no head (above), make it the head
            bound_variables = set(map(lambda i: i[0], filter(lambda i: i[1] is not None, sense_map.bindings.items())))
            for i, prop in enumerate(sense.semstruc.properties(bound_variables)):
                frame = candidate.basic_tmr.new_instance(prop.property)
                frame.resolutions.add(candidate.bind(sense_map.word.index, prop, frame))
                if i == 0 and head is None:
                    frame.resolutions.add(candidate.bind(sense_map.word.index, SemStruc.Head(), frame))
                yield frame

    def bind_variables(self, candidate: Candidate):
        # For each sense in the synmap, take all mapped variables, and index resolutions in the candidate.

        for sense_map in candidate.senses:
            frame = candidate.resolve(sense_map.word, SemStruc.Head())
            if frame is not None:
                frame.resolutions.add(candidate.bind(sense_map.word.index, SemStruc.Variable(0), frame))

            for k, v in sense_map.bindings.items():
                variable = int(k.replace("$VAR", ""))
                word = v

                if variable == 0:
                    continue

                if word is None:
                    continue

                frame = candidate.resolve(word, SemStruc.Head())
                if frame is None:
                    continue

                frame.resolutions.add(candidate.bind(sense_map.word.index, SemStruc.Variable(variable), frame))

    def populate_frames(self, candidate: Candidate):
        # Go through each sense mapping in binding count order (highest binding first), and populate the frames.
        for sense_map in candidate.words_by_binding_count():
            sense = self.lexicon.sense(sense_map.sense)
            bound_variables = set(map(lambda i: i[0], filter(lambda i: i[1] is not None, sense_map.bindings.items())))
            for element in sense.semstruc.elements(bound_variables):
                # Resolve the element to a frame; if it does not exist, skip it.  This happens for optional variables
                # that are not found in the sense mapping (e.g., a prepositional components).

                frame = candidate.resolve(sense_map.word.index, element)
                if frame is None:
                    continue

                self.populate_semantic_properties(frame, sense_map, element, candidate)

                if isinstance(element, SemStruc.Head) or isinstance(element, SemStruc.RefSem):
                    self.populate_syntactic_properties(frame, sense_map, element, candidate)

    def populate_semantic_properties(self, frame: TMRInstance, sense_map: SenseMap, element: Union[SemStruc.Head, SemStruc.Sub, SemStruc.RefSem, SemStruc.Variable], candidate: Candidate):
        # First, if the element is a refsem, use its head
        if isinstance(element, SemStruc.RefSem):
            element = element.semstruc.head()

        # Head, sub, and variable elements can now all be treated the same (and therefore, refsems now can be as well)
        # Loop through each property / filler in the content, adding it the frame.  Resolve variables or refsems as encountered.

        for k, v in element.properties():
            original_v = v                              # Keep a reference (used after resolving variables)

            if isinstance(v, dict) and "VALUE" in v:    # This is either a refsem or variable, pull it out
                v = v["VALUE"]

            # If the property is a lexical constraint, add it to the constraints, and continue
            if k == "SEM":
                candidate.add_constraint(frame, v, sense_map)
                continue
            if isinstance(element, SemStruc.Head) and element.concept == "SET" and k == "MEMBER-TYPE":
                # If the contents are a dict, these are constraints
                if isinstance(v, dict):
                    constraints = set()
                    if "SEM" in v: constraints.add(v["SEM"])
                    if "DEFAULT" in v: constraints.add(v["DEFAULT"])
                    candidate.add_constraint(frame, constraints, sense_map)
                    continue

            # Wrap the value in a list; there are three possible shapes the value can naturally take in the lexicon:
            # 1) A string; wrap it in a list
            # 2) A list whose property is of a certain subset (TIME, CARDINALITY); wrap it in a list
            # 3) Rarely, a list of elements (e.g., AND-CONJ8); keep them as a list (do not wrap), so they are individually assessed
            v_list = v
            if not isinstance(v_list, list):
                v_list = [v_list]
            if v_list[0] in SemStruc.IEQS or v_list[0] in SemStruc.MPS:
                v_list = [v_list]

            for v in v_list:

                # Resolve any refsems or variables
                if isinstance(v, str) and v.startswith("REFSEM"):
                    parts = v.split(".")
                    if len(parts) == 1:
                        v = candidate.resolve(sense_map.word.index, SemStruc.RefSem(int(v.replace("REFSEM", ""))))
                        v = v.id()
                    else:
                        # Create an unresolved link if the filler had dot notation
                        # Unresolved links look like: ~TMR.FRAME.123?PROPERTY
                        v = candidate.resolve(sense_map.word.index, SemStruc.RefSem(int(parts[0].replace("REFSEM", ""))))
                        v = "%s?%s" % (v.id(), parts[1])
                elif isinstance(v, str) and v.startswith("^$VAR"):
                    # If the variable can't be resolved, skip it; this is the case where optional variables are declared in
                    # the lexicon (such as prepositional attachments) and aren't found in the synmap.

                    parts = v.split(".")
                    v = parts[0]

                    v = candidate.resolve(sense_map.word.index, SemStruc.Variable(int(v.replace("^$VAR", ""))))
                    if v is None:
                        continue

                    # If the original value had a SEM field, add that as a constraint.
                    if isinstance(original_v, dict) and "SEM" in original_v:
                        candidate.add_constraint(v, original_v["SEM"], sense_map)

                    v = v.id()

                    # Create an unresolved link if the filler had dot notation
                    # Unresolved links look like: ~TMR.FRAME.123?PROPERTY
                    if len(parts) > 1:
                        v = "%s?%s" % (v, parts[1])

                elif isinstance(v, list):
                    v = self.resolve_embedded_semstruc(v, sense_map, candidate)

                elif k == "NULL-SEM" and v == "+":
                    # Replace the NULL-SEM marker with the word index that is null-semming
                    # This index is used later to change relations pointing to a null-semmed word to the word that null-semmed it
                    v = candidate.resolve(sense_map.word.index, SemStruc.Head())

                    # In the case where the sem-struc has no HEAD, use the first element instead
                    if v is None:
                        sense = self.lexicon.sense(sense_map.sense)
                        elements = sense.semstruc.elements()
                        if len(elements) > 0:
                            v = candidate.resolve(sense_map.word.index, elements[0])

                    # Assuming something has resolved, use that ID; otherwise, retain the "+" as a placeholder
                    # for an unknown value.
                    if v is not None:
                        v = v.id()
                    else:
                        v = "+"

                frame.add_filler(k, v)

    def resolve_embedded_semstruc(self, semstruc: list, sense_map: SenseMap, candidate: Candidate) -> list:
        # Some semstruc fillers have an embedded list that represents a comparator, meaning procedure, or other
        # programmatic element.  These lists can be arbitrarily complex.  Variables and refsems can be found in them
        # as arguments to the procedures, and must be resolved.  Further, these variables and refsems may refer
        # via dot notation to properties of the resolvable frame.  This method recursively inspects each element in
        # the list and resolves it if possible.  Any unresolvable variable or refsem is output as-is.

        results = []

        for e in semstruc:
            if isinstance(e, str) and e.startswith("^$VAR"):
                parts = e.split(".")
                resolved = candidate.resolve(sense_map.word.index, SemStruc.Variable(int(parts[0].replace("^$VAR", ""))))

                if resolved is None:
                    resolved = parts[0]
                else:
                    resolved = resolved.id()

                parts[0] = resolved

                if len(parts) == 1:
                    results.append(parts[0])
                else:
                    results.append("%s?%s" % (parts[0], parts[1]))

                continue
            if isinstance(e, str) and e.startswith("REFSEM"):
                parts = e.split(".")
                resolved = candidate.resolve(sense_map.word.index, SemStruc.RefSem(int(parts[0].replace("REFSEM", ""))))

                if resolved is None:
                    resolved = parts[0]
                else:
                    resolved = resolved.id()

                parts[0] = resolved

                if len(parts) == 1:
                    results.append(parts[0])
                else:
                    results.append("%s?%s" % (parts[0], parts[1]))

                continue
            if isinstance(e, list):
                results.append(self.resolve_embedded_semstruc(e, sense_map, candidate))
                continue
            results.append(e)

        return results

    def populate_syntactic_properties(self, frame: TMRInstance, sense_map: SenseMap, element: Union[SemStruc.Head, SemStruc.RefSem], candidate: Candidate):
        word = sense_map.word

        # If the frame is an event, and the head word is a past tense verb...
        if frame.concept.isa(self.ontology.concept("EVENT")) and "V" in word.pos and "PAST" in word.pos:
            frame.add_filler("TIME", ["<", "FIND-ANCHOR-TIME"])
        if frame.concept.isa(self.ontology.concept("EVENT")) and "V" in word.pos and "PRESENT" in word.pos:
            frame.add_filler("TIME", ["FIND-ANCHOR-TIME"])
        if frame.concept.isa(self.ontology.concept("EVENT")) and "V" in word.pos and "INFINITIVE" in word.pos:
            frame.add_filler("TIME", [">", "FIND-ANCHOR-TIME"])
        if "N" in word.pos and "PLURAL" in word.pos:
            frame.add_filler("CARDINALITY", [">", 1])

    def redirect_null_sem_relations(self, candidate: Candidate):
        # Find any frame with a relation to a null-semmed frame.
        # Update those relations to point to the frame that performed the null-sem.
        # In the case of multiple, select the first.
        # Ignore frames that null-sem themselves.

        # Find all of the null-semmed frames
        null_sem_frames = filter(lambda f: len(f.fillers("NULL-SEM")) > 0, candidate.basic_tmr.instances.values())

        # Now map each to the frame that null-semmed them; if there is none (or they null-semmed themselves), omit
        # them from the mapping.  If more than one valid frame null-semmed one, select the first.
        null_sem_replacements = dict()
        for frame in null_sem_frames:
            for responsible_frame in frame.values("NULL-SEM"):
                if responsible_frame == frame.id():
                    continue
                null_sem_replacements[frame.id()] = responsible_frame
                break

        # Now find each usage of one of the null-semmed frames, and replace it with the responsible frame.
        # Any frames that were null-semmed by themselves only will not be replaced here, but the relations to them
        # will be removed when the null-sems are removed.
        for frame in candidate.basic_tmr.instances.values():
            for k, v in list(frame.properties.items()):
                for filler in map(lambda x: x.value, v):
                    if not isinstance(filler, str) or filler not in null_sem_replacements.keys():
                        continue
                    replacement = null_sem_replacements[filler]
                    frame.remove_filler(k, filler)
                    frame.add_filler(k, replacement)

    def remove_null_sems(self, candidate: Candidate):
        # Any frame marked with NULL-SEM + is removed.
        for frame in list(candidate.basic_tmr.instances.values()):
            if len(frame.fillers("NULL-SEM")) > 0:
                candidate.basic_tmr.remove_instance(frame)

    def fix_inverses(self, candidate: Candidate):
        inverses = self.properties.inverses()

        for frame in candidate.basic_tmr.instances.values():
            for property in list(frame.properties.keys()):
                if property not in inverses or property == "RELATION":
                    continue
                for filler in frame.values(property):
                    if filler not in candidate.basic_tmr.instances:
                        continue
                    filler_frame = candidate.basic_tmr.instances[filler]

                    filler_frame.add_filler(inverses[property], frame.id())
                    frame.remove_filler(property, filler)

    def build_mp_frames(self, candidate: Candidate):
        # For each sense-map in the candidate, look for MEANING-PROCEDURES in the associated sense.  For each such
        # MP, make a new frame whose type is MEANING-PROCEDURE, with a NAME property for the MP type itself.  Attach
        # each variable to the VARIABLES field, but resolve any [VALUE "^$VAR#"] (recursively, if needed).

        for sense_map in candidate.senses:
            sense = self.lexicon.sense(sense_map.sense)

            for meaning_procedure in sense.meaning_procedures:
                mp_frame = candidate.basic_tmr.new_instance("MEANING-PROCEDURE")
                mp_frame.add_filler("NAME", meaning_procedure.name())

                parameters = self.resolve_embedded_mp_parameters(candidate, sense_map.word, meaning_procedure.parameters())
                for parameter in parameters:
                    mp_frame.add_filler("PARAMETERS", parameter)

    def resolve_embedded_mp_parameters(self, candidate: Candidate, word: Union[int, Word], parameters: list) -> Iterable:

        def resolve(identifier: str) -> Union[str, None]:
            if identifier.startswith("^$VAR"):
                return resolve_var(identifier)
            if identifier.startswith("REFSEM"):
                return resolve_ref(identifier)
            return identifier

        def resolve_var(var: str) -> Union[str, None]:
            parts = var.split(".")
            frame = candidate.resolve(word, SemStruc.Variable(int(parts[0].replace("^$VAR", ""))))

            if frame is None:
                return None
            elif len(parts) == 1:
                return frame.id()
            else:
                return "%s?%s" % (frame.id(), parts[1])

        def resolve_ref(ref: str) -> Union[str, None]:
            parts = ref.split(".")
            frame = candidate.resolve(word, SemStruc.RefSem(int(parts[0].replace("REFSEM", ""))))

            if frame is None:
                return None
            elif len(parts) == 1:
                return frame.id()
            else:
                return "%s?%s" % (frame.id(), parts[1])

        for parameter in parameters:
            if isinstance(parameter, list):
                if len(parameter) == 2 and parameter[0] == "VALUE":
                    yield resolve(parameter[1])
                else:
                    yield from self.resolve_embedded_mp_parameters(candidate, word, parameter)
            elif isinstance(parameter, str):
                yield resolve(parameter)
            else:
                yield parameter
