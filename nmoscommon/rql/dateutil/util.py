from datetime import datetime
import re
import logging

FORMAT_SEPERATOR_DEFAULT_REGEX = r'%.'
ISO_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


def split_in_two(x, sep):
    max_split = 1
    try:
        before, after = x.split(sep, max_split)
    except ValueError:
        before, after = x, ''
    return before, after


def partial_match(x, seperators):
    if not seperators:
        return '', []

    sep, remaining_seps = seperators[0], seperators[1:]
    match, rest = split_in_two(x, sep)

    if rest:
        next_match, next_found_seperator = partial_match(rest, remaining_seps)
        if next_match:
            match += sep + next_match
        found_seperators = [sep] + next_found_seperator
    else:
        sep_found = len(match) < len(x)
        found_seperators = [sep] if sep_found else []

    return match, found_seperators


def _partial_match_format(x, format):
    seperators = re.split(FORMAT_SEPERATOR_DEFAULT_REGEX, format)
    seperators = [s for s in seperators if s != '']

    _, found_seperators = partial_match(x, seperators)

    if found_seperators == seperators:
        matched_format = format
    else:
        matched_format, _ = partial_match(format, found_seperators + [seperators[len(found_seperators)]])

    return matched_format


def strptime_partial(x, format=ISO_FORMAT):
    logging.info('looking for partial match with initial format: {}'.format(format))

    matched_format = _partial_match_format(x, format)
    logging.info('found partial format: {} for {}'.format(matched_format, x))

    ret = datetime.strptime(x, matched_format)
    logging.info('returning datetime {}'.format(ret))

    return ret
