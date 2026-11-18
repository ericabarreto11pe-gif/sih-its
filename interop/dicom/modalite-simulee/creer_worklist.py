#!/usr/bin/env python3
"""
Crée une entrée de worklist DICOM (fichier .wl) pour Orthanc à partir d'un examen programmé.

Rôle dans le parcours : quand le RIS passe une demande à l'état « planifiée »
(Appointment.status = booked), il dépose une entrée de worklist. La modalité
(simulée ici par modalite.py) l'interroge en C-FIND, récupère le patient, le numéro
d'examen (AccessionNumber) et le Study Instance UID, et les recopie dans les images.

Sources possibles des données :
  --fhir   URL du serveur FHIR (ex. http://localhost:8080/fhir)
  --bundle fichier Bundle JSON local (ex. interop/fhir/scenario-complet.json)

Exemples :
  python creer_worklist.py --bundle ../../fhir/scenario-complet.json --accession ACC-2026-0001
  python creer_worklist.py --fhir http://localhost:8080/fhir --accession ACC-2026-0001 --sortie ../worklists
  python creer_worklist.py --supprimer --accession ACC-2026-0001        # quand l'examen est réalisé
"""
import argparse
import base64
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

# Racine OID du projet (voir docs/conception/01-identifiants.md). Surchargeable par variable d'environnement.
RACINE_OID = os.environ.get("SIH_OID_RACINE", "2.25.15160578678088058174301844912568396362")
MWL_FIND = "1.2.840.10008.5.1.4.31"  # Modality Worklist Information Model – FIND
DOSSIER_PAR_DEFAUT = Path(__file__).resolve().parent.parent / "worklists"


def study_uid_depuis_accession(accession: str) -> str:
    """Règle commune RIS / modalité : ACC-2026-0001 -> <racine>.6.1.20260001 (max 64 caractères)."""
    chiffres = re.sub(r"\D", "", accession)
    uid = f"{RACINE_OID}.6.1.{int(chiffres)}"
    if len(uid) > 64:
        raise ValueError(f"UID trop long ({len(uid)} > 64) : {uid}")
    return uid


# ---------- Lecture des ressources FHIR ----------
class SourceBundle:
    def __init__(self, chemin):
        bundle = json.loads(Path(chemin).read_text(encoding="utf-8"))
        self.index = {}
        for e in bundle.get("entry", []):
            r = e["resource"]
            self.index[f"{r['resourceType']}/{r['id']}"] = r

    def lire(self, ref):
        return self.index.get(ref)

    def chercher(self, type_, filtre):
        return [r for k, r in self.index.items() if k.startswith(type_ + "/") and filtre(r)]


class SourceFhir:
    def __init__(self, base, utilisateur=None, mot_de_passe=None):
        self.base = base.rstrip("/")
        self.entetes = {"Accept": "application/fhir+json"}
        if utilisateur:
            jeton = base64.b64encode(f"{utilisateur}:{mot_de_passe}".encode()).decode()
            self.entetes["Authorization"] = "Basic " + jeton

    def _get(self, chemin):
        req = urllib.request.Request(f"{self.base}/{chemin}", headers=self.entetes)
        with urllib.request.urlopen(req, timeout=15) as rep:
            return json.load(rep)

    def lire(self, ref):
        return self._get(ref)

    def rechercher(self, type_, **params):
        b = self._get(f"{type_}?{urllib.parse.urlencode(params)}")
        return [e["resource"] for e in b.get("entry", [])]


def charger_examen(source, accession):
    """Retourne (ServiceRequest, Patient, Appointment, Location|None, Practitioner|None)."""
    if isinstance(source, SourceBundle):
        srs = source.chercher("ServiceRequest", lambda r: any(i.get("value") == accession for i in r.get("identifier", [])))
    else:
        srs = source.rechercher("ServiceRequest", identifier=accession)
    if not srs:
        sys.exit(f"Aucune demande (ServiceRequest) avec le numéro d'examen {accession}.")
    sr = srs[0]
    if sr.get("status") in ("revoked", "entered-in-error"):
        sys.exit(f"La demande {accession} est annulée (status={sr['status']}) : pas de worklist.")
    patient = source.lire(sr["subject"]["reference"])
    ref_sr = f"ServiceRequest/{sr['id']}"
    if isinstance(source, SourceBundle):
        rdvs = source.chercher("Appointment", lambda r: any(b.get("reference") == ref_sr for b in r.get("basedOn", [])))
    else:
        rdvs = source.rechercher("Appointment", **{"based-on": ref_sr})
    rdvs = [r for r in rdvs if r.get("status") not in ("cancelled", "noshow", "entered-in-error")]
    if not rdvs:
        sys.exit(f"La demande {accession} n'est pas encore programmée (aucun Appointment actif).")
    rdv = rdvs[0]
    salle = next((source.lire(p["actor"]["reference"]) for p in rdv.get("participant", [])
                  if p.get("actor", {}).get("reference", "").startswith("Location/")), None)
    prescripteur = source.lire(sr["requester"]["reference"]) if sr.get("requester") else None
    return sr, patient, rdv, salle, prescripteur


# ---------- Construction de l'entrée de worklist ----------
def nom_dicom(nom_fhir):
    """HumanName FHIR -> Person Name DICOM « NOM^Prénom^^Titre »."""
    n = nom_fhir[0]
    return "^".join([n.get("family", ""), " ".join(n.get("given", [])), "", " ".join(n.get("prefix", []))]).rstrip("^")


def date_heure(fhir_datetime):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}):?(\d{2})?)?", fhir_datetime)
    d = "".join(m.group(1, 2, 3))
    h = "".join(x or "00" for x in m.group(4, 5, 6)) if m.group(4) else ""
    return d, h


def construire_worklist(sr, patient, rdv, salle, prescripteur, accession, aet_station, modalite):
    ds = Dataset()
    ds.SpecificCharacterSet = "ISO_IR 192"  # UTF-8 (accents)
    # Patient
    ds.PatientName = nom_dicom(patient["name"])
    ds.PatientID = next(i["value"] for i in patient["identifier"])
    ds.IssuerOfPatientID = "SIH-ITS"
    ds.PatientBirthDate = patient.get("birthDate", "").replace("-", "")
    ds.PatientSex = {"male": "M", "female": "F"}.get(patient.get("gender"), "O")
    # Demande (Requested Procedure)
    ds.AccessionNumber = accession
    ds.ReferringPhysicianName = nom_dicom(prescripteur["name"]) if prescripteur else ""
    ds.StudyInstanceUID = study_uid_depuis_accession(accession)
    ds.RequestedProcedureID = accession
    ds.RequestedProcedureDescription = sr["code"].get("text", "")[:64]
    code = sr["code"]["coding"][0]
    proc = Dataset()
    proc.CodeValue, proc.CodingSchemeDesignator, proc.CodeMeaning = code["code"], "LN", code.get("display", "")[:64]
    ds.RequestedProcedureCodeSequence = [proc]
    ds.ReasonForTheRequestedProcedure = (sr.get("reasonCode") or [{}])[0].get("text", "")[:64]
    # Étape programmée (Scheduled Procedure Step) – vient de l'Appointment
    sps = Dataset()
    sps.Modality = modalite
    sps.ScheduledStationAETitle = aet_station
    sps.ScheduledProcedureStepStartDate, sps.ScheduledProcedureStepStartTime = date_heure(rdv["start"])
    sps.ScheduledProcedureStepID = "SPS-" + accession.removeprefix("ACC-")  # SH : 16 caractères max
    sps.ScheduledProcedureStepDescription = rdv.get("description", sr["code"].get("text", ""))[:64]
    sps.ScheduledProcedureStepLocation = (salle or {}).get("name", "")[:16]
    sps.ScheduledProcedureStepStatus = "SCHEDULED"
    ds.ScheduledProcedureStepSequence = [sps]
    # En-tête de fichier DICOM (Part 10) attendu par le plugin Worklists d'Orthanc
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = MWL_FIND
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds.file_meta = meta
    return ds


def main():
    p = argparse.ArgumentParser(description="Crée ou supprime une entrée de worklist DICOM (.wl) pour Orthanc.")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--fhir", help="URL du serveur FHIR, ex. http://localhost:8080/fhir")
    src.add_argument("--bundle", help="Bundle FHIR JSON local, ex. ../../fhir/scenario-complet.json")
    p.add_argument("--accession", required=True, help="Numéro d'examen, ex. ACC-2026-0001")
    p.add_argument("--aet-station", default="MODSIM", help="AE Title de la modalité qui réalisera l'examen")
    p.add_argument("--modalite", default="CR", help="Type de modalité DICOM (CR, DX, CT, MR…)")
    p.add_argument("--sortie", default=str(DOSSIER_PAR_DEFAUT), help="Dossier des worklists lu par Orthanc")
    p.add_argument("--utilisateur", default=os.environ.get("FHIR_UTILISATEUR"))
    p.add_argument("--mot-de-passe", default=os.environ.get("FHIR_MOT_DE_PASSE"))
    p.add_argument("--supprimer", action="store_true", help="Supprime l'entrée (examen réalisé ou annulé)")
    a = p.parse_args()

    fichier = Path(a.sortie) / f"{a.accession}.wl"
    if a.supprimer:
        if fichier.exists():
            fichier.unlink()
            print(f"Entrée supprimée : {fichier}")
        else:
            print(f"Aucune entrée à supprimer : {fichier}")
        return
    if not (a.fhir or a.bundle):
        p.error("indiquer --fhir ou --bundle")

    source = SourceFhir(a.fhir, a.utilisateur, a.mot_de_passe) if a.fhir else SourceBundle(a.bundle)
    sr, patient, rdv, salle, prescripteur = charger_examen(source, a.accession)
    ds = construire_worklist(sr, patient, rdv, salle, prescripteur, a.accession, a.aet_station, a.modalite)
    fichier.parent.mkdir(parents=True, exist_ok=True)
    ds.save_as(fichier, enforce_file_format=True)
    sps = ds.ScheduledProcedureStepSequence[0]
    print(f"Worklist créée : {fichier}")
    print(f"  Patient       : {ds.PatientName} ({ds.PatientID})")
    print(f"  Examen        : {ds.AccessionNumber} – {ds.RequestedProcedureDescription}")
    print(f"  Programmé le  : {sps.ScheduledProcedureStepStartDate} à {sps.ScheduledProcedureStepStartTime}"
          f" sur {sps.ScheduledStationAETitle} ({sps.Modality})")
    print(f"  StudyInstanceUID : {ds.StudyInstanceUID}")


if __name__ == "__main__":
    main()
