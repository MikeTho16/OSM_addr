#!/usr/bin/python3
"""Unit tests for the addr_prep program.

Usage:
$ python3 addr_prep_test.py

"""
import unittest
import addr_prep

class UnitTestCase(unittest.TestCase):
    def setUp(self):
        addr_prep.get_conf()

    def test_unit_label(self):
        label, unit_id  = addr_prep.make_addr_unit_and_label('APT', '5')
        self.assertEqual(label, 'Apartment')
        self.assertEqual(unit_id, '5')
        label, unit_id  = addr_prep.make_addr_unit_and_label('', 'APT 5')
        self.assertEqual(label, 'Apartment')
        self.assertEqual(unit_id, '5')
        label, unit_id  = addr_prep.make_addr_unit_and_label('', 'apt 5')
        self.assertEqual(label, 'Apartment')
        self.assertEqual(unit_id, '5')
        label, unit_id  = addr_prep.make_addr_unit_and_label('', 'APT5')
        self.assertEqual(label, 'Apartment')
        self.assertEqual(unit_id, '5')
        label, unit_id  = addr_prep.make_addr_unit_and_label('', 'BSMT')
        self.assertEqual(label, '')
        self.assertEqual(unit_id, 'Basement')
        label, unit_id  = addr_prep.make_addr_unit_and_label('BSMT', '')
        self.assertEqual(label, '')
        self.assertEqual(unit_id, 'Basement')
        label, unit_id  = addr_prep.make_addr_unit_and_label('', '')
        self.assertEqual(label, '')
        self.assertEqual(unit_id, '')
        label, unit_id  = addr_prep.make_addr_unit_and_label('UNIT', 'OFC')
        self.assertEqual(label, 'Unit')
        self.assertEqual(unit_id, 'Office')

if __name__ == '__main__':
    unittest.main()
