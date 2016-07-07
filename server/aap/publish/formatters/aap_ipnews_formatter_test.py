# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014, 2015 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

from superdesk.publish.subscribers import SUBSCRIBER_TYPES

from test_factory import SuperdeskTestCase
from apps.publish import init_app
from .aap_ipnews_formatter import AAPIpNewsFormatter
from .aap_formatter_common import set_subject
import json
from copy import deepcopy


class AapIpNewsFormatterTest(SuperdeskTestCase):
    subscribers = [{"_id": "1", "name": "ipnews", "subscriber_type": SUBSCRIBER_TYPES.WIRE, "media_type": "media",
                    "is_active": True, "sequence_num_settings": {"max": 10, "min": 1},
                    "destinations": [{"name": "AAP IPNEWS", "delivery_type": "email", "format": "AAP IPNEWS",
                                      "config": {"recipients": "test@sourcefabric.org"}
                                      }]
                    }]

    desks = [{'_id': 1, 'name': 'National'},
             {'_id': 2, 'name': 'Sports'},
             {'_id': 3, 'name': 'Finance'}]

    article = {
        'source': 'AAP',
        'anpa_category': [{'qcode': 'a'}],
        'headline': 'This is a test headline',
        'byline': 'joe',
        'slugline': 'slugline',
        'subject': [{'qcode': '02011001'}],
        'anpa_take_key': 'take_key',
        'unique_id': '1',
        'format': 'preserved',
        'type': 'text',
        'body_html': 'The story body',
        'word_count': '1',
        'priority': 1,
        'place': [{'qcode': 'VIC', 'name': 'VIC'}],
        'genre': []
    }

    pkg = [{'_id': 'package',
            'type': 'composite',
            'package_type': 'takes',
            'last_take': '3'}]

    vocab = [{'_id': 'categories', 'items': [
        {'is_active': True, 'name': 'Overseas Sport', 'qcode': 'S', 'subject': '15000000'},
        {'is_active': True, 'name': 'Finance', 'qcode': 'F', 'subject': '04000000'}
    ]}, {'_id': 'geographical_restrictions', 'items': [{'name': 'New South Wales', 'qcode': 'NSW', 'is_active': True},
                                                       {'name': 'Victoria', 'qcode': 'VIC', 'is_active': True}]}]

    def setUp(self):
        super().setUp()
        self.app.data.insert('subscribers', self.subscribers)
        self.app.data.insert('vocabularies', self.vocab)
        self.app.data.insert('desks', self.desks)
        self.app.data.insert('archive', self.pkg)
        init_app(self.app)

    def testIPNewsFormatterWithNoSelector(self):
        subscriber = self.app.data.find('subscribers', None, None)[0]

        f = AAPIpNewsFormatter()
        seq, item = f.format(self.article, subscriber)[0]
        item = json.loads(item)

        self.assertGreater(int(seq), 0)
        self.assertEqual(seq, item['sequence'])
        item.pop('sequence')
        self.assertDictEqual(item,
                             {'category': 'a', 'texttab': 't', 'fullStory': 1, 'ident': '0',
                              'headline': 'VIC:This is a test headline', 'service_level': 'a', 'originator': 'AAP',
                              'take_key': 'take_key', 'article_text': 'The story body\r\nAAP', 'priority': 'f',
                              'usn': '1',
                              'subject_matter': 'international law', 'news_item_type': 'News',
                              'subject_reference': '02011001', 'subject': 'crime, law and justice',
                              'wordcount': '1', 'subject_detail': 'international court or tribunal',
                              'selector_codes': ' ',
                              'genre': 'Current', 'keyword': 'slugline', 'author': 'joe'})

    def testIPNewsHtmlToText(self):
        article = {
            '_id': '1',
            'source': 'AAP',
            'anpa_category': [{'qcode': 'a'}],
            'headline': 'This is a test headline',
            'byline': 'joe',
            'slugline': 'slugline',
            'subject': [{'qcode': '02011001'}],
            'anpa_take_key': 'take_key',
            'unique_id': '1',
            'type': 'text',
            'body_html': '<p>The story body line 1<br>Line 2</p>'
                         '<p>abcdefghi abcdefghi abcdefghi abcdefghi abcdefghi abcdefghi abcdefghi abcdefghi</p>',
            'word_count': '1',
            'priority': 1,
            "linked_in_packages": [
                {
                    "package": "package",
                    "package_type": "takes"
                }
            ],
        }

        subscriber = self.app.data.find('subscribers', None, None)[0]

        f = AAPIpNewsFormatter()
        seq, item = f.format(article, subscriber)[0]
        item = json.loads(item)

        expected = '   The story body line 1\r\nLine 2\r\n   abcdefghi abcdefghi abcdefghi abcdefghi ' \
                   'abcdefghi abcdefghi abcdefghi abcdefghi\r\n\r\nMORE'
        self.assertEqual(item['article_text'], expected)

    def testLastTake(self):
        article = {
            '_id': '3',
            'source': 'AAP',
            'anpa_category': [{'qcode': 'a'}],
            'headline': 'This is a test headline',
            'byline': 'joe',
            'slugline': 'slugline',
            'subject': [{'qcode': '02011001'}],
            'anpa_take_key': 'take_key',
            'unique_id': '1',
            'type': 'text',
            'body_html': '<p>The story body line 1<br>Line 2</p>'
                         '<p>abcdefghi abcdefghi abcdefghi abcdefghi abcdefghi abcdefghi abcdefghi abcdefghi</p>',
            'word_count': '1',
            'priority': 1,
            "linked_in_packages": [
                {
                    "package": "package",
                    "package_type": "takes"
                }
            ],
        }

        subscriber = self.app.data.find('subscribers', None, None)[0]

        f = AAPIpNewsFormatter()
        seq, item = f.format(article, subscriber)[0]
        item = json.loads(item)
        expected = '   The story body line 1\r\nLine 2\r\n   abcdefghi abcdefghi abcdefghi abcdefghi ' \
                   'abcdefghi abcdefghi abcdefghi abcdefghi\r\n\r\nAAP'
        self.assertEqual(item['article_text'], expected)

    def testDivContent(self):
        article = {
            '_id': '3',
            'source': 'AAP',
            'anpa_category': [{'qcode': 'a'}],
            'headline': 'This is a test headline',
            'byline': 'joe',
            'slugline': 'slugline',
            'subject': [{'qcode': '02011001'}],
            'anpa_take_key': 'take_key',
            'unique_id': '1',
            'type': 'text',
            'body_html': '<div>Kathmandu Holdings has lodged a claim in the New Zealand High'
                         'Court for the recovery of costs associated with last years takeover bid from Briscoe'
                         'Group.</div><div>Kathmandu Holdings has lodged a claim in the New Zealand High Court for '
                         'the recovery of costs associated with last years takeover bid from Briscoe Group.'
                         '</div><div><br></div><div>Kathmandu incurred costs in relation to the takeover bid. '
                         'After an initial request for payment on November 20, 2015 and subsequent correspondence, '
                         'Briscoe made a payment of $637,711.65 on May 25, 2016 without prejudice to its position on '
                         'what sum Kathmandu is entitled to recover.</div><div><br></div><div>Kathmandu considers the '
                         'full amount claimed is recoverable and has issued legal proceedings for the balance of monies'
                         ' owed.</div>',
            'word_count': '1',
            'priority': 1,
            "linked_in_packages": [
                {
                    "package": "package",
                    "package_type": "takes"
                }
            ],
        }
        subscriber = self.app.data.find('subscribers', None, None)[0]

        f = AAPIpNewsFormatter()
        seq, item = f.format(article, subscriber)[0]
        item = json.loads(item)

        expected = '   Kathmandu Holdings has lodged a claim in the New Zealand HighCourt for the \r\n' + \
            'recovery of costs associated with last years takeover bid from BriscoeGroup.\r\n' + \
            '   Kathmandu Holdings has lodged a claim in the New Zealand High Court for the \r\nrecovery of ' + \
            'costs associated with last years takeover bid from Briscoe Group.\r\n   Kathmandu ' + \
            'incurred costs in relation to the takeover bid. After an initial \r\nrequest for payment on ' + \
            'November 20, 2015 and subsequent correspondence, Briscoe \r\nmade a payment of $637,711.65 on May ' + \
            '25, 2016 without prejudice to its position \r\non what sum Kathmandu is entitled to ' + \
            'recover.\r\n   Kathmandu considers the full amount claimed is recoverable and has ' + \
            'issued legal \r\nproceedings for the balance of monies owed.\r\n\r\nAAP'

        self.maxDiff = None
        self.assertEqual(item['article_text'], expected)

    def testLFContent(self):
        article = {
            '_id': '3',
            'source': 'AAP',
            'anpa_category': [{'qcode': 'a'}],
            'headline': 'This is a test headline',
            'byline': 'joe',
            'slugline': 'slugline',
            'subject': [{'qcode': '02011001'}],
            'anpa_take_key': 'take_key',
            'unique_id': '1',
            'type': 'text',
            'body_html': '<p><span style=\"background-color: transparent;\">The Australian dollar has tumbled'
                         ' after&nbsp;</span>Standard &amp; Poor\'s warned the country\'s triple-A credit rating '
                         'is at risk.<br></p><p>   At 1200 AEST on Thursday, the currency was trading at 74.98 US '
                         'cents, up from\n\n 74.41\n\n cents on Wednesday, but down from a high of 75.38 on Thursday '
                         'morning.</p><p>S&amp;P downgraded its outlook on Australia\'s credit rating from stable '
                         'to negative, due to the prospect of ongoing budget deficits without substantial reforms '
                         'being passed by parliament.</p><p>Westpac chief currency strategist&nbsp;Robert Rennie '
                         'said the uncertain election outcome is likely to result in a longer run of budget'
                         'deficits.</p><p>\"It was clearly a risk and the market has been living in its shadow since'
                         'Monday morning,\" he said.</p><p>\"Gridlock or the inability to improve the fiscal situation '
                         'over the forecast period is something I think a ratings agency ought to take into '
                         'account.\"</p><p><span style=\"background-color: transparent;\">The currency had a sudden '
                         'plunge to 74.67 US cents on the announcement from S&amp;P, before recovering some of that '
                         'ground.</span></p><p><span style=\"background-color: transparent;\">Mr Rennie tipped the '
                         'Australian dollar will slip further on Thursday.</span></p><p><span style=\"background-color:'
                         'transparent;\">\"We should make fresh lows, we should be pushing down though 74 US cents '
                         'and possibly lower,\" he said.</span></p><p><span style=\"background-color: '
                         'transparent;\">KEY MOVEMENTS:</span></p><p><span style=\"background-color: transparent;\">One'
                         'Australian dollar buys:</span><br></p><p>   * 74.98 US cents, from\n\n 74.41\n\ncents on '
                         'Wednesday</p><p>   * 75.63 Japanese yen, from \n\n75.15\n\n yen</p><p>   * 67.64 euro cents, '
                         'from \n\n67.24\n\n euro cents</p><p>   * 105.01 New Zealand cents, from \n\n104.85\n\n NZ '
                         'cents</p><p>   * 57.96 British pence, from \n\n57.53\n\n pence</p><p>   Government bond '
                         'yields:</p><p>   * CGS 5.25pct March 2019, 1.510pct, from \n\n1.513pct</p><p>   * CGS 4.25pct'
                         'April 2026, 1.868pct, from \n\n1.862pct</p><p>   Sydney Futures Exchange prices:</p><p>   *'
                         'September 2016 10-year bond futures contract, was at 98.125\n\n (1.875\n\n per cent), '
                         'unchanged from Wednesday</p><p>   * September 2016 3-year bond futures contract, at 98.570 '
                         '(1.430 per cent), up from \n\n98.550\n\n (1.450\n\n per cent)</p><p>   (*Currency closes '
                         'taken at 1700 AEST previous local session, bond market closes taken at 1630 AEST previous '
                         'local session)</p><p>   Source: IRESS</p>',
            'word_count': '1',
            'priority': 1,
            "linked_in_packages": [
                {
                    "package": "package",
                    "package_type": "takes"
                }
            ],
        }
        subscriber = self.app.data.find('subscribers', None, None)[0]

        f = AAPIpNewsFormatter()
        seq, item = f.format(article, subscriber)[0]
        item = json.loads(item)

        expected = '   * 74.98 US cents, from 74.41 cents on Wednesday'

        self.maxDiff = None
        self.assertEqual(item['article_text'].split('\x19\r\n')[11], expected)

    def testMultipleCategories(self):
        article = {
            'source': 'AAP',
            'anpa_category': [{'name': 'Finance', 'qcode': 'F'},
                              {'name': 'Overseas Sport', 'qcode': 'S'}],
            'headline': 'This is a test headline',
            'byline': 'joe',
            'slugline': 'slugline',
            'subject': [{'qcode': '04001005'}, {'qcode': '15011002'}],
            'anpa_take_key': 'take_key',
            'unique_id': '1',
            'type': 'text',
            'body_html': 'body',
            'word_count': '1',
            'priority': 1,
            'task': {'desk': 1},
            'place': [{'qcode': 'VIC', 'name': 'VIC'}]
        }

        subscriber = self.app.data.find('subscribers', None, None)[0]

        f = AAPIpNewsFormatter()
        docs = f.format(article, subscriber, ['Aaa', 'Bbb', 'Ccc'])
        self.assertEqual(len(docs), 2)
        for seq, doc in docs:
            doc = json.loads(doc)
            if doc['category'] == 'S':
                self.assertEqual(doc['subject_reference'], '15011002')
                self.assertEqual(doc['subject_detail'], 'four-man sled')
                self.assertEqual(doc['headline'], 'VIC:This is a test headline')
            if doc['category'] == 'F':
                self.assertEqual(doc['subject_reference'], '04001005')
                self.assertEqual(doc['subject_detail'], 'viniculture')
                self.assertEqual(doc['headline'], 'VIC:This is a test headline')
                codes = set(doc['selector_codes'].split(' '))
                expected_codes = set('Aaa Bbb Ccc'.split(' '))
                self.assertSetEqual(codes, expected_codes)

    def testGeoBlock(self):
        article = {
            'source': 'AAP',
            'anpa_category': [{'qcode': 'a'}],
            'headline': 'This is a test headline',
            'byline': 'joe',
            'slugline': 'slugline',
            'subject': [{'qcode': '04001005'}, {'qcode': '15011002'}],
            'anpa_take_key': 'take_key',
            'unique_id': '1',
            'type': 'text',
            'body_html': 'body',
            'word_count': '1',
            'priority': 1,
            'task': {'desk': 1},
            'urgency': 1,
            'place': [{'qcode': 'VIC', 'name': 'VIC'}]
        }

        subscriber = self.app.data.find('subscribers', None, None)[0]

        f = AAPIpNewsFormatter()
        codes = ['an5', 'an4', 'an7', 'an6', 'ax5', 'an3', 'ax6', 'ax7', '0hw']
        seq, doc = f.format(article, subscriber, codes)[0]
        doc = json.loads(doc)
        codes = set(doc['selector_codes'].split(' '))
        expected_codes_str = 'an5 an4 an7 an6 ax5 an3 ax6 ax7 0hw'
        expected_codes = set(expected_codes_str.split(' '))
        self.assertSetEqual(codes, expected_codes)

    def testIpNewsFormatterNoSubject(self):
        article = {
            'source': 'AAP',
            'anpa_category': [{'qcode': 'a'}],
            'headline': 'This is a test headline',
            'byline': 'joe',
            'slugline': 'slugline',
            'subject': [],
            'anpa_take_key': 'take_key',
            'unique_id': '1',
            'type': 'text',
            'body_html': 'body',
            'word_count': '1',
            'priority': 1,
            'task': {'desk': 1},
            'urgency': 1,
            'place': [{'qcode': 'VIC', 'name': 'VIC'}]
        }
        subscriber = self.app.data.find('subscribers', None, None)[0]

        f = AAPIpNewsFormatter()
        seq, doc = f.format(article, subscriber)[0]
        doc = json.loads(doc)
        self.assertEqual(doc['subject_reference'], '00000000')
        self.assertEqual(doc['headline'], 'VIC:This is a test headline')

        article = {
            'source': 'AAP',
            'anpa_category': [{'qcode': 'a'}],
            'headline': 'This is a test headline',
            'byline': 'joe',
            'slugline': 'slugline',
            'subject': None,
            'anpa_take_key': 'take_key',
            'unique_id': '1',
            'type': 'text',
            'body_html': 'body',
            'word_count': '1',
            'priority': 1,
            'task': {'desk': 1},
            'urgency': 1,
            'place': None
        }

        seq, doc = f.format(article, subscriber)[0]
        doc = json.loads(doc)
        self.assertEqual(doc['subject_reference'], '00000000')
        self.assertEqual(doc['headline'], 'This is a test headline')

    def test_aap_ipnews_formatter_with_body_footer(self):
        subscriber = self.app.data.find('subscribers', None, None)[0]
        doc = self.article.copy()
        doc['body_footer'] = '<p>call helpline 999 if you are planning to quit smoking</p>'

        f = AAPIpNewsFormatter()
        seq, item = f.format(doc, subscriber, ['Axx'])[0]
        item = json.loads(item)

        self.assertGreater(int(seq), 0)
        self.assertEqual(seq, item['sequence'])
        item.pop('sequence')
        self.assertDictEqual(item,
                             {'category': 'a', 'texttab': 't', 'fullStory': 1, 'ident': '0',
                              'headline': 'VIC:This is a test headline', 'service_level': 'a', 'originator': 'AAP',
                              'take_key': 'take_key',
                              'article_text': 'The story body\r\ncall helpline 999 if you are planning to '
                              'quit smoking\r\nAAP',
                              'priority': 'f', 'usn': '1',
                              'subject_matter': 'international law', 'news_item_type': 'News',
                              'subject_reference': '02011001', 'subject': 'crime, law and justice',
                              'wordcount': '1', 'subject_detail': 'international court or tribunal',
                              'selector_codes': 'Axx',
                              'genre': 'Current', 'keyword': 'slugline', 'author': 'joe'})

    def test_aap_ipnews_formatter_with_body_formatted(self):
        subscriber = self.app.data.find('subscribers', None, None)[0]
        doc = deepcopy(self.article)
        doc['body_footer'] = '<p>call helpline 999 if you are planning to quit smoking</p>'
        doc['body_html'] = ('<pre>  The story\n body\r\n</pre>'
                            '<pre>  second line<br></pre><br>')
        doc['format'] = 'preserved'

        f = AAPIpNewsFormatter()
        seq, item = f.format(doc, subscriber, ['Axx'])[0]
        item = json.loads(item)

        self.assertGreater(int(seq), 0)
        self.assertEqual(seq, item['sequence'])
        item.pop('sequence')
        self.assertDictEqual(item,
                             {'category': 'a', 'texttab': 't', 'fullStory': 1, 'ident': '0',
                              'headline': 'VIC:This is a test headline', 'service_level': 'a', 'originator': 'AAP',
                              'take_key': 'take_key',
                              'article_text': '  The story\r\n body\r\n  second line\r\n\r\n\r\ncall helpline '
                                              '999 if you are planning to quit smoking\r\nAAP',
                              'priority': 'f', 'usn': '1',
                              'subject_matter': 'international law', 'news_item_type': 'News',
                              'subject_reference': '02011001', 'subject': 'crime, law and justice',
                              'wordcount': '1', 'subject_detail': 'international court or tribunal',
                              'selector_codes': 'Axx',
                              'genre': 'Current', 'keyword': 'slugline', 'author': 'joe'})


class DefaultSubjectTest(SuperdeskTestCase):

    def setUp(self):
        super().setUp()
        vocabularies = [{
            '_id': 'categories',
            'display_name': 'Categories',
            'type': 'manageable',
            'items': [
                {'is_active': True, 'name': 'Australian General News', 'qcode': 'a'},
                {'is_active': True, 'name': 'Australian Weather', 'qcode': 'b', 'subject': '17000000'},
                {'is_active': True, 'name': 'General Features', 'qcode': 'c'},
                {'is_active': False, 'name': 'Reserved (obsolete/unused)', 'qcode': 'd'},
                {'is_active': True, 'name': 'Entertainment', 'qcode': 'e', 'subject': '01000000'},
                {'is_active': True, 'name': 'Finance', 'qcode': 'f', 'subject': '04000000'},
                {'is_active': False, 'name': 'SportSet', 'qcode': 'g'},
                {'is_active': True, 'name': 'FormGuide', 'qcode': 'h'},
                {'is_active': True, 'name': 'International News', 'qcode': 'i'},
                {'is_active': False, 'name': 'Reserved (obsolete/unused)', 'qcode': 'k'},
                {'is_active': True, 'name': 'Press Release Service', 'qcode': 'j'},
                {'is_active': True, 'name': 'Lotteries', 'qcode': 'l'},
                {'is_active': True, 'name': 'Line Check Messages', 'qcode': 'm'},
                {'is_active': False, 'name': 'Reserved', 'qcode': 'n'},
                {'is_active': True, 'name': 'State Parliaments', 'qcode': 'o', 'subject': '11000000'},
                {'is_active': True, 'name': 'Federal Parliament', 'qcode': 'p', 'subject': '11000000'},
                {'is_active': True, 'name': 'Stockset', 'qcode': 'q', 'subject': '04000000'},
                {'is_active': True, 'name': 'Racing (Turf)', 'qcode': 'r', 'subject': '15000000'},
                {'is_active': True, 'name': 'Overseas Sport', 'qcode': 's', 'subject': '15000000'},
                {'is_active': True, 'name': 'Domestic Sport', 'qcode': 't', 'subject': '15000000'},
                {'is_active': False, 'name': 'Reserved (Obsolete/unused)', 'qcode': 'u'},
                {'is_active': True, 'name': 'Advisories', 'qcode': 'v'},
                {'is_active': False, 'name': 'Reserved (Obsolete/unused)', 'qcode': 'w'},
                {'is_active': True, 'name': 'Special Events (olympics/ Aus elections)', 'qcode': 'x'},
                {'is_active': False, 'name': 'Special Events (obsolete/unused)', 'qcode': 'y'},
                {'is_active': False, 'name': 'Supplementary Traffic', 'qcode': 'z'}
            ]
        }]

        self.app.data.insert('vocabularies', vocabularies)
        init_app(self.app)

    def test_subject(self):
        article = {
            'anpa_category': [{'qcode': 'a'}, {'qcode': 's'}],
            'subject': [{'qcode': '04001005'}, {'qcode': '15011002'}]
        }

        self.assertEqual(set_subject({'qcode': 'a'}, article), '04001005')
        self.assertEqual(set_subject({'qcode': 's'}, article), '15011002')
        article = {
            'anpa_category': [{'qcode': 'a'}, {'qcode': 's'}],
            'subject': None
        }

        self.assertEqual(set_subject({'qcode': 'a'}, article), None)
        self.assertEqual(set_subject({'qcode': 's'}, article), None)

        article = {
            'anpa_category': None,
            'subject': [{'qcode': '04001005'}, {'qcode': '15011002'}]
        }

        self.assertEqual(set_subject(None, article), '04001005')