import os

for arquivo in os.listdir(os.path.dirname(__file__)):
    if arquivo.endswith((".png", ".jpg", ".jpeg", ".ico")):
        globals()[arquivo[:-4]] = arquivo
