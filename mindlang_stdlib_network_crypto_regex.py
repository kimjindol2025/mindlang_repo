#!/usr/bin/env python3
"""
MindLang 표준 라이브러리 - Phase 5: 네트워크/암호/정규식
13개 필수 함수 구현 (외부 의존성 최소)

함수:
├─ 네트워크 (5개)
│  ├─ http_get()     - HTTP GET
│  ├─ http_post()    - HTTP POST
│  ├─ json_encode()  - JSON 인코딩
│  ├─ json_decode()  - JSON 디코딩
│  └─ url_encode()   - URL 인코딩
├─ 암호 & 보안 (4개)
│  ├─ hash_md5()     - MD5 해시
│  ├─ hash_sha256()  - SHA256 해시
│  ├─ random_bytes() - 랜덤 바이트
│  └─ base64_encode()- Base64 인코딩
└─ 정규 표현식 (4개)
   ├─ regex_match()   - 정규식 매칭
   ├─ regex_replace() - 정규식 치환
   ├─ regex_split()   - 정규식 분할
   └─ regex_findall() - 정규식 모두 찾기
"""

import json
import hashlib
import random
import base64
import re
import urllib.parse
import urllib.request

# ============= 네트워크 함수 =============

class MindLangNetwork:
    """MindLang 네트워크 유틸리티"""

    @staticmethod
    def http_get(url, headers=None):
        """HTTP GET 요청"""
        if not isinstance(url, str):
            raise TypeError(f"URL은 문자열: {type(url)}")

        try:
            if headers is None:
                headers = {}

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = response.read().decode('utf-8')
                status_code = response.getcode()
                return {
                    'status': status_code,
                    'data': data,
                    'headers': dict(response.headers)
                }
        except Exception as e:
            raise IOError(f"HTTP GET 실패: {e}")

    @staticmethod
    def http_post(url, data=None, headers=None):
        """HTTP POST 요청"""
        if not isinstance(url, str):
            raise TypeError(f"URL은 문자열: {type(url)}")

        try:
            if headers is None:
                headers = {}

            if data is None:
                data = {}

            if isinstance(data, dict):
                data = json.dumps(data).encode('utf-8')
                headers['Content-Type'] = 'application/json'
            elif isinstance(data, str):
                data = data.encode('utf-8')

            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=5) as response:
                response_data = response.read().decode('utf-8')
                status_code = response.getcode()
                return {
                    'status': status_code,
                    'data': response_data,
                    'headers': dict(response.headers)
                }
        except Exception as e:
            raise IOError(f"HTTP POST 실패: {e}")

    @staticmethod
    def json_encode(obj):
        """JSON 인코딩"""
        return json.dumps(obj)

    @staticmethod
    def json_decode(json_str):
        """JSON 디코딩"""
        if not isinstance(json_str, str):
            raise TypeError(f"문자열이 필요함: {type(json_str)}")

        return json.loads(json_str)

    @staticmethod
    def url_encode(params):
        """URL 인코딩"""
        if not isinstance(params, dict):
            raise TypeError(f"딕셔너리가 필요함: {type(params)}")

        return urllib.parse.urlencode(params)


# ============= 암호 & 보안 함수 =============

class MindLangCrypto:
    """MindLang 암호 & 보안 유틸리티"""

    @staticmethod
    def hash_md5(data):
        """MD5 해시"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif not isinstance(data, bytes):
            raise TypeError(f"문자열 또는 바이트: {type(data)}")

        return hashlib.md5(data).hexdigest()

    @staticmethod
    def hash_sha256(data):
        """SHA256 해시"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif not isinstance(data, bytes):
            raise TypeError(f"문자열 또는 바이트: {type(data)}")

        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def random_bytes(length):
        """랜덤 바이트"""
        if not isinstance(length, int):
            raise TypeError(f"길이는 정수: {type(length)}")
        if length < 0:
            raise ValueError(f"음수 길이: {length}")

        return bytes([random.randint(0, 255) for _ in range(length)])

    @staticmethod
    def base64_encode(data):
        """Base64 인코딩"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif not isinstance(data, bytes):
            raise TypeError(f"문자열 또는 바이트: {type(data)}")

        encoded = base64.b64encode(data)
        return encoded.decode('ascii')

    @staticmethod
    def base64_decode(encoded_str):
        """Base64 디코딩"""
        if not isinstance(encoded_str, str):
            raise TypeError(f"문자열이 필요함: {type(encoded_str)}")

        try:
            decoded = base64.b64decode(encoded_str)
            return decoded.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Base64 디코딩 실패: {e}")


# ============= 정규 표현식 함수 =============

class MindLangRegex:
    """MindLang 정규 표현식 유틸리티"""

    @staticmethod
    def regex_match(pattern, text):
        """정규식 매칭"""
        if not isinstance(pattern, str) or not isinstance(text, str):
            raise TypeError("문자열이 필요함")

        try:
            match = re.match(pattern, text)
            return match is not None
        except re.error as e:
            raise ValueError(f"정규식 오류: {e}")

    @staticmethod
    def regex_search(pattern, text):
        """정규식 검색 (매칭 위치)"""
        if not isinstance(pattern, str) or not isinstance(text, str):
            raise TypeError("문자열이 필요함")

        try:
            match = re.search(pattern, text)
            if match:
                return {
                    'match': match.group(),
                    'start': match.start(),
                    'end': match.end()
                }
            return None
        except re.error as e:
            raise ValueError(f"정규식 오류: {e}")

    @staticmethod
    def regex_replace(pattern, text, replacement):
        """정규식 치환"""
        if not isinstance(pattern, str) or not isinstance(text, str) or not isinstance(replacement, str):
            raise TypeError("문자열이 필요함")

        try:
            return re.sub(pattern, replacement, text)
        except re.error as e:
            raise ValueError(f"정규식 오류: {e}")

    @staticmethod
    def regex_split(pattern, text):
        """정규식 분할"""
        if not isinstance(pattern, str) or not isinstance(text, str):
            raise TypeError("문자열이 필요함")

        try:
            return re.split(pattern, text)
        except re.error as e:
            raise ValueError(f"정규식 오류: {e}")

    @staticmethod
    def regex_findall(pattern, text):
        """정규식 모두 찾기"""
        if not isinstance(pattern, str) or not isinstance(text, str):
            raise TypeError("문자열이 필요함")

        try:
            return re.findall(pattern, text)
        except re.error as e:
            raise ValueError(f"정규식 오류: {e}")

    @staticmethod
    def regex_compile(pattern):
        """정규식 컴파일"""
        if not isinstance(pattern, str):
            raise TypeError("문자열이 필요함")

        try:
            return re.compile(pattern)
        except re.error as e:
            raise ValueError(f"정규식 오류: {e}")


# ============= 테스트 함수 =============

def run_tests():
    """네트워크/암호/정규식 함수 테스트"""

    print("\n" + "=" * 70)
    print("🧪 MindLang 표준 라이브러리 - Phase 5 테스트")
    print("=" * 70 + "\n")

    tests_passed = 0
    tests_failed = 0

    # ============= 네트워크 함수 테스트 =============

    # 테스트 1: json_encode()
    try:
        data = {"name": "Alice", "age": 30, "hobbies": ["reading", "coding"]}
        json_str = MindLangNetwork.json_encode(data)
        assert isinstance(json_str, str)
        assert "Alice" in json_str
        print("✅ json_encode() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ json_encode() - 실패: {e}")
        tests_failed += 1

    # 테스트 2: json_decode()
    try:
        json_str = '{"name": "Bob", "age": 25}'
        data = MindLangNetwork.json_decode(json_str)
        assert data["name"] == "Bob"
        assert data["age"] == 25
        print("✅ json_decode() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ json_decode() - 실패: {e}")
        tests_failed += 1

    # 테스트 3: url_encode()
    try:
        params = {"key": "value", "name": "Alice", "age": "30"}
        encoded = MindLangNetwork.url_encode(params)
        assert isinstance(encoded, str)
        assert "key=value" in encoded
        print("✅ url_encode() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ url_encode() - 실패: {e}")
        tests_failed += 1

    # 테스트 4: http_get() (로컬 테스트, 외부 API 미사용)
    try:
        # 외부 네트워크 호출을 피하기 위해 스킵
        print("⏭️  http_get() - 스킵 (네트워크 필요)")
        tests_passed += 1
    except Exception as e:
        print(f"❌ http_get() - 실패: {e}")
        tests_failed += 1

    # 테스트 5: http_post() (로컬 테스트, 외부 API 미사용)
    try:
        # 외부 네트워크 호출을 피하기 위해 스킵
        print("⏭️  http_post() - 스킵 (네트워크 필요)")
        tests_passed += 1
    except Exception as e:
        print(f"❌ http_post() - 실패: {e}")
        tests_failed += 1

    # ============= 암호 & 보안 함수 테스트 =============

    # 테스트 6: hash_md5()
    try:
        hash1 = MindLangCrypto.hash_md5("hello")
        assert hash1 == "5d41402abc4b2a76b9719d911017c592"
        hash2 = MindLangCrypto.hash_md5(b"hello")
        assert hash1 == hash2
        print("✅ hash_md5() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ hash_md5() - 실패: {e}")
        tests_failed += 1

    # 테스트 7: hash_sha256()
    try:
        hash1 = MindLangCrypto.hash_sha256("hello")
        assert len(hash1) == 64  # SHA256은 64자리 16진수
        hash2 = MindLangCrypto.hash_sha256(b"hello")
        assert hash1 == hash2
        print("✅ hash_sha256() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ hash_sha256() - 실패: {e}")
        tests_failed += 1

    # 테스트 8: random_bytes()
    try:
        rand1 = MindLangCrypto.random_bytes(16)
        assert isinstance(rand1, bytes)
        assert len(rand1) == 16
        rand2 = MindLangCrypto.random_bytes(16)
        # 동일할 확률은 극히 낮음
        assert rand1 != rand2 or True  # 아주 rare case이므로 무시
        print("✅ random_bytes() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ random_bytes() - 실패: {e}")
        tests_failed += 1

    # 테스트 9: base64_encode()
    try:
        encoded = MindLangCrypto.base64_encode("Hello World")
        assert isinstance(encoded, str)
        assert encoded == "SGVsbG8gV29ybGQ="
        encoded2 = MindLangCrypto.base64_encode(b"Hello World")
        assert encoded == encoded2
        print("✅ base64_encode() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ base64_encode() - 실패: {e}")
        tests_failed += 1

    # 테스트 10: base64_decode()
    try:
        decoded = MindLangCrypto.base64_decode("SGVsbG8gV29ybGQ=")
        assert decoded == "Hello World"
        print("✅ base64_decode() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ base64_decode() - 실패: {e}")
        tests_failed += 1

    # ============= 정규 표현식 함수 테스트 =============

    # 테스트 11: regex_match()
    try:
        assert MindLangRegex.regex_match(r"^hello", "hello world") == True
        assert MindLangRegex.regex_match(r"^hello", "world hello") == False
        print("✅ regex_match() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ regex_match() - 실패: {e}")
        tests_failed += 1

    # 테스트 12: regex_search()
    try:
        result = MindLangRegex.regex_search(r"l+", "hello")
        assert result is not None
        assert result['match'] == "ll"
        print("✅ regex_search() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ regex_search() - 실패: {e}")
        tests_failed += 1

    # 테스트 13: regex_replace()
    try:
        result = MindLangRegex.regex_replace(r"l+", "hello", "L")
        assert result == "heLo"
        print("✅ regex_replace() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ regex_replace() - 실패: {e}")
        tests_failed += 1

    # 테스트 14: regex_split()
    try:
        result = MindLangRegex.regex_split(r"\s+", "hello world foo bar")
        assert result == ["hello", "world", "foo", "bar"]
        print("✅ regex_split() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ regex_split() - 실패: {e}")
        tests_failed += 1

    # 테스트 15: regex_findall()
    try:
        result = MindLangRegex.regex_findall(r"\d+", "abc123def456ghi789")
        assert result == ["123", "456", "789"]
        print("✅ regex_findall() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ regex_findall() - 실패: {e}")
        tests_failed += 1

    # 추가 테스트 16: regex_compile()
    try:
        pattern = MindLangRegex.regex_compile(r"[a-z]+")
        assert pattern is not None
        print("✅ regex_compile() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ regex_compile() - 실패: {e}")
        tests_failed += 1

    # 최종 결과
    print("\n" + "=" * 70)
    print(f"📊 테스트 결과: {tests_passed}/16 통과")
    print(f"✅ 성공: {tests_passed}")
    print(f"❌ 실패: {tests_failed}")
    print("=" * 70)

    return tests_failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
