# Python Version: 3.x
import io
import re
import urllib.parse
import zipfile
from typing import *

import bs4
import requests

import onlinejudge.dispatch
import onlinejudge.implementation.logging as log
import onlinejudge.implementation.utils as utils
import onlinejudge.type
from onlinejudge.type import LabeledString, TestCase


@utils.singleton
class KattisService(onlinejudge.type.Service):
    def get_url(self) -> str:
        # NOTE: sometimes this URL is not correct, i.e. something like https://hanoi18.kattis.com/ exists
        return 'http://open.kattis.org/'

    def get_name(self) -> str:
        return 'kattis'

    @classmethod
    def from_url(cls, s: str) -> Optional['KattisService']:
        # example: https://open.kattis.com/
        # example: https://hanoi18.kattis.com/
        result = urllib.parse.urlparse(s)
        if result.scheme in ('', 'http', 'https') \
                and result.netloc.endswith('.kattis.com'):
            # NOTE: ignore the subdomain
            return cls()
        return None


class KattisProblem(onlinejudge.type.Problem):
    def __init__(self, problem_id: str, contest: Optional[str] = None, domain: str = 'open.kattis.com'):
        self.domain = domain
        self.contest = contest
        self.problem_id = problem_id

    def download_sample_cases(self, session: Optional[requests.Session] = None) -> List[onlinejudge.type.TestCase]:
        session = session or utils.new_default_session()
        # get
        url = self.get_url(contests=False) + '/file/statement/samples.zip'
        resp = utils.request('GET', url, session=session)
        # parse
        with zipfile.ZipFile(io.BytesIO(resp.content)) as fh:
            samples = []  # type: List[TestCase]
            for filename in sorted(fh.namelist()):
                log.debug('filename: %s', filename)
                if filename.endswith('.in'):
                    inpath = filename
                    outpath = filename[:-3] + '.ans'
                    indata = fh.read(inpath).decode()
                    outdata = fh.read(outpath).decode()
                    samples += [TestCase(LabeledString(inpath, indata), LabeledString(outpath, outdata))]
            return samples

    def get_url(self, contests=True) -> str:
        if contests and self.contest is not None:
            # the URL without "/contests/{}" also works
            return 'https://{}/contests/{}/problems/{}'.format(self.domain, self.contest, self.problem_id)
        else:
            return 'https://{}/problems/{}'.format(self.domain, self.problem_id)

    def get_service(self) -> KattisService:
        # NOTE: ignore the subdomain
        return KattisService()

    @classmethod
    def from_url(cls, s: str) -> Optional['KattisProblem']:
        # example: https://open.kattis.com/problems/hello
        # example: https://open.kattis.com/contests/asiasg15prelwarmup/problems/8queens
        result = urllib.parse.urlparse(s)
        if result.scheme in ('', 'http', 'https') \
                and result.netloc.endswith('.kattis.com'):
            m = re.match(r'(?:/contests/([0-9A-Z_a-z-]+))?/problems/([0-9A-Z_a-z-]+)/?', result.path)
            if m:
                contest = m.group(1) or None
                problem_id = m.group(2)
                return cls(problem_id, contest=contest, domain=result.netloc)
        return None


onlinejudge.dispatch.services += [KattisService]
onlinejudge.dispatch.problems += [KattisProblem]
