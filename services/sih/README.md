# SIH / DPI (Membre A)

> Responsabilité (cahier des charges) : *patients, consultations, prescriptions et accès aux résultats.*
> Il ne doit pas être réduit à une page de téléconsultation.

## Ce que le SIH doit faire (socle)

| Fonction | Ressources FHIR |
|---|---|
| Créer / retrouver un patient fictif | `Patient` (`PAT-NNNN`) |
| Réaliser une consultation | `Encounter` (`ENC-AAAA-NNNN`) |
| Prescrire un examen d'imagerie (médecin authentifié uniquement) | `ServiceRequest` (`ACC-AAAA-NNNN`, `status = active`) |
| Afficher les résultats dans le dossier | lire `DiagnosticReport` (`final`), `DocumentReference` → `Binary` (CDA), lien vers Orthanc |
| Espace patient / téléconsultation (reprise ITS2) | `Appointment` (lecture), CR validés uniquement |

Les formats d'identifiants et les liens attendus sont dans `docs/conception/01-identifiants.md`.
Exemples de ressources : `interop/fhir/exemples/02-…`, `06-…`, `07-…`.

## Organisation du code (indépendante du langage choisi)

```
services/sih/
├── README.md
├── Dockerfile
├── src/
│   ├── domaine/     # règles : qui peut prescrire, qui voit quoi
│   ├── fhir/        # client FHIR
│   ├── api/         # routes et écrans (dossier patient, consultation, prescription, espace patient)
│   └── config
└── tests/
```
