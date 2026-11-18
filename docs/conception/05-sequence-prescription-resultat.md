# 05 · Diagramme de séquence : de la prescription au résultat

> Cahier des charges, §7 : *« UML – séquence : cheminement d'une demande d'imagerie, de la prescription au résultat. »*

Version éditable pour le rapport : `docs/uml/sequence-prescription-resultat.drawio` (s'ouvre dans draw.io ou dans VS Code
avec l'extension *Draw.io Integration*). La version ci-dessous s'affiche directement sur GitHub.

```mermaid
sequenceDiagram
    autonumber
    actor MED as Médecin
    participant SIH as SIH / DPI
    participant IAM as IAM
    participant FHIR as Serveur FHIR R4
    participant RIS as RIS
    actor RAD as Radiologue
    participant PACS as Orthanc (PACS + worklist)
    participant MOD as Modalité simulée
    participant CDA as Connecteur CDA

    rect rgba(47,111,179,0.08)
    Note over MED,FHIR: 1. Consultation et prescription
    MED->>SIH: se connecter
    SIH->>IAM: authentifier
    IAM-->>SIH: jeton (rôle = médecin)
    MED->>SIH: ouvrir le dossier PAT-0001, réaliser la consultation
    SIH->>FHIR: PUT Encounter (ENC-2026-0001)
    MED->>SIH: prescrire « radio du thorax »
    alt rôle ≠ médecin
        SIH-->>MED: 403 refusé + trace dans les journaux
    else rôle = médecin
        SIH->>FHIR: PUT ServiceRequest (ACC-2026-0001, status = active)
        FHIR-->>SIH: 201 Created
    end
    end

    rect rgba(180,99,43,0.08)
    Note over FHIR,PACS: 2. Réception et programmation (état : demandée → planifiée)
    RIS->>FHIR: GET ServiceRequest?status=active
    FHIR-->>RIS: liste de travail
    RAD->>RIS: programmer (date, salle)
    RIS->>FHIR: PUT Appointment (booked, basedOn ServiceRequest)
    opt extension worklist
        RIS->>PACS: dépôt entrée worklist (PAT, ACC, StudyInstanceUID)
    end
    end

    rect rgba(106,79,163,0.08)
    Note over RIS,MOD: 3. Acquisition (état : planifiée → réalisée)
    MOD->>PACS: C-FIND worklist
    PACS-->>MOD: examen ACC-2026-0001
    MOD->>PACS: C-STORE images (même ACC et StudyInstanceUID)
    RIS->>PACS: POST /tools/find { AccessionNumber }
    PACS-->>RIS: étude trouvée
    RIS->>FHIR: PUT ImagingStudy (basedOn ServiceRequest)<br/>PATCH Appointment → fulfilled
    end

    rect rgba(15,110,86,0.08)
    Note over RIS,CDA: 4. Interprétation et validation (→ interprétée → validée)
    RAD->>RIS: ouvrir l'étude (visionneuse Orthanc)
    RAD->>RIS: rédiger le compte rendu
    RIS->>FHIR: PUT DiagnosticReport (preliminary)
    RAD->>RIS: valider (signer)
    RIS->>CDA: générer le CDA (CR, patient, auteur, ACC, StudyInstanceUID)
    CDA-->>RIS: document CDA R2 (XML)
    RIS->>FHIR: transaction : Binary (CDA) + DiagnosticReport final<br/>+ DocumentReference + ServiceRequest completed
    FHIR-->>RIS: 200 OK (tout ou rien)
    end

    rect rgba(47,111,179,0.08)
    Note over MED,PACS: 5. Retour du résultat dans le dossier patient
    MED->>SIH: consulter le dossier PAT-0001
    SIH->>FHIR: GET DiagnosticReport?based-on=…&status=final
    FHIR-->>SIH: compte rendu + lien DocumentReference
    SIH->>FHIR: GET Binary (CDA)
    SIH->>PACS: lien visionneuse (via le proxy)
    SIH-->>MED: compte rendu, CDA et images
    end
```

## Lecture du diagramme

| Phase | Ce qui est démontré | Ressources / échanges |
|---|---|---|
| 1. Prescription | Authentification, contrôle du rôle, refus tracé | `Encounter`, `ServiceRequest` (FHIR) |
| 2. Programmation | La demande arrive dans le RIS sans ressaisie | `Appointment` (FHIR), entrée de worklist (DICOM) |
| 3. Acquisition | L'étude porte les identifiants de la demande | C-FIND / C-STORE (DICOM), `ImagingStudy` (FHIR) |
| 4. Validation | Seul le radiologue valide ; CR et document enregistrés ensemble | `DiagnosticReport`, `Binary`, `DocumentReference` (FHIR), CDA R2 |
| 5. Retour | Le médecin retrouve CR, CDA et images dans le même dossier | Recherches FHIR, visionneuse Orthanc |

Cette séquence correspond au déroulé de démonstration du cahier des charges (§9).
Les flèches indiquent une progression fonctionnelle : en pratique, le RIS peut interroger le serveur FHIR à intervalles
réguliers (*polling*) plutôt que d'être notifié.
