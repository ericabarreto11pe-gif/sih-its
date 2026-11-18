# Tests

> Cahier des charges, §7 et §9 : jeux de données fictives, scénarios nominaux et tests d'échec.

## Scénario nominal (déroulé de la démonstration)

| # | Étape | Vérification | Responsable |
|---|---|---|---|
| 1 | Connexion avec un rôle autorisé, création / recherche du patient | `Patient` PAT-0001 trouvé | A |
| 2 | Consultation puis prescription | `Encounter` + `ServiceRequest` ACC-2026-0001 `active` | A |
| 3 | Demande visible dans le RIS, programmation | `Appointment` `booked`, état « planifiée » | B |
| 4 | Acquisition (modalité simulée) | Étude dans Orthanc avec AccessionNumber = ACC-2026-0001 | B + C |
| 5 | Étude liée | `ImagingStudy` `available`, état « réalisée » | B |
| 6 | CR saisi puis validé | `DiagnosticReport` `final`, CDA valide, `DocumentReference` `current` | B |
| 7 | Retour dans le dossier patient | CR, CDA et lien images visibles dans le SIH | A |

## Tests négatifs

| Cas | Comportement attendu | Où | Responsable |
|---|---|---|---|
| Utilisateur non autorisé (ex. secrétariat qui valide un CR) | Refus 403 ; trace dans les journaux | RIS, SIH, IAM | A, B, C |
| Référence patient incorrecte | Refus, pas de rattachement silencieux | `interop/fhir/requetes.http` (tests négatifs) | A |
| Transition d'état interdite (ex. annulée → planifiée) | Refus avec message | RIS (`docs/conception/02-…` §3) | B |
| Demande annulée envoyée en worklist | Refus | `creer_worklist.py` | B |
| PACS momentanément indisponible | Erreur contrôlée, RIS et SIH restent utilisables | RIS, modalité simulée | B + C |
| Redémarrage des conteneurs | Dossiers, demandes et études conservés | `docker compose restart` | C |
| Accès direct à la base ou à Orthanc depuis l'extérieur | Connexion impossible | Pare-feu VM3 | C |

Pour chaque test, garder une trace (capture, sortie de commande, extrait de journal) pour le rapport.
