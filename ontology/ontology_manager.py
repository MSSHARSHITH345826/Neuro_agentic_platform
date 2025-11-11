# ontology/ontology_manager.py

from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import RDF, OWL

class OntologyManager:
    def __init__(self, ontology_path):
        self.graph = Graph()
        self.graph.parse(ontology_path)
        self.ns = Namespace("http://example.org/healthcare#")

    def get_classes(self):
        """Return all classes in the ontology."""
        return set(self.graph.subjects(RDF.type, OWL.Class))

    def get_individuals(self, class_name=None):
        """Return all individuals, or those of a given class."""
        if class_name:
            class_uri = self.ns[class_name]
            return set(self.graph.subjects(RDF.type, class_uri))
        else:
            return set(self.graph.subjects(RDF.type, OWL.NamedIndividual))

    def get_object_properties(self):
        """Return all object properties."""
        return set(self.graph.subjects(RDF.type, OWL.ObjectProperty))

    def get_individual_properties(self, individual_uri):
        """Return all predicates and objects for an individual."""
        return list(self.graph.predicate_objects(subject=individual_uri))

    def get_individual_by_name(self, name):
        uri = self.ns[name]
        if (uri, None, None) in self.graph:
            return uri
        return None
