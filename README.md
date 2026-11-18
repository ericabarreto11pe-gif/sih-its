# SIH-ITS – Système hospitalier interconnecté

Projet ECUE531 (EPISEN ITS3, 2026–2027). Maquette fonctionnelle reliant **consultation, prescription, RIS, serveur FHIR R4,
compte rendu CDA R2 et PACS Orthanc**, autour d'un parcours d'imagerie de bout en bout sur un patient **fictif**.

| Membre | Rôle principal |
|---|---|
| A – _nom_ | SIH / dossier patient (consultation, prescription, espace patient) |
| B – _nom_ | RIS, compte rendu, connecteur CDA, worklist DICOM |
| C – _nom_ | Infrastructure (3 VM, proxy HTTPS, IAM), serveur FHIR, Orthanc |

## Arborescence

```
sih-its/
├── README.md                    ce fichier (installation et redéploiement)
├── docker-compose.yml           dev : FHIR + PostgreSQL + Orthanc sur un seul PC
├── .env.example                 modèle des secrets (copier en .env, jamais commité)
├── sih-its.code-workspace       espace de travail VS Code (un dossier par composant)
├── .vscode/                     extensions recommandées et réglages partagés
├── services/
│   ├── sih/                     A – SIH / DPI
│   ├── ris/                     B – RIS
│   └── cda-connector/           B – génération du CDA
├── interop/
│   ├── fhir/                    exemples FHIR R4, bundle du scénario, requêtes .http
│   ├── cda/                     exemple CDA R2 + script de validation
│   └── dicom/                   worklists + modalité simulée (extension)
├── infra/                       C – vm1-proxy, vm2-apps, vm3-data, scripts
├── data/demo/                   description des données fictives
├── tests/                       scénario nominal et tests négatifs
└── docs/
    ├── conception/              identifiants, cycle de vie RIS, FHIR, worklist, séquence
    ├── uml/                     diagrammes draw.io (cas d'utilisation, séquence)
    ├── gestion-projet/          backlog, Gantt, SWOT
    └── rapport/
```

## Démarrage rapide (développement)

Prérequis : Docker Desktop, Git, Python 3.10+.

```bash
cp .env.example .env              # puis changer les mots de passe
docker compose up -d              # FHIR : http://localhost:8080/fhir · Orthanc : http://localhost:8042
```

Charger le scénario fictif : ouvrir `interop/fhir/requetes.http` dans VS Code et lancer la requête 0
(ou `curl -X POST -H "Content-Type: application/fhir+json" --data @interop/fhir/scenario-complet.json http://localhost:8080/fhir`).

Simuler l'acquisition d'une image : voir `docs/conception/04-worklist-modalite-simulee.md`.

## Conception

| Document | Contenu |
|---|---|
| [01 · Identifiants](docs/conception/01-identifiants.md) | Formats, correspondances FHIR / DICOM / CDA, OID du projet |
| [02 · Cycle de vie RIS](docs/conception/02-cycle-de-vie-ris.md) | États, transitions autorisées et interdites |
| [03 · FHIR du RIS](docs/conception/03-fhir-appointment-diagnosticreport-documentreference.md) | Appointment, DiagnosticReport, DocumentReference |
| [04 · Worklist et modalité simulée](docs/conception/04-worklist-modalite-simulee.md) | Extension DICOM |
| [05 · Séquence prescription → résultat](docs/conception/05-sequence-prescription-resultat.md) | Diagramme UML de séquence |

## Règles de travail

- Une branche par tâche (`feature/ris-transitions-etat`), jamais de commit direct sur `main`.
- Messages de commit : `type(composant): description`, par exemple `feat(ris): programmation d'un examen`.
- Toute pull request est relue par un autre membre avant la fusion.
- Aucune donnée réelle, aucun mot de passe dans le dépôt.
- Versions utilisées (à compléter pour le rapport) : HAPI FHIR `…`, Orthanc `…`, PostgreSQL `16`, pydicom `3.0.2`, pynetdicom `3.0.4`.
