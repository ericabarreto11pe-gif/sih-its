# Interopérabilité : FHIR, CDA, DICOM

| Dossier | Contenu |
|---|---|
| `fhir/exemples/` | Exemples officiels HL7 FHIR R4, un par type de ressource (génériques, sans lien avec le scénario) |
| `fhir/scenario-complet.json` | Le scénario entier en un Bundle `transaction` (à envoyer au serveur FHIR) |
| `fhir/requetes.http` | Requêtes FHIR et Orthanc à lancer depuis VS Code (extension REST Client), dont les tests négatifs |
| `cda/CR-ACC-2026-0001.xml` | Compte rendu CDA R2 d'exemple (valide contre le schéma HL7) |
| `cda/valider_cda.sh` | Vérification de la structure d'un CDA |
| `dicom/modalite-simulee/` | Création de worklist et modalité simulée (extension) |
| `dicom/worklists/` | Dossier partagé avec Orthanc (fichiers `.wl`, non versionnés) |

Le Bundle du scénario a été vérifié avec le modèle FHIR R4 4.0.1 (structure et champs obligatoires) et le compte rendu CDA avec le schéma CDA R2 officiel.
Explications : `docs/conception/`.

## Référentiel FHIR R4 utilisé

- **Version :** FHIR R4 **4.0.1** – <https://hl7.org/fhir/R4/>
- **Paquet officiel des définitions :** `hl7.fhir.r4.core#4.0.1`. Le validateur HL7 le télécharge au
  premier lancement dans `~/.fhir/packages/hl7.fhir.r4.core#4.0.1/package/`.
- **Exemple :** la définition de la ressource Patient est le fichier
  `~/.fhir/packages/hl7.fhir.r4.core#4.0.1/package/StructureDefinition-Patient.json`.
- **Validation d'un fichier** (validateur placé dans `tools/`, Java installé avec `brew install openjdk`) :

  ```bash
  java -jar tools/validator_cli.jar interop/fhir/scenario-complet.json -version 4.0.1
  ```

Le paquet n'est **pas versionné** dans le dépôt (ni le validateur : `tools/` est ignoré par Git).
