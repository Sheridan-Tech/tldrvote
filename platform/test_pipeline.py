"""Unit tests for schema, provenance, candidate-position parity and fail-closed gates."""
from pathlib import Path
import unittest,copy,hashlib,json
from datetime import datetime
from zoneinfo import ZoneInfo
from build_editions import build_clark,build_multnomah
from validate_release import qa
from election_tracker import registry,status
ROOT=Path(__file__).resolve().parent.parent
HERE=Path(__file__).resolve().parent
class ContractTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.clark=build_clark()
  cls.mult=build_multnomah()
 def test_counts(self):
  for d,topics,races,measures,people in [(self.clark,45,30,15,51),(self.mult,66,60,6,155)]:
   self.assertEqual(d["coverage"]["topics"],topics)
   self.assertEqual(d["coverage"]["races"],races)
   self.assertEqual(d["coverage"]["measures"],measures)
   self.assertEqual(d["coverage"]["candidates"],people)
 def test_qa_structural(self):
  for d in [self.clark,self.mult]:
   self.assertEqual(qa(d)["structural_status"],"PASS")
   self.assertEqual(qa(d)["authoritative_release"],"BLOCKED")
 def test_missing_source_fails(self):
  d=copy.deepcopy(self.mult)
  m=next(t for t in d["contests"] if t["kind"]=="measure")
  m["measure_sections"]["yes"]["source_ids"]=["not-a-source"]
  self.assertEqual(qa(d)["structural_status"],"FAIL")
 def test_forged_approval_fails(self):
  d=copy.deepcopy(self.clark)
  m=next(t for t in d["contests"] if t["kind"]=="race")
  m["office_role"]["status"]="EDITOR_APPROVED"
  self.assertEqual(qa(d)["structural_status"],"FAIL")
 def test_missing_stances_not_inferred(self):
  for d in [self.clark,self.mult]:
   for t in d["contests"]:
    if t["kind"]!="race":continue
    ids={c["id"] for c in t["candidates"]}
    for row in t["issue_matrix"]:
     self.assertEqual({p["candidate_id"] for p in row["positions"]},ids)
     for p in row["positions"]:
      if p["state"]=="NOT_FOUND":self.assertEqual(p["claim"]["status"],"UNKNOWN")
      if p["state"]=="MENTION_ONLY":self.assertNotEqual(p["claim"]["status"],"EDITOR_APPROVED")
 def test_original_pdf_bytes_match_manifest(self):
  pdfs=json.loads((ROOT/"multnomah/source_manifest.json").read_text("utf8"))
  self.assertEqual(len(pdfs),4)
  if not all((ROOT/'multnomah'/name).is_file() for name in pdfs):
   self.skipTest('Original pinned PDFs are not checked into Git; run source download/watch to reverify hashes')
  for name,metadata in pdfs.items():
   path=ROOT/'multnomah'/name
   self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),metadata['sha256'])
 def test_original_multnomah_match_report(self):
  audit=json.loads((ROOT/"multnomah/matched_profile_heading_audit.json").read_text("utf8"))
  self.assertEqual(audit["matched_profiles"],130)
  self.assertEqual(audit["suspicious_matches"],0)
  self.assertEqual(self.mult["coverage"]["unmatched_profiles"],25)
 def test_election_phase_no_inferred_certification(self):
  entries={e["id"]:e for e in registry()}
  tz=ZoneInfo("America/Los_Angeles")
  for entry in entries.values():
   self.assertEqual(status(entry,datetime(2026,10,1,tzinfo=tz)),"UPCOMING")
   self.assertEqual(status(entry,datetime(2026,10,20,tzinfo=tz)),"VOTING_PERIOD")
   self.assertEqual(status(entry,datetime(2026,11,3,21,tzinfo=tz)),"POLLS_CLOSED_CERTIFICATION_NOT_VERIFIED")
  self.assertEqual(status(entries["or-2026-11-03-general"],datetime(2026,12,1,tzinfo=tz)),"PAST_CERTIFICATION_DEADLINE_NOT_VERIFIED")
 def test_public_feedback_requires_verifiable_details(self):
  text=(ROOT/".github/ISSUE_TEMPLATE/correction.yml").read_text("utf8")
  for key in ["Exact TLDR Vote page","What exactly appears wrong","Supporting primary sources","Public report notice"]:
   self.assertIn(key,text)
if __name__=="__main__":unittest.main(verbosity=2)
