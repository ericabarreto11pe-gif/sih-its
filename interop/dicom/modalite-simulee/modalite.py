#!/usr/bin/env python3
"""
Modalité d'imagerie simulée (radiographie « CR »).

Ce que fait une vraie modalité, et ce que fait ce script :
  1. C-FIND sur la worklist (MWL) d'Orthanc : « quels examens sont prévus pour moi ? »
  2. choix de l'examen (par numéro d'examen, sinon le premier de la liste) ;
  3. « acquisition » : génération d'une image synthétique (aucune donnée réelle),
     avec les identifiants recopiés depuis la worklist (patient, AccessionNumber,
     StudyInstanceUID) – c'est ce qui garantit la traçabilité demande ↔ étude ;
  4. C-STORE de l'image vers Orthanc.

Exemples :
  python modalite.py --lister                         # voir la worklist du jour
  python modalite.py --lister --date toutes           # toutes les dates
  python modalite.py --accession ACC-2026-0001 --date toutes
  python modalite.py --hote 192.168.56.13 --port 4242 --aet-pacs ORTHANC --accession ACC-2026-0001
"""
import argparse
import datetime as dt
import sys
from pathlib import Path

import numpy as np
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, ImplicitVRLittleEndian, generate_uid
from pynetdicom import AE
from pynetdicom.sop_class import ComputedRadiographyImageStorage, ModalityWorklistInformationFind

CR_IMAGE = "1.2.840.10008.5.1.4.1.1.1"


def interroger_worklist(args):
    """C-FIND MWL : retourne la liste des entrées programmées pour cette modalité."""
    ae = AE(ae_title=args.aet)
    ae.add_requested_context(ModalityWorklistInformationFind)
    requete = Dataset()
    requete.SpecificCharacterSet = "ISO_IR 192"
    for mot in ("PatientName", "PatientID", "PatientBirthDate", "PatientSex", "StudyInstanceUID",
                "ReferringPhysicianName", "RequestedProcedureID", "RequestedProcedureDescription"):
        setattr(requete, mot, "")
    requete.AccessionNumber = args.accession or ""
    sps = Dataset()
    sps.ScheduledStationAETitle = args.aet
    sps.Modality = ""
    sps.ScheduledProcedureStepStartDate = "" if args.date == "toutes" else args.date
    sps.ScheduledProcedureStepStartTime = ""
    sps.ScheduledProcedureStepID = ""
    sps.ScheduledProcedureStepDescription = ""
    sps.ScheduledProcedureStepLocation = ""
    requete.ScheduledProcedureStepSequence = [sps]

    assoc = ae.associate(args.hote, args.port, ae_title=args.aet_pacs)
    if not assoc.is_established:
        sys.exit(f"Connexion DICOM refusée ou impossible vers {args.aet_pacs}@{args.hote}:{args.port}. "
                 "Vérifier que la modalité est déclarée dans Orthanc (DicomModalities) et que le port est ouvert.")
    resultats = []
    try:
        for statut, ident in assoc.send_c_find(requete, ModalityWorklistInformationFind):
            if statut is None:
                sys.exit("Pas de réponse du PACS (délai dépassé).")
            if statut.Status in (0xFF00, 0xFF01) and ident is not None:
                resultats.append(ident)
            elif statut.Status not in (0x0000, 0xFF00, 0xFF01):
                sys.exit(f"C-FIND refusé, statut 0x{statut.Status:04X}")
    finally:
        assoc.release()
    return resultats


def image_thorax_synthetique(taille=512, graine=0):
    """Image 12 bits qui ressemble vaguement à une radio du thorax (formes géométriques + bruit)."""
    rng = np.random.default_rng(graine)
    y, x = np.mgrid[0:taille, 0:taille] / taille
    img = np.full((taille, taille), 150.0)
    torse = ((x - 0.5) / 0.42) ** 2 + ((y - 0.55) / 0.48) ** 2 < 1
    img[torse] = 2200
    for cx in (0.33, 0.67):  # poumons (air = sombre)
        poumon = ((x - cx) / 0.15) ** 2 + ((y - 0.48) / 0.3) ** 2 < 1
        cotes = 0.5 + 0.5 * np.sin(y * 70)
        img[poumon] = 700 + 450 * cotes[poumon]
    img[(abs(x - 0.5) < 0.035) & torse] = 3300  # rachis
    coeur = ((x - 0.56) / 0.12) ** 2 + ((y - 0.62) / 0.12) ** 2 < 1
    img[coeur] = 2700
    img += rng.normal(0, 60, img.shape)
    return np.clip(img, 0, 4095).astype(np.uint16)


def creer_image(entree, args):
    """Construit une instance DICOM CR en recopiant les identifiants de la worklist."""
    sps = entree.ScheduledProcedureStepSequence[0] if "ScheduledProcedureStepSequence" in entree else Dataset()
    maintenant = dt.datetime.now()
    ds = Dataset()
    ds.SpecificCharacterSet = "ISO_IR 192"
    ds.SOPClassUID = CR_IMAGE
    ds.SOPInstanceUID = generate_uid(prefix=None)
    # --- recopiés depuis la worklist : c'est le cœur de la traçabilité ---
    for mot in ("PatientName", "PatientID", "PatientBirthDate", "PatientSex",
                "AccessionNumber", "StudyInstanceUID", "ReferringPhysicianName"):
        setattr(ds, mot, entree.get(mot, ""))
    ds.IssuerOfPatientID = "SIH-ITS"
    ds.StudyDescription = entree.get("RequestedProcedureDescription", "")
    ds.StudyID = (entree.get("RequestedProcedureID", "") or "1")[:16]
    attr = Dataset()  # lien explicite vers la demande et l'étape programmée
    attr.AccessionNumber = entree.get("AccessionNumber", "")
    attr.RequestedProcedureID = entree.get("RequestedProcedureID", "")
    attr.ScheduledProcedureStepID = sps.get("ScheduledProcedureStepID", "")
    attr.ScheduledProcedureStepDescription = sps.get("ScheduledProcedureStepDescription", "")
    ds.RequestAttributesSequence = [attr]
    # --- produits par la modalité ---
    ds.StudyDate = ds.SeriesDate = ds.ContentDate = maintenant.strftime("%Y%m%d")
    ds.StudyTime = ds.SeriesTime = ds.ContentTime = maintenant.strftime("%H%M%S")
    ds.Modality = "CR"
    ds.Manufacturer = "SIH-ITS"
    ds.ManufacturerModelName = "Modalite simulee (pas un dispositif medical)"
    ds.StationName = args.aet
    ds.InstitutionName = "Hopital ITS (fictif)"
    ds.SeriesInstanceUID = generate_uid(prefix=None)
    ds.SeriesNumber = 1
    ds.SeriesDescription = "Thorax face"
    ds.InstanceNumber = 1
    ds.BodyPartExamined = "CHEST"
    ds.ViewPosition = "PA"
    ds.PatientOrientation = ["L", "F"]
    pixels = image_thorax_synthetique()
    ds.Rows, ds.Columns = pixels.shape
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated, ds.BitsStored, ds.HighBit, ds.PixelRepresentation = 16, 12, 11, 0
    ds.WindowCenter, ds.WindowWidth = 2048, 4096
    ds.PixelData = pixels.tobytes()
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = CR_IMAGE
    meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds.file_meta = meta
    return ds


def envoyer(ds, args):
    ae = AE(ae_title=args.aet)
    ae.add_requested_context(ComputedRadiographyImageStorage, [ExplicitVRLittleEndian, ImplicitVRLittleEndian])
    assoc = ae.associate(args.hote, args.port, ae_title=args.aet_pacs)
    if not assoc.is_established:
        sys.exit("Association C-STORE impossible.")
    try:
        statut = assoc.send_c_store(ds)
    finally:
        assoc.release()
    if not statut or statut.Status != 0x0000:
        sys.exit(f"C-STORE en échec : {statut}")


def main():
    p = argparse.ArgumentParser(description="Modalité DICOM simulée : worklist (C-FIND) puis envoi d'image (C-STORE).")
    p.add_argument("--hote", default="localhost", help="Adresse d'Orthanc")
    p.add_argument("--port", type=int, default=4242, help="Port DICOM d'Orthanc")
    p.add_argument("--aet-pacs", default="ORTHANC", help="AE Title d'Orthanc")
    p.add_argument("--aet", default="MODSIM", help="AE Title de cette modalité (déclaré dans Orthanc)")
    p.add_argument("--date", default=dt.date.today().strftime("%Y%m%d"), help="AAAAMMJJ, ou « toutes »")
    p.add_argument("--accession", help="Numéro d'examen à réaliser (sinon : premier de la liste)")
    p.add_argument("--lister", action="store_true", help="Affiche la worklist sans rien envoyer")
    p.add_argument("--copie", help="Dossier où garder une copie du fichier DICOM envoyé")
    args = p.parse_args()

    entrees = interroger_worklist(args)
    print(f"Worklist reçue de {args.aet_pacs} : {len(entrees)} examen(s) programmé(s) pour {args.aet}")
    for e in entrees:
        s = e.ScheduledProcedureStepSequence[0]
        print(f"  - {e.AccessionNumber:<16} {str(e.PatientName):<22} {e.PatientID:<10} "
              f"{s.get('ScheduledProcedureStepStartDate', '')} {s.get('ScheduledProcedureStepStartTime', '')} "
              f"{e.get('RequestedProcedureDescription', '')}")
    if args.lister:
        return
    if not entrees:
        sys.exit("Rien à réaliser. Vérifier la date (--date toutes) et que le RIS a bien créé l'entrée.")
    choix = [e for e in entrees if not args.accession or e.AccessionNumber == args.accession]
    if not choix:
        sys.exit(f"{args.accession} n'est pas dans la worklist.")
    entree = choix[0]

    ds = creer_image(entree, args)
    envoyer(ds, args)
    if args.copie:
        Path(args.copie).mkdir(parents=True, exist_ok=True)
        ds.save_as(Path(args.copie) / f"{ds.AccessionNumber}_{ds.SOPInstanceUID}.dcm", enforce_file_format=True)
    print("\nImage envoyée à Orthanc :")
    print(f"  Patient          : {ds.PatientName} ({ds.PatientID})")
    print(f"  AccessionNumber  : {ds.AccessionNumber}")
    print(f"  StudyInstanceUID : {ds.StudyInstanceUID}")
    print(f"  SeriesInstanceUID: {ds.SeriesInstanceUID}")
    print(f"  SOPInstanceUID   : {ds.SOPInstanceUID}")
    print("Le RIS peut maintenant retrouver l'étude : POST /tools/find "
          f'{{"Level":"Study","Query":{{"AccessionNumber":"{ds.AccessionNumber}"}}}}')


if __name__ == "__main__":
    main()
