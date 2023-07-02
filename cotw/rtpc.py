from deca.ff_rtpc import RtpcVisitorDumpToString, rtpc_from_binary, RtpcNode
from pathlib import Path
import json

def open_rtpc(filename: Path) -> RtpcNode:
  with filename.open("rb") as f:
    data = rtpc_from_binary(f) 
  root = data.root_node
  return root.child_table[0].child_table

def load_rtpc(filename: Path) -> None:
  data = filename.read_bytes()
  dump = RtpcVisitorDumpToString()
  dump.visit(data)
  parsed = dump.result()
  (Path.cwd() / f"{filename.name}.txt").write_text(parsed)  

def parse_animal_types() -> None:
  animals = open_rtpc(Path("global_animal_types.blo"))
  global_furs = {}
  for animal in animals:
    name = animal.prop_table[-11].data
    if type(name) == bytes:
      name = name.decode("utf-8")
    else:
      name = (animal.prop_table[-12].data).decode("utf-8")
    
    i = 0
    table_index = None
    max_i = len(animal.child_table)
    while not table_index and i < max_i:
      table_type = animal.child_table[i].prop_table[0].data
      if type(table_type) == bytes and table_type.decode("utf-8") == 'CAnimalTypeVisualVariationSettings':
        table_index = i
        break
      else:
        i = i + 1        
        
    fur_details = animal.child_table[table_index].child_table
    male_furs = []
    female_furs = []
    for fur in fur_details:
      fur_name = fur.prop_table[-1].data.decode("utf-8")
      if "great_one" in fur_name:
        continue
      
      gender = fur.prop_table[3].data
      if type(gender) == int:
        gender = "male" if gender == 1 else "female"
        if gender == "male":
          male_furs.append(fur_name)
        else:
          female_furs.append(fur_name)
      else:
        gender = "both"      
        male_furs.append(fur_name)
        female_furs.append(fur_name)        
          
    global_furs[name] = { "male_cnt": len(male_furs), "female_cnt": len(female_furs)}
    
  Path("global_furs.json").write_text(json.dumps(global_furs, indent=2))
  
    

if __name__ == "__main__":
  parse_animal_types()