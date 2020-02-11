# Copyright 2019 British Broadcasting Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from time import time


BEARER_TOKEN = {
    "access_token": "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhcC16NDIwLTUucmQuYmJjLmNvLnVrIiwic3ViIjoiZGVtbyIs\
Im5iZiI6MTU4MTQyMDA1MiwiZXhwIjoyNTgxNDIwMDUyLCJhdWQiOiIqLnJkLmJiYy5jby51ayIsImNsaWVudF9pZCI6Im5zenVLWXA5bHQyNVJtY3\
lRMzUxMDJ2cyIsIngtbm1vcy1hcGkiOnsiY29ubmVjdGlvbiI6eyJyZWFkIjpbIioiXX0sInJlZ2lzdHJhdGlvbiI6eyJyZWFkIjpbIioiXSwid3Jp\
dGUiOlsiKiJdfX0sInNjb3BlIjoiY29ubmVjdGlvbiByZWdpc3RyYXRpb24iLCJpYXQiOjE1ODE0MjAwNTJ9.ZI72XoHk1kA5vRi6EBqILaWZPBr6t\
pudGH60j8iNic6otX75GH_1nEItTznP5ibi0LYVTHFh53na040ImVHUmKlme-RyGhcsk-wS39wyFkFs_3ssSfqGmCW9lAz5x3GZonsO5A6G9ehrCh3\
HFosBvrZjz3jWLWAxJXgjq9Mr9eewOs4S56j0hnt5CtTN8LgvXrwCerIQeQCr8Nde6qn8QC-I00YoWV5NCK-Tk1a66gLbXnTu2ghr2U4pIJ20hOFJM\
i86V6lQGOHZtVM7_yzkdbma3CRqlzDF_FG87LI9Ds0DDSsQrllw6sMc3TOaQ06REsUTI6ugBWcPpB0ujmcqPw",
    "expires_in": 1000000000,
    "refresh_token": "4DB8hZYrJdy1DNoZ1IIvmm4uzX0cfYe1LzZpSi70Om0eADrJ",
    "scope": "registration connection",
    "token_type": "Bearer"
}

"""
EQUIVALENT TO:
{
  "iss": "ap-z420-5.rd.bbc.co.uk",
  "sub": "demo",
  "nbf": 1581420052,
  "exp": 2581420052,
  "aud": "*.rd.bbc.co.uk",
  "client_id": "nszuKYp9lt25RmcyQ35102vs",
  "x-nmos-api": {
    "connection": {
      "read": [
        "*"
      ]
    },
    "registration": {
      "read": [
        "*"
      ],
      "write": [
        "*"
      ]
    }
  },
  "scope": "connection registration",
  "iat": 1581420052
}
"""

CERT = '''-----BEGIN CERTIFICATE-----
MIIDeTCCAmECAgPoMA0GCSqGSIb3DQEBDQUAMIGBMQswCQYDVQQGEwJVSzEPMA0G
A1UECAwGTG9uZG9uMQ8wDQYDVQQHDAZMb25kb24xGjAYBgNVBAoMEUR1bW15IENv
bXBhbnkgTHRkMRowGAYDVQQLDBFEdW1teSBDb21wYW55IEx0ZDEYMBYGA1UEAwwP
d3d3LmV4YW1wbGUuY29tMB4XDTE5MTIwOTE0NTYzNVoXDTI5MTIwNjE0NTYzNVow
gYExCzAJBgNVBAYTAlVLMQ8wDQYDVQQIDAZMb25kb24xDzANBgNVBAcMBkxvbmRv
bjEaMBgGA1UECgwRRHVtbXkgQ29tcGFueSBMdGQxGjAYBgNVBAsMEUR1bW15IENv
bXBhbnkgTHRkMRgwFgYDVQQDDA93d3cuZXhhbXBsZS5jb20wggEiMA0GCSqGSIb3
DQEBAQUAA4IBDwAwggEKAoIBAQDJ+sy9MZC+Rsq+0dkUo42S2MlPNpJTM95OPYTs
/9jMukLLOglpUqePqu//HDCeO0lftyI1cNT8P8nCiDecssH61ZkcZuuI27DKcF6R
5Mru4jNZhh1ie3NMGpk1ZSxREQuu751yV3iAu+txJPmyAxRBujm4dyQcBNBoK9EJ
kn4dD0s5dEKDT4+hlo76ZIiHBTjyexjSpkf6rD1bT1qxhTZoyboNg7DCy5A+45ws
f25m2bkdmfrxI2jYHyovCw1MoDx/AHXaZRnFcE4JSA4YXPLR3wfVabJZbrjL7Hg/
miFaA70jKZS8zLeZ0h3Islcb3bLFHrfNheRkdgeXLS+C2i9lAgMBAAEwDQYJKoZI
hvcNAQENBQADggEBAAAay70fjCtGCgKKGpKU+aDQ1YkulRYdzDg0nBMoXCj0VrBK
EGOi4j2gpyCEguY6D3YG2JvzmnXdH9E6lt4kwf04RwbLBq15kNyCgn/Rb9JUZL08
Cb0ltQlMVx/qArmurK4e6kX7DlqIPKpB68rMh+4AOomuZE/A6ntI/Do6BvQF/huP
HESLfyJL9XQuYTQ6MPwTh9Cb9E81pgM8gSWK1iRPFXXy0OMkxWiW23EdZVXSJwyp
2feSYkdPafmqSi5jb5x6t7dcOPGhYWAEOWwI/2p3I3odc3AUBiBUR0z5YDBn/zHQ
DMjXP9UFSnp3qXFI9grT4Z6jJnXWq94zm+SwCXs=
-----END CERTIFICATE-----'''

PUB_KEY = '''-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyfrMvTGQvkbKvtHZFKON
ktjJTzaSUzPeTj2E7P/YzLpCyzoJaVKnj6rv/xwwnjtJX7ciNXDU/D/Jwog3nLLB
+tWZHGbriNuwynBekeTK7uIzWYYdYntzTBqZNWUsURELru+dcld4gLvrcST5sgMU
Qbo5uHckHATQaCvRCZJ+HQ9LOXRCg0+PoZaO+mSIhwU48nsY0qZH+qw9W09asYU2
aMm6DYOwwsuQPuOcLH9uZtm5HZn68SNo2B8qLwsNTKA8fwB12mUZxXBOCUgOGFzy
0d8H1WmyWW64y+x4P5ohWgO9IymUvMy3mdIdyLJXG92yxR63zYXkZHYHly0vgtov
ZQIDAQAB
-----END PUBLIC KEY-----
'''

TEST_PRIV_KEY = '''-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDJ+sy9MZC+Rsq+
0dkUo42S2MlPNpJTM95OPYTs/9jMukLLOglpUqePqu//HDCeO0lftyI1cNT8P8nC
iDecssH61ZkcZuuI27DKcF6R5Mru4jNZhh1ie3NMGpk1ZSxREQuu751yV3iAu+tx
JPmyAxRBujm4dyQcBNBoK9EJkn4dD0s5dEKDT4+hlo76ZIiHBTjyexjSpkf6rD1b
T1qxhTZoyboNg7DCy5A+45wsf25m2bkdmfrxI2jYHyovCw1MoDx/AHXaZRnFcE4J
SA4YXPLR3wfVabJZbrjL7Hg/miFaA70jKZS8zLeZ0h3Islcb3bLFHrfNheRkdgeX
LS+C2i9lAgMBAAECggEARiT7hZj5E5uyPaLTKP/D4wO2pfPlzU9uHO3wg/42ZKMr
HzkAm7tAxfwvbQF1QP6F9N+82aJd1VyxzQVRivHpvBsCGYMEuXrSYvuzXCeA8oVM
IAMboWAOIpf6LTj9swmgbRh6LYODLfIVSi31KYU4O7tY4F9AAxsI5aSR7Ckb8ysG
m+HDPKgjBmzm7P+ia38EZtxUgvBMptSvs5TX3QbrbvfmEZLLj8NhpXwVitkFlU1U
WY1WOq6DlD/YQjBgfkGykY4JoyEbRJzKe9v8N2FV2zq5FA5GuWCexW8DlTHYfq3h
q/GxAQSXuzsbnQT3c5E9o/eHlgYum05zZIlbd0sd4QKBgQDjaU5tR6iD5q28XVgY
lwGI4K+wkp4qCe7k2foBdTPVmgjyeYrLNuZ12OXm8DbJzn1eRJ1QkwItTGM+b9Qq
cYPL/6zTjFPSUrt7DiCrHSxpCj9FeRPlhuwjDsSE4tXWrrlEAuNM8ndShH1vdZoe
zy642AWhhBjw2CV1dohYe4WWwwKBgQDjXwkjcg3PMChKRMrBskUyNT1Je/7xf7Tn
ZPAUYMZCmOf0jXvacyliSNy9hqAZ3HHXk2ld4eaVaD4TIuhkLQ95AlWT5Qby+vBn
FbdEh3/vDHQ/z1cHUJU1qNhOBG7VmJfDnGmWfphsX7bdYkuMsnIicx0Yp2Rw4Hs8
s1oQhSROtwKBgFATk7ctRWx0vPaYE95MxhCRtavCZQk+iC1zh/IdeAwd+kqPe80E
3u/eWU4RhelX2ZNpK8/khB65SDUDIb10TUl3FT9EqXtlAHlbRyuZ0TqHjjIDaXso
IFxT5eU5Dr1Stw/4yFsfAd8/of+udH+myrfx8UGnhzS/l6kd/PLTQ/4LAoGBAIky
GjiKJK0FOPp/gfzYzgoat+10ZYRhc85ASOFy947N5wDYsohA/xKwNooiBs80Bnl3
GJgurE0xBmvTn3h6/CAfeXXxN308T/1TzC8Mt/SNhkPOn4vpYu9q/4IsCJjYJ5M/
+TJ3FxAlvRjerAmsz1PcNA1hTCkUOyiIbGsVe7AHAoGAQmVZWEgOywIvcj6HSuIz
r10/WOGp97UY+Co+/ptzM+5YBuB9qnUmpdFIDabXi2ekCOypuVZfNo0chTYHVLcB
g5op8Z1l9K6Rh54I3Bx2ozemflllnNechWdumm1TeV7B5lIpD5DLZZqITS9ee90V
zO24ZZX0XksFLTxmcat3CTw=
-----END PRIVATE KEY-----'''


TEST_JWK = {
    "kid": "x-nmos-{}".format(int(time())),
    "use": "sig",
    "key_ops": "verify",
    "kty": "RSA",
    "alg": "RS512",
    "e": "AQAB",
    "n": "yfrMvTGQvkbKvtHZFKONktjJTzaSUzPeTj2E7P_YzLpCyzoJaVKnj6rv_xwwnjtJX7ciNXDU_D_Jwog3nLLB-tWZHGbriNuwynBe\
keTK7uIzWYYdYntzTBqZNWUsURELru-dcld4gLvrcST5sgMUQbo5uHckHATQaCvRCZJ-HQ9LOXRCg0-PoZaO-mSIhwU48nsY0qZH-qw9W09asYU2aMm6DY\
OwwsuQPuOcLH9uZtm5HZn68SNo2B8qLwsNTKA8fwB12mUZxXBOCUgOGFzy0d8H1WmyWW64y-x4P5ohWgO9IymUvMy3mdIdyLJXG92yxR63zYXkZHYHly0v\
gtovZQ"
}

TEST_JWKS = {
    "keys": [
        {
            "kid": "x-nmos-{}".format(int(time())),
            "use": "sig",
            "key_ops": "verify",
            "kty": "RSA",
            "alg": "RS512",
            "e": "AQAB",
            "n": "yfrMvTGQvkbKvtHZFKONktjJTzaSUzPeTj2E7P_YzLpCyzoJaVKnj6rv_xwwnjtJX7ciNXDU_D_Jwog3nLLB-tWZHGbriNuwynBe\
keTK7uIzWYYdYntzTBqZNWUsURELru-dcld4gLvrcST5sgMUQbo5uHckHATQaCvRCZJ-HQ9LOXRCg0-PoZaO-mSIhwU48nsY0qZH-qw9W09asYU2aMm6DY\
OwwsuQPuOcLH9uZtm5HZn68SNo2B8qLwsNTKA8fwB12mUZxXBOCUgOGFzy0d8H1WmyWW64y-x4P5ohWgO9IymUvMy3mdIdyLJXG92yxR63zYXkZHYHly0v\
gtovZQ"
        },
        {
            "kid": "x-nmos-{}".format(int(time())-5),
            "use": "sig",
            "key_ops": "verify",
            "kty": "RSA",
            "alg": "RS512",
            "e": "AQAB",
            "n": "yfrMvTGQvkbKvtHZFKONktjJTzaSUzPeTj2E7P_YzLpCyzoJaVKnj6rv_xwwnjtJX7ciNXDU_D_Jwog3nLLB-tWZHGbriNuwynBe\
        keTK7uIzWYYdYntzTBqZNWUsURELru-dcld4gLvrcST5sgMUQbo5uHckHATQaCvRCZJ-HQ9LOXRCg0-PoZaO-mSIhwU48nsY0qZH-qw9W09asYU2aMm6DY\
        OwwsuQPuOcLH9uZtm5HZn68SNo2B8qLwsNTKA8fwB12mUZxXBOCUgOGFzy0d8H1WmyWW64y-x4P5ohWgO9IymUvMy3mdIdyLJXG92yxR63zYXkZHYHly0v\
        gtovZQ"
        }
    ]
}
