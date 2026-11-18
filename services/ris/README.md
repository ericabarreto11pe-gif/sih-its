# RIS – Radiology Information System (Membre B)

> Responsabilité (cahier des charges) : *suivi de la demande, programmation, états de l'examen et compte rendu.*
> Il ne doit pas être réduit à un simple calendrier.

## Ce que le RIS doit faire (socle)

| Fonction | Détail | Conception |
|---|---|---|
| Liste de travail | Afficher les `ServiceRequest` actifs reçus du SIH | `docs/conception/03-…` |
| Programmer | Créer l'`Appointment` (créneau, salle) ; refuser les chevauchements | `docs/conception/03-…` §1 |
| Gérer l'état | demandée → planifiée → réalisée → interprétée → validée, ou annulée | `docs/conception/02-cycle-de-vie-ris.md` |
| Lier l'étude | Retrouver l'étude dans Orthanc par `AccessionNumber`, créer l'`ImagingStudy` | `docs/conception/01-identifiants.md` |
| Compte rendu | Saisie, `DiagnosticReport` `preliminary` puis `final` (radiologue uniquement) | `docs/conception/03-…` §3 |
| Publier | Appeler le connecteur CDA, envoyer la transaction de validation | `docs/conception/03-…` §5 |
| Extension | Déposer / retirer l'entrée de worklist | `docs/conception/04-worklist-modalite-simulee.md` |

## Organisation du code (indépendante du langage choisi)

```
services/ris/
├── README.md
├── Dockerfile
├── src/
│   ├── domaine/      # règles métier pures : table des transitions, contrôles de rôle (testées unitairement)
│   ├── fhir/         # client FHIR : lire ServiceRequest, écrire Appointment, ImagingStudy, DiagnosticReport
│   ├── pacs/         # client Orthanc : /tools/find, lien visionneuse, dépôt de worklist
│   ├── api/          # routes HTTP et écrans (liste de travail, fiche examen, saisie du CR)
│   └── config        # lecture des variables d'environnement (URL FHIR, Orthanc, secrets)
└── tests/            # transitions autorisées / interdites, refus de rôle, PACS indisponible
```

Règle : `domaine/` ne fait aucun appel réseau. Il décide ; `fhir/` et `pacs/` exécutent.

## Variables d'environnement

| Variable | Exemple (dev) |
|---|---|
| `FHIR_URL` | `http://localhost:8080/fhir` |
| `ORTHANC_URL` | `http://localhost:8042` |
| `ORTHANC_UTILISATEUR` / `ORTHANC_MOT_DE_PASSE` | voir `.env` |
| `WORKLIST_DOSSIER` | `interop/dicom/worklists` |
| `SIH_OID_RACINE` | voir `.env.example` |
