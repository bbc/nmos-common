from ..parser import parse
from .fixtures import query_pairs


def test_generator():
    for test_cases in query_pairs.values():
        for q, expected in test_cases.items():

            print 'next query {} -> {}'.format(q, expected)

            actual = parse(q)

            # some of the tests are not in their final form..
            if isinstance(expected, str):
                expected = parse(expected)
            if expected.get('cache'):
                del expected['cache']

            yield check_params, actual, expected


def check_params(a, b):
    print 'found actual {}, expected {}. Result: {}'.format(a, b, a == b)

    if isinstance(b, dict):
        # poor mans deep comparison
        assert set(a) == set(b)
        assert str(a) == str(b)
    else:
        assert a == b
