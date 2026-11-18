# 03 · Ressources FHIR R4 du RIS : Appointment, DiagnosticReport, DocumentReference

Ces trois ressources sont produites par le **RIS** et le **connecteur CDA** (Membre B).
Elles s'appuient sur les ressources créées par le SIH (`Patient`, `Encounter`, `ServiceRequest`) et sur l'étude
stockée dans Orthanc (`ImagingStudy`).

Exemples complets et validés (modèle FHIR R4 4.0.1) : `interop/fhir/exemples/`.
Tout le scénario en une transaction : `interop/fhir/scenario-complet.json`.
Requêtes prêtes à l'emploi : `interop/fhir/requetes.http`.

## 0. Conventions communes

- **Version** : FHIR **R4** (4.0.1) uniquement. Ne pas copier d'exemples R5 trouvés en ligne : plusieurs champs diffèrent
  (par exemple `DocumentReference.masterIdentifier` et `DocumentReference.context` n'ont plus la même forme en R5,
  et `Appointment.cancelationReason` y devient `cancellationReason`).
- **Id logique = identifiant métier en minuscules** : `ServiceRequest/sr-acc-2026-0001`, `Appointment/apt-2026-0001`,
  `DiagnosticReport/dr-acc-2026-0001`, `DocumentReference/doc-acc-2026-0001`, `Binary/cda-acc-2026-0001`.
  On écrit avec `PUT` (création ou mise à jour), ce qui rend les envois rejouables sans créer de doublons.
- **Toujours une référence vers la demande** : `basedOn: [{ "reference": "ServiceRequest/sr-acc-2026-0001" }]`.
- Les statuts FHIR suivent le cycle de vie du RIS (voir `02-cycle-de-vie-ris.md`).

| État RIS | ServiceRequest | Appointment | ImagingStudy | DiagnosticReport | DocumentReference |
|---|---|---|---|---|---|
| demandée | `active` | – | – | – | – |
| planifiée | `active` | `booked` | – | – | – |
| *(patient arrivé)* | `active` | `arrived` | – | – | – |
| réalisée | `active` | `fulfilled` | `available` | – | – |
| interprétée | `active` | `fulfilled` | `available` | `preliminary` | – |
| validée | `completed` | `fulfilled` | `available` | `final` | `current` (`docStatus = final`) |
| rectifiée | `completed` | `fulfilled` | `available` | `amended` | nouvelle version `current`, ancienne `superseded` |
| annulée | `revoked` | `cancelled` | – | – | – |

---

## 1. Appointment : la programmation de l'examen

**Rôle.** Représente le rendez-vous d'imagerie : quand, où, pour qui, et pour quelle demande.
Ce n'est pas qu'un calendrier : le rendez-vous est rattaché à la demande (`basedOn`) et son statut suit l'examen.

**Créé par** le RIS au passage *demandée → planifiée*. **Lu par** le SIH (le patient voit son rendez-vous dans son espace)
et par le script de worklist (date, heure, salle).

| Élément | Card. R4 | Valeur dans le projet | Pourquoi |
|---|---|---|---|
| `identifier` | 0..* | `RDV-2026-0001` | Identifiant métier du RIS |
| `status` | **1..1** | `booked` → `arrived` → `fulfilled` (ou `cancelled`) | Suit l'examen |
| `basedOn` | 0..* | `ServiceRequest/sr-acc-2026-0001` | **Lien vers la prescription** (traçabilité) |
| `serviceType` | 0..* | « Radiographie conventionnelle » | Type d'examen (référentiel de l'admin) |
| `appointmentType` | 0..1 | `ROUTINE` (v2-0276) | Programmé / urgence |
| `description` | 0..1 | « Radiographie du thorax – ACC-2026-0001 » | Libellé affiché |
| `start`, `end` | 0..1 | `2026-11-25T10:00:00+01:00` → `10:15` | Obligatoires dès que le statut est `booked` (règle app-3) |
| `minutesDuration` | 0..1 | `15` | Durée prévue |
| `participant` | **1..\*** | Patient, `Location/loc-rx1`, radiologue | Qui et où |
| `participant.status` | **1..1** | `accepted` | Obligatoire : l'oublier est l'erreur la plus fréquente |
| `cancelationReason` | 0..1 | « Patient indisponible » | Seulement si `cancelled` (une seule lettre « l » en R4) |

Création au moment de la programmation :

```http
PUT /fhir/Appointment/apt-2026-0001
Content-Type: application/fhir+json
```
```json
{
  "resourceType": "Appointment",
  "id": "apt-2026-0001",
  "identifier": [{ "system": "http://sih-its.local/sid/rendez-vous", "value": "RDV-2026-0001" }],
  "status": "booked",
  "basedOn": [{ "reference": "ServiceRequest/sr-acc-2026-0001" }],
  "serviceType": [{ "text": "Radiographie conventionnelle" }],
  "description": "Radiographie du thorax (face + profil) – ACC-2026-0001",
  "start": "2026-11-25T10:00:00+01:00",
  "end": "2026-11-25T10:15:00+01:00",
  "minutesDuration": 15,
  "participant": [
    { "actor": { "reference": "Patient/pat-0001" }, "required": "required", "status": "accepted" },
    { "actor": { "reference": "Location/loc-rx1" }, "required": "required", "status": "accepted" }
  ]
}
```

Changer seulement le statut (patient arrivé, examen réalisé) avec un PATCH :

```http
PATCH /fhir/Appointment/apt-2026-0001
Content-Type: application/json-patch+json

[{ "op": "replace", "path": "/status", "value": "fulfilled" }]
```

**Recherches utiles** : `Appointment?based-on=ServiceRequest/…` (le RDV d'une demande),
`Appointment?location=Location/loc-rx1&date=2026-11-25` (planning d'une salle), `Appointment?patient=Patient/pat-0001` (espace patient).

**Règle métier à coder** : refuser deux rendez-vous `booked` qui se chevauchent dans la même salle
(rechercher les RDV de la salle sur le créneau avant d'écrire).

---

## 2. ImagingStudy : le lien vers l'étude du PACS (rappel)

Créé par le RIS au passage *planifiée → réalisée*, après avoir retrouvé l'étude dans Orthanc par son `AccessionNumber`.

> ImagingStudy décrit l'étude (**métadonnées** : UID, séries, nombre d'images). Les **images** restent dans Orthanc.
> Ne jamais mettre de pixels dans FHIR.

Points clés : `identifier` contient le Study Instance UID (`urn:dicom:uid`) **et** le numéro d'examen (type `ACSN`),
`basedOn` pointe vers la demande, `status = available`. Exemple complet : `09-imagingstudy-is-acc-2026-0001.json`.

---

## 3. DiagnosticReport : le compte rendu et le résultat médical

**Rôle.** C'est le **compte rendu structuré** côté FHIR : statut, conclusion, auteur, lien vers la demande et vers l'étude.
C'est la ressource que le SIH interroge pour afficher « résultat disponible » dans le dossier patient.

**Créé par** le RIS quand le radiologue enregistre son CR (*réalisée → interprétée*, `preliminary`), puis
**mis à jour** à la validation (`final`). **Lu par** le SIH (médecin et patient), uniquement si `status = final`
pour le patient.

| Élément | Card. R4 | Valeur dans le projet | Pourquoi |
|---|---|---|---|
| `identifier` | 0..* | `CR-ACC-2026-0001` | Identifiant du CR |
| `basedOn` | 0..* | `ServiceRequest/sr-acc-2026-0001` | **Lien vers la prescription** |
| `status` | **1..1** | `preliminary` → `final` (→ `amended`) | Seul `final` est visible par le patient |
| `category` | 0..* | `RAD` (v2-0074) | Compte rendu de radiologie |
| `code` | **1..1** | LOINC `18748-4` *Diagnostic imaging study* | Type de compte rendu |
| `subject` | 0..1 | `Patient/pat-0001` | Le patient |
| `encounter` | 0..1 | `Encounter/enc-2026-0001` | La consultation d'origine |
| `effectiveDateTime` | 0..1 | date de l'acquisition | Moment de l'examen |
| `issued` | 0..1 | date de validation | Moment de la publication du résultat |
| `resultsInterpreter` | 0..* | `Practitioner/pra-0002` | **Le radiologue qui a validé** |
| `imagingStudy` | 0..* | `ImagingStudy/is-acc-2026-0001` | **Lien vers l'étude** (donc vers Orthanc) |
| `conclusion` | 0..1 | texte de la conclusion | Affichée dans le dossier patient |
| `conclusionCode` | 0..* | SNOMED `17621005` *Normal* | Optionnel, utile pour les filtres |

Exemple complet : `interop/fhir/exemples/10-diagnosticreport-dr-acc-2026-0001.json`.

**Contrôle d'accès à coder** : seul le rôle *radiologue* peut passer un DiagnosticReport à `final`.
Le secrétariat ne peut ni lire ni écrire un DiagnosticReport (cahier : « ne peut pas rédiger un compte rendu médical »).

---

## 4. DocumentReference : l'accès au document CDA

**Rôle.** Indexe le **document CDA** : de quel document il s'agit, pour quel patient, par qui, et **où le récupérer**.
Le XML lui-même est stocké dans une ressource `Binary`. C'est ce que le cahier appelle
« DocumentReference renvoyant vers le document, XML accessible ».

**Créé par** le connecteur CDA au passage *interprétée → validée*, en même temps que le `Binary`.

| Élément | Card. R4 | Valeur dans le projet | Pourquoi |
|---|---|---|---|
| `masterIdentifier` | 0..1 | `DOC-ACC-2026-0001-v1` (system = OID documents) | Même identifiant que `ClinicalDocument/id` du CDA |
| `status` | **1..1** | `current` (ancienne version : `superseded`) | Statut de l'**index** |
| `docStatus` | 0..1 | `final` | Statut du **document** |
| `type` | 0..1 | LOINC `18748-4` | Même code que le CDA |
| `category` | 0..* | LOINC `18726-0` *Radiology studies* | Classement dans le dossier |
| `subject` | 0..1 | `Patient/pat-0001` | Le patient |
| `date` | 0..1 | date de validation | Date du document |
| `author` / `authenticator` | 0..* / 0..1 | `Practitioner/pra-0002` | Auteur et signataire |
| `custodian` | 0..1 | `Organization/org-hopital-its` | Établissement responsable |
| `relatesTo` | 0..* | `{ "code": "replaces", "target": DocumentReference/v1 }` | Seulement pour une version rectifiée |
| `content.attachment` | **1..\*** | `contentType = text/xml`, `url = Binary/cda-acc-2026-0001` | **Où lire le XML** |
| `context.encounter` | 0..* | `Encounter/enc-2026-0001` | Consultation d'origine |
| `context.related` | 0..* | ServiceRequest, ImagingStudy, DiagnosticReport | **Traçabilité demande ↔ étude ↔ CR** |

Récupérer le XML brut : `GET /fhir/Binary/cda-acc-2026-0001` avec l'en-tête `Accept: text/xml`.

---

## 5. La validation en une seule transaction

À la validation, le RIS envoie **un seul Bundle `transaction`** : soit tout est enregistré, soit rien
(pas de CR « final » sans document, ni de document sans CR).

```json
{
  "resourceType": "Bundle",
  "type": "transaction",
  "entry": [
    { "resource": { "resourceType": "Binary", "id": "cda-acc-2026-0001",
                    "contentType": "text/xml", "data": "<XML CDA encodé en base64>" },
      "request": { "method": "PUT", "url": "Binary/cda-acc-2026-0001" } },
    { "resource": { "resourceType": "DiagnosticReport", "id": "dr-acc-2026-0001", "status": "final", "…": "…" },
      "request": { "method": "PUT", "url": "DiagnosticReport/dr-acc-2026-0001" } },
    { "resource": { "resourceType": "DocumentReference", "id": "doc-acc-2026-0001", "status": "current", "…": "…" },
      "request": { "method": "PUT", "url": "DocumentReference/doc-acc-2026-0001" } },
    { "resource": { "resourceType": "ServiceRequest", "id": "sr-acc-2026-0001", "status": "completed", "…": "…" },
      "request": { "method": "PUT", "url": "ServiceRequest/sr-acc-2026-0001" } }
  ]
}
```

On utilise des `PUT` avec des id connus à l'avance plutôt que des `urn:uuid`, parce que
`DocumentReference.content.attachment.url` est une simple URL : le serveur ne la réécrit pas comme une référence.

## 6. Correspondance CDA ↔ FHIR

| Information | CDA R2 (`interop/cda/CR-ACC-2026-0001.xml`) | FHIR |
|---|---|---|
| Identifiant du document | `ClinicalDocument/id` | `DocumentReference.masterIdentifier` |
| Type de document | `ClinicalDocument/code` (18748-4) | `DocumentReference.type`, `DiagnosticReport.code` |
| Patient | `recordTarget/patientRole/id` | `subject` → `Patient.identifier` |
| Auteur | `author/assignedAuthor` | `DocumentReference.author`, `DiagnosticReport.resultsInterpreter` |
| Signature | `legalAuthenticator` | `DocumentReference.authenticator` |
| Date | `effectiveTime` | `DocumentReference.date`, `DiagnosticReport.issued` |
| Demande | `inFulfillmentOf/order/id` (ACC-…) | `basedOn` → `ServiceRequest` |
| Étude | `documentationOf/serviceEvent/id` (Study UID) | `imagingStudy` → `ImagingStudy.identifier` |
| Conclusion | section LOINC `19005-8` | `DiagnosticReport.conclusion` |

Vérifier la structure du CDA : `./interop/cda/valider_cda.sh interop/cda/CR-ACC-2026-0001.xml`
(schéma officiel HL7 CDA R2 ; l'exemple fourni passe la validation).
