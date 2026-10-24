import unittest
from .countries import map_country
class CountryTests(unittest.TestCase):
    def test_explicit_iso3_case_independent_of_recorded_name(self):
        for name in ("UNITED STATES","United States of America","United States"):
            country=map_country("USA",name)
            self.assertEqual(country["country_id"],"United States")
            self.assertEqual(country["recorded_country_name"],name)
            self.assertEqual(country["country_mapping_status"],"registry_mapped")
            self.assertEqual(len(country["country_registry_sha256"]),64)
        self.assertEqual(map_country("NGA","NIGERIA")["country_id"],"Nigeria")
        self.assertEqual(map_country("PLW","PALAU")["country_id"],"Palau")
    def test_unknown_code_does_not_match_known_name(self):
        unknown=map_country("XXX","UNITED STATES")
        self.assertEqual(unknown["country_id"],"unmapped:XXX")
        self.assertEqual(unknown["country_mapping_status"],"unmapped_code")
        with self.assertRaises(ValueError):map_country("US","United States")
if __name__=="__main__":unittest.main()
