from tests.tests import MyTestCase
from tests.common import initValuesFactory
from tests.common import load_correct_answers

import json
import os

from pyramid.httpexceptions import (
    HTTPNotFound,
    HTTPOk,
    HTTPBadRequest,
    HTTPConflict,
    HTTPInternalServerError,
    HTTPUnauthorized,
    HTTPFound,
    HTTPForbidden
)

class LexicalEntriesTest(MyTestCase):

    def setUp(self):
        super(LexicalEntriesTest, self).setUp()
        self.id_tester = self.signup_common()
        self.id_u1 = self.signup_common('user1')
        self.id_u2 = self.signup_common('user2')
        self.id_l1 = self.create_language('language1')
        self.dict_1 = self.create_dictionary('user1_dict1', self.id_l1)
        self.persp_1 = self.create_perspective('translation_string1', self.dict_1, "Published", False)
        response = self.app.get('/dictionary/%s/%s/perspective/%s/%s/fields'
                                % (1, 1, 1, 1))
        fields = response.json
        response = self.app.post_json('/dictionary/%s/%s/perspective/%s/%s/fields'
                                      % (self.dict_1['client_id'], self.dict_1['object_id'],
                                         self.persp_1['client_id'], self.persp_1['object_id']),
                                      params=fields)

        self.strings = ["uyzrljiirs", "kxmzpclrns", "kgrrdjafqz", "jdavwdmuqe", "zlswwsfjrc", "bkrmwpshnh",
                       "cpnltteyzj", "iyornljisb", "ozidqyatiz", "hxjzmtthxp", "jlsodufkah", "wiymxkmzhs",
                       "hjwsojizle", "ylbrqdpzzp", "zeomhyqhwl", "ficbqfhrzv", "upmedjsbli", "ylbrqdpzzp",
                       "dgjomjdnhy", "wajysnmtvb"]

        params = initValuesFactory.get_role_params([self.id_u1, self.id_u2])
        response = self.app.post_json('/dictionary/%s/%s/perspective/%s/%s/roles' % (self.dict_1['client_id'],
                                   self.dict_1['object_id'], self.persp_1['client_id'], self.persp_1['object_id']),
                                      params=params)

    def testLexicalEntriesAll(self):
        correct_answers = load_correct_answers("lexical_entries/answers_lexical_entries_all.json")

        test_name = "test_empty"
        response = self.app.get('/dictionary/%s/%s/perspective/%s/%s/all' %
                                      (self.dict_1['client_id'], self.dict_1['object_id'],
                                       self.persp_1['client_id'], self.persp_1['object_id']),
                                      params={'sort_by': 'Word'})
        self.assertEqual(response.status_int, HTTPOk.code)
        self.assertEqual(response.json, correct_answers[test_name])
        # check that the order is correct
        self.assertEqual([(i['client_id'], i['object_id']) for i in response.json['lexical_entries']],
                         [(i['client_id'], i['object_id']) for i in correct_answers[test_name]['lexical_entries']])

        response = self.app.post_json('/dictionary/%s/%s/perspective/%s/%s/lexical_entries' %
                                      (self.dict_1['client_id'], self.dict_1['object_id'],
                                       self.persp_1['client_id'], self.persp_1['object_id']),
                                      params={'count': len(self.strings) + 1})
        lex_entries = list(zip(response.json, self.strings))

        self.login_common('user2')
        self.add_l1e(self.dict_1, self.persp_1, lex_entries[0][0], lex_entries[0][1], 'Word')
        self.login_common('user1')
        for lex in lex_entries[1:-1]:
            self.add_l1e(self.dict_1, self.persp_1, lex[0], lex[1], 'Word')
        self.add_l1e(self.dict_1, self.persp_1, lex_entries[-1][0], lex_entries[-1][1], 'Translation')

        test_name = "test_full"
        response = self.app.get('/dictionary/%s/%s/perspective/%s/%s/all' %
                                      (self.dict_1['client_id'], self.dict_1['object_id'],
                                       self.persp_1['client_id'], self.persp_1['object_id']),
                                      params={'sort_by': 'Word'})
        self.assertEqual(response.status_int, HTTPOk.code)
        self.assertEqual(response.json, correct_answers[test_name])
        self.assertEqual([(i['client_id'], i['object_id']) for i in response.json['lexical_entries']],
                         [(i['client_id'], i['object_id']) for i in correct_answers[test_name]['lexical_entries']])

        test_name = "test_0_count"
        response = self.app.get('/dictionary/%s/%s/perspective/%s/%s/all' %
                                      (self.dict_1['client_id'], self.dict_1['object_id'],
                                       self.persp_1['client_id'], self.persp_1['object_id']),
                                      params={'sort_by': 'Word', "count": "0", "start_from": "0"})
        self.assertEqual(response.status_int, HTTPOk.code)
        self.assertEqual(response.json, correct_answers[test_name])
        self.assertEqual([(i['client_id'], i['object_id']) for i in response.json['lexical_entries']],
                         [(i['client_id'], i['object_id']) for i in correct_answers[test_name]['lexical_entries']])

        test_name = "test_start_from"
        response = self.app.get('/dictionary/%s/%s/perspective/%s/%s/all' %
                                      (self.dict_1['client_id'], self.dict_1['object_id'],
                                       self.persp_1['client_id'], self.persp_1['object_id']),
                                      params={'sort_by': 'Word', "count": "20", "start_from": "18"})
        self.assertEqual(response.status_int, HTTPOk.code)
        self.assertEqual(response.json, correct_answers[test_name])
        self.assertEqual([(i['client_id'], i['object_id']) for i in response.json['lexical_entries']],
                         [(i['client_id'], i['object_id']) for i in correct_answers[test_name]['lexical_entries']])

        test_name = "test_start_over_size"
        response = self.app.get('/dictionary/%s/%s/perspective/%s/%s/all' %
                                      (self.dict_1['client_id'], self.dict_1['object_id'],
                                       self.persp_1['client_id'], self.persp_1['object_id']),
                                      params={'sort_by': 'Word', "count": "2", "start_from": "30"})
        self.assertEqual(response.status_int, HTTPOk.code)
        self.assertEqual(response.json, correct_answers[test_name])
        self.assertEqual([(i['client_id'], i['object_id']) for i in response.json['lexical_entries']],
                         [(i['client_id'], i['object_id']) for i in correct_answers[test_name]['lexical_entries']])

        test_name = "test_sort_by_fake_column"
        response = self.app.get('/dictionary/%s/%s/perspective/%s/%s/all' %
                                      (self.dict_1['client_id'], self.dict_1['object_id'],
                                       self.persp_1['client_id'], self.persp_1['object_id']),
                                      params={'sort_by': 'Fake', "count": "3", "start_from": "10"})
        self.assertEqual(response.status_int, HTTPOk.code)
        self.assertEqual(response.json, correct_answers[test_name])
        self.assertEqual([(i['client_id'], i['object_id']) for i in response.json['lexical_entries']],
                         [(i['client_id'], i['object_id']) for i in correct_answers[test_name]['lexical_entries']])

    def testLexicalEntriesPublished(self):
        correct_answers = load_correct_answers("lexical_entries/answers_lexical_entries_published.json")

        test_name = "test_empty"
        response = self.app.get('/dictionary/%s/%s/perspective/%s/%s/published' %
                                      (self.dict_1['client_id'], self.dict_1['object_id'],
                                       self.persp_1['client_id'], self.persp_1['object_id']),
                                      params={'sort_by': 'Word'})
        self.assertEqual(response.status_int, HTTPOk.code)
        self.assertEqual(response.json, correct_answers[test_name])
        # check that the order is correct
        self.assertEqual([(i['client_id'], i['object_id']) for i in response.json['lexical_entries']],
                         [(i['client_id'], i['object_id']) for i in correct_answers[test_name]['lexical_entries']])

        response = self.app.post_json('/dictionary/%s/%s/perspective/%s/%s/lexical_entries' %
                                      (self.dict_1['client_id'], self.dict_1['object_id'],
                                       self.persp_1['client_id'], self.persp_1['object_id']),
                                      params={'count': len(self.strings) + 1})
        lex_entries = list(zip(response.json, self.strings))

        to_be_approved = list()
        self.login_common('user2')
        to_be_approved.append(self.add_l1e(self.dict_1, self.persp_1, lex_entries[0][0], lex_entries[0][1], 'Word'))
        self.login_common('user1')
        for lex in lex_entries[1:-1]:
            to_be_approved.append(self.add_l1e(self.dict_1, self.persp_1, lex[0], lex[1], 'Word'))
        to_be_approved.append(self.add_l1e(self.dict_1, self.persp_1, lex_entries[-1][0],
                                           lex_entries[-1][1], 'Translation'))
        # Leave half of the entities for approving
        to_be_approved = [i for i in to_be_approved[::2]]
        for x in to_be_approved: x.update({"type": 'leveloneentity'})
        response = self.app.patch_json(
            '/dictionary/%s/%s/perspective/%s/%s/approve' % (self.dict_1['client_id'], self.dict_1['object_id'],
                                                             self.persp_1['client_id'], self.persp_1['object_id']),
            params={"entities": to_be_approved}
        )

        test_name = "test_full"

        response = self.app.get('/dictionary/%s/%s/perspective/%s/%s/published' %
                                      (self.dict_1['client_id'], self.dict_1['object_id'],
                                       self.persp_1['client_id'], self.persp_1['object_id']),
                                      params={'sort_by': 'Word'})
        self.assertEqual(response.status_int, HTTPOk.code)
        self.assertEqual(response.json, correct_answers[test_name])
        self.assertEqual([(i['client_id'], i['object_id']) for i in response.json['lexical_entries']],
                         [(i['client_id'], i['object_id']) for i in correct_answers[test_name]['lexical_entries']])

        test_name = "test_0_count"
        response = self.app.get('/dictionary/%s/%s/perspective/%s/%s/published' %
                                      (self.dict_1['client_id'], self.dict_1['object_id'],
                                       self.persp_1['client_id'], self.persp_1['object_id']),
                                      params={'sort_by': 'Word', "count": "0", "start_from": "0"})
        self.assertEqual(response.status_int, HTTPOk.code)
        self.assertEqual(response.json, correct_answers[test_name])
        self.assertEqual([(i['client_id'], i['object_id']) for i in response.json['lexical_entries']],
                         [(i['client_id'], i['object_id']) for i in correct_answers[test_name]['lexical_entries']])

        test_name = "test_start_from"
        response = self.app.get('/dictionary/%s/%s/perspective/%s/%s/published' %
                                      (self.dict_1['client_id'], self.dict_1['object_id'],
                                       self.persp_1['client_id'], self.persp_1['object_id']),
                                      params={'sort_by': 'Word', "count": "20", "start_from": "8"})
        self.assertEqual(response.status_int, HTTPOk.code)
        self.assertEqual(response.json, correct_answers[test_name])
        self.assertEqual([(i['client_id'], i['object_id']) for i in response.json['lexical_entries']],
                         [(i['client_id'], i['object_id']) for i in correct_answers[test_name]['lexical_entries']])

        test_name = "test_start_over_size"
        response = self.app.get('/dictionary/%s/%s/perspective/%s/%s/published' %
                                      (self.dict_1['client_id'], self.dict_1['object_id'],
                                       self.persp_1['client_id'], self.persp_1['object_id']),
                                      params={'sort_by': 'Word', "count": "2", "start_from": "30"})
        self.assertEqual(response.status_int, HTTPOk.code)
        self.assertEqual(response.json, correct_answers[test_name])
        self.assertEqual([(i['client_id'], i['object_id']) for i in response.json['lexical_entries']],
                         [(i['client_id'], i['object_id']) for i in correct_answers[test_name]['lexical_entries']])

        test_name = "test_sort_by_fake_column"
        response = self.app.get('/dictionary/%s/%s/perspective/%s/%s/published' %
                                      (self.dict_1['client_id'], self.dict_1['object_id'],
                                       self.persp_1['client_id'], self.persp_1['object_id']),
                                      params={'sort_by': 'Fake', "count": "3", "start_from": "5"})
        self.assertEqual(response.status_int, HTTPOk.code)
        self.assertEqual(response.json, correct_answers[test_name])
        self.assertEqual([(i['client_id'], i['object_id']) for i in response.json['lexical_entries']],
                         [(i['client_id'], i['object_id']) for i in correct_answers[test_name]['lexical_entries']])