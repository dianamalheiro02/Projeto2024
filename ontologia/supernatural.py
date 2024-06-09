import requests
from bs4 import BeautifulSoup
import json
import re

# Fetch the list of creatures
html_content = requests.get("https://supernatural.fandom.com/wiki/Category:Creatures").text
soup = BeautifulSoup(html_content, 'html.parser')
members=[]
members= soup.find_all("a",class_="category-page__member-link")
creatures = []
for member in members:
    #print(member.text)
    creatures.append(re.sub(r"\s+","_",member.text).strip())

# Dictionary to store creature data
creatures_dict = {}

# Function to parse individual creature pages
def parse_creature(creature):
    link = f"https://supernatural.fandom.com/wiki/{creature}"
    html_content = requests.get(link).text
    soup = BeautifulSoup(html_content, 'html.parser')

    data = {'strengths': [], 'weakness': [], 'seasons': []}
    parent = soup.find("div", class_= "mw-parser-output")
    elements = parent.find_all(['h2', 'ul'])

    parsing_weaknesses = False
    parsing_strengths = False

    for element in elements:
        if element.name == "h2":
            if "Weaknesses" in element.text:
                parsing_weaknesses = True
                parsing_strengths = False
            elif "Powers and Abilities" in element.text:
                parsing_strengths = True
                parsing_weaknesses = False
            else:
                parsing_weaknesses = False
                parsing_strengths = False

        if element.name == "ul":
            if parsing_weaknesses:
                for item in element.find_all("b"):
                    data['weakness'].append(item.text.strip())
            elif parsing_strengths:
                for item in element.find_all("b"):
                    data['strengths'].append(item.text.strip())
            elif 'Season' in element.text:
                for li in element.find_all("li"):
                    season_match = re.search(r"Season \d+", li.text)
                    if season_match and season_match.group() not in data['seasons']:
                        data['seasons'].append(season_match.group())

    return data

# Parse each creature and add to the dictionary
for creature in creatures:
    creatures_dict[creature] = parse_creature(creature)

# Print and save the dictionary to a JSON file
print(creatures_dict)
with open("supernatural.json", "w", encoding='utf-8') as f_out:
    json.dump(creatures_dict, f_out, indent=4, ensure_ascii=False)
