import requests
import logging
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.DEBUG)

base_url = 'https://www.sbiz.or.kr/' # 로컬
# base_url = 'http://211.252.121.132:18882/' # 운영

test1 = '/sup/policy/json/policyfound.do'
test2 = '/sup/policy/json/policygrow.do'
test3 = '/sup/policy/json/policycomeback.do'
test4 = '/sup/policy/json/policystartup.do'
test5 = '/sup/policy/json/policymarket.do'
test6 = '/sup/policy/json/policygrnty.do'

# 정책자금  https://www.sbiz.or.kr/sup/policy/json/policyfound.do
# 성장지원  https://www.sbiz.or.kr/sup/policy/json/policygrow.do
# 재기지원  https://www.sbiz.or.kr/sup/policy/json/policycomeback.do
# 창업지원  https://www.sbiz.or.kr/sup/policy/json/policystartup.do
# 전통시장활성화   https://www.sbiz.or.kr/sup/policy/json/policymarket.do
# 보증지원  https://www.sbiz.or.kr/sup/policy/json/policygrnty.do

if __name__ == "__main__":
    logging.debug("crawl_sup_api.py 시작")
    logging.info(requests.get(base_url+test1).json())
    logging.info(requests.get(base_url+test2).json())
    logging.info(requests.get(base_url+test3).json())
    logging.info(requests.get(base_url+test4).json())
    logging.info(requests.get(base_url+test5).json())
    logging.info(requests.get(base_url+test6).json())
    logging.debug("crawl_sup_api.py 종료")
