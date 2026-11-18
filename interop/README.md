# Interopérabilité : FHIR, CDA, DICOM

| Dossier | Contenu |
|---|---|
| `fhir/exemples/` | Une ressource FHIR R4 par fichier, pour tout le scénario (Patient → DocumentReference) |
| `fhir/scenario-complet.json` | Le scénario entier en un Bundle `transaction` (à envoyer au serveur FHIR) |
| `fhir/requetes.http` | Requêtes FHIR et Orthanc à lancer depuis VS Code (extension REST Client), dont les tests négatifs |
| `cda/CR-ACC-2026-0001.xml` | Compte rendu CDA R2 d'exemple (valide contre le schéma HL7) |
| `cda/valider_cda.sh` | Vérification de la structure d'un CDA |
| `dicom/modalite-simulee/` | Création de worklist et modalité simulée (extension) |
| `dicom/worklists/` | Dossier partagé avec Orthanc (fichiers `.wl`, non versionnés) |

Les exemples ont été vérifiés avec le modèle FHIR R4 4.0.1 (structure et champs obligatoires) et avec le schéma CDA R2 officiel.
Explications : `docs/conception/`.
