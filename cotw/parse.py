import sys
from pathlib import Path
from cotw import adf, sarc

def main():  
  type = sys.argv[1]
  filename = sys.argv[2]
  if type == "adf":
    adf.load_adf(Path.cwd() / filename)
  elif type == "gdcc":
    adf.load_global_gdcc(Path.cwd() / filename)
  elif type == "sarc":
    sarc.load_sarc(Path().cwd() / filename)