from flask import Flask, render_template
import requests

from flask import request, jsonify

app = Flask(__name__)

def get_readable_name(uri):
    name = uri.split('/')[-1].replace('_', ' ')
    if name.startswith('Season '):
        return int(name.split(' ')[-1]), name  # Return tuple for numeric sorting of seasons
    return name

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/add_monster', methods=['POST'])
def add_monster():
    monster_data = request.get_json()
    result = add_monster_to_ontology(monster_data)
    return result

def add_monster_to_ontology(monster_data):
    query_prefix = """
    PREFIX ns: <http://rpcw.di.uminho.pt/2024/2024/5/untitled-ontology-28/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    """

    # Prepare URIs for strengths and weaknesses
    strengths = [f'ns:hasStrength ns:{strength.replace(" ", "_")}' for strength in monster_data.get('strengths', [])]
    weaknesses = [f'ns:hasWeakness ns:{weakness.replace(" ", "_")}' for weakness in monster_data.get('weaknesses', [])]

    # Ensure that each property is terminated correctly with a semicolon
    properties = strengths + weaknesses
    properties_string = ";\n        ".join(properties) + (";" if properties else "")

    # Forming the SPARQL query to insert data
    query_insert = f"""
    INSERT DATA {{
        <http://rpcw.di.uminho.pt/2024/2024/5/untitled-ontology-28/{monster_data['name'].replace(' ', '_')}> a ns:Monster,
            owl:NamedIndividual ;
        ns:description "{monster_data['description']}"^^xsd:string ;
        ns:origin "{monster_data['origin']}"^^xsd:string ;
        {properties_string}
        ns:killing "{monster_data['killing']}"^^xsd:string .
    }}
    """

    headers = {
        "Content-Type": "application/sparql-update"
    }

    response = requests.post('http://localhost:7200/repositories/supernatural2/statements', data=query_prefix + query_insert, headers=headers)
    if response.status_code == 200:
        return jsonify({'message': 'Monster added successfully'}), 200
    else:
        return jsonify({'message': 'Failed to add monster', 'error': response.text}), response.status_code


@app.route('/monsters')
def monsters():
    query = """
    PREFIX ns: <http://rpcw.di.uminho.pt/2024/2024/5/untitled-ontology-28/>
    SELECT DISTINCT ?monster
    WHERE {{
      ?monster a ns:Monster .
    }}
    """
    headers = {
        "Accept": "application/sparql-results+json"
    }
    response = requests.post('http://localhost:7200/repositories/supernatural2', data={'query': query}, headers=headers)
    monsters = [{'name': get_readable_name(monster['monster']['value'])[1] if isinstance(get_readable_name(monster['monster']['value']), tuple) else get_readable_name(monster['monster']['value']), 'uri': monster['monster']['value']} for monster in response.json()['results']['bindings']]
    monsters.sort(key=lambda x: x['name'])  # Alphabetical sorting
    return render_template('monsters.html', monsters=monsters)

@app.route('/monster/<path:uri>')
def monster(uri):
    query = f"""
    PREFIX ns: <http://rpcw.di.uminho.pt/2024/2024/5/untitled-ontology-28/>
    SELECT ?property ?value
    WHERE {{
      <{uri}> ?property ?value .
    }}
    """
    headers = {
        "Accept": "application/sparql-results+json"
    }
    response = requests.post('http://localhost:7200/repositories/supernatural2', data={'query': query}, headers=headers)
    details = response.json()['results']['bindings']
    processed_details = {
        'strengths': [],
        'weaknesses': [],
        'seasons': [],
        'description': '',
        'origin': '',
        'killing': ''
    }
    for detail in details:
        prop = detail['property']['value'].split('/')[-1]
        if 'hasStrength' in prop:
            strength_uri = detail['value']['value']
            strength_name = get_readable_name(strength_uri)[1] if isinstance(get_readable_name(strength_uri), tuple) else get_readable_name(strength_uri)
            processed_details['strengths'].append({'name': strength_name, 'uri': strength_uri})
        elif 'hasWeakness' in prop:
            weakness_uri = detail['value']['value']
            weakness_name = get_readable_name(weakness_uri)[1] if isinstance(get_readable_name(weakness_uri), tuple) else get_readable_name(weakness_uri)
            processed_details['weaknesses'].append({'name': weakness_name, 'uri': weakness_uri})
        elif 'hasSeason' in prop:
            val = get_readable_name(detail['value']['value'])
            if isinstance(val, tuple):
                processed_details['seasons'].append(val[0])  # Append only the season number
            else:
                processed_details['seasons'].append(val)  # Fallback if not a tuple
        elif 'description' in prop:
            processed_details['description'] = detail['value']['value']
        elif 'origin' in prop:
            processed_details['origin'] = detail['value']['value']
        elif 'killing' in prop:
            processed_details['killing'] = detail['value']['value']
    
    processed_details['strengths'].sort(key=lambda x: x['name'])
    processed_details['weaknesses'].sort(key=lambda x: x['name'])
    processed_details['seasons'].sort()  # Sort by season number
    name = get_readable_name(uri)[1] if isinstance(get_readable_name(uri), tuple) else get_readable_name(uri)
    
    return render_template('monster.html', name=name, details=processed_details)


@app.route('/seasons')
def seasons():
    query = """
    PREFIX ns: <http://rpcw.di.uminho.pt/2024/2024/5/untitled-ontology-28/>
    SELECT ?season ?rating
    WHERE {
      ?season a ns:Season .
      ?season ns:rating ?rating .
    }
    """
    headers = {
        "Accept": "application/sparql-results+json"
    }
    response = requests.post('http://localhost:7200/repositories/supernatural2', data={'query': query}, headers=headers)
    seasons = [{'name': get_readable_name(season['season']['value'])[1], 'uri': season['season']['value'], 'rating': season['rating']['value']} for season in response.json()['results']['bindings']]
    # Extract season number and sort by it
    seasons.sort(key=lambda x: int(x['name'].split(' ')[-1]))  
    return render_template('seasons.html', seasons=seasons)


@app.route('/season/<int:season_number>')
def season(season_number):
    # Original query for listing monsters
    query_monsters = f"""
    PREFIX ns: <http://rpcw.di.uminho.pt/2024/2024/5/untitled-ontology-28/>
    SELECT ?monster
    WHERE {{
      ?monster ns:hasSeason ns:Season_{season_number} .
    }}
    """
    headers = {"Accept": "application/sparql-results+json"}
    response = requests.post('http://localhost:7200/repositories/supernatural2', data={'query': query_monsters}, headers=headers)
    monsters = [{'name': get_readable_name(monster['monster']['value']), 'uri': monster['monster']['value']} for monster in response.json()['results']['bindings']]
    monsters.sort(key=lambda x: x['name'])
    total_monsters = len(monsters)  

    # New query for strengths and weaknesses counts
    query_stats = f"""
    PREFIX ns: <http://rpcw.di.uminho.pt/2024/2024/5/untitled-ontology-28/>
    SELECT ?strength ?weakness
    WHERE {{
      ?monster ns:hasSeason ns:Season_{season_number} ;
               ns:hasStrength ?strength ;
               ns:hasWeakness ?weakness .
    }}
    """
    response_stats = requests.post('http://localhost:7200/repositories/supernatural2', data={'query': query_stats}, headers=headers)
    results = response_stats.json()['results']['bindings']

    strengths_count = {}
    weaknesses_count = {}
    for result in results:
        strength_uri = result['strength']['value']
        weakness_uri = result['weakness']['value']
        
        strength_name = get_readable_name(strength_uri)
        weakness_name = get_readable_name(weakness_uri)

        if strength_name in strengths_count:
            strengths_count[strength_name] += 1
        else:
            strengths_count[strength_name] = 1

        if weakness_name in weaknesses_count:
            weaknesses_count[weakness_name] += 1
        else:
            weaknesses_count[weakness_name] = 1

    # Get top 5 strengths and weaknesses
    common_strengths = sorted(strengths_count.items(), key=lambda item: item[1], reverse=True)[:5]
    common_weaknesses = sorted(weaknesses_count.items(), key=lambda item: item[1], reverse=True)[:5]

    query_origin_killing = f"""
    PREFIX ns: <http://rpcw.di.uminho.pt/2024/2024/5/untitled-ontology-28/>
    SELECT ?origin (COUNT(?origin) as ?count_origin) ?killing (COUNT(?killing) as ?count_killing)
    WHERE {{
      ?monster ns:hasSeason ns:Season_{season_number} ;
               ns:origin ?origin ;
               ns:killing ?killing .
    }}
    GROUP BY ?origin ?killing
    ORDER BY DESC(?count_origin) DESC(?count_killing)
    LIMIT 1
    """

    response_ok = requests.post('http://localhost:7200/repositories/supernatural2', data={'query': query_origin_killing}, headers=headers)
    results_ok = response_ok.json()['results']['bindings']
    most_common_origin = results_ok[0]['origin']['value'] if results_ok else 'Unknown'
    most_common_killing = results_ok[0]['killing']['value'] if results_ok else 'Unknown'

    return render_template('season.html', season_number=season_number, monsters=monsters, total_monsters=total_monsters, common_strengths=common_strengths, common_weaknesses=common_weaknesses,most_common_origin=most_common_origin, most_common_killing=most_common_killing)

@app.route('/strengths')
def strengths():
    query = """
    PREFIX ns: <http://rpcw.di.uminho.pt/2024/2024/5/untitled-ontology-28/>
    SELECT ?strength
    WHERE {
      ?strength a ns:Strength .
    }
    """
    headers = {
        "Accept": "application/sparql-results+json"
    }
    response = requests.post('http://localhost:7200/repositories/supernatural2', data={'query': query}, headers=headers)
    strengths = [{'name': get_readable_name(strength['strength']['value']), 'uri': strength['strength']['value']} for strength in response.json()['results']['bindings']]
    strengths.sort(key=lambda x: x['name'])
    return render_template('strengths.html', strengths=strengths)

@app.route('/strength/<path:uri>')
def strength(uri):
    query = f"""
    PREFIX ns: <http://rpcw.di.uminho.pt/2024/2024/5/untitled-ontology-28/>
    SELECT ?monster
    WHERE {{
      ?monster ns:hasStrength <{uri}> .
    }}
    """
    headers = {
        "Accept": "application/sparql-results+json"
    }
    response = requests.post('http://localhost:7200/repositories/supernatural2', data={'query': query}, headers=headers)
    monsters = [{'name': get_readable_name(monster['monster']['value']), 'uri': monster['monster']['value']} for monster in response.json()['results']['bindings']]
    monsters.sort(key=lambda x: x['name'])
    name = get_readable_name(uri)
    return render_template('strength.html', name=name, monsters=monsters)

@app.route('/weaknesses')
def weaknesses():
    query = """
    PREFIX ns: <http://rpcw.di.uminho.pt/2024/2024/5/untitled-ontology-28/>
    SELECT ?weakness
    WHERE {
      ?weakness a ns:Weakness .
    }
    """
    headers = {
        "Accept": "application/sparql-results+json"
    }
    response = requests.post('http://localhost:7200/repositories/supernatural2', data={'query': query}, headers=headers)
    weaknesses = [{'name': get_readable_name(weakness['weakness']['value']), 'uri': weakness['weakness']['value']} for weakness in response.json()['results']['bindings']]
    weaknesses.sort(key=lambda x: x['name'])
    return render_template('weaknesses.html', weaknesses=weaknesses)

@app.route('/weakness/<path:uri>')
def weakness(uri):
    query = f"""
    PREFIX ns: <http://rpcw.di.uminho.pt/2024/2024/5/untitled-ontology-28/>
    SELECT ?monster
    WHERE {{
      ?monster ns:hasWeakness <{uri}> .
    }}
    """
    headers = {
        "Accept": "application/sparql-results+json"
    }
    response = requests.post('http://localhost:7200/repositories/supernatural2', data={'query': query}, headers=headers)
    monsters = [{'name': get_readable_name(monster['monster']['value']), 'uri': monster['monster']['value']} for monster in response.json()['results']['bindings']]
    monsters.sort(key=lambda x: x['name'])
    name = get_readable_name(uri)
    return render_template('weakness.html', name=name, monsters=monsters)


if __name__ == '__main__':
    app.run(debug=True)