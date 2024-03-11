"""
REACS id format
---
ХХ	     класс
ХХ.Х	 подкласс
ХХ.ХХ	 группа
ХХ.ХХ.Х	 подгруппа
ХХ.ХХ.ХХ вид
"""

import csv
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
BUILD_DIR = Path(__file__).parent / "build"

skg_prefix = "sec-kg"
d3f_prefix = "d3f"
reacs_prefix = "reacs"

classifiername = f"{skg_prefix}:REACSClassifier"
sectionname = f"{reacs_prefix}:REACSSection"
classname = f"{reacs_prefix}:REACSClass"
subclassname = f"{reacs_prefix}:REACSSubClass"
groupname = f"{reacs_prefix}:REACSGroup"
subgroupname = f"{reacs_prefix}:REACSSubGroup"
speciesname = f"{reacs_prefix}:REACSSpecies"
             
subrel = f"{d3f_prefix}:has-parent" 
idrel = f"{reacs_prefix}:reacs-id"
namerel = f"{d3f_prefix}:name"
synrel = f"{skg_prefix}:aliases"

namedindividual = "owl:NamedIndividual"

entries = {}

def get_stix_and_misp(entry: dict) -> dict:
    result = {
        "stix": [],
        "misp": []
    }
    
    if "stix-name-en" in entry:
        for name in [e for e in entry['stix-name-en'].split(',')if e]:
            result['stix'].append({
                "name_en": name,
                "name_ru": entry['stix-name-ru'],
                "aliases_ru": entry['stix-name-syn-ru'].split(',') if entry['stix-name-syn-ru'] else []
            })
            
        for name in [x for x in entry['other-name-en'].split(',') if x]:
            result['misp'].append({
                "name_en": name,
                "name_ru": entry['other-name-ru']
            })

    return result

with open(DATA_DIR / 'manual_reacs_mapping.csv', 'r', encoding='utf-8') as fp: 
    reader = csv.DictReader(fp, delimiter=';')
    
    for row in reader:
        
        result = get_stix_and_misp(row)
        
        if row['letter'] not in entries:
            entries[row['letter']] = {
                'name': row['name'],
                'stix-equivalents': result['stix'],
                'misp-equivalents': result['misp'],
                'classes': {}
            }
        else:
            parts = row['id'].split('.')
            class_id = parts[0]
            match len(parts):
                case 1:
                    entries[row['letter']]['classes'][class_id] = {
                    'name': row['name'],
                    'id': row['id'],
                    'stix-equivalents': result['stix'],
                    'misp-equivalents': result['misp'],
                    'subclasses': {}
                }
                case 2:
                    if len(parts[1]) == 1:
                        subclass_id = parts[1]
                        entries[row['letter']]['classes'][class_id]['subclasses'][subclass_id] = {
                        'name': row['name'],
                        'id': row['id'],
                        'stix-equivalents': result['stix'],
                        'misp-equivalents': result['misp'],
                        'groups': {}   
                    }
                    else:
                        digits = [d for d in str(parts[1])]
                        subclass_id = digits[0]
                        group_id = parts[1]
                        entries[row['letter']]['classes'][class_id]['subclasses'][subclass_id]['groups'][group_id] = {
                        'name': row['name'],
                        'id': row['id'],
                        'stix-equivalents': result['stix'],
                        'misp-equivalents': result['misp'],
                        'subgroups': {}   
                    }
                case 3:
                    if len(parts[2]) == 1:
                        class_digits = [d for d in str(parts[1])]
                        subclass_id = class_digits[0]
                        group_id = parts[1]
                        group_digits = [d for d in str(parts[2])]
                        subgroup_id = group_digits[0]
                        entries[row['letter']]['classes'][class_id]['subclasses'][subclass_id]['groups'][group_id]['subgroups'][subgroup_id] = {
                        'name': row['name'],
                        'id': row['id'],
                        'stix-equivalents': result['stix'],
                        'misp-equivalents': result['misp'],
                        'spices': {}   
                    }
                    else:
                        class_digits = [d for d in str(parts[1])]
                        subclass_id = class_digits[0]
                        group_id = parts[1]
                        group_digits = [d for d in str(parts[2])]
                        subgroup_id = group_digits[0]
                        spice_id = parts[2]
                        entries[row['letter']]['classes'][class_id]['subclasses'][subclass_id]['groups'][group_id]['subgroups'][subgroup_id]['spices'][spice_id] = {
                        'name': row['name'],
                        'id': row['id'],
                        'stix-equivalents': result['stix'],
                        'misp-equivalents': result['misp'],
                    }
                case _:
                    raise Exception("Unexpected id format!")

with open(BUILD_DIR / "reacs_mappped.json", "w") as fp:
    json.dump(entries, fp)

triples = []

def handle_stix_misp(entry: dict, iri: str) -> list[str]:
    result = []
    for stix_entry in entry['stix-equivalents']:
        stix_iri = f"{skg_prefix}:stix-sector--{stix_entry['name_en'].replace(' ', '-')}"
        result.extend(
            [
                f"{stix_iri} a stix:IndustrySector ,",
                "\t\towl:NamedIndividual ;" ,
                f"\t{namerel} \"{stix_entry['name_en']}\"@en ,",
                f"\t\t\"{stix_entry['name_ru']}\"@ru ;",
                f"\towl:sameAs {iri} .",
                f"{iri} owl:sameAs {stix_iri} .",
            ]
        )
        
        for alias in stix_entry['aliases_ru']:
            result.append(f"{stix_iri} {synrel} \"{alias}\"@ru .")
    
    for misp_entry in entry['misp-equivalents']:
        misp_iri = f"{skg_prefix}:misp-sector--{misp_entry['name_en'].replace(' ', '-')}"
        result.extend(
            [
                f"{misp_iri} a {skg_prefix}:Industry ,",
                "\t\towl:NamedIndividual ;" ,
                f"\t{namerel} \"{misp_entry['name_en']}\"@en ,",
                f"\t\t\"{misp_entry['name_ru']}\"@ru ;",
                f"\towl:sameAs {iri} .",
                f"{iri} owl:sameAs {misp_iri} .",
            ]
        )

    return result


def handle_spice(entry: dict, parent_iri: str) -> list[str]:
    result = []
    iri = f'{reacs_prefix}:reacs-spice--{entry["id"]}'
    result.extend([
        f'{iri} a {speciesname} ,',
        f'\t\t{namedindividual} ;',
        f'\t{subrel} {parent_iri} ;',
        f'\t{idrel} "{entry["id"]}" ;',
        f'\t{namerel} "{entry["name"]}"@ru .'
    ])
    
    result.extend(handle_stix_misp(entry, iri))

    return result

def handle_subgroup(entry: dict, parent_iri: str) -> list[str]:
    result = []
    iri = f'{reacs_prefix}:reacs-subgroup--{entry["id"]}'
    result.extend([
        f'{iri} a {subgroupname} ,',
        f'\t\t{namedindividual} ;',
        f'\t{subrel} {parent_iri} ;',
        f'\t{idrel} "{entry["id"]}" ;',
        f'\t{namerel} "{entry["name"]}"@ru .'
    ])
    result.extend(handle_stix_misp(entry, iri))
    
    for subclass in entry['spices']:
        result.extend(handle_spice(entry['spices'][subclass], iri))
    return result

def handle_group(entry: dict, parent_iri: str) -> list[str]:
    result = []
    iri = f'{reacs_prefix}:reacs-group--{entry["id"]}'
    result.extend([
        f'{iri} a {groupname} ,',
        f'\t\t{namedindividual} ;',
        f'\t{subrel} {parent_iri} ;',
        f'\t{idrel} "{entry["id"]}" ;',
        f'\t{namerel} "{entry["name"]}"@ru .'
    ])
    result.extend(handle_stix_misp(entry, iri))
    
    for subclass in entry['subgroups']:
        result.extend(handle_subgroup(entry['subgroups'][subclass], iri))
    return result

def handle_subclass (entry: dict, parent_iri: str) -> list[str]:
    result = []
    iri = f'{reacs_prefix}:reacs-subclass--{entry["id"]}'
    result.extend([
        f'{iri} a {subclassname} ,',
        f'\t\t{namedindividual} ;',
        f'\t{subrel} {parent_iri} ;',
        f'\t{idrel} "{entry["id"]}" ;',
        f'\t{namerel} "{entry["name"]}"@ru .'
    ])
    result.extend(handle_stix_misp(entry, iri))
    
    for group in entry['groups']:
        result.extend(handle_group(entry['groups'][group], iri))
    return result

def handle_class(entry: dict, parent_iri: str) -> list[str]:
    result = []
    iri = f'{reacs_prefix}:reacs-class--{entry["id"]}'
    result.extend([
        f'{iri} a {classname} ,',
        f'\t\t{namedindividual} ;',
        f'\t{subrel} {parent_iri} ;',
        f'\t{idrel} "{entry["id"]}" ;',
        f'\t{namerel} "{entry["name"]}"@ru .'
    ])
    result.extend(handle_stix_misp(entry, iri))
    
    for subclass in entry['subclasses']:
        result.extend(handle_subclass(entry['subclasses'][subclass], iri))
    return result

for key in entries:
    category_name = entries[key]['name']
    iri = f'{reacs_prefix}:reacs-section--{key}'
    triples.extend(
        [        
            f'{iri} a {sectionname} ,',
            f'\t\t{namedindividual} ;',
            f'\t{namerel} "{entries[key]["name"]}"@ru .'
        ]
    )
    triples.extend(handle_stix_misp(entries[key], iri))
    for entry in entries[key]['classes']:
        triples.extend(handle_class(entries[key]['classes'][entry], iri))

header = f"""
@prefix reacs: <http://sec-kg.org/ontologies/reacs#> .
@prefix {d3f_prefix}: <http://d3fend.mitre.org/ontologies/d3fend.owl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix {skg_prefix}: <http://sec-kg.org/ontologies/sec-kg#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix stix: <http://docs.oasis-open.org/ns/cti/stix#> .


<http://sec-kg.org/ontologies/reacs> a owl:Ontology .

{classifiername} a owl:Class .
stix:IndustrySector a owl:Class .
{skg_prefix}:Industry a owl:Class .

{sectionname} a owl:Class ;
    rdfs:subClassOf {classifiername} .

{classname} a owl:Class ;
    rdfs:subClassOf {sectionname} .

{subclassname} a owl:Class ;
    rdfs:subClassOf {classname} .

{groupname} a owl:Class ;
    rdfs:subClassOf {subclassname} .

{subgroupname} a owl:Class ;
    rdfs:subClassOf {groupname} .

{speciesname} a owl:Class ;
    rdfs:subClassOf {subgroupname} .


{idrel}
  rdf:type owl:DatatypeProperty ;
  rdfs:range xsd:string ;
  rdfs:subPropertyOf owl:topDataProperty .
  
"""
         
with open(BUILD_DIR / 'reacs-ontology.ttl', 'w') as f:
    f.write(header)
    for line in triples:
        f.write(line)
        f.write('\n')
    