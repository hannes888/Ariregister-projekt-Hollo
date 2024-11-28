### How to run
Rakenduse käivitamiseks on vajalikud järgnevad sammud:
 - Veenduge, et teil on alla laetud Docker Desktop (https://www.docker.com/products/docker-desktop/) või manuaalselt seadistatud Docker Engine ja Docker Compose
 - Liikuge terminalis projektikausta
 - Veenduge, et pordid 5000 ja 5432 on vabad (või muutke vastavalt docker-compose.yml failis)
 - Terminalis `docker-compose up --build`\
Rakenduse käivitamisel luuakse automaatselt andmebaas ja lisatakse sinna algandmed füüsiliste ja juriidiliste isikute kohta.\
Rakendus on kättesaadav aadressil http://localhost:5000/ (kui te pole muutnud porti docker-compose.yml failis)