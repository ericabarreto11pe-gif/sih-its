# Connecteur CDA (Membre B)

> Cahier des charges, §6 : *un document CDA XML devra être généré à partir du compte rendu finalisé dans le RIS.
> Il comportera une identification du document, une identification du patient, son auteur, sa date et un contenu
> clinique lisible. Il devra pouvoir être récupéré depuis le SIH, directement ou via une référence FHIR.*

## Entrée → sortie

- **Entrée** (appelé par le RIS à la validation) : le CR finalisé, le patient, le radiologue, le numéro d'examen,
  le Study Instance UID, la consultation d'origine.
- **Sortie** : un XML CDA R2, conforme au modèle `interop/cda/CR-ACC-2026-0001.xml`.

Le RIS enregistre ensuite le XML dans un `Binary` et l'indexe par un `DocumentReference`
(voir `docs/conception/03-fhir-appointment-diagnosticreport-documentreference.md`, §4 et §5).

## Contenu obligatoire du document

| Exigence | Élément CDA |
|---|---|
| Identification du document | `id`, `code` (LOINC 18748-4), `title`, `setId`, `versionNumber` |
| Identification du patient | `recordTarget/patientRole/id` (PAT-…) |
| Auteur | `author` (radiologue) + `legalAuthenticator` (signature à la validation) |
| Date | `effectiveTime` |
| Contenu clinique lisible | sections Indication, Technique, Résultats, Conclusion |
| Traçabilité | `inFulfillmentOf/order/id` (ACC-…), `documentationOf/serviceEvent/id` (Study UID), `componentOf` (ENC-…) |

## Vérification

```bash
./interop/cda/valider_cda.sh mon-document.xml     # schéma officiel HL7 CDA R2
```

Conseil : partir du modèle XML et remplacer les valeurs (gabarit), plutôt que de construire l'arbre XML élément par élément.
Un document CDA n'est **pas** un PDF renommé en `.xml` (cahier des charges).
