# Infrastructure (Membre C)

> Cahier des charges, §4 : ne pas exposer directement bases de données et PACS ; représenter les ports ouverts ;
> présenter les flux et la résolution des noms ; persistance, redémarrage reproductible, journalisation, secrets ;
> démontrer un refus d'accès et une reprise après redémarrage.

| Dossier | VM | Services | Ports ouverts |
|---|---|---|---|
| `vm1-proxy/` | VM1 · Entrée | Reverse proxy, HTTPS, pare-feu | 443 (80 → 443) depuis l'extérieur |
| `vm2-apps/` | VM2 · Applications | SIH, RIS, connecteur CDA, IAM | ports applicatifs, depuis VM1 uniquement |
| `vm3-data/` | VM3 · Données | Serveur FHIR, PostgreSQL, Orthanc (+ worklists) | 5432, 8080, 8042, 4242, depuis VM2 uniquement |
| `scripts/` | toutes | sauvegarde, restauration, règles ufw | – |

En développement, `docker-compose.yml` à la racine lance les services de données sur un seul PC.
Chaque dossier `vmX-…/` contiendra son propre `docker-compose.yml` pour le déploiement sur la VM correspondante.

Résolution des noms (proposition) : même fichier `/etc/hosts` sur les 3 VM
(`proxy.sih.local`, `apps.sih.local`, `data.sih.local`).

Versions à relever pour le rapport : `docker image ls` sur chaque VM (HAPI FHIR, Orthanc, PostgreSQL, proxy, IAM).
