from zeroconf import BadTypeInNameException, _HAS_A_TO_Z
from zeroconf import _HAS_ONLY_A_TO_Z_NUM_HYPHEN, _HAS_ASCII_CONTROL_CHARS


# This file exists because we need to over-ride the original implementation in
# python-zeroconf, because nmos-registration breaks the RFC6763 rules on length


def service_type_name(type_, allow_underscores=False):
    """
    Validate a fully qualified service name, instance or subtype. [rfc6763]
    Returns fully qualified service name.
    Domain names used by mDNS-SD take the following forms:
                   <sn> . <_tcp|_udp> . local.
      <Instance> . <sn> . <_tcp|_udp> . local.
      <sub>._sub . <sn> . <_tcp|_udp> . local.
    1) must end with 'local.'
      This is true because we are implementing mDNS and since the 'm' means
      multi-cast, the 'local.' domain is mandatory.
    2) local is preceded with either '_udp.' or '_tcp.'
    3) service name <sn> precedes <_tcp|_udp>
      The rules for Service Names [RFC6335] state that they may be no more
      than fifteen characters long (not counting the mandatory underscore),
      consisting of only letters, digits, and hyphens, must begin and end
      with a letter or digit, must not contain consecutive hyphens, and
      must contain at least one letter.
    The instance name <Instance> and sub type <sub> may be up to 63 bytes.
    The portion of the Service Instance Name is a user-
    friendly name consisting of arbitrary Net-Unicode text [RFC5198]. It
    MUST NOT contain ASCII control characters (byte values 0x00-0x1F and
    0x7F) [RFC20] but otherwise is allowed to contain any characters,
    without restriction, including spaces, uppercase, lowercase,
    punctuation -- including dots -- accented characters, non-Roman text,
    and anything else that may be represented using Net-Unicode.
    :param type_: Type, SubType or service name to validate
    :return: fully qualified service name (eg: _http._tcp.local.)
    """
    if not (type_.endswith('._tcp.local.') or type_.endswith('._udp.local.')):
        raise BadTypeInNameException(
            "Type '%s' must end with '._tcp.local.' or '._udp.local.'" %
            type_)

    remaining = type_[:-len('._tcp.local.')].split('.')
    name = remaining.pop()
    if not name:
        raise BadTypeInNameException("No Service name found")

    if len(remaining) == 1 and len(remaining[0]) == 0:
        raise BadTypeInNameException(
            "Type '%s' must not start with '.'" % type_)

    if name[0] != '_':
        raise BadTypeInNameException(
            "Service name (%s) must start with '_'" % name)

    # remove leading underscore
    name = name[1:]

    if '--' in name:
        raise BadTypeInNameException(
            "Service name (%s) must not contain '--'" % name)

    if '-' in (name[0], name[-1]):
        raise BadTypeInNameException(
            "Service name (%s) may not start or end with '-'" % name)

    if not _HAS_A_TO_Z.search(name):
        raise BadTypeInNameException(
            "Service name (%s) must contain at least one letter (eg: 'A-Z')" %
            name)

    if not _HAS_ONLY_A_TO_Z_NUM_HYPHEN.search(name):
        raise BadTypeInNameException(
            "Service name (%s) must contain only these characters: "
            "A-Z, a-z, 0-9, hyphen ('-')" % name)

    if remaining and remaining[-1] == '_sub':
        remaining.pop()
        if len(remaining) == 0 or len(remaining[0]) == 0:
            raise BadTypeInNameException(
                "_sub requires a subtype name")

    if len(remaining) > 1:
        remaining = ['.'.join(remaining)]

    if remaining:
        length = len(remaining[0].encode('utf-8'))
        if length > 63:
            raise BadTypeInNameException("Too long: '%s'" % remaining[0])

        if _HAS_ASCII_CONTROL_CHARS.search(remaining[0]):
            raise BadTypeInNameException(
                "Ascii control character 0x00-0x1F and 0x7F illegal in '%s'" %
                remaining[0])

    return '_' + name + type_[-len('._tcp.local.'):]
