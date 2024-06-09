from rdflib import Graph, Namespace, URIRef, RDF, OWL, Literal, XSD
import json
from urllib.parse import quote

print("Started")

# Initialize graph
g = Graph()
ontology_file = "supernatural.ttl"  # This should be the path to your ontology file
g.parse(ontology_file, format="turtle") 

print("Got ontologia")

# Define namespaces
ns = Namespace("http://rpcw.di.uminho.pt/2024/2024/5/untitled-ontology-28/")
g.bind("ns", ns)
g.bind("owl", OWL)
g.bind("rdf", RDF)
g.bind("xsd", XSD)

# JSON data
with open("supernatural.json", 'r') as f:
    monsters_data = json.load(f)
    
# Load additional JSON data for monster properties
with open("origin.json", 'r') as f:
    additional_monsters_data = json.load(f)

ratings_json = """
{
    "Season_1": 8.2,
    "Season_2": 8.6,
    "Season_3": 8.5,
    "Season_4": 9.0,
    "Season_5": 8.8,
    "Season_6": 8.4,
    "Season_7": 8.4,
    "Season_8": 7.9,
    "Season_9": 8.2,
    "Season_10": 8.2,
    "Season_11": 8.5,
    "Season_12": 8.1,
    "Season_13": 8.4,
    "Season_14": 8.2,
    "Season_15": 8.0
}
"""

ratings_data = json.loads(ratings_json)

print("Got it all!")

# Define helper functions to create URIs
def create_uri(name):
    # Encode the name ensuring only necessary characters are encoded
    safe_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.,~()Ōō:;/\|[]'
    # Here we do not encode non-ASCII characters
    return URIRef(ns[quote(name.replace(" ", "_").replace("'", "_"),safe=safe_chars + ''.join(chr(i) for i in range(128, 256)))])

# Add data to graph
for monster, details in monsters_data.items():
    monster_uri = create_uri(monster)
    g.add((monster_uri, RDF.type, OWL.NamedIndividual))
    g.add((monster_uri, RDF.type, ns.Monster))

    # Add strengths
    for strength in details["strengths"]:
        strength_uri = create_uri(strength)
        g.add((strength_uri, RDF.type, OWL.NamedIndividual))
        g.add((strength_uri, RDF.type, ns.Strength))
        g.add((monster_uri, ns.hasStrength, strength_uri))
    
    # Add weaknesses
    for weakness in details["weakness"]:
        weakness_uri = create_uri(weakness)
        g.add((weakness_uri, RDF.type, OWL.NamedIndividual))
        g.add((weakness_uri, RDF.type, ns.Weakness))
        g.add((monster_uri, ns.hasWeakness, weakness_uri))
    
    # Add seasons
    for season in details["seasons"]:
        season_uri = create_uri(season)
        g.add((season_uri, RDF.type, OWL.NamedIndividual))
        g.add((season_uri, RDF.type, ns.Season))
        g.add((monster_uri, ns.hasSeason, season_uri))
        
    # Check and add additional properties if they exist in the additional data
    if monster in additional_monsters_data:
        #print(monster)
        additional_details = additional_monsters_data[monster]
        
        # Add origin
        if "Origin" in additional_details:
            g.add((monster_uri, ns.origin, Literal(additional_details["Origin"], datatype=XSD.string)))
        
        # Add killing method
        if "Killing" in additional_details:
            g.add((monster_uri, ns.killing, Literal(additional_details["Killing"], datatype=XSD.string)))
        
        # Add description
        if "Description" in additional_details:
            g.add((monster_uri, ns.description, Literal(additional_details["Description"], datatype=XSD.string)))

# Add ratings data
for season, rating in ratings_data.items():
    season_uri = create_uri(season)
    g.add((season_uri, RDF.type, OWL.NamedIndividual))
    g.add((season_uri, RDF.type, ns.Season))
    g.add((season_uri, ns.rating, Literal(rating, datatype=XSD.float)))

# Output the graph
output_file = 'output2.ttl'
g.serialize(destination=output_file, format="turtle")

print(f"Graph serialized to {output_file}")

# Print the number of triples in the graph
print(f"Number of triples: {len(g)}")
