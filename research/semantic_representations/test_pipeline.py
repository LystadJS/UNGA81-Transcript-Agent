"""Synthetic-only regression suite; never imports or opens UN transcript content."""
import copy
import json
import math
import pathlib
import tempfile
import unittest

from pipeline import digest, sha, validate_frame, frame_identity, encode, SCHEMA
from fixtures import (fixture_frame, FixtureEncoder, FIXTURE_MODEL, LEXICAL_MODEL,
                      SEMANTIC_SETTINGS, LEXICAL_SETTINGS, contrast_audit)
from comparison import (validate_paired, neighborhood, adjusted_rand, medoid_fit,
                        clustering_sensitivity)
from interchange import (lexical_reference, readonly_browser, check_parallel_v1,
                         LEXICAL)
from local_model import UPSTREAM_GIT_BLOBS, DEPENDENCIES, verify_source, REVISION


def make_saved(frame, vector_view):
    return {"schema":LEXICAL, "method":"lsa", "fit_source":"archived_saved_fit",
            "frame_sha256":frame_identity(frame), "source_schema":frame["source_schema"],
            "source_hash_basis":frame["source_hash_basis"], "source_sha256":frame["source_sha256"],
            "selection_sha256":frame["selection_sha256"],"population":frame["population"],
            "unit":frame["unit"],"representation_id":"saved-lsa-"+"a"*64,
            "representation_basis_id":"saved-lsa-"+"a"*64,
            "parameters_sha256":"b"*64,"model_sha256":"c"*64,"fit_version":"synthetic-saved-1",
            "source_observation_order":[r["id"] for r in frame["rows"]],
            "vectors":[{k:r[k] for k in ("id","text_sha256","source_sha256","vector","vector_sha256")}
                       for r in vector_view["rows"] if r["status"]=="encoded"]}


def sample_interchange():
    model={"model_id":"partition-1","representation_id":"rep-1"}
    x = {"schema":"un.parallel-analysis.v1","contract_version":"1.0.0",
            "producer":{"workstream_id":"W1"},
            "upstream":{"source_schema":"synthetic.v1","source_hash_basis":"synthetic",
                        "source_sha256":"a"*64,"selection_sha256":"b"*64},
            "cohort":{"split":"synthetic","eligible":2,"unit":"synthetic"},
            "observations":[{"id":"a","text_sha256":"c"*64,"unit":"synthetic","start":None,"end":None},
                            {"id":"b","text_sha256":"d"*64,"unit":"synthetic","start":None,"end":None},
                            {"id":"c","text_sha256":None,"unit":"synthetic","start":None,"end":None}],
            "models":[model],
            "results":[{"model_id":"partition-1","observation_id":"a","status":"assigned","cluster":1,"representation_basis_id":"rep-1"},
                       {"model_id":"partition-1","observation_id":"b","status":"unassigned","cluster":0,"representation_basis_id":"rep-1"},
                       {"model_id":"partition-1","observation_id":"c","status":"excluded","cluster":None,"reason":"absent source","representation_basis_id":"rep-1"}],
            "coverage":{"observations_total":3,"eligible":2,"excluded":1,
                        "models":[{"model_id":"partition-1","eligible":2,"assigned":1,"unassigned":1,
                                   "not_fitted":0,"excluded":1,"attempted_fits":1,"successful_fits":1,"failed_fits":0}]},
            "publication_eligible":False,"evaluation_role":"engineering_only"}

    x["producer"].update(adapter_version="1.0.0",code_sha256="e"*64,runtime="python-3.13",generated_at="2026-10-15T12:00:00Z",fixture_kind="synthetic")
    x["upstream"].update(source_engine="synthetic-test",frame_sha256=None,corpus_sha256=None,review_sha256=None,missing_reason=None)
    x["cohort"].update(population="synthetic_passages",selection_policy="all",weighting="equal_passage",source_group_unit="synthetic",duplicate_policy="retain",total_in_frame=3)
    for idx,o in enumerate(x["observations"]):
        o.update(parent_id=None,parent_text_sha256=None,meeting_id=None,speech_id=None,source_family_id=None,date="2026-10-01",country=None,source_url=None,json_pointer=None,review_status="not_applicable",exclusion_reasons=[],source_status="available",missing_reason=None)
        if idx==2:
            o.update(source_status="unavailable",missing_reason="absent source",exclusion_reasons=["missing_source"])
    model.update(method_family="partition",method="pam",representation_version="1",fit_version="1",fit_split="synthetic",parameters_sha256="f"*64,training_selection_sha256="b"*64,diagnostic_basis="synthetic")
    for r in x["results"]:
        r.update(membership_kind="none",memberships=None,membership_strength=None)
        r.setdefault("reason",None)
    x["coverage"].update(inventory_meetings=3,unavailable_sources=1,failure_ledger=[])
    x["evidence"]=[]
    x["diagnostics"]=[]
    x["limitations"]=[{"code":"synthetic","scope":"all","description":"fixture"}]
    return x


class SourceTests(unittest.TestCase):
    def setUp(self):self.frame=fixture_frame()
    def test_valid(self):self.assertEqual(validate_frame(self.frame)["eligible"],16)
    def test_identity_replay(self):self.assertEqual(frame_identity(self.frame),frame_identity(copy.deepcopy(self.frame)))
    def test_order_matters(self):
        changed=copy.deepcopy(self.frame);changed["rows"].reverse()
        self.assertNotEqual(frame_identity(self.frame),frame_identity(changed))
    def test_duplicate(self):
        f=copy.deepcopy(self.frame);f["rows"].append(copy.deepcopy(f["rows"][0]));f["inventory_total"]+=1
        with self.assertRaisesRegex(ValueError,"duplicate"):validate_frame(f)
    def test_text_hash_mutation(self):
        f=copy.deepcopy(self.frame);f["rows"][0]["text"]+=" x"
        with self.assertRaisesRegex(ValueError,"UTF8 text hash"):validate_frame(f)
    def test_nfc_is_not_silent(self):
        f=copy.deepcopy(self.frame);f["rows"][0]["text"]="Cafe\u0301"
        with self.assertRaises(ValueError):validate_frame(f)
    def test_reserved_holdout_rejected(self):
        f=copy.deepcopy(self.frame);f["split"]="holdout"
        with self.assertRaises(ValueError):validate_frame(f)
    def test_development_requires_real_source_schema(self):
        f=copy.deepcopy(self.frame);f["split"]="development"
        with self.assertRaises(ValueError):validate_frame(f)
    def test_unknown_hash_basis(self):
        f=copy.deepcopy(self.frame);f["source_hash_basis"]="guess"
        with self.assertRaises(ValueError):validate_frame(f)
    def test_unit_mismatch(self):
        f=copy.deepcopy(self.frame);f["rows"][0]["unit"]="passage"
        with self.assertRaises(ValueError):validate_frame(f)
    def test_parent_not_verified(self):
        f=copy.deepcopy(self.frame);f["rows"][0]["parent_id"]="parent1"
        with self.assertRaisesRegex(ValueError,"parent"):validate_frame(f)
    def test_bad_parent_span(self):
        f=copy.deepcopy(self.frame);r=f["rows"][0]
        r.update(parent_id="parent1",parent_text_sha256="d"*64,parent_length=10,start=0,end=11)
        with self.assertRaisesRegex(ValueError,"Unicode"):validate_frame(f)
    def test_good_parent_span(self):
        f=copy.deepcopy(self.frame);r=f["rows"][0]
        r.update(parent_id="parent1",parent_text_sha256="d"*64,parent_length=100,start=0,end=11)
        self.assertEqual(validate_frame(f)["eligible"],16)
    def test_unverified_speech(self):
        f=copy.deepcopy(self.frame);f["rows"][0]["speech_id"]="invented"
        with self.assertRaisesRegex(ValueError,"speech"):validate_frame(f)
    def test_missing_unavailable_classification(self):
        f=copy.deepcopy(self.frame);r=f["rows"][0]
        r.update(source_status="missing_transcript",text=None,missing_reason="not transcribed")
        a=validate_frame(f)
        self.assertEqual((a["eligible"],a["unavailable"]),(15,1))
    def test_no_false_negative_from_missing(self):
        f=copy.deepcopy(self.frame);r=f["rows"][0]
        r.update(source_status="missing_document",text=None,missing_reason=None)
        with self.assertRaisesRegex(ValueError,"reason"):validate_frame(f)
    def test_excluded_not_encoded(self):
        f=copy.deepcopy(self.frame);r=f["rows"][0]
        r.update(exclusion_reasons=["duplicate"],text=None,missing_reason="excluded duplicate")
        self.assertEqual(validate_frame(f)["excluded"],1)
    def test_unknown_source_url(self):
        f=copy.deepcopy(self.frame);f["rows"][0]["source_url"]="http://example.org"
        with self.assertRaises(ValueError):validate_frame(f)
    def test_empty_source_frame(self):
        f=copy.deepcopy(self.frame);f["rows"]=[]
        with self.assertRaises(ValueError):validate_frame(f)
    def test_ledger_inventory_missing(self):
        f=copy.deepcopy(self.frame);f["inventory_total"]+=3
        self.assertEqual(validate_frame(f)["not_in_frame"],3)


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.frame=fixture_frame()
        self.tmp=tempfile.TemporaryDirectory()
        self.root=pathlib.Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def run_fixture(self,model=FIXTURE_MODEL,settings=SEMANTIC_SETTINGS,encoder=None,frame=None):
        return encode(frame or self.frame, model,settings,encoder or FixtureEncoder(),self.root,batch_size=3)
    def test_cache_replay(self):
        a=self.run_fixture();encoder=FixtureEncoder();b=self.run_fixture(encoder=encoder)
        self.assertEqual(a["rows"],b["rows"]);self.assertEqual(encoder.calls,0)
        self.assertEqual(b["coverage"]["cache_hits"],16)
    def test_restart_partial_failure(self):
        bad=FixtureEncoder(fail_text="ceasefire");first=self.run_fixture(encoder=bad)
        self.assertGreater(first["coverage"]["not_fitted"],0)
        self.assertGreater(first["coverage"]["encoded"],0)
        self.assertEqual(first["coverage"]["attempted_batches"],6)
        second=self.run_fixture()
        self.assertEqual(second["coverage"]["encoded"],16)
        self.assertEqual(second["coverage"]["cache_hits"],first["coverage"]["encoded"])
    def test_vector_mutation_detected(self):
        self.run_fixture();file=next(self.root.glob("*.json"));obj=json.loads(file.read_text())
        obj["vector"][0]+=0.01;file.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ValueError,"corrupted"):self.run_fixture()
    def test_cache_id_mutation_detected(self):
        self.run_fixture();file=next(self.root.glob("*.json"));obj=json.loads(file.read_text())
        obj["key"]="invalid";file.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ValueError,"identity"):self.run_fixture()
    def test_source_change_not_cached(self):
        self.run_fixture();changed=copy.deepcopy(self.frame);changed["rows"][0]["source_sha256"]="c"*64
        out=self.run_fixture(frame=changed)
        self.assertEqual(out["coverage"]["cache_hits"],0)
    def test_selection_change_not_cached(self):
        self.run_fixture();changed=copy.deepcopy(self.frame);changed["selection_sha256"]="d"*64
        self.assertEqual(self.run_fixture(frame=changed)["coverage"]["cache_hits"],0)
    def test_model_change_not_cached(self):
        self.run_fixture();self.assertEqual(self.run_fixture(model=LEXICAL_MODEL)["coverage"]["cache_hits"],0)
    def test_settings_change_not_cached(self):
        self.run_fixture();self.assertEqual(self.run_fixture(settings=LEXICAL_SETTINGS)["coverage"]["cache_hits"],0)
    def test_token_length_overflow_chunked(self):
        f=fixture_frame();r=f["rows"][0];r["text"]="climate "*600
        r["text_sha256"]=sha(r["text"].encode())
        out=self.run_fixture(frame=f)
        self.assertEqual(out["rows"][0]["tokens"],600)
        self.assertEqual(out["rows"][0]["chunks"],3)
        self.assertEqual(out["coverage"]["not_fitted"],0)
    def test_chunk_boundary(self):
        f=fixture_frame();r=f["rows"][0];r["text"]="climate "*254
        r["text_sha256"]=sha(r["text"].encode())
        self.assertEqual(self.run_fixture(frame=f)["rows"][0]["chunks"],1)
    def test_unicode_tail_full_coverage(self):
        f=fixture_frame();r=f["rows"][0];r["text"]="🌎 à 🌎 "*300
        r["text_sha256"]=sha(r["text"].encode())
        self.assertGreater(self.run_fixture(frame=f)["rows"][0]["chunks"],1)
    def test_failed_batch_not_claimed_success(self):
        f=fixture_frame();broken=FixtureEncoder(fail_text="financial");o=self.run_fixture(frame=f,encoder=broken)
        self.assertGreater(o["coverage"]["failed_batches"],0)
        self.assertEqual(o["coverage"]["successful_batches"]+o["coverage"]["failed_batches"],o["coverage"]["attempted_batches"])
        self.assertEqual(o["coverage"]["encoded"]+o["coverage"]["not_fitted"],16)
    def test_cache_not_raw_text(self):
        self.run_fixture();cache=''.join(p.read_text() for p in self.root.glob("*.json"))
        self.assertNotIn("We support ending financial",cache)
    def test_no_cache_symlink(self):
        root=self.root/"alias";root.symlink_to(self.root)
        with self.assertRaisesRegex(ValueError,"symlink"):encode(self.frame,FIXTURE_MODEL,SEMANTIC_SETTINGS,FixtureEncoder(),root)
    def test_bad_encoder_cannot_claim_truncation(self):
        class Broken:
            def encode(self,rows,batch_size): return [[1.0] for _ in rows],[],{"passages":len(rows),"chunks":0,"truncated_wordpieces":10}
        self.assertEqual(self.run_fixture(encoder=Broken())["coverage"]["not_fitted"],16)


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture_frame();self.tmp=tempfile.TemporaryDirectory();p=pathlib.Path(self.tmp.name)
        self.semantic=encode(self.f,FIXTURE_MODEL,SEMANTIC_SETTINGS,FixtureEncoder(),p/"s")
        self.lexical=encode(self.f,LEXICAL_MODEL,LEXICAL_SETTINGS,FixtureEncoder(lexical=True),p/"l")
    def tearDown(self):self.tmp.cleanup()
    def test_paired(self):self.assertEqual(validate_paired(self.lexical,self.semantic)["paired"],16)
    def test_identical_identity_refused(self):
        with self.assertRaisesRegex(ValueError,"indistinct"):validate_paired(self.semantic,self.semantic)
    def test_source_sha_refused(self):
        other=copy.deepcopy(self.semantic);other["rows"][0]["source_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"lineage"):validate_paired(self.lexical,other)
    def test_hash_basis_refused(self):
        other=copy.deepcopy(self.semantic);other["source_hash_basis"]="raw_response_bytes"
        with self.assertRaisesRegex(ValueError,"incompatible"):validate_paired(self.lexical,other)
    def test_selection_refused(self):
        other=copy.deepcopy(self.semantic);other["selection_sha256"]="d"*64
        with self.assertRaises(ValueError):validate_paired(self.lexical,other)
    def test_unit_refused(self):
        other=copy.deepcopy(self.semantic);other["unit"]="passage"
        with self.assertRaises(ValueError):validate_paired(self.lexical,other)
    def test_basis_refused(self):
        other=copy.deepcopy(self.semantic);other["representation_basis_id"]="wrong"
        with self.assertRaisesRegex(ValueError,"basis"):validate_paired(self.lexical,other)
    def test_population_order_refused(self):
        other=copy.deepcopy(self.semantic);other["rows"].reverse()
        with self.assertRaises(ValueError):validate_paired(self.lexical,other)
    def test_vector_sha_refused(self):
        other=copy.deepcopy(self.semantic);other["rows"][0]["vector"][0]+=0.01
        with self.assertRaisesRegex(ValueError,"vector hash"):validate_paired(self.lexical,other)
    def test_neighbor_denominator(self):
        result=neighborhood(self.lexical,self.semantic,2)
        self.assertEqual((result["assessable"],result["counts"]["paired"]),(16,16))
        self.assertGreaterEqual(result["overlap_mean"],0)
        self.assertLessEqual(result["overlap_mean"],1)
    def test_exclude_meeting(self):
        result=neighborhood(self.lexical,self.semantic,2,"meeting")
        meetings={r["id"]:r["meeting_id"] for r in self.semantic["rows"]}
        for point in result["points"]:
            for neighbor in point["semantic_neighbors"]:self.assertNotEqual(meetings[neighbor],meetings[point["id"]])
    def test_unverified_group_refused(self):
        other=copy.deepcopy(self.semantic);other["rows"][0]["meeting_id"]=None
        l=copy.deepcopy(self.lexical);l["rows"][0]["meeting_id"]=None
        with self.assertRaisesRegex(ValueError,"grouping"):neighborhood(l,other,1,"meeting")
    def test_no_denominator_shortcut(self):
        other=copy.deepcopy(self.semantic);other["rows"][0]["status"]="not_fitted"
        other["rows"][0]["vector"]=None;other["rows"][0]["vector_sha256"]=None
        counts=validate_paired(self.lexical,other)
        self.assertEqual((counts["paired"],counts["unpaired_left"]),(15,1))
        self.assertEqual(neighborhood(self.lexical,other,1)["counts"]["eligible"],16)
    def test_ari_label_permutation(self):self.assertAlmostEqual(adjusted_rand([1,1,2,2],[4,4,5,5]),1)
    def test_ari_difference(self):self.assertLess(adjusted_rand([1,1,2,2],[1,2,1,2]),1)
    def test_cluster_determinism(self):
        self.assertEqual(medoid_fit(self.semantic,3,42),medoid_fit(self.semantic,3,42))
    def test_cluster_audit(self):
        result=clustering_sensitivity(self.lexical,self.semantic,3,seeds=(11,17,23))
        self.assertEqual(result["planned_cross_pairs"],9)
        self.assertEqual(result["within_representation"]["semantic"]["attempted"],3)
    def test_contrast_negation_not_stance(self):
        result=contrast_audit(self.semantic)
        self.assertEqual(result["denominator"],4)
        self.assertTrue(all(c["stance_classification"]=="withheld" for c in result["cases"]))
        self.assertEqual(result["checkpoint_execution"],"NOT_RUN")
        self.assertEqual(result["paraphrase_closer_than_opposite"],4)


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture_frame();self.tmp=tempfile.TemporaryDirectory()
        self.v=encode(self.f,LEXICAL_MODEL,LEXICAL_SETTINGS,FixtureEncoder(lexical=True),pathlib.Path(self.tmp.name))
        self.saved=make_saved(self.f,self.v)
    def tearDown(self):self.tmp.cleanup()
    def test_saved_lexical(self):
        imported=lexical_reference(self.f,self.saved)
        self.assertEqual(imported["coverage"]["encoded"],16)
    def test_lexical_cannot_refit(self):
        bad=copy.deepcopy(self.saved);bad["fit_source"]="new_fit"
        with self.assertRaises(ValueError):lexical_reference(self.f,bad)
    def test_wrong_saved_basis(self):
        bad=copy.deepcopy(self.saved);bad["representation_basis_id"]="changed"
        with self.assertRaises(ValueError):lexical_reference(self.f,bad)
    def test_missing_saved_rows(self):
        bad=copy.deepcopy(self.saved);bad["vectors"].pop()
        with self.assertRaises(ValueError):lexical_reference(self.f,bad)
    def test_changed_saved_source(self):
        bad=copy.deepcopy(self.saved);bad["vectors"][0]["text_sha256"]="e"*64
        with self.assertRaises(ValueError):lexical_reference(self.f,bad)
    def test_readonly_drops_vectors_and_text(self):
        view=readonly_browser(self.v,public=True)
        self.assertEqual(view["schema"],"un.semantic-readonly.v1")
        self.assertNotIn("vector",view["rows"][0]);self.assertNotIn("text",view["rows"][0])
        self.assertFalse(view["publication_eligible"])
    def test_public_development_rejected(self):
        bad=copy.deepcopy(self.v);bad["split"]="development"
        with self.assertRaisesRegex(ValueError,"public"):readonly_browser(bad,public=True)
    def test_readonly_duplicate_refusal(self):
        bad=copy.deepcopy(self.v);bad["rows"][1]["id"]=bad["rows"][0]["id"]
        with self.assertRaisesRegex(ValueError,"duplicate"):readonly_browser(bad)
    def test_parallel_v1_valid(self):
        self.assertEqual(check_parallel_v1(sample_interchange())["observation_count"],3)
    def test_parallel_v1_wrong_basis(self):
        bad=sample_interchange();bad["results"][0]["representation_basis_id"]="different"
        with self.assertRaises(ValueError):check_parallel_v1(bad)
    def test_parallel_v1_missing_pair(self):
        bad=sample_interchange();bad["results"].pop()
        with self.assertRaises(ValueError):check_parallel_v1(bad)
    def test_parallel_v1_duplicate_pair(self):
        bad=sample_interchange();bad["results"].append(bad["results"][0])
        with self.assertRaises(ValueError):check_parallel_v1(bad)
    def test_parallel_v1_wrong_offset(self):
        bad=sample_interchange();bad["observations"][0].update(start=10,end=3)
        with self.assertRaises(ValueError):check_parallel_v1(bad)
    def test_parallel_v1_fake_status(self):
        bad=sample_interchange();bad["results"][0].update(status="assigned",cluster=0)
        with self.assertRaises(ValueError):check_parallel_v1(bad)
    def test_parallel_v1_failed_fit_count(self):
        bad=sample_interchange();bad["coverage"]["models"][0]["failed_fits"]=1
        with self.assertRaises(ValueError):check_parallel_v1(bad)
    def test_parallel_v1_official_synthetic_example(self):
        import json
        from pathlib import Path
        official = Path(__file__).with_name("official_v1_synthetic.json")
        self.assertEqual(check_parallel_v1(json.loads(official.read_text()))["observation_count"], 1)
    def test_parallel_v1_missing_reason(self):
        bad=sample_interchange();bad["observations"][2]["missing_reason"]=None
        with self.assertRaises(ValueError):check_parallel_v1(bad)
    def test_parallel_v1_parent_missing_hash(self):
        bad=sample_interchange();bad["observations"][0]["parent_id"]="p"
        with self.assertRaises(ValueError):check_parallel_v1(bad)
    def test_parallel_v1_unverified_speech(self):
        bad=sample_interchange();bad["observations"][0]["speech_id"]="fabricated"
        with self.assertRaises(ValueError):check_parallel_v1(bad)
    def test_parallel_v1_invalid_membership(self):
        bad=sample_interchange();bad["results"][0].update(membership_kind="nmf_share",memberships=[0.1,0.2])
        with self.assertRaises(ValueError):check_parallel_v1(bad)
    def test_parallel_v1_orphan_evidence(self):
        bad=sample_interchange();bad["evidence"].append({"observation_id":"missing"})
        with self.assertRaises(ValueError):check_parallel_v1(bad)
    def test_parallel_v1_eligible_population(self):
        bad=sample_interchange();bad["observations"][1]["exclusion_reasons"]=["declared_exclusion"]
        with self.assertRaises(ValueError):check_parallel_v1(bad)
    def test_parallel_v1_missing_failed_reason(self):
        bad=sample_interchange();bad["diagnostics"].append({"model_id":None,"status":"failed","reason":None})
        with self.assertRaises(ValueError):check_parallel_v1(bad)
    def test_parallel_v1_reserved_development_date(self):
        bad=sample_interchange();bad["cohort"]["split"]="development"
        bad["producer"]["fixture_kind"]="private_development"
        bad["observations"][0]["date"]="2026-10-05"
        with self.assertRaises(ValueError):check_parallel_v1(bad)
    def test_parallel_v1_unregistered_w8(self):
        bad=sample_interchange();bad["producer"]["workstream_id"]="W8"
        with self.assertRaises(ValueError):check_parallel_v1(bad)


class LockTests(unittest.TestCase):
    def test_exact_checkpoint_revision(self):self.assertEqual(len(REVISION),40)
    def test_requirements_frozen(self):self.assertEqual(DEPENDENCIES["onnxruntime"],"1.23.0")
    def test_sources_have_git_blobs(self):
        self.assertEqual(len(UPSTREAM_GIT_BLOBS),3)
        self.assertTrue(all(len(v)==40 for v in UPSTREAM_GIT_BLOBS.values()))
    def test_missing_local_upstream_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):verify_source(pathlib.Path(d))


# Extra cross-process replay checks use a fresh cache, without checkpoint downloads.
class CliTests(unittest.TestCase):
    def test_cli_independent_process_replay(self):
        import subprocess, sys
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            script=pathlib.Path(__file__).with_name("cli.py")
            def invoke(out):
                return subprocess.run([sys.executable,str(script),"synthetic","--cache",str(root/"cache"),
                                       "--output",str(root/out),"--k","3"],check=True,capture_output=True,text=True)
            invoke("first.json")
            second=invoke("second.json")
            a=json.loads((root/"first.json").read_text());b=json.loads((root/"second.json").read_text())
            self.assertEqual(a["semantic_readonly"]["representation_id"],b["semantic_readonly"]["representation_id"])
            self.assertEqual(b["semantic_coverage"]["cache_hits"],16)
            self.assertEqual(b["semantic_coverage"]["cache_misses"],0)
            self.assertGreaterEqual(a["synthetic_length_sensitivity"]["long_chunks"],3)
            self.assertEqual(a["synthetic_contrasts"]["paraphrase_closer_than_opposite"],4)
            self.assertIn('"status": "completed"',second.stdout)
    def test_cli_no_overwrite(self):
        from cli import main
        with tempfile.TemporaryDirectory() as d:
            path=pathlib.Path(d);outfile=path/"report.json"
            self.assertEqual(main(["synthetic","--cache",str(path/"cache"),"--output",str(outfile)]),0)
            with self.assertRaises(FileExistsError):main(["synthetic","--cache",str(path/"cache"),"--output",str(outfile)])
    def test_cli_refuses_repo_cache(self):
        from cli import private_path
        with self.assertRaisesRegex(ValueError,"public repository"):private_path(pathlib.Path(__file__).resolve().parent/"private-data")

if __name__ == "__main__":
    unittest.main(verbosity=2)
