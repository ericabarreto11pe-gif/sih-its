# Données de démonstration

**Aucune donnée personnelle réelle** dans ce dépôt (cahier des charges, §3 et §8).

| Donnée | Où | Origine |
|---|---|---|
| Patiente fictive Léa Martin (`PAT-0001`), médecin, radiologue, salle | `interop/fhir/scenario-complet.json` | Inventée pour le projet |
| Parcours complet (consultation → CR validé) | même fichier, ressources à l'état final | Inventé |
| Compte rendu CDA | `interop/cda/CR-ACC-2026-0001.xml` | Inventé |
| Images DICOM | générées par `interop/dicom/modalite-simulee/modalite.py` | Images synthétiques, sans restriction de licence |

Pour ajouter des patients, garder les formats d'identifiants de `docs/conception/01-identifiants.md`
(`PAT-0002`, `ACC-2026-0002`…).
