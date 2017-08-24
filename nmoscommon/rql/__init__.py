from .parser import parse, ParserError
from .query import mongodb


def convert_to_mongo(rql_str):
    try:
        return mongodb.unparse(parse(rql_str))
    except ValueError:
        raise ParserError('query not valid: {}'.format(rql_str))
