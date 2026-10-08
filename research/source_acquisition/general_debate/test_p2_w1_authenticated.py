"""Synthetic-only P2→W1 original source authentication tests."""
import io,hashlib,tarfile,tempfile,unittest,zipfile,pathlib
from p2_w1_authenticated import source_rows
H=lambda b:hashlib.sha256(b).hexdigest()
class AuthTests(unittest.TestCase):
    def setUp(self):
        self.work=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.work.name)
        self.pv=b"%PDF-1.7\nfictional synthetic document\n%%EOF\n"
        self.text=b"fictional synthetic country speech\n"
        self.pdfpath=self.root/"original_pvs.zip"
        with zipfile.ZipFile(self.pdfpath,"w") as z:z.writestr("original_UN_GA_PV/A_73_PV.13.pdf",self.pv)
        self.tarpath=self.root/"source.tar.gz"
        with tarfile.open(self.tarpath,"w:gz") as z:
            meta=tarfile.TarInfo("TXT/Session 73 - 2018/ZZZ_73_2018.txt");meta.size=len(self.text)
            z.addfile(meta,io.BytesIO(self.text))
        self.row={"id":"fictional-ZZZ-2018","source_status":"available","iso3":"ZZZ",
          "year":2018,"observed_p2_strong_match":True,"actor_kind":"recorded_affiliation",
          "person_identity_authenticated":False,"date_basis":"independent_UN_index",
          "source_hash_basis":"raw_response_bytes","meeting_id":"A/73/PV.13","source_family_id":"A/73/PV.13",
          "source_sha256":H(self.pv),"text_sha256":H(self.text),"date":"2018-09-25",
          "actor_id":"ZZZ","genre":"general_debate"}
        self.claim={"iso3":"ZZZ","year":"2018",
          "status":"strong_original_PV_full_speech_correspondence",
          "original_PV_Harvard_7gram_coverage":"0.99",
          "original_official_meeting_symbol":"A/73/PV.13",
          "official_PV_original_byte_sha256":H(self.pv),
          "Harvard_v14_corresponding_text_sha256":H(self.text),
          "official_date_from_UN_index":"2018-09-25"}
        self.manifest={"symbol":"A/73/PV.13","official_pdf_sha256":H(self.pv),
            "official_pdf_bytes":str(len(self.pv))}
        self.panel={"observations":[self.row,{"id":"fictional-unverified","iso3":"QQQ",
          "year":2017,"source_status":"unverified","date":None,
          "text_sha256":None,"source_sha256":None,"vector":None}]}
        self.unknown={"iso3":"QQQ","year":"2017","status":"unverified_not_absent"}
    def tearDown(self):self.work.cleanup()
    def call(self):
        return source_rows(self.panel,[self.claim,self.unknown],[self.manifest],
                           self.pdfpath,self.tarpath)
    def test_real_bytes_and_untouched_unverified_inventory(self):
        good,excluded,pvs=self.call()
        self.assertEqual((len(good),excluded,pvs),(1,1,1))
        self.assertEqual(good[0]["text_sha256"],H(self.text))
        self.assertEqual(good[0]["text"],self.text.decode())
    def test_reject_corrupt_un_pdf_hash(self):
        self.manifest["official_pdf_sha256"]=H(b"imposter")
        with self.assertRaises(AssertionError):self.call()
    def test_reject_misattributed_meeting(self):
        self.claim["original_official_meeting_symbol"]="A/73/PV.11"
        with self.assertRaises(AssertionError):self.call()
    def test_reject_insufficient_full_speech_correspondence(self):
        self.claim["original_PV_Harvard_7gram_coverage"]="0.25"
        with self.assertRaises(AssertionError):self.call()
    def test_reject_fake_person_authentication(self):
        self.row["person_identity_authenticated"]=True
        with self.assertRaises(AssertionError):self.call()
    def test_reject_wrong_speech_hash(self):
        self.row["text_sha256"]=H(b"wrong")
        with self.assertRaises(AssertionError):self.call()
    def test_unverified_must_remain_null(self):
        self.panel["observations"][1]["date"]="2017-09-24"
        with self.assertRaises(AssertionError):self.call()
if __name__=="__main__":unittest.main(verbosity=2)
