# Exemples officiels HL7 FHIR R4

Ce dossier contient un exemple officiel par type de ressource utilisé dans le projet.

## Source et licence

- **Source :** archive `examples-json.zip` de la page Downloads de la spécification FHIR R4,
  téléchargée depuis <https://hl7.org/fhir/R4/examples-json.zip> (page : <https://hl7.org/fhir/R4/downloads.html>).
- **Version :** FHIR R4 **4.0.1**.
- **Licence :** CC0 (domaine public), comme l'ensemble de la spécification FHIR ([licence HL7 FHIR](https://hl7.org/fhir/R4/license.html)).
- Les fichiers sont copiés **sans modification**, avec leur nom d'origine.

| Ressource | Fichier |
|---|---|
| Organization | `organization-example.json` |
| Patient | `patient-example.json` |
| Practitioner | `practitioner-example.json` |
| Location | `location-example.json` |
| Encounter | `encounter-example.json` |
| ServiceRequest | `servicerequest-example-di.json` (imagerie : scanner thoracique) |
| Appointment | `appointment-example.json` |
| ImagingStudy | `imagingstudy-example.json` |
| DiagnosticReport | `diagnosticreport-example-f201-brainct.json` (imagerie : scanner tête et cou) |
| Binary | `binary-example.json` |
| DocumentReference | `documentreference-example.json` |

## À savoir

- Ce sont des **exemples génériques HL7** : ils n'ont **aucun lien entre eux** (les références
  pointent vers des ressources absentes de ce dossier) ni avec le scénario SIH-ITS.
- Ils servent uniquement de **référence de lecture** (structure, champs, codes).
  **Ne pas les envoyer au serveur FHIR du projet.**
- Certains contiennent des URLs `example.org` : le validateur HL7 les signale comme erreurs
  (`appointment-example.json`, `documentreference-example.json`, `practitioner-example.json`).
  C'est attendu pour des exemples de la spécification.

## Données du scénario SIH-ITS

Les ressources du scénario du projet (patient, demande, rendez-vous, étude, compte rendu…)
sont dans [`../scenario-complet.json`](../scenario-complet.json) (Bundle `transaction`).
